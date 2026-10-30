"""Unit tests for mechanical, cost, charging, ageing, variation, and evaluate."""

from core.data_loader import load_cells
from core.schemas import PackDesign, CoolingType, BMSTier, Scenario
from models.mechanical import calculate_mechanical_properties
from models.cost import calculate_bom_cost
from models.charging import calculate_charge_time
from models.ageing import estimate_cycle_life
from models.variation import simulate_cell_variation
from models.evaluate import evaluate


def test_mechanical_and_cost():
    cells = load_cells()
    cell = cells["samsung_inr21700_50e"]
    design = PackDesign(cell_id=cell.id, ns=14, np=4, cooling=CoolingType.FORCED_AIR, bms_tier=BMSTier.STANDARD)

    mech = calculate_mechanical_properties(cell, design)
    assert 5.0 < mech["pack_mass_kg"] < 10.0
    assert 2.0 < mech["pack_volume_L"] < 12.0
    assert len(mech["dimensions_L_W_H_mm"]) == 3

    cost = calculate_bom_cost(cell, design, enclosure_mass_kg=mech["mass_breakdown_kg"]["enclosure"])
    assert cost["bom_cost_USD"] > 0
    assert "cells" in cost["itemized_cost_USD"]
    assert "bms" in cost["itemized_cost_USD"]
    assert "cooling" in cost["itemized_cost_USD"]


def test_charging_derating():
    cells = load_cells()
    cell = cells["samsung_inr21700_50e"]
    design = PackDesign(cell_id=cell.id, ns=14, np=4)

    # Moderate temperature: no derating
    chg_normal = calculate_charge_time(cell, design, peak_operating_temp_C=38.0)
    assert not chg_normal["is_thermally_derated"]

    # High temperature: derating triggered, charge time increases
    chg_hot = calculate_charge_time(cell, design, peak_operating_temp_C=52.0)
    assert chg_hot["is_thermally_derated"]
    assert chg_hot["charge_time_min"] > chg_normal["charge_time_min"]


def test_ageing_trend():
    cells = load_cells()
    cell = cells["samsung_inr21700_50e"]
    design = PackDesign(cell_id=cell.id, ns=14, np=4)

    # Operating at 25 C vs 50 C
    age_cool = estimate_cycle_life(cell, design, mean_operating_temp_C=25.0)
    age_hot = estimate_cycle_life(cell, design, mean_operating_temp_C=50.0)

    # Hot operation reduces cycle life
    assert age_cool["estimated_cycle_life"] > age_hot["estimated_cycle_life"]


def test_variation_statistics():
    cells = load_cells()
    cell = cells["samsung_inr21700_50e"]
    design = PackDesign(cell_id=cell.id, ns=14, np=4)

    var = simulate_cell_variation(cell, design, n_iterations=200, seed=42)
    p5 = var["mc_usable_energy_P5_Wh"]
    p50 = var["mc_usable_energy_P50_Wh"]
    p95 = var["mc_usable_energy_P95_Wh"]

    # Verify monotonic quantiles: P5 <= P50 <= P95
    assert p5 <= p50 <= p95
    assert 0.0 <= var["mc_violation_probability"] <= 1.0


def test_evaluate_fast_mode_speed_and_caching():
    cells = load_cells()
    cell = cells["samsung_inr21700_50e"]
    design = PackDesign(cell_id=cell.id, ns=14, np=4, cooling=CoolingType.FORCED_AIR)
    scenario = Scenario()

    # First run in fast mode
    res_fast = evaluate(design, scenario, fast=True, cell=cell)
    assert res_fast.eval_time_ms < 50.0  # Well within target
    assert res_fast.usable_energy_Wh > 800.0
    assert len(res_fast.requirements) == 12

    # High capacity design 14S8P meets 2.0 kWh requirement (R-03)
    design_2kwh = PackDesign(cell_id=cell.id, ns=14, np=8, cooling=CoolingType.FORCED_AIR)
    res_2kwh = evaluate(design_2kwh, scenario, fast=True, cell=cell)
    assert res_2kwh.usable_energy_Wh >= 1700.0

    # Second run should be instant (cached)
    res_cached = evaluate(design, scenario, fast=True, cell=cell)
    assert res_cached is res_fast
