"""Cost Subsystem Model for PackForge.

Calculates itemized Bill-of-Materials (BOM) across cells, BMS, thermal hardware,
busbars, and structural enclosures.
"""

from __future__ import annotations
from typing import Dict
from core.schemas import Cell, PackDesign, BMSTier, CoolingType


BMS_COST_TABLE = {
    BMSTier.BASIC: {"base": 25.0, "per_s": 0.80},
    BMSTier.STANDARD: {"base": 45.0, "per_s": 1.20},
    BMSTier.ADVANCED: {"base": 85.0, "per_s": 2.00},
}

COOLING_COST_TABLE = {
    CoolingType.PASSIVE: 0.0,
    CoolingType.FORCED_AIR: 35.0,
    CoolingType.COLD_PLATE: 95.0,
}


def calculate_bom_cost(
    cell: Cell,
    design: PackDesign,
    enclosure_mass_kg: float,
    enclosure_cost_per_kg_USD: float = 14.0,  # Assumption A-10
    busbar_cost_per_cell_USD: float = 0.25,
) -> Dict[str, any]:
    """Calculate bottom-up BOM cost in USD."""
    total_cells = design.ns * design.np

    cells_cost_USD = total_cells * cell.unit_cost_USD

    bms_cfg = BMS_COST_TABLE.get(design.bms_tier, BMS_COST_TABLE[BMSTier.STANDARD])
    bms_cost_USD = bms_cfg["base"] + (design.ns * bms_cfg["per_s"])

    cooling_cost_USD = COOLING_COST_TABLE.get(design.cooling, 0.0)
    busbars_cost_USD = total_cells * busbar_cost_per_cell_USD
    enclosure_cost_USD = enclosure_mass_kg * enclosure_cost_per_kg_USD

    total_bom_USD = (
        cells_cost_USD
        + bms_cost_USD
        + cooling_cost_USD
        + busbars_cost_USD
        + enclosure_cost_USD
    )

    itemized = {
        "cells": round(cells_cost_USD, 2),
        "bms": round(bms_cost_USD, 2),
        "cooling": round(cooling_cost_USD, 2),
        "busbars": round(busbars_cost_USD, 2),
        "enclosure": round(enclosure_cost_USD, 2),
    }

    return {
        "bom_cost_USD": round(total_bom_USD, 2),
        "itemized_cost_USD": itemized,
    }

