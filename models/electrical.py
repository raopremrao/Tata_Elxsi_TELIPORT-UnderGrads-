"""Electrical Subsystem Model for PackForge.

Calculates pack nominal/max/cutoff voltages, internal impedance with busbars,
terminal voltage sag with chemistry-specific OCV(SoC) lookup, and current flows
over reference power profiles.
"""

from __future__ import annotations
import numpy as np
from typing import Dict, Tuple, Optional
from core.schemas import Cell, PackDesign, ChemistryEnum


# Empirical 11-point OCV(SoC) curves (Assumption A-02)
SOC_GRID = np.array([0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0])

OCV_NMC = np.array([2.50, 3.30, 3.52, 3.62, 3.70, 3.80, 3.90, 4.00, 4.10, 4.16, 4.20])
OCV_LFP = np.array([2.00, 3.05, 3.20, 3.25, 3.28, 3.30, 3.32, 3.35, 3.40, 3.50, 3.65])


def get_cell_ocv(soc: float, chemistry: ChemistryEnum) -> float:
    """Interpolate cell open-circuit voltage from SoC."""
    soc_clamped = float(np.clip(soc, 0.0, 1.0))
    table = OCV_LFP if chemistry == ChemistryEnum.LFP else OCV_NMC
    return float(np.interp(soc_clamped, SOC_GRID, table))


def calculate_electrical_properties(
    cell: Cell,
    design: PackDesign,
    busbar_resistance_per_cell_mOhm: float = 0.15,
) -> Dict[str, float]:
    """Calculate static electrical metrics for a design configuration."""
    v_nom = design.ns * cell.nominal_voltage_V
    v_max = design.ns * cell.max_voltage_V
    v_min = design.ns * cell.cutoff_voltage_V

    total_capacity_Ah = design.np * cell.capacity_Ah
    total_energy_Wh = v_nom * total_capacity_Ah

    # Pack internal resistance = (ns * R_cell / np) + interconnect resistance (Assumption A-01)
    r_cell_mOhm = cell.internal_resistance_mOhm
    r_interconnect_mOhm = design.ns * busbar_resistance_per_cell_mOhm / max(1.0, np.sqrt(design.np))
    pack_resistance_mOhm = (design.ns * r_cell_mOhm / design.np) + r_interconnect_mOhm

    # Currents at continuous (2.5 kW) and peak (6.0 kW) powers
    v_term_nominal = v_nom
    i_cont_pack = 2500.0 / v_term_nominal
    i_peak_pack = 6000.0 / max(30.0, (v_nom - (6000.0 / v_nom) * (pack_resistance_mOhm / 1000.0)))

    i_cell_cont = i_cont_pack / design.np
    i_cell_peak = i_peak_pack / design.np

    return {
        "nominal_voltage_V": round(v_nom, 2),
        "max_voltage_V": round(v_max, 2),
        "cutoff_voltage_V": round(v_min, 2),
        "total_capacity_Ah": round(total_capacity_Ah, 2),
        "total_energy_Wh": round(total_energy_Wh, 1),
        "pack_resistance_mOhm": round(pack_resistance_mOhm, 2),
        "cont_current_A": round(i_cont_pack, 2),
        "peak_current_A": round(i_peak_pack, 2),
        "max_cell_current_cont_A": round(i_cell_cont, 2),
        "max_cell_current_peak_A": round(i_cell_peak, 2),
    }


def simulate_drive_cycle_discharge(
    cell: Cell,
    design: PackDesign,
    power_profile_W: np.ndarray,
    dt_s: float = 1.0,
    ambient_temp_C: float = 35.0,
    inverter_eff: float = 0.95,
) -> Tuple[float, Dict[str, np.ndarray]]:
    """Simulate time-domain discharge over power profile.

    Returns:
        usable_energy_Wh: Total energy delivered before cutoff.
        time_series: Dictionary of voltages, currents, powers, and heat generation.
    """
    elec = calculate_electrical_properties(cell, design)
    r_pack_ohm = elec["pack_resistance_mOhm"] / 1000.0
    v_cutoff = elec["cutoff_voltage_V"]
    cap_As = elec["total_capacity_Ah"] * 3600.0

    n_steps = len(power_profile_W)
    v_term_arr = np.zeros(n_steps, dtype=float)
    i_pack_arr = np.zeros(n_steps, dtype=float)
    soc_arr = np.zeros(n_steps, dtype=float)
    heat_W_arr = np.zeros(n_steps, dtype=float)

    soc = 1.0
    energy_delivered_Wh = 0.0

    for t in range(n_steps):
        soc_arr[t] = soc
        ocv_cell = get_cell_ocv(soc, cell.chemistry)
        v_ocv_pack = design.ns * ocv_cell

        p_req = power_profile_W[t] / inverter_eff

        # Solve V_term * I = P where V_term = V_ocv - I * R_pack:
        # R_pack * I^2 - V_ocv * I + P = 0
        discriminant = v_ocv_pack**2 - 4.0 * r_pack_ohm * p_req
        if discriminant <= 0.0:
            # Voltage collapse under excessive load
            i_pack = v_ocv_pack / (2.0 * r_pack_ohm)
            v_term = v_ocv_pack - i_pack * r_pack_ohm
        else:
            i_pack = (v_ocv_pack - np.sqrt(discriminant)) / (2.0 * r_pack_ohm)
            v_term = v_ocv_pack - i_pack * r_pack_ohm

        v_term_arr[t] = v_term
        i_pack_arr[t] = i_pack
        heat_W_arr[t] = (i_pack ** 2) * r_pack_ohm

        if v_term < v_cutoff or soc <= 0.05:
            # Pack reached lower cutoff
            break

        energy_delivered_Wh += (power_profile_W[t] * dt_s) / 3600.0
        soc -= (i_pack * dt_s) / cap_As

    time_series = {
        "v_term_V": v_term_arr[: t + 1],
        "i_pack_A": i_pack_arr[: t + 1],
        "soc": soc_arr[: t + 1],
        "heat_W": heat_W_arr[: t + 1],
    }

    # Usable energy considering standard DoD to 5% SoC and IR losses
    usable_energy_Wh = energy_delivered_Wh
    return round(usable_energy_Wh, 1), time_series

