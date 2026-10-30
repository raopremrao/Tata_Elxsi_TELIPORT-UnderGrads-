"""Unit tests for electrical subsystem model."""

from core.data_loader import load_cells
from core.schemas import PackDesign, CoolingType, BMSTier, ChemistryEnum
from models.electrical import calculate_electrical_properties, get_cell_ocv


def test_hand_calculated_13s2p():
    """Verify hand-calculable test case: 13S2P Panasonic NCR18650B."""
    cells = load_cells()
    cell = cells["panasonic_ncr18650b"]

    design = PackDesign(
        name="Test 13S2P",
        cell_id=cell.id,
        ns=13,
        np=2,
        cooling=CoolingType.PASSIVE,
        bms_tier=BMSTier.BASIC,
    )

    elec = calculate_electrical_properties(cell, design)

    # Hand calculations
    # V_nom = 13 * 3.60 = 46.80 V
    assert elec["nominal_voltage_V"] == 46.80
    # V_max = 13 * 4.20 = 54.60 V
    assert elec["max_voltage_V"] == 54.60
    # V_min = 13 * 2.50 = 32.50 V
    assert elec["cutoff_voltage_V"] == 32.50
    # Capacity = 2 * 3.35 = 6.70 Ah
    assert elec["total_capacity_Ah"] == 6.70
    # Energy = 46.80 * 6.70 = 313.56 Wh -> rounded to 313.6 Wh
    assert elec["total_energy_Wh"] == 313.6


def test_ocv_lookup_bounds():
    """Verify OCV lookup endpoints and monotonic behavior."""
    assert get_cell_ocv(0.0, ChemistryEnum.NMC) == 2.50
    assert get_cell_ocv(1.0, ChemistryEnum.NMC) == 4.20
    assert get_cell_ocv(0.0, ChemistryEnum.LFP) == 2.00
    assert get_cell_ocv(1.0, ChemistryEnum.LFP) == 3.65

    # Check monotonicity in mid-range
    ocv_30 = get_cell_ocv(0.3, ChemistryEnum.NMC)
    ocv_70 = get_cell_ocv(0.7, ChemistryEnum.NMC)
    assert ocv_30 < ocv_70

