"""Unified Multi-Disciplinary Simulation Evaluator for Q-Pack.

Single pure entry point:
    evaluate(design: PackDesign, scenario: Optional[Scenario] = None, fast: bool = False) -> EvaluationResult

Evaluates electrical, thermal lumped IVP, mechanical, charging, cost, ageing,
Monte Carlo cell variation, requirement constraints, and conflict rules.
"""

from __future__ import annotations
import hashlib
import time
from functools import lru_cache
from typing import Dict, Optional, Tuple, Any

import numpy as np
import pandas as pd

from core.schemas import (
    Cell,
    PackDesign,
    Scenario,
    EvaluationResult,
    RequirementStatus,
    Finding,
)
from core.data_loader import load_cells, load_drive_cycle
from models.electrical import calculate_electrical_properties, simulate_drive_cycle_discharge
from models.thermal import simulate_pack_thermal
from models.mechanical import calculate_mechanical_properties
from models.cost import calculate_bom_cost
from models.charging import calculate_charge_time
from models.ageing import estimate_cycle_life
from models.variation import simulate_cell_variation
from analysis.constraints import evaluate_requirements
from analysis.conflicts import detect_conflicts


MODEL_VERSION = "Q-Pack-v1.0.0"
MODEL_HASH = hashlib.sha256(MODEL_VERSION.encode()).hexdigest()[:12]

# Cache dictionary for fast evaluations during optimization
_EVAL_CACHE: Dict[Tuple[str, int, int, str, str, float, bool], EvaluationResult] = {}


