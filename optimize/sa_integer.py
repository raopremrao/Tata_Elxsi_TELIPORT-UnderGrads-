"""Classical Integer Simulated Annealing Optimizer for Q-Pack.

Operates directly on discrete integer indices with the true physics simulator
in the loop and Metropolis acceptance criteria.
"""

from __future__ import annotations
import time
import copy
from typing import List, Tuple, Dict, Any, Optional
import numpy as np

from core.schemas import PackDesign, Scenario, EvaluationResult
from core.data_loader import load_cells
from models.evaluate import evaluate
from optimize.qubo_build import (
    CELL_LIST,
    NS_LIST,
    NP_LIST,
    COOLING_LIST,
    BMS_LIST,
    SPACING_LIST,
)


def run_integer_sa(
    scenario: Scenario,
    weights: Dict[str, float],
    n_steps: int = 100,
    seed: int = 42,
) -> Tuple[PackDesign, EvaluationResult, float, int]:
    """Execute classical integer SA with simulator in the loop."""
    t0 = time.perf_counter()
    rng = np.random.default_rng(seed)
    cells = load_cells()

    # Current parameter indices: [cell, ns, np, cool, bms, spacing]
    current_idx = [
        rng.integers(0, len(CELL_LIST)),
        rng.integers(0, len(NS_LIST)),
        rng.integers(0, len(NP_LIST)),
        rng.integers(0, len(COOLING_LIST)),
        rng.integers(0, len(BMS_LIST)),
        rng.integers(0, len(SPACING_LIST)),
    ]

    def indices_to_design(idx: List[int]) -> PackDesign:
        return PackDesign(
            name="Integer SA Candidate",
            cell_id=CELL_LIST[idx[0]],
            ns=NS_LIST[idx[1]],
            np=NP_LIST[idx[2]],
            cooling=COOLING_LIST[idx[3]],
            bms_tier=BMS_LIST[idx[4]],
            cell_spacing_mm=SPACING_LIST[idx[5]],
        )

    def eval_score(design: PackDesign) -> Tuple[float, EvaluationResult]:
        res = evaluate(design, scenario, fast=True, cell=cells[design.cell_id])
        crit_fails = sum(1 for f in res.findings if f.severity == "critical")
        req_fails = sum(1 for r in res.requirements.values() if not r.passed)
        score = (crit_fails * 100.0) + (req_fails * 10.0) - (res.usable_energy_Wh / 100.0) + (res.bom_cost_USD / 100.0)
        return score, res

    current_design = indices_to_design(current_idx)
    current_score, current_res = eval_score(current_design)

    best_design = current_design
    best_score = current_score
    best_res = current_res

    dim_lens = [
        len(CELL_LIST),
        len(NS_LIST),
        len(NP_LIST),
        len(COOLING_LIST),
        len(BMS_LIST),
        len(SPACING_LIST),
    ]

    t_init = 10.0
    t_final = 0.1
    alpha = (t_final / t_init) ** (1.0 / max(1, n_steps))
    temp = t_init

    eval_count = 1

    for step in range(n_steps):
        neighbor_idx = copy.copy(current_idx)
        # Mutate 1 or 2 discrete parameters
        dim_to_change = rng.integers(0, 6)
        neighbor_idx[dim_to_change] = rng.integers(0, dim_lens[dim_to_change])

        neighbor_design = indices_to_design(neighbor_idx)
        neighbor_score, neighbor_res = eval_score(neighbor_design)
        eval_count += 1

        delta = neighbor_score - current_score
        if delta < 0.0 or rng.random() < np.exp(-delta / temp):
            current_idx = neighbor_idx
            current_score = neighbor_score
            current_res = neighbor_res

            if current_score < best_score:
                best_score = current_score
                best_design = current_design
                best_res = current_res

        temp *= alpha

    runtime_s = time.perf_counter() - t0
    return best_design, best_res, runtime_s, eval_count

