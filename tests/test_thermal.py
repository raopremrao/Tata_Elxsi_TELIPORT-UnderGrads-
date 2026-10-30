"""Unit tests for thermal subsystem model."""

import numpy as np
from core.data_loader import load_cells
from core.schemas import PackDesign, CoolingType, BMSTier
from models.thermal import simulate_pack_thermal


def test_cooling_monotonicity():
    """Verify that enhanced cooling strictly reduces peak operating temperature."""
    cells = load_cells()
    cell = cells["samsung_inr21700_50e"]

    time_s = np.linspace(0, 1800, 1800)
    heat_W = np.full(1800, 150.0)  # Continuous 150 W heat generation

    res_passive = simulate_pack_thermal(
        cell=cell,
        design=PackDesign(cell_id=cell.id, ns=14, np=4, cooling=CoolingType.PASSIVE),
        heat_profile_W=heat_W,
        time_s=time_s,
        ambient_temp_C=35.0,
        fast=False,
    )

    res_air = simulate_pack_thermal(
        cell=cell,
        design=PackDesign(cell_id=cell.id, ns=14, np=4, cooling=CoolingType.FORCED_AIR),
        heat_profile_W=heat_W,
        time_s=time_s,
        ambient_temp_C=35.0,
        fast=False,
    )

    res_cold = simulate_pack_thermal(
        cell=cell,
        design=PackDesign(cell_id=cell.id, ns=14, np=4, cooling=CoolingType.COLD_PLATE),
        heat_profile_W=heat_W,
        time_s=time_s,
        ambient_temp_C=35.0,
        fast=False,
    )

    # Monotonicity: Passive > Forced Air > Cold Plate
    assert res_passive["peak_temp_C"] > res_air["peak_temp_C"]
    assert res_air["peak_temp_C"] > res_cold["peak_temp_C"]


def test_thermal_spatial_gradient():
    """Verify core cells are hotter than surface cells in 2D layout."""
    cells = load_cells()
    cell = cells["samsung_inr21700_50e"]

    time_s = np.linspace(0, 1800, 1800)
    heat_W = np.full(1800, 120.0)

    res = simulate_pack_thermal(
        cell=cell,
        design=PackDesign(cell_id=cell.id, ns=14, np=4, cooling=CoolingType.FORCED_AIR),
        heat_profile_W=heat_W,
        time_s=time_s,
        ambient_temp_C=35.0,
        fast=False,
    )

    grid = np.array(res["temp_grid_C"])
    assert grid.shape[0] > 1 and grid.shape[1] > 1
    # Center cell is hotter than corner cell
    center_temp = grid[grid.shape[0] // 2, grid.shape[1] // 2]
    corner_temp = grid[0, 0]
    assert center_temp > corner_temp
    assert res["temp_gradient_C"] > 0.0

