"""Tests for Q-Pack Data Layer (Milestone M1)."""

import pandas as pd
from core.data_loader import load_cells, load_requirements, load_components, load_drive_cycle


def test_load_cells():
    cells = load_cells()
    assert len(cells) >= 5
    assert "samsung_inr21700_50e" in cells
    assert "panasonic_ncr18650b" in cells
    assert "generic_lfp_32700" in cells

    # Check verification flags (honesty rule)
    samsung_50e = cells["samsung_inr21700_50e"]
    assert samsung_50e.verified is True
    assert samsung_50e.source_url.startswith("http")

    generic_lfp = cells["generic_lfp_32700"]
    assert generic_lfp.verified is False
    assert generic_lfp.chemistry == "LFP"


def test_load_requirements():
    reqs = load_requirements()
    assert len(reqs) == 12
    for i in range(1, 13):
        req_id = f"R-{i:02d}"
        assert req_id in reqs
        req = reqs[req_id]
        assert len(req.text) > 0
        assert len(req.rationale) > 0
        assert req.target_value > 0


def test_load_components():
    comps = load_components()
    assert "bms_tiers" in comps
    assert "basic" in comps["bms_tiers"]
    assert "standard" in comps["bms_tiers"]
    assert "advanced" in comps["bms_tiers"]

    assert "cooling_options" in comps
    assert "passive" in comps["cooling_options"]
    assert "forced_air" in comps["cooling_options"]
    assert "cold_plate" in comps["cooling_options"]

    assert "mechanical" in comps
    assert comps["mechanical"]["busbar_resistance_per_cell_mOhm"] > 0


def test_load_drive_cycle():
    df = load_drive_cycle()
    assert isinstance(df, pd.DataFrame)
    assert len(df) == 1800
    assert "time_s" in df.columns
    assert "power_W" in df.columns
    assert "is_synthetic" in df.columns
    assert df["is_synthetic"].all()  # Flagged synthetic everywhere
    assert df["power_W"].max() >= 6000.0  # R-04 peak power present

