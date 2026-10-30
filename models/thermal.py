"""Thermal Subsystem Model for PackForge.

Implements lumped-parameter thermal ODE integration (solve_ivp) over the drive cycle,
transient cooling dynamics, and a 2D spatial cell layout conduction gradient model.
"""

from __future__ import annotations
import numpy as np
from scipy.integrate import solve_ivp
from typing import Dict, Tuple, Optional
from core.schemas import Cell, PackDesign, CoolingType


COOLING_COEFFICIENTS = {
    CoolingType.PASSIVE: {"h_eff": 10.0, "added_mass_kg": 0.0, "cost_USD": 0.0, "parasitic_W": 0.0},
    CoolingType.FORCED_AIR: {"h_eff": 35.0, "added_mass_kg": 0.85, "cost_USD": 35.0, "parasitic_W": 15.0},
    CoolingType.COLD_PLATE: {"h_eff": 150.0, "added_mass_kg": 2.20, "cost_USD": 95.0, "parasitic_W": 30.0},
}


def compute_pack_surface_area_and_mass(
    cell: Cell,
    design: PackDesign,
    cell_mass_kg: float,
) -> Tuple[float, float, Tuple[int, int]]:
    """Compute surface area (m^2) and total thermal mass (kg).

    Returns:
        surface_area_m2, thermal_mass_kg, (rows, cols)
    """
    total_cells = design.ns * design.np
    # Layout cells in approximately 2:1 or square grid
    cols = int(np.ceil(np.sqrt(total_cells * 1.5)))
    rows = int(np.ceil(total_cells / cols))

    d_eff_m = (cell.diameter_mm + design.cell_spacing_mm) / 1000.0
    h_m = (cell.height_mm + 25.0) / 1000.0

    length_m = cols * d_eff_m + 0.010  # 10mm wall margin
    width_m = rows * d_eff_m + 0.010
    height_m = h_m

    # Effective surface area for convection / heat rejection
    surface_area_m2 = 2.0 * (length_m * width_m + length_m * height_m + width_m * height_m)

    # Thermal mass includes cells and hardware
    cooling_meta = COOLING_COEFFICIENTS[design.cooling]
    active_cell_mass = total_cells * (cell.mass_g / 1000.0)
    enclosure_mass = active_cell_mass * 0.18  # Assumption A-09
    thermal_mass_kg = active_cell_mass + enclosure_mass + cooling_meta["added_mass_kg"]

    return surface_area_m2, thermal_mass_kg, (rows, cols)


def simulate_pack_thermal(
    cell: Cell,
    design: PackDesign,
    heat_profile_W: np.ndarray,
    time_s: np.ndarray,
    ambient_temp_C: float = 35.0,
    fast: bool = False,
) -> Dict[str, any]:
    """Simulate pack temperature rise during operation.

    Returns:
        Dict containing peak_temp_C, temp_gradient_C, temp_time_series, and 2D spatial grid.
    """
    cooling_meta = COOLING_COEFFICIENTS[design.cooling]
    h_eff = cooling_meta["h_eff"]  # Assumption A-05
    p_parasitic = cooling_meta["parasitic_W"]

    cell_mass_kg = cell.mass_g / 1000.0
    surface_area_m2, thermal_mass_kg, (rows, cols) = compute_pack_surface_area_and_mass(
        cell, design, cell_mass_kg
    )

    c_p = 950.0  # Cell specific heat capacity J/(kg*K) (Assumption A-04)
    c_th = max(500.0, thermal_mass_kg * c_p)  # Thermal capacitance J/K
    g_th = max(0.5, h_eff * surface_area_m2)   # Thermal conductance W/K

    total_duration_s = float(time_s[-1] - time_s[0]) if len(time_s) > 1 else 1800.0

    if fast:
        # Fast analytical approximation for optimizer loops
        mean_heat = float(np.mean(heat_profile_W)) + p_parasitic
        tau_th = c_th / g_th
        t_rise = (mean_heat / g_th) * (1.0 - np.exp(-total_duration_s / tau_th))
        mean_final_temp = ambient_temp_C + t_rise

        # Spatial gradient (Assumption A-06)
        gradient = 0.25 * t_rise
        peak_temp = mean_final_temp + gradient

        return {
            "peak_temp_C": round(peak_temp, 2),
            "temp_gradient_C": round(gradient, 2),
            "mean_temp_C": round(mean_final_temp, 2),
            "temp_series": None,
            "temp_grid_C": None,
        }

    # High-fidelity solve_ivp lumped ODE integration
    # Interpolator for heat generation
    def q_gen(t: float) -> float:
        idx = int(np.clip(t, 0, len(heat_profile_W) - 1))
        return heat_profile_W[idx] + p_parasitic

    def ode(t: float, y: list[float]) -> list[float]:
        t_pack = y[0]
        q_in = q_gen(t)
        q_out = g_th * (t_pack - ambient_temp_C)
        dTdt = (q_in - q_out) / c_th
        return [dTdt]

    sol = solve_ivp(
        ode,
        t_span=(0.0, total_duration_s),
        y0=[ambient_temp_C],
        t_eval=time_s,
        method="RK23",
    )

    temp_series = sol.y[0]
    final_mean_temp = temp_series[-1]
    max_mean_temp = float(np.max(temp_series))

    # 2D Spatial Layout Temperature Distribution
    # Core cells experience higher temperatures than boundary cells
    grid = np.zeros((rows, cols), dtype=float)
    cy, cx = (rows - 1) / 2.0, (cols - 1) / 2.0
    max_radius = max(1.0, np.sqrt(cx**2 + cy**2))

    t_rise = max_mean_temp - ambient_temp_C
    max_grad = 0.25 * t_rise  # Assumption A-06

    for r in range(rows):
        for c in range(cols):
            dist = np.sqrt((r - cy)**2 + (c - cx)**2)
            # Center cells (dist ~ 0) run hot, outer cells run near mean
            cell_temp = max_mean_temp + max_grad * (1.0 - (dist / max_radius)**2)
            grid[r, c] = round(cell_temp, 2)

    peak_temp = float(np.max(grid))
    gradient = float(peak_temp - np.min(grid))

    return {
        "peak_temp_C": round(peak_temp, 2),
        "temp_gradient_C": round(gradient, 2),
        "mean_temp_C": round(max_mean_temp, 2),
        "temp_series": temp_series.tolist(),
        "temp_grid_C": grid.tolist(),
    }

