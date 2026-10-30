"""Mechanical Subsystem Model for Q-Pack.

Calculates pack mass, volume, packing density, and 3D bounding dimensions (L x W x H).
"""

from __future__ import annotations
import numpy as np
from typing import Dict, List, Tuple
from core.schemas import Cell, PackDesign, BMSTier, CoolingType


BMS_MASS_KG = {
    BMSTier.BASIC: 0.35,
    BMSTier.STANDARD: 0.50,
    BMSTier.ADVANCED: 0.75,
}

COOLING_MASS_KG = {
    CoolingType.PASSIVE: 0.0,
    CoolingType.FORCED_AIR: 0.85,
    CoolingType.COLD_PLATE: 2.20,
}


def calculate_mechanical_properties(
    cell: Cell,
    design: PackDesign,
    enclosure_mass_fraction: float = 0.18, # Assumption A-09
    busbar_mass_per_cell_g: float = 4.5,
    wall_thickness_mm: float = 3.0,
    vertical_clearance_mm: float = 25.0,
) -> Dict[str, any]:
    """Calculate mass, envelope dimensions, and volume."""
    total_cells = design.ns * design.np

    # Mass itemization (kg)
    cell_active_mass_kg = total_cells * (cell.mass_g / 1000.0)
    busbars_mass_kg = total_cells * (busbar_mass_per_cell_g / 1000.0)
    bms_mass_kg = BMS_MASS_KG.get(design.bms_tier, 0.50)
    cooling_mass_kg = COOLING_MASS_KG.get(design.cooling, 0.0)
    enclosure_mass_kg = cell_active_mass_kg * enclosure_mass_fraction

    total_pack_mass_kg = (
        cell_active_mass_kg
        + busbars_mass_kg
        + bms_mass_kg
        + cooling_mass_kg
        + enclosure_mass_kg
    )

    # Grid packing dimensions (mm)
    cols = int(np.ceil(np.sqrt(total_cells * 1.5)))
    rows = int(np.ceil(total_cells / cols))

    pitch_mm = cell.diameter_mm + design.cell_spacing_mm
    length_mm = cols * pitch_mm + 2.0 * wall_thickness_mm
    width_mm = rows * pitch_mm + 2.0 * wall_thickness_mm
    height_mm = cell.height_mm + vertical_clearance_mm

    # Add extra cooling duct height if forced air or cold plate
    if design.cooling == CoolingType.FORCED_AIR:
        height_mm += 20.0
    elif design.cooling == CoolingType.COLD_PLATE:
        height_mm += 15.0

    # Volume in Liters (1 L = 10^6 mm^3)
    volume_L = (length_mm * width_mm * height_mm) / 1.0e6

    return {
        "pack_mass_kg": round(total_pack_mass_kg, 2),
        "pack_volume_L": round(volume_L, 2),
        "dimensions_L_W_H_mm": [round(length_mm, 1), round(width_mm, 1), round(height_mm, 1)],
        "grid_layout": (rows, cols),
        "mass_breakdown_kg": {
            "cells": round(cell_active_mass_kg, 2),
            "busbars": round(busbars_mass_kg, 2),
            "bms": round(bms_mass_kg, 2),
            "cooling": round(cooling_mass_kg, 2),
            "enclosure": round(enclosure_mass_kg, 2),
        },
    }

