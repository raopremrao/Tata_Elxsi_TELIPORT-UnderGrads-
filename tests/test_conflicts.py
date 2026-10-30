"""Tests for Conflict Rule Engine on Deliberately Broken Designs (Milestone M3).

Verifies Definition of Done requirement:
'Conflict engine fires correctly on at least 5 deliberately broken test designs.'
"""

from core.data_loader import load_cells
from core.schemas import PackDesign, CoolingType, BMSTier, Scenario
from models.evaluate import evaluate


def test_conflict_rule_01_cell_overcurrent():
    """Broken Design 1: Single cell parallel (np=1) with 18650 cell forces massive overcurrent."""
    cells = load_cells()
    cell = cells["panasonic_ncr18650b"]  # max pulse 10 A, max cont 6.7 A
    # Peak current at 6 kW / 48V is >100 A -> 100 A / cell >> 10 A limit!
    design = PackDesign(cell_id=cell.id, ns=13, np=1, cooling=CoolingType.PASSIVE, bms_tier=BMSTier.BASIC)
    res = evaluate(design, Scenario(), fast=True, cell=cell)

    finding_ids = [f.id for f in res.findings]
    assert "RULE-01" in finding_ids, "RULE-01 (Cell Overcurrent) did not trigger!"


def test_conflict_rule_02_elv_breach():
    """Broken Design 2: High series count (ns=18 NMC) breaches 60V ELV safety limit (18 * 4.2 = 75.6V)."""
    cells = load_cells()
    cell = cells["samsung_inr21700_50e"]
    design = PackDesign(cell_id=cell.id, ns=18, np=4, cooling=CoolingType.PASSIVE, bms_tier=BMSTier.BASIC)
    res = evaluate(design, Scenario(), fast=True, cell=cell)

    finding_ids = [f.id for f in res.findings]
    assert "RULE-02" in finding_ids, "RULE-02 (ELV Boundary Breached) did not trigger!"


def test_conflict_rule_03_bms_undersized():
    """Broken Design 3: Low voltage pack (ns=10) with Basic BMS (40A limit) exceeds continuous current (2500W / 36V = 69A)."""
    cells = load_cells()
    cell = cells["samsung_inr21700_50e"]
    design = PackDesign(cell_id=cell.id, ns=10, np=4, cooling=CoolingType.PASSIVE, bms_tier=BMSTier.BASIC)
    res = evaluate(design, Scenario(), fast=True, cell=cell)

    finding_ids = [f.id for f in res.findings]
    assert "RULE-03" in finding_ids, "RULE-03 (BMS Continuous Undersized) did not trigger!"


def test_conflict_rule_04_thermal_insufficient():
    """Broken Design 4: High internal resistance cell with passive cooling overheats beyond 45 C."""
    cells = load_cells()
    cell = cells["panasonic_ncr18650b"]  # High IR (38 mOhm)
    design = PackDesign(cell_id=cell.id, ns=13, np=2, cooling=CoolingType.PASSIVE, bms_tier=BMSTier.BASIC)
    res = evaluate(design, Scenario(), fast=True, cell=cell)

    finding_ids = [f.id for f in res.findings]
    assert "RULE-04" in finding_ids, "RULE-04 (Thermal Cooling Insufficient) did not trigger!"


def test_conflict_rule_06_sensing_gap():
    """Broken Design 5: 16S pack on Basic BMS (only 2 thermistors, requires ceil(16/6) = 3 thermistors)."""
    cells = load_cells()
    cell = cells["generic_lfp_32700"]  # LFP at 16S
    design = PackDesign(cell_id=cell.id, ns=16, np=2, cooling=CoolingType.PASSIVE, bms_tier=BMSTier.BASIC)
    res = evaluate(design, Scenario(), fast=True, cell=cell)

    finding_ids = [f.id for f in res.findings]
    assert "RULE-06" in finding_ids, "RULE-06 (Sensing Gap) did not trigger!"


def test_conflict_rule_10_unverified_provenance():
    """Broken Design 6: Generic LFP cell flags unverified datasheet provenance."""
    cells = load_cells()
    cell = cells["generic_lfp_32700"]
    assert cell.verified is False
    design = PackDesign(cell_id=cell.id, ns=15, np=3, cooling=CoolingType.FORCED_AIR, bms_tier=BMSTier.STANDARD)
    res = evaluate(design, Scenario(), fast=True, cell=cell)

    finding_ids = [f.id for f in res.findings]
    assert "RULE-10" in finding_ids, "RULE-10 (Unverified Provenance) did not trigger!"