def evaluate(
    design: PackDesign,
    scenario: Optional[Scenario] = None,
    fast: bool = False,
    cell: Optional[Cell] = None,
) -> EvaluationResult:
    """Evaluate a battery pack design across all engineering disciplines."""
    t_start = time.perf_counter()

    if scenario is None:
        scenario = Scenario()

    cache_key = (
        design.cell_id,
        design.ns,
        design.np,
        design.cooling.value,
        design.bms_tier.value,
        float(design.cell_spacing_mm),
        fast,
    )
    if cache_key in _EVAL_CACHE:
        return _EVAL_CACHE[cache_key]

    if cell is None:
        cells = load_cells()
        cell = cells[design.cell_id]

    # 1. Electrical static calculations
    elec = calculate_electrical_properties(cell, design)

    # 2. Drive cycle power profile simulation
    if fast:
        # Fast analytic approximation for usable energy and heat
        # Base energy = total Wh * 0.93 depth of discharge * IR loss factor
        r_pack_ohm = elec["pack_resistance_mOhm"] / 1000.0
        v_nom = elec["nominal_voltage_V"]
        ir_loss = min(0.15, (2074.0 / max(30.0, v_nom)) * r_pack_ohm / v_nom)
        usable_energy_Wh = round(elec["total_energy_Wh"] * 0.93 * (1.0 - ir_loss), 1)

        # Average heat during drive cycle (mean power ~ 2074 W)
        i_mean = 2074.0 / max(30.0, v_nom)
        heat_mean_W = (i_mean ** 2) * r_pack_ohm
        heat_profile = np.full(10, heat_mean_W)
        time_arr = np.linspace(0, 1800, 10)
        time_series = None
    else:
        drive_df = load_drive_cycle()
        power_profile = drive_df["power_W"].values
        time_arr = drive_df["time_s"].values
        usable_energy_Wh, discharge_ts = simulate_drive_cycle_discharge(
            cell=cell,
            design=design,
            power_profile_W=power_profile,
            ambient_temp_C=scenario.ambient_temp_C,
        )
        heat_profile = discharge_ts["heat_W"]
        time_series = {
            "time_s": time_arr[: len(discharge_ts["v_term_V"])].tolist(),
            "v_term_V": discharge_ts["v_term_V"].tolist(),
            "i_pack_A": discharge_ts["i_pack_A"].tolist(),
            "soc": discharge_ts["soc"].tolist(),
            "heat_W": discharge_ts["heat_W"].tolist(),
        }

    # 3. Thermal simulation
    thermal = simulate_pack_thermal(
        cell=cell,
        design=design,
        heat_profile_W=heat_profile,
        time_s=time_arr,
        ambient_temp_C=scenario.ambient_temp_C,
        fast=fast,
    )
    if not fast and time_series is not None and thermal.get("temp_series") is not None:
        time_series["temp_C"] = thermal["temp_series"]

    # 4. Mechanical & Packaging
    mech = calculate_mechanical_properties(cell, design)

    # 5. Cost BOM
    enclosure_mass_kg = mech["mass_breakdown_kg"]["enclosure"]
    cost = calculate_bom_cost(cell, design, enclosure_mass_kg=enclosure_mass_kg)

    # 6. Fast Charging
    chg = calculate_charge_time(
        cell=cell,
        design=design,
        peak_operating_temp_C=thermal["peak_temp_C"],
    )

    # 7. Ageing Surrogate
    age = estimate_cycle_life(
        cell=cell,
        design=design,
        mean_operating_temp_C=thermal.get("mean_temp_C", thermal["peak_temp_C"]),
    )

    # 8. Monte Carlo cell-to-cell variation
    mc_iters = 50 if fast else scenario.mc_iterations
    var = simulate_cell_variation(
        cell=cell,
        design=design,
        n_iterations=mc_iters,
        seed=scenario.seed,
        base_peak_temp_C=thermal["peak_temp_C"],
    )

    # Compile metric dictionary for constraints & rules
    metrics: Dict[str, Any] = {
        **elec,
        "usable_energy_Wh": usable_energy_Wh,
        **thermal,
        **mech,
        **cost,
        **chg,
        **age,
        **var,
    }

    # 9. Requirement compliance evaluation
    req_statuses = evaluate_requirements(cell, design, scenario, metrics)

    # 10. Conflict detection engine
    findings = detect_conflicts(cell, design, scenario, metrics)

    t_end = time.perf_counter()
    eval_time_ms = round((t_end - t_start) * 1000.0, 2)

    assumption_ids = [
        "A-01", "A-02", "A-03", "A-04",
        "A-05a" if design.cooling.value == "passive" else ("A-05b" if design.cooling.value == "forced_air" else "A-05c"),
        "A-06", "A-07", "A-08", "A-09", "A-10", "A-11", "A-12", "A-13", "A-14", "A-15",
    ]

    result = EvaluationResult(
        design=design,
        nominal_voltage_V=elec["nominal_voltage_V"],
        max_voltage_V=elec["max_voltage_V"],
        cutoff_voltage_V=elec["cutoff_voltage_V"],
        total_capacity_Ah=elec["total_capacity_Ah"],
        total_energy_Wh=elec["total_energy_Wh"],
        usable_energy_Wh=usable_energy_Wh,
        pack_resistance_mOhm=elec["pack_resistance_mOhm"],
        peak_current_A=elec["peak_current_A"],
        cont_current_A=elec["cont_current_A"],
        max_cell_current_peak_A=elec["max_cell_current_peak_A"],
        max_cell_current_cont_A=elec["max_cell_current_cont_A"],
        peak_temp_C=thermal["peak_temp_C"],
        temp_gradient_C=thermal["temp_gradient_C"],
        charge_time_min=chg["charge_time_min"],
        pack_mass_kg=mech["pack_mass_kg"],
        pack_volume_L=mech["pack_volume_L"],
        dimensions_L_W_H_mm=mech["dimensions_L_W_H_mm"],
        bom_cost_USD=cost["bom_cost_USD"],
        itemized_cost_USD=cost["itemized_cost_USD"],
        estimated_cycle_life=age["estimated_cycle_life"],
        mc_usable_energy_P5_Wh=var["mc_usable_energy_P5_Wh"],
        mc_usable_energy_P50_Wh=var["mc_usable_energy_P50_Wh"],
        mc_usable_energy_P95_Wh=var["mc_usable_energy_P95_Wh"],
        mc_temp_P95_C=var["mc_temp_P95_C"],
        mc_violation_probability=var["mc_violation_probability"],
        requirements=req_statuses,
        findings=findings,
        assumption_ids_used=assumption_ids,
        time_series=time_series,
        eval_time_ms=eval_time_ms,
        model_version_hash=MODEL_HASH,
    )

    _EVAL_CACHE[cache_key] = result
    return result

