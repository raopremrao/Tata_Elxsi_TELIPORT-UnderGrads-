"""PackForge Core Data Schemas

Pydantic v2 data models defining shared interfaces across physics models,
optimization routines, analysis engines, and dashboard layers.
"""

from __future__ import annotations
from enum import Enum
from typing import Dict, List, Literal, Optional
from pydantic import BaseModel, ConfigDict, Field


class ChemistryEnum(str, Enum):
    NMC = "NMC"
    LFP = "LFP"


class CoolingType(str, Enum):
    PASSIVE = "passive"
    FORCED_AIR = "forced_air"
    COLD_PLATE = "cold_plate"


class BMSTier(str, Enum):
    BASIC = "basic"
    STANDARD = "standard"
    ADVANCED = "advanced"


class Cell(BaseModel):
    """Specification of an individual battery cell."""
    model_config = ConfigDict(frozen=True)

    id: str
    manufacturer: str
    model: str
    chemistry: ChemistryEnum
    form_factor: str  # e.g., "18650", "21700", "32700"
    nominal_voltage_V: float = Field(..., gt=0.0)
    max_voltage_V: float = Field(..., gt=0.0)
    cutoff_voltage_V: float = Field(..., gt=0.0)
    capacity_Ah: float = Field(..., gt=0.0)
    mass_g: float = Field(..., gt=0.0)
    diameter_mm: float = Field(..., gt=0.0)
    height_mm: float = Field(..., gt=0.0)
    max_continuous_discharge_A: float = Field(..., gt=0.0)
    max_pulse_discharge_A: float = Field(..., gt=0.0)
    max_charge_A: float = Field(..., gt=0.0)
    internal_resistance_mOhm: float = Field(..., gt=0.0)
    max_cell_temp_C: float = Field(default=60.0)
    unit_cost_USD: float = Field(..., gt=0.0)
    cycle_life_ref: int = Field(default=1000, gt=0)
    source_url: str = Field(default="")
    verified: bool = Field(default=False)
    notes: Optional[str] = None


class PackDesign(BaseModel):
    """Specification of a battery pack configuration."""
    model_config = ConfigDict(frozen=True)

    name: str = "Design Candidate"
    cell_id: str
    ns: int = Field(..., ge=1, le=30, description="Series cell count")
    np: int = Field(..., ge=1, le=20, description="Parallel cell count")
    cooling: CoolingType = CoolingType.PASSIVE
    bms_tier: BMSTier = BMSTier.BASIC
    cell_spacing_mm: float = Field(default=1.0, ge=0.5, le=10.0)


class Scenario(BaseModel):
    """Operational conditions and requirement constraints."""
    model_config = ConfigDict(frozen=True)

    application: str = "48 V-Class Light Electric Mobility"
    ambient_temp_C: float = 35.0
    drive_cycle_path: str = "data/drive_cycle_urban.csv"
    duration_s: float = 1800.0
    power_peak_kW: float = 6.0
    power_continuous_kW: float = 2.5
    cost_budget_USD: float = 450.0
    max_mass_kg: float = 18.0
    max_volume_L: float = 22.0
    mc_iterations: int = 500
    seed: int = 42


class Requirement(BaseModel):
    """System-level engineering requirement."""
    model_config = ConfigDict(frozen=True)

    id: str
    text: str
    rationale: str
    verification_method: str
    target_value: float
    comparison_op: Literal["<=", ">=", "=="]
    unit: str


class RequirementStatus(BaseModel):
    """Compliance evaluation for a specific requirement."""
    model_config = ConfigDict(frozen=True)

    req_id: str
    passed: bool
    actual_value: float
    target_value: float
    margin: float
    unit: str
    rationale: str


class Finding(BaseModel):
    """Safety or engineering conflict identified by analysis rules."""
    model_config = ConfigDict(frozen=True)

    id: str
    severity: Literal["info", "warning", "critical"]
    subsystem: str
    title: str
    explanation: str
    suggested_fix: str
    linked_requirements: List[str] = Field(default_factory=list)
    linked_assumptions: List[str] = Field(default_factory=list)


class EvaluationResult(BaseModel):
    """Complete multi-disciplinary simulation output for a PackDesign."""
    model_config = ConfigDict(frozen=True)

    design: PackDesign
    nominal_voltage_V: float
    max_voltage_V: float
    cutoff_voltage_V: float
    total_capacity_Ah: float
    total_energy_Wh: float
    usable_energy_Wh: float
    pack_resistance_mOhm: float
    peak_current_A: float
    cont_current_A: float
    max_cell_current_peak_A: float
    max_cell_current_cont_A: float
    peak_temp_C: float
    temp_gradient_C: float
    charge_time_min: float
    pack_mass_kg: float
    pack_volume_L: float
    dimensions_L_W_H_mm: List[float]
    bom_cost_USD: float
    itemized_cost_USD: Dict[str, float]
    estimated_cycle_life: int
    mc_usable_energy_P5_Wh: float
    mc_usable_energy_P50_Wh: float
    mc_usable_energy_P95_Wh: float
    mc_temp_P95_C: float
    mc_violation_probability: float
    requirements: Dict[str, RequirementStatus]
    findings: List[Finding]
    assumption_ids_used: List[str]
    time_series: Optional[Dict[str, List[float]]] = None
    eval_time_ms: float
    model_version_hash: str

