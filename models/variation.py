"""Monte Carlo Cell-to-Cell Variation Model for PackForge.

Propagates manufacturing cell-level capacity and impedance spreads to system-level
pack performance, calculating weakest-group capacity bottleneck and failure probabilities.
"""

from __future__ import annotations
import numpy as np
from typing import Dict, List, Tuple
from core.schemas import Cell, PackDesign


def simulate_cell_variation(
    cell: Cell,
    design: PackDesign,
    n_iterations: int = 500,
    seed: int = 42,
    capacity_sigma_rel: float = 0.02,   # Assumption A-13 (+/- 2%)
    resistance_sigma_rel: float = 0.08, # Assumption A-14 (+/- 8%)
    target_energy_Wh: float = 2000.0,
    max_temp_threshold_C: float = 45.0,
    base_peak_temp_C: float = 40.0,
) -> Dict[str, any]:
    """Run Monte Carlo simulation of cell variation propagating to pack level.

    Returns:
        P5, P50, P95 usable energy, P95 temperature, and violation probability.
    """
    rng = np.random.default_rng(seed)

    ns = design.ns
    np_count = design.np
    total_cells = ns * np_count

    mu_c = cell.capacity_Ah
    mu_r = cell.internal_resistance_mOhm / 1000.0  # Ohms

    # Sample cell capacities shape: (n_iterations, ns, np)
    c_samples = rng.normal(mu_c, mu_c * capacity_sigma_rel, size=(n_iterations, ns, np_count))
    c_samples = np.clip(c_samples, mu_c * 0.85, mu_c * 1.15)

    # Sample cell resistances shape: (n_iterations, ns, np)
    r_samples = rng.normal(mu_r, mu_r * resistance_sigma_rel, size=(n_iterations, ns, np_count))
    r_samples = np.clip(r_samples, mu_r * 0.70, mu_r * 1.40)

    # Parallel group capacity = sum of parallel cells
    group_capacities = np.sum(c_samples, axis=2)  # shape: (n_iterations, ns)

    # Weakest series group limits total pack capacity (Assumption A-15)
    weakest_group_capacities = np.min(group_capacities, axis=1)  # shape: (n_iterations,)

    # Effective pack resistance: sum of harmonic parallel group resistances
    # 1 / R_group = sum(1 / R_cell)
    inv_r_groups = np.sum(1.0 / r_samples, axis=2)
    group_resistances = 1.0 / inv_r_groups
    pack_resistances = np.sum(group_resistances, axis=1)  # shape: (n_iterations,)

    # Pack nominal voltage
    v_nom = ns * cell.nominal_voltage_V

    # Usable energy distribution (Wh), incorporating 92% discharge depth & IR losses
    mean_resistance = ns * (mu_r / np_count)
    ir_loss_factor = 1.0 - (pack_resistances / (v_nom * 10.0))
    usable_energies_Wh = v_nom * weakest_group_capacities * 0.93 * ir_loss_factor

    # Temperature variations: scales proportionally with pack resistance
    resistance_ratio = pack_resistances / max(1e-4, mean_resistance)
    simulated_peak_temps_C = base_peak_temp_C + (base_peak_temp_C - 35.0) * (resistance_ratio - 1.0)

    # Statistical quantiles
    p5_energy = float(np.percentile(usable_energies_Wh, 5))
    p50_energy = float(np.percentile(usable_energies_Wh, 50))
    p95_energy = float(np.percentile(usable_energies_Wh, 95))

    p95_temp = float(np.percentile(simulated_peak_temps_C, 95))

    # Probability of violating requirement R-03 (Energy < 2.0 kWh) or R-05 (Temp > 45 C)
    energy_violations = usable_energies_Wh < target_energy_Wh
    temp_violations = simulated_peak_temps_C > max_temp_threshold_C
    total_violations = np.logical_or(energy_violations, temp_violations)
    violation_probability = float(np.mean(total_violations))

    return {
        "mc_usable_energy_P5_Wh": round(p5_energy, 1),
        "mc_usable_energy_P50_Wh": round(p50_energy, 1),
        "mc_usable_energy_P95_Wh": round(p95_energy, 1),
        "mc_temp_P95_C": round(p95_temp, 2),
        "mc_violation_probability": round(violation_probability, 4),
        "energy_samples_Wh": usable_energies_Wh[:100].tolist(),  # First 100 for fast UI display
        "temp_samples_C": simulated_peak_temps_C[:100].tolist(),
    }

