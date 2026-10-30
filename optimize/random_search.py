"""Random Search Baseline Optimizer for PackForge."""

from __future__ import annotations
import time
from typing import List, Tuple, Dict, Any, Optional
import numpy as np

from core.schemas import PackDesign, Scenario, EvaluationResult
from core.data_loader import load_cells
from models.evaluate import evaluate
from optimize.space import enumerate_design_space


def run_random_search(
    scenario: Scenario,
    weights: Dict[str, float],
    budget: int = 100,
    seed: int = 42,
) -> Tuple[PackDesign, EvaluationResult, float, int]:
    """Run random search baseline over feasible configurations.

    Returns:
        (best_design, best_result, runtime_s, evaluations_used)
    """
    t0 = time.perf_counter()
    rng = np.random.default_rng(seed)

    feasible_designs, _ = enumerate_design_space()
    cells = load_cells()

    indices = rng.choice(len(feasible_designs), size=min(budget, len(feasible_designs)), replace=False)

    best_score = float("inf")
    best_design = feasible_designs[indices[0]]
    best_res = None

    for idx in indices:
        d = feasible_designs[idx]
        res = evaluate(d, scenario, fast=True, cell=cells[d.cell_id])

        # Rank score
        crit_fails = sum(1 for f in res.findings if f.severity == "critical")
        req_fails = sum(1 for r in res.requirements.values() if not r.passed)
        score = (crit_fails * 100.0) + (req_fails * 10.0) - (res.usable_energy_Wh / 100.0) + (res.bom_cost_USD / 100.0)

        if score < best_score:
            best_score = score
            best_design = d
            best_res = res

    runtime_s = time.perf_counter() - t0
    return best_design, best_res, runtime_s, len(indices)

