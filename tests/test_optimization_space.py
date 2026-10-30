"""Tests for Design Space, Baselines, and Pareto Utilities (Milestone M4)."""

import numpy as np
from optimize.space import enumerate_design_space, get_baseline_designs
from optimize.pareto import is_dominant, extract_pareto_front, compute_hypervolume_2d
from optimize.exhaustive import run_exhaustive_search
from models.evaluate import evaluate
from core.schemas import Scenario


def test_design_space_enumeration():
    feasible, infeasible = enumerate_design_space()
    assert len(feasible) > 1000
    assert len(infeasible) > 0
    # Infeasible configurations should not have passed hard limits
    for d in infeasible[:10]:
        assert d.ns * 4.2 > 60.0 or (136.0 / d.np) > 10.0


def test_baseline_designs_evaluation():
    baselines = get_baseline_designs()
    assert "Design 0" in baselines
    assert "Design A" in baselines
    assert "Design B" in baselines

    scenario = Scenario()
    for name, d in baselines.items():
        res = evaluate(d, scenario, fast=True)
        assert res.nominal_voltage_V > 0
        assert res.pack_mass_kg > 0
        assert res.usable_energy_Wh > 0


def test_pareto_dominance():
    # Vector a strictly better than b on both objectives
    a = np.array([1.0, 2.0])
    b = np.array([1.5, 2.5])
    assert is_dominant(a, b)
    assert not is_dominant(b, a)

    # Incomparable
    c = np.array([0.8, 3.0])
    assert not is_dominant(a, c)
    assert not is_dominant(c, a)

    front_pts, indices = extract_pareto_front(np.array([a, b, c]))
    assert len(indices) == 2  # a and c are non-dominated


def test_exhaustive_search_subset():
    """Run fast exhaustive search on 100 designs to verify optimization loop."""
    exh = run_exhaustive_search(max_designs=100, force_recompute=True)
    assert len(exh.designs) == 100
    assert 0 <= exh.optimum_index < 100
    assert len(exh.pareto_indices) > 0
    assert exh.optimal_result.usable_energy_Wh > 0
    assert exh.eval_time_s < 5.0

