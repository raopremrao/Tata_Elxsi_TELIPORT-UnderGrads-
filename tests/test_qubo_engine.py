"""Tests for QUBO Formulation, Vectorized SA, and Hardware Export (Milestone M5)."""

import numpy as np
from core.schemas import PackDesign, CoolingType, BMSTier, Scenario
from optimize.qubo_build import (
    TOTAL_QUBITS,
    design_to_binary,
    binary_to_design,
    build_qubo_model,
)
from optimize.qubo_sa import solve_qubo_vectorized_sa, solve_qubo_with_reevaluation
from optimize.export_qubo import export_qubo_json, export_to_dimod_bqm, HAS_DIMOD
from optimize.exhaustive import run_exhaustive_search


def test_binary_encoding_roundtrip():
    design = PackDesign(
        cell_id="samsung_inr21700_50e",
        ns=14,
        np=4,
        cooling=CoolingType.FORCED_AIR,
        bms_tier=BMSTier.STANDARD,
        cell_spacing_mm=2.0,
    )
    b = design_to_binary(design)
    assert len(b) == TOTAL_QUBITS
    assert np.sum(b) == 6  # Exactly 6 ones (one per group)

    recovered = binary_to_design(b)
    assert recovered.cell_id == design.cell_id
    assert recovered.ns == design.ns
    assert recovered.np == design.np
    assert recovered.cooling == design.cooling
    assert recovered.bms_tier == design.bms_tier
    assert recovered.cell_spacing_mm == design.cell_spacing_mm


def test_qubo_build_and_fidelity():
    # Run a small exhaustive sample to fit QUBO
    exh = run_exhaustive_search(max_designs=200, force_recompute=True)
    qubo = build_qubo_model(exh.designs, exh.scalar_scores)

    assert qubo.Q.shape == (TOTAL_QUBITS, TOTAL_QUBITS)
    # Check surrogate fidelity metrics
    assert qubo.r2_score >= 0.0
    assert -1.0 <= qubo.spearman_corr <= 1.0


def test_vectorized_sa_solver_and_reevaluation():
    exh = run_exhaustive_search(max_designs=200, force_recompute=True)
    qubo = build_qubo_model(exh.designs, exh.scalar_scores)

    best_design, best_true_res, candidates = solve_qubo_with_reevaluation(
        qubo=qubo,
        scenario=Scenario(),
        n_reads=50,
        n_sweeps=100,
        seed=42,
    )

    assert best_design is not None
    assert best_true_res.nominal_voltage_V > 0
    assert best_true_res.usable_energy_Wh > 0
    assert len(candidates) > 0


def test_qubo_export():
    exh = run_exhaustive_search(max_designs=100, force_recompute=True)
    qubo = build_qubo_model(exh.designs, exh.scalar_scores)

    json_path = export_qubo_json(qubo, output_path="outputs/test_qubo.json")
    assert json_path == "outputs/test_qubo.json"

    if HAS_DIMOD:
        bqm = export_to_dimod_bqm(qubo)
        assert bqm is not None
        assert bqm.num_variables == TOTAL_QUBITS

