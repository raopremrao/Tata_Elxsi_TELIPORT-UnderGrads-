"""Tests for Traceability Graph and Matrix Engine (Milestone M3)."""

from core.data_loader import load_cells, load_requirements
from core.schemas import PackDesign, CoolingType, BMSTier, Scenario
from models.evaluate import evaluate
from analysis.traceability import (
    build_traceability_graph,
    generate_traceability_matrix,
    generate_design_dossier,
)


def test_traceability_graph_integrity():
    g = build_traceability_graph()
    assert g.number_of_nodes() >= 30
    assert g.number_of_edges() >= 25

    # Check that all requirements exist in graph and have outgoing/incoming edges
    reqs = load_requirements()
    for req_id in reqs.keys():
        assert req_id in g
        # Degree > 0 (no orphan requirement nodes)
        assert g.degree(req_id) > 0


def test_traceability_matrix_and_dossier():
    cells = load_cells()
    cell = cells["samsung_inr21700_50e"]
    design = PackDesign(cell_id=cell.id, ns=14, np=4, cooling=CoolingType.FORCED_AIR, bms_tier=BMSTier.STANDARD)
    res = evaluate(design, Scenario(), fast=True, cell=cell)

    df_matrix = generate_traceability_matrix(res)
    assert len(df_matrix) == 12
    assert "Requirement ID" in df_matrix.columns
    assert "Compliance Status" in df_matrix.columns

    dossier = generate_design_dossier(res)
    assert "compliance_matrix" in dossier
    assert "risks" in dossier
    assert "limitations" in dossier
    assert len(dossier["limitations"]) >= 3
    assert "recommended_next_experiment" in dossier

