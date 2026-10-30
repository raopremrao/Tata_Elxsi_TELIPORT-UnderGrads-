"""Unit tests for PackForge core schemas, units, and parameter bus."""

import pytest
from pydantic import ValidationError
from core.schemas import (
    Cell,
    PackDesign,
    Scenario,
    Requirement,
    RequirementStatus,
    Finding,
    ChemistryEnum,
    CoolingType,
    BMSTier,
)
from core.units import (
    wh_to_kwh,
    kwh_to_wh,
    s_to_min,
    min_to_s,
    c_to_k,
    k_to_c,
    mm_to_m,
    m3_to_l,
    l_to_m3,
    g_to_kg,
    mohm_to_ohm,
)
from core.context import DesignContext


@pytest.fixture
def sample_cell():
    return Cell(
        id="samsung_inr21700_50e",
        manufacturer="Samsung SDI",
        model="INR21700-50E",
        chemistry=ChemistryEnum.NMC,
        form_factor="21700",
        nominal_voltage_V=3.6,
        max_voltage_V=4.2,
        cutoff_voltage_V=2.5,
        capacity_Ah=5.0,
        mass_g=69.0,
        diameter_mm=21.25,
        height_mm=70.8,
        max_continuous_discharge_A=9.8,
        max_pulse_discharge_A=14.7,
        max_charge_A=4.9,
        internal_resistance_mOhm=25.0,
        max_cell_temp_C=60.0,
        unit_cost_USD=4.80,
        cycle_life_ref=1000,
        source_url="https://datasheetspdf.com/pdf/1315802/Samsung/INR21700-50E/1",
        verified=True,
    )


@pytest.fixture
def sample_design():
    return PackDesign(
        name="Test 14S4P Design",
        cell_id="samsung_inr21700_50e",
        ns=14,
        np=4,
        cooling=CoolingType.FORCED_AIR,
        bms_tier=BMSTier.STANDARD,
        cell_spacing_mm=2.0,
    )


@pytest.fixture
def sample_scenario():
    return Scenario()


def test_cell_schema_valid(sample_cell):
    assert sample_cell.model == "INR21700-50E"
    assert sample_cell.capacity_Ah == 5.0
    assert sample_cell.chemistry == ChemistryEnum.NMC
    assert sample_cell.verified is True


def test_cell_schema_immutability(sample_cell):
    with pytest.raises(ValidationError):
        sample_cell.capacity_Ah = 6.0  # Should be frozen


def test_pack_design_bounds(sample_cell):
    # Valid design
    design = PackDesign(
        cell_id=sample_cell.id,
        ns=14,
        np=4,
        cooling=CoolingType.FORCED_AIR,
        bms_tier=BMSTier.STANDARD,
        cell_spacing_mm=2.0,
    )
    assert design.ns == 14
    assert design.np == 4

    # Invalid series count <= 0
    with pytest.raises(ValidationError):
        PackDesign(cell_id=sample_cell.id, ns=0, np=4)

    # Invalid cell spacing
    with pytest.raises(ValidationError):
        PackDesign(cell_id=sample_cell.id, ns=14, np=4, cell_spacing_mm=0.1)


def test_units_conversion():
    assert wh_to_kwh(2000.0) == 2.0
    assert kwh_to_wh(2.5) == 2500.0
    assert s_to_min(1800.0) == 30.0
    assert min_to_s(90.0) == 5400.0
    assert c_to_k(25.0) == 298.15
    assert k_to_c(298.15) == 25.0
    assert mm_to_m(1000.0) == 1.0
    assert m3_to_l(0.02) == 20.0
    assert l_to_m3(22.0) == 0.022
    assert g_to_kg(18000.0) == 18.0
    assert mohm_to_ohm(25.0) == 0.025


def test_design_context_bus(sample_design, sample_cell, sample_scenario):
    bus = DesignContext(design=sample_design, cell=sample_cell, scenario=sample_scenario)
    assert bus.get("cell.capacity_Ah") == 5.0
    assert bus.get("design.ns") == 14

    # Register new computed value
    bus.set("electrical.V_nom", 50.4, unit="V", provenance="models/electrical.py")
    assert bus.get("electrical.V_nom") == 50.4
    entry = bus.get_entry("electrical.V_nom")
    assert entry.unit == "V"
    assert entry.provenance == "models/electrical.py"

