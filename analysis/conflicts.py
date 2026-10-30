"""Conflict Detection Rule Engine for Q-Pack.

Implements multidisciplinary rule checks (Section 10) identifying interface
mismatches, safety violations, sensing gaps, and data provenance issues.
"""

from __future__ import annotations
import math
from typing import Dict, List, Any
from core.schemas import Finding, Cell, PackDesign, Scenario, BMSTier, CoolingType


def detect_conflicts(
    cell: Cell,
    design: PackDesign,
    scenario: Scenario,
    metrics: Dict[str, Any],
) -> List[Finding]:
    """Run all conflict detection rules against simulated metrics."""
    findings: List[Finding] = []

    # RULE-01: Cell overcurrent at selected np
    i_cell_cont = metrics["max_cell_current_cont_A"]
    i_cell_peak = metrics["max_cell_current_peak_A"]
    if i_cell_cont > cell.max_continuous_discharge_A or i_cell_peak > cell.max_pulse_discharge_A:
        findings.append(Finding(
            id="RULE-01",
            severity="critical",
            subsystem="Electrical / Cell",
            title="Cell Overcurrent Exceeded",
            explanation=f"Cell continuous current ({i_cell_cont:.1f} A) or pulse ({i_cell_peak:.1f} A) exceeds cell datasheet ratings ({cell.max_continuous_discharge_A} A cont, {cell.max_pulse_discharge_A} A pulse).",
            suggested_fix="Increase parallel count (np) or switch to a high-discharge cell such as Samsung 40T.",
            linked_requirements=["R-04", "R-10"],
            linked_assumptions=[],
        ))

    # RULE-02: Extra-Low Voltage (ELV) safety boundary exceeded
    v_max = metrics["max_voltage_V"]
    if v_max > 60.0:
        findings.append(Finding(
            id="RULE-02",
            severity="critical",
            subsystem="Electrical / Safety",
            title="ELV 60V Safety Boundary Breached",
            explanation=f"Maximum pack voltage ({v_max:.1f} V) exceeds the 60 V DC extra-low voltage threshold, requiring high-voltage insulation and interlocks.",
            suggested_fix=f"Reduce series count (ns) from {design.ns} to stay strictly at or below 60.0 V.",
            linked_requirements=["R-02"],
            linked_assumptions=[],
        ))

    # RULE-03: BMS continuous current undersized
    i_cont_pack = metrics["cont_current_A"]
    bms_cont_limits = {BMSTier.BASIC: 40.0, BMSTier.STANDARD: 80.0, BMSTier.ADVANCED: 120.0}
    bms_limit = bms_cont_limits.get(design.bms_tier, 40.0)
    if i_cont_pack > bms_limit:
        findings.append(Finding(
            id="RULE-03",
            severity="critical",
            subsystem="BMS / Protection",
            title="BMS Continuous Current Rating Undersized",
            explanation=f"Pack continuous demand ({i_cont_pack:.1f} A) exceeds {design.bms_tier.value} BMS continuous rating ({bms_limit:.1f} A).",
            suggested_fix="Upgrade BMS tier to Standard (80A) or Advanced (120A).",
            linked_requirements=["R-12"],
            linked_assumptions=[],
        ))

    # RULE-04: Insufficient cooling capacity
    peak_temp = metrics["peak_temp_C"]
    if peak_temp > 45.0:
        findings.append(Finding(
            id="RULE-04",
            severity="warning" if peak_temp <= 60.0 else "critical",
            subsystem="Thermal / Cooling",
            title="Thermal Cooling Capacity Insufficient",
            explanation=f"Peak cell temperature reaches {peak_temp:.1f} C under reference drive cycle, exceeding the 45.0 C commuter reliability limit.",
            suggested_fix="Upgrade cooling from Passive to Forced Air or Cold Plate, or increase inter-cell spacing.",
            linked_requirements=["R-05"],
            linked_assumptions=["A-05a", "A-05b", "A-05c"],
        ))

    # RULE-05: Thermal derating during fast charge
    if metrics.get("is_thermally_derated", False) and metrics["charge_time_min"] > 90.0:
        findings.append(Finding(
            id="RULE-05",
            severity="warning",
            subsystem="Charging / Thermal",
            title="Thermal Derating Violates Fast Charge Target",
            explanation=f"Elevated pack temperature triggered thermal charge current derating, extending 10-80% charge time to {metrics['charge_time_min']:.1f} min (> 90 min).",
            suggested_fix="Improve pack heat dissipation or lower cell internal impedance.",
            linked_requirements=["R-06"],
            linked_assumptions=["A-07", "A-08"],
        ))

    # RULE-06: Sensing channel coverage gap
    bms_thermistors = {BMSTier.BASIC: 2, BMSTier.STANDARD: 4, BMSTier.ADVANCED: 8}.get(design.bms_tier, 2)
    bms_v_taps = {BMSTier.BASIC: 16, BMSTier.STANDARD: 20, BMSTier.ADVANCED: 24}.get(design.bms_tier, 16)
    req_thermistors = math.ceil(design.ns / 6.0)

    if bms_thermistors < req_thermistors or bms_v_taps < design.ns:
        findings.append(Finding(
            id="RULE-06",
            severity="critical",
            subsystem="BMS / Sensing",
            title="Inadequate BMS Sensing Channels",
            explanation=f"Selected BMS tier provides {bms_thermistors} thermistors (requires {req_thermistors} for 1 per 6s) and {bms_v_taps} taps (requires {design.ns}).",
            suggested_fix="Upgrade BMS tier to meet minimum safety sensing density (R-11).",
            linked_requirements=["R-11"],
            linked_assumptions=[],
        ))

    # RULE-07: Mass, Volume, or Budget overshoot
    mass = metrics["pack_mass_kg"]
    cost = metrics["bom_cost_USD"]
    if mass > scenario.max_mass_kg or cost > scenario.cost_budget_USD:
        reasons = []
        if mass > scenario.max_mass_kg:
            reasons.append(f"mass ({mass:.1f} kg > {scenario.max_mass_kg:.1f} kg)")
        if cost > scenario.cost_budget_USD:
            reasons.append(f"BOM cost (${cost:.2f} > ${scenario.cost_budget_USD:.2f})")
        findings.append(Finding(
            id="RULE-07",
            severity="warning",
            subsystem="Mechanical / Commercial",
            title="Packaging or Commercial Limit Exceeded",
            explanation=f"Pack design violates {' and '.join(reasons)}.",
            suggested_fix="Optimize cell selection (higher specific energy), reduce parallel count, or downgrade oversized cooling.",
            linked_requirements=["R-07", "R-08"],
            linked_assumptions=["A-09", "A-10"],
        ))

    # RULE-08: Monte Carlo variation bottleneck at P5
    p5_energy = metrics.get("mc_usable_energy_P5_Wh", 2000.0)
    if p5_energy < 2000.0 and metrics["usable_energy_Wh"] >= 2000.0:
        findings.append(Finding(
            id="RULE-08",
            severity="warning",
            subsystem="Reliability / Variation",
            title="Cell Variation Pushes P5 Energy Below Threshold",
            explanation=f"Nominal energy is {metrics['usable_energy_Wh']:.1f} Wh, but manufacturing spread drops P5 usable energy to {p5_energy:.1f} Wh (< 2.0 kWh).",
            suggested_fix="Increase parallel count (np) or add cell binning screening during module assembly.",
            linked_requirements=["R-03"],
            linked_assumptions=["A-13", "A-15"],
        ))

    # RULE-09: Incompatible thermal and ageing assumptions
    if peak_temp > 50.0:
        findings.append(Finding(
            id="RULE-09",
            severity="info",
            subsystem="Cross-Subsystem / Ageing",
            title="Severe Thermal Acceleration of Ageing",
            explanation=f"High pack operating temperature ({peak_temp:.1f} C) severely accelerates SEI layer degradation (Arrhenius factor > 2.0x).",
            suggested_fix="Upgrade cooling system to preserve cell cycle life.",
            linked_requirements=["R-05", "R-09"],
            linked_assumptions=["A-12"],
        ))

    # RULE-10: Unverified cell data provenance
    if not cell.verified:
        findings.append(Finding(
            id="RULE-10",
            severity="info",
            subsystem="Data Provenance",
            title="Unverified Cell Datasheet Parameters",
            explanation=f"Cell '{cell.model}' values are estimated or derived from unofficial sources (verified=False).",
            suggested_fix="Obtain official manufacturer specification sheet or complete lab cell cycler characterization.",
            linked_requirements=[],
            linked_assumptions=[],
        ))

    return findings

