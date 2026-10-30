"""Battery Ageing Subsystem Model for Q-Pack.

NOTE: This is a semi-empirical engineering surrogate model calibrated to cell
reference cycle life, NOT a multi-physics electrochemical degradation model.
Labeled as surrogate per Section 6 honesty requirements.
"""

from __future__ import annotations
import numpy as np
from typing import Dict
from core.schemas import Cell, PackDesign


def estimate_cycle_life(
    cell: Cell,
    design: PackDesign,
    mean_operating_temp_C: float = 38.0,
    mean_discharge_power_W: float = 2074.0,
    arrhenius_ea_over_r: float = 4500.0, # Assumption A-12
    c_rate_exponent: float = 0.65,
) -> Dict[str, any]:
    """Estimate pack cycle life (cycles to 80% capacity retention).

    Uses Arrhenius temperature acceleration and C-rate severity scaling.
    """
    t_ref_k = 298.15  # 25 C
    t_oper_k = mean_operating_temp_C + 273.15

    # Arrhenius acceleration factor (Assumption A-12)
    # Higher temperature accelerates SEI growth
    arrhenius_factor = float(np.exp(arrhenius_ea_over_r * (1.0 / t_ref_k - 1.0 / t_oper_k)))
    arrhenius_factor = float(np.clip(arrhenius_factor, 0.70, 3.50))

    # Mean C-rate during operation
    pack_v_nom = design.ns * cell.nominal_voltage_V
    mean_current_A = mean_discharge_power_W / max(30.0, pack_v_nom)
    pack_capacity_Ah = design.np * cell.capacity_Ah
    c_rate = mean_current_A / max(1.0, pack_capacity_Ah)

    c_rate_ref = 0.50
    c_rate_factor = float((c_rate / c_rate_ref) ** c_rate_exponent)
    c_rate_factor = float(np.clip(c_rate_factor, 0.80, 2.50))

    total_degradation_multiplier = arrhenius_factor * c_rate_factor
    estimated_cycles = int(np.clip(cell.cycle_life_ref / total_degradation_multiplier, 150, 4000))

    return {
        "estimated_cycle_life": estimated_cycles,
        "arrhenius_acceleration_factor": round(arrhenius_factor, 2),
        "c_rate_severity_factor": round(c_rate_factor, 2),
        "mean_c_rate": round(c_rate, 2),
        "is_surrogate": True,
    }

