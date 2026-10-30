"""Fast Charging Subsystem Model for Q-Pack.

Implements CC-CV charge timing estimation (10% to 80% SoC) with thermal derating
and cell maximum charge current limits.
"""

from __future__ import annotations
import numpy as np
from typing import Dict
from core.schemas import Cell, PackDesign, CoolingType


def calculate_charge_time(
    cell: Cell,
    design: PackDesign,
    peak_operating_temp_C: float = 40.0,
    cv_tail_tau_min: float = 18.0,            # Assumption A-07
    derating_threshold_C: float = 45.0,        # Assumption A-08
) -> Dict[str, any]:
    """Estimate 10% to 80% SoC charge time in minutes."""
    pack_capacity_Ah = design.np * cell.capacity_Ah

    # Max allowed pack charge current based on cell datasheet
    max_pack_charge_current_A = design.np * cell.max_charge_A

    # Thermal derating check: if operating temp exceeds threshold during charge,
    # derate allowed current by 10% per deg C above threshold down to 25% floor
    temp_excess = max(0.0, peak_operating_temp_C - derating_threshold_C)
    derating_factor = float(np.clip(1.0 - 0.10 * temp_excess, 0.25, 1.0))

    effective_charge_current_A = max_pack_charge_current_A * derating_factor

    # CC Phase covers 10% to 70% SoC (delta SoC = 0.60)
    delta_ah_cc = 0.60 * pack_capacity_Ah
    t_cc_min = (delta_ah_cc / max(1.0, effective_charge_current_A)) * 60.0

    # CV Phase covers 70% to 80% SoC (delta SoC = 0.10) with exponential current taper
    # Higher internal resistance prolongs the CV phase
    ir_penalty = 1.0 + (cell.internal_resistance_mOhm / 100.0)
    t_cv_min = cv_tail_tau_min * ir_penalty * (1.0 / derating_factor**0.5)

    total_charge_time_min = t_cc_min + t_cv_min

    return {
        "charge_time_min": round(total_charge_time_min, 1),
        "t_cc_min": round(t_cc_min, 1),
        "t_cv_min": round(t_cv_min, 1),
        "effective_charge_current_A": round(effective_charge_current_A, 2),
        "thermal_derating_factor": round(derating_factor, 2),
        "is_thermally_derated": derating_factor < 0.99,
    }

