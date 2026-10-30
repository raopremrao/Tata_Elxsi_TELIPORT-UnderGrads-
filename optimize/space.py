"""Design Space Definition and Enumeration for Q-Pack.

Defines discrete variables, bounds, configuration filtering, and fixed baseline designs.
"""

from __future__ import annotations
import itertools
from typing import List, Dict, Tuple, Optional
from core.schemas import PackDesign, CoolingType, BMSTier, ChemistryEnum
from core.data_loader import load_cells


# Discrete variable search spaces
COOLING_OPTIONS = [CoolingType.PASSIVE, CoolingType.FORCED_AIR, CoolingType.COLD_PLATE]
BMS_TIERS = [BMSTier.BASIC, BMSTier.STANDARD, BMSTier.ADVANCED]
SPACINGS_MM = [1.0, 2.0, 4.0]
NP_OPTIONS = [1, 2, 3, 4, 5, 6, 7, 8]


def get_series_range_for_cell(chemistry: ChemistryEnum) -> List[int]:
    """Return series counts keeping nominal voltage roughly between 44V and 56V."""
    if chemistry == ChemistryEnum.LFP:
        # 3.2V nominal -> 14S (44.8V) to 17S (54.4V)
        return [14, 15, 16, 17]
    else:
        # 3.6V / 3.63V nominal -> 12S (43.5V) to 15S (54.5V)
        return [12, 13, 14, 15]


def enumerate_design_space() -> Tuple[List[PackDesign], List[PackDesign]]:
    """Enumerate all discrete design configurations.

    Returns:
        (feasible_designs, infeasible_designs)
    """
    cells = load_cells()
    feasible = []
    infeasible = []

    for cell_id, cell in cells.items():
        ns_range = get_series_range_for_cell(cell.chemistry)
        for ns, np_val, cooling, bms, spacing in itertools.product(
            ns_range, NP_OPTIONS, COOLING_OPTIONS, BMS_TIERS, SPACINGS_MM
        ):
            design = PackDesign(
                name=f"{cell_id}_{ns}S{np_val}P_{cooling.value}_{bms.value}",
                cell_id=cell_id,
                ns=ns,
                np=np_val,
                cooling=cooling,
                bms_tier=bms,
                cell_spacing_mm=spacing,
            )

            # Quick structural feasibility filter
            v_max = ns * cell.max_voltage_V
            # Must not exceed 60 V DC extra-low voltage hard limit
            if v_max > 60.0:
                infeasible.append(design)
                continue

            # Must not have severe cell overcurrent at peak (10s pulse limit)
            # Minimum nominal voltage ~ 44V -> 6000W / 44V ~ 136A -> i_cell = 136 / np
            i_cell_est = 136.0 / np_val
            if i_cell_est > (cell.max_pulse_discharge_A * 1.25):
                infeasible.append(design)
                continue

            feasible.append(design)

    return feasible, infeasible


def get_baseline_designs() -> Dict[str, PackDesign]:
    """Return fixed, reproducible named baseline designs (Section 7)."""
    return {
        "Design 0": PackDesign(
            name="Design 0 (Starting Baseline)",
            cell_id="panasonic_ncr18650b",
            ns=13,
            np=2,
            cooling=CoolingType.PASSIVE,
            bms_tier=BMSTier.BASIC,
            cell_spacing_mm=1.0,
        ),
        "Design A": PackDesign(
            name="Design A (Engineer's Choice)",
            cell_id="samsung_inr21700_50e",
            ns=14,
            np=4,
            cooling=CoolingType.FORCED_AIR,
            bms_tier=BMSTier.STANDARD,
            cell_spacing_mm=2.0,
        ),
        "Design B": PackDesign(
            name="Design B (LFP Safety-First)",
            cell_id="generic_lfp_32700",
            ns=15,
            np=3,
            cooling=CoolingType.FORCED_AIR,
            bms_tier=BMSTier.STANDARD,
            cell_spacing_mm=2.0,
        ),
    }

