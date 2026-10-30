"""DesignContext: Shared Parameter Bus for PackForge Subsystem Integration.

Maintains unified state, units, provenance, and dependency tracking across
electrical, thermal, mechanical, BMS, and cost subsystems.
"""

from __future__ import annotations
from typing import Any, Dict, Optional
from core.schemas import Cell, PackDesign, Scenario


class ParameterEntry:
    def __init__(self, value: Any, unit: str, provenance: str, description: str = ""):
        self.value = value
        self.unit = unit
        self.provenance = provenance  # e.g., "electrical.py:line42", "cell_datasheet", "A-01"
        self.description = description

    def __repr__(self) -> str:
        return f"ParameterEntry(value={self.value}, unit='{self.unit}', provenance='{self.provenance}')"


class DesignContext:
    """Bus that passes values, units, and provenance across subsystems."""

    def __init__(self, design: PackDesign, cell: Cell, scenario: Scenario):
        self.design = design
        self.cell = cell
        self.scenario = scenario
        self.registry: Dict[str, ParameterEntry] = {}

        # Prepopulate known inputs with provenance
        self.set("cell.model", cell.model, unit="", provenance="datasheet")
        self.set("cell.capacity_Ah", cell.capacity_Ah, unit="Ah", provenance="datasheet")
        self.set("cell.nominal_voltage_V", cell.nominal_voltage_V, unit="V", provenance="datasheet")
        self.set("cell.internal_resistance_mOhm", cell.internal_resistance_mOhm, unit="mOhm", provenance="datasheet")
        self.set("design.ns", design.ns, unit="cells", provenance="pack_design")
        self.set("design.np", design.np, unit="cells", provenance="pack_design")
        self.set("design.cooling", design.cooling.value, unit="", provenance="pack_design")
        self.set("design.bms_tier", design.bms_tier.value, unit="", provenance="pack_design")
        self.set("scenario.ambient_temp_C", scenario.ambient_temp_C, unit="C", provenance="scenario_config")

    def set(self, key: str, value: Any, unit: str, provenance: str, description: str = "") -> None:
        """Register or update a parameter on the bus."""
        self.registry[key] = ParameterEntry(value, unit, provenance, description)

    def get(self, key: str, default: Any = None) -> Any:
        """Retrieve the parameter value."""
        if key in self.registry:
            return self.registry[key].value
        return default

    def get_entry(self, key: str) -> Optional[ParameterEntry]:
        """Retrieve parameter entry with provenance and unit."""
        return self.registry.get(key)

    def summary(self) -> Dict[str, Dict[str, Any]]:
        """Return dict summary of all parameters on the bus."""
        return {
            k: {
                "value": v.value,
                "unit": v.unit,
                "provenance": v.provenance,
                "description": v.description,
            }
            for k, v in self.registry.items()
        }

