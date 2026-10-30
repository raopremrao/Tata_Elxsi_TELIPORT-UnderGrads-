"""High-Performance Vectorized NumPy Simulated Annealing for QUBO.

Vectorized over multiple parallel reads with geometric cooling schedule,
automatic bit repair, and mandatory true-simulator re-evaluation.
"""

from __future__ import annotations
import time
from typing import List, Tuple, Dict, Any, Optional
import numpy as np

from core.schemas import PackDesign, Scenario, EvaluationResult
from core.data_loader import load_cells
from models.evaluate import evaluate
from optimize.qubo_build import (
    TOTAL_QUBITS,
    OFFSETS,
    QUBOPackage,
    binary_to_design,
    design_to_binary,
)


def solve_qubo_vectorized_sa(
    qubo: QUBOPackage,
    n_reads: int = 100,
    n_sweeps: int = 200,
    t_initial: Optional[float] = None,
    t_final: float = 0.05,
    seed: int = 42,
) -> Tuple[np.ndarray, np.ndarray]:
    """Execute vectorized multi-start simulated annealing in pure NumPy.

    Returns:
        (best_samples, best_energies) of shape (n_reads, K) and (n_reads,)
    """
    rng = np.random.default_rng(seed)
    K = TOTAL_QUBITS
    Q = qubo.Q

    # Auto-calibrate initial temperature from scale of Q transitions
    if t_initial is None:
        diag_std = float(np.std(np.diag(Q)))
        t_initial = max(5.0, diag_std * 2.0)

    # Initialize random binary states shape: (n_reads, K)
    # Start with valid one-hot states to seed the chains nicely
    states = np.zeros((n_reads, K), dtype=float)
    for group_name, (start, end) in OFFSETS.items():
        chosen_indices = rng.integers(start, end, size=n_reads)
        for r in range(n_reads):
            states[r, chosen_indices[r]] = 1.0

    # Geometric cooling decay rate
    alpha = (t_final / t_initial) ** (1.0 / max(1, n_sweeps))
    temp = t_initial

    # Vectorized Metropolis annealing sweeps
    for sweep in range(n_sweeps):
        # In each sweep, propose flips for all variables in random order
        var_order = rng.permutation(K)
        for bit in var_order:
            current_vals = states[:, bit]  # shape: (n_reads,)
            proposed_vals = 1.0 - current_vals
            delta_val = proposed_vals - current_vals  # +1 if 0->1, -1 if 1->0

            # Delta Energy for flipping bit i:
            # dE = delta_val * (2 * (Q @ state) + Q[bit, bit] * delta_val)
            q_dot_state = states @ Q[:, bit]
            dE = delta_val * (2.0 * q_dot_state + Q[bit, bit] * delta_val)

            # Metropolis acceptance criterion: accept if dE <= 0 or rand < exp(-dE / T)
            accept_prob = np.exp(-np.clip(dE / temp, -50.0, 50.0))
            accept = (dE <= 0.0) | (rng.random(n_reads) < accept_prob)

            # Apply accepted bit flips
            states[accept, bit] = proposed_vals[accept]

        temp *= alpha

    # Compute final energies: E = diag(states @ Q @ states.T)
    energies = np.einsum("ri,ij,rj->r", states, Q, states)
    sort_order = np.argsort(energies)

    return states[sort_order], energies[sort_order]


def solve_qubo_with_reevaluation(
    qubo: QUBOPackage,
    scenario: Optional[Scenario] = None,
    bounds: Optional[Dict[str, Tuple[float, float]]] = None,
    weights: Optional[Dict[str, float]] = None,
    n_reads: int = 100,
    n_sweeps: int = 200,
    seed: int = 42,
) -> Tuple[PackDesign, EvaluationResult, List[EvaluationResult]]:
    """Solve QUBO, decode designs, repair one-hot, and re-evaluate with true simulator.

    Returns:
        (best_design, best_true_result, top_candidate_results)
    """
    from optimize.exhaustive import compute_scalar_score

    if scenario is None:
        scenario = Scenario()

    samples, qubo_energies = solve_qubo_vectorized_sa(
        qubo=qubo,
        n_reads=n_reads,
        n_sweeps=n_sweeps,
        seed=seed,
    )

    cells = load_cells()
    evaluated_candidates: List[EvaluationResult] = []
    seen_hashes = set()

    for idx in range(min(len(samples), 40)):
        design = binary_to_design(samples[idx], name=f"QUBO Candidate {idx}")
        design_key = (design.cell_id, design.ns, design.np, design.cooling.value, design.bms_tier.value, design.cell_spacing_mm)

        if design_key in seen_hashes:
            continue
        seen_hashes.add(design_key)

        # RE-EVALUATE with true physics models!
        true_res = evaluate(design, scenario, fast=True, cell=cells[design.cell_id])
        evaluated_candidates.append(true_res)

    if bounds is not None:
        evaluated_candidates.sort(key=lambda r: compute_scalar_score(r, bounds, weights))
    else:
        def design_rank_key(res: EvaluationResult) -> float:
            crit_fails = sum(1 for f in res.findings if f.severity == "critical")
            req_fails = sum(1 for r in res.requirements.values() if not r.passed)
            return (crit_fails * 100.0) + (req_fails * 10.0) - (res.usable_energy_Wh / 100.0) + (res.bom_cost_USD / 100.0)
        evaluated_candidates.sort(key=design_rank_key)

    best_res = evaluated_candidates[0]
    best_design = best_res.design

    return best_design, best_res, evaluated_candidates
