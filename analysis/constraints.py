"""Requirements Compliance Evaluator for PackForge.

Checks simulation metrics against R-01 through R-12, returning margins and pass/fail states.
"""

from __future__ import annotations
import math
from typing import Dict, Any
from core.schemas import RequirementStatus, Cell, PackDesign, Scenario, BMSTier


BMS_SPECS = {
    BMSTier.BASIC: {"voltage_taps": 16, "thermistors": 2, "max_cont_A": 40.0},
    BMSTier.STANDARD: {"voltage_taps": 20, "thermistors": 4, "max_cont_A": 80.0},
    BMSTier.ADVANCED: {"voltage_taps": 24, "thermistors": 8, "max_cont_A": 120.0},
}


def evaluate_requirements(
    cell: Cell,
    design: PackDesign,
    scenario: Scenario,
    metrics: Dict[str, Any],
) -> Dict[str, RequirementStatus]:
    """Evaluate all 12 system requirements."""
    statuses = {}

    # R-01: Nominal pack voltage between 46 V and 54 V
    v_nom = metrics["nominal_voltage_V"]
    r01_pass = 46.0 <= v_nom <= 54.0
    r01_margin = min(v_nom - 46.0, 54.0 - v_nom)
    statuses["R-01"] = RequirementStatus(
        req_id="R-01",
        passed=r01_pass,
        actual_value=v_nom,
        target_value=48.0,
        margin=round(r01_margin, 2),
        unit="V",
        rationale=f"V_nom = {v_nom:.1f} V (Target: 46.0 - 54.0 V)",
    )

    # R-02: Maximum pack voltage <= 60 V DC
    v_max = metrics["max_voltage_V"]
    r02_pass = v_max <= 60.0
    statuses["R-02"] = RequirementStatus(
        req_id="R-02",
        passed=r02_pass,
        actual_value=v_max,
        target_value=60.0,
        margin=round(60.0 - v_max, 2),
        unit="V",
        rationale=f"V_max = {v_max:.1f} V (Extra-low voltage limit <= 60 V)",
    )

    # R-03: Usable energy >= 2.0 kWh (2000 Wh)
    e_usable = metrics["usable_energy_Wh"]
    r03_pass = e_usable >= 2000.0
    statuses["R-03"] = RequirementStatus(
        req_id="R-03",
        passed=r03_pass,
        actual_value=e_usable,
        target_value=2000.0,
        margin=round(e_usable - 2000.0, 1),
        unit="Wh",
        rationale=f"Usable energy = {e_usable:.1f} Wh (Target >= 2000 Wh)",
    )

    # R-04: Discharge power: 6 kW peak for 10 s, 2.5 kW cont
    i_cell_peak = metrics["max_cell_current_peak_A"]
    r04_pass = i_cell_peak <= cell.max_pulse_discharge_A
    statuses["R-04"] = RequirementStatus(
        req_id="R-04",
        passed=r04_pass,
        actual_value=i_cell_peak,
        target_value=cell.max_pulse_discharge_A,
        margin=round(cell.max_pulse_discharge_A - i_cell_peak, 2),
        unit="A",
        rationale=f"Cell peak current = {i_cell_peak:.1f} A (Limit: {cell.max_pulse_discharge_A:.1f} A)",
    )

    # R-05: Cell temperature <= 45 C
    t_peak = metrics["peak_temp_C"]
    r05_pass = t_peak <= 45.0
    statuses["R-05"] = RequirementStatus(
        req_id="R-05",
        passed=r05_pass,
        actual_value=t_peak,
        target_value=45.0,
        margin=round(45.0 - t_peak, 2),
        unit="C",
        rationale=f"Peak cell temp = {t_peak:.1f} C (Target <= 45.0 C)",
    )

    # R-06: Charge from 10% to 80% SoC in <= 90 min
    t_chg = metrics["charge_time_min"]
    r06_pass = t_chg <= 90.0
    statuses["R-06"] = RequirementStatus(
        req_id="R-06",
        passed=r06_pass,
        actual_value=t_chg,
        target_value=90.0,
        margin=round(90.0 - t_chg, 1),
        unit="min",
        rationale=f"Charge time = {t_chg:.1f} min (Target <= 90.0 min)",
    )

    # R-07: Mass <= 18 kg, Volume <= 22 L
    mass = metrics["pack_mass_kg"]
    vol = metrics["pack_volume_L"]
    r07_pass = (mass <= scenario.max_mass_kg) and (vol <= scenario.max_volume_L)
    statuses["R-07"] = RequirementStatus(
        req_id="R-07",
        passed=r07_pass,
        actual_value=mass,
        target_value=scenario.max_mass_kg,
        margin=round(scenario.max_mass_kg - mass, 2),
        unit="kg",
        rationale=f"Mass = {mass:.1f} kg, Volume = {vol:.1f} L (Limits: 18 kg, 22 L)",
    )

    # R-08: BOM Cost <= budget (default $450)
    cost = metrics["bom_cost_USD"]
    r08_pass = cost <= scenario.cost_budget_USD
    statuses["R-08"] = RequirementStatus(
        req_id="R-08",
        passed=r08_pass,
        actual_value=cost,
        target_value=scenario.cost_budget_USD,
        margin=round(scenario.cost_budget_USD - cost, 2),
        unit="USD",
        rationale=f"BOM Cost = ${cost:.2f} (Budget <= ${scenario.cost_budget_USD:.2f})",
    )

    # R-09: Cycle life >= 800 cycles
    cycles = metrics["estimated_cycle_life"]
    r09_pass = cycles >= 800
    statuses["R-09"] = RequirementStatus(
        req_id="R-09",
        passed=r09_pass,
        actual_value=float(cycles),
        target_value=800.0,
        margin=float(cycles - 800),
        unit="cycles",
        rationale=f"Cycle life = {cycles} cycles (Target >= 800 cycles)",
    )

    # R-10: No single cell exceeds continuous or pulse limits
    i_cell_cont = metrics["max_cell_current_cont_A"]
    r10_pass = (i_cell_cont <= cell.max_continuous_discharge_A) and (i_cell_peak <= cell.max_pulse_discharge_A)
    statuses["R-10"] = RequirementStatus(
        req_id="R-10",
        passed=r10_pass,
        actual_value=i_cell_cont,
        target_value=cell.max_continuous_discharge_A,
        margin=round(cell.max_continuous_discharge_A - i_cell_cont, 2),
        unit="A",
        rationale=f"Continuous cell current {i_cell_cont:.1f} A <= {cell.max_continuous_discharge_A:.1f} A",
    )

    # R-11: Sensing: >= 1 tap per parallel group, >= 1 thermistor per 6 groups
    bms_info = BMS_SPECS.get(design.bms_tier, BMS_SPECS[BMSTier.BASIC])
    req_thermistors = math.ceil(design.ns / 6.0)
    r11_pass = (bms_info["voltage_taps"] >= design.ns) and (bms_info["thermistors"] >= req_thermistors)
    statuses["R-11"] = RequirementStatus(
        req_id="R-11",
        passed=r11_pass,
        actual_value=float(bms_info["thermistors"]),
        target_value=float(req_thermistors),
        margin=float(bms_info["thermistors"] - req_thermistors),
        unit="channels",
        rationale=f"BMS thermistors: {bms_info['thermistors']}/{req_thermistors}, V-taps: {bms_info['voltage_taps']}/{design.ns}",
    )

    # R-12: Protection thresholds: BMS max current >= pack continuous current
    i_cont_pack = metrics["cont_current_A"]
    r12_pass = bms_info["max_cont_A"] >= i_cont_pack
    statuses["R-12"] = RequirementStatus(
        req_id="R-12",
        passed=r12_pass,
        actual_value=bms_info["max_cont_A"],
        target_value=i_cont_pack,
        margin=round(bms_info["max_cont_A"] - i_cont_pack, 1),
        unit="A",
        rationale=f"BMS rating {bms_info['max_cont_A']} A >= {i_cont_pack:.1f} A pack continuous",
    )

    return statuses

