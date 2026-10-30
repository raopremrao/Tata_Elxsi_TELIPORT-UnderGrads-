"""Exhaustive Evaluation and Ground-Truth Generator for Q-Pack.

Evaluates all structurally feasible configurations in the discrete design space,
yielding the true global optimum and true Pareto front for benchmark comparison.
"""

from __future__ import annotations
import time
from typing import Dict, List, Tuple, Optional
import numpy as np
import pandas as pd

from core.schemas import PackDesign, Scenario, EvaluationResult
from core.data_loader import load_cells
from models.evaluate import evaluate
from optimize.space import enumerate_design_space
from optimize.pareto import extract_pareto_front


class ExhaustiveResults:
    def __init__(
        self,
        designs: List[PackDesign],
        results: List[EvaluationResult],
        objective_matrix: np.ndarray,
        scalar_scores: np.ndarray,
        optimum_index: int,
        pareto_indices: List[int],
        bounds: Dict[str, Tuple[float, float]],
        eval_time_s: float,
    ):
        self.designs = designs
        self.results = results
        self.objective_matrix = objective_matrix
        self.scalar_scores = scalar_scores
        self.optimum_index = optimum_index
        self.pareto_indices = pareto_indices
        self.bounds = bounds
        self.eval_time_s = eval_time_s

    @property
    def optimal_design(self) -> PackDesign:
        return self.designs[self.optimum_index]

    @property
    def optimal_result(self) -> EvaluationResult:
        return self.results[self.optimum_index]

    @property
    def pareto_designs(self) -> List[PackDesign]:
        return [self.designs[i] for i in self.pareto_indices]

    @property
    def pareto_results(self) -> List[EvaluationResult]:
        return [self.results[i] for i in self.pareto_indices]


_EXHAUSTIVE_CACHE: Optional[ExhaustiveResults] = None


def run_exhaustive_search(
    scenario: Optional[Scenario] = None,
    weights: Optional[Dict[str, float]] = None,
    max_designs: Optional[int] = None,
    force_recompute: bool = False,
) -> ExhaustiveResults:
    """Evaluate all feasible designs to obtain ground truth."""
    global _EXHAUSTIVE_CACHE

    if _EXHAUSTIVE_CACHE is not None and not force_recompute and max_designs is None:
        return _EXHAUSTIVE_CACHE

    if scenario is None:
        scenario = Scenario()

    if weights is None:
        weights = {
            "cost": 0.25,
            "peak_temp": 0.20,
            "mass": 0.15,
            "charge_time": 0.15,
            "usable_energy": 0.15,
            "cycle_life": 0.10,
        }

    t0 = time.perf_counter()
    feasible_designs, _ = enumerate_design_space()
    if max_designs is not None:
        feasible_designs = feasible_designs[:max_designs]

    cells = load_cells()
    results: List[EvaluationResult] = []

    for d in feasible_designs:
        res = evaluate(d, scenario, fast=True, cell=cells[d.cell_id])
        results.append(res)

    # Extract raw metrics
    costs = np.array([r.bom_cost_USD for r in results])
    temps = np.array([r.peak_temp_C for r in results])
    masses = np.array([r.pack_mass_kg for r in results])
    chg_times = np.array([r.charge_time_min for r in results])
    energies = np.array([r.usable_energy_Wh for r in results])
    lives = np.array([float(r.estimated_cycle_life) for r in results])

    bounds = {
        "cost": (float(np.min(costs)), float(np.max(costs))),
        "peak_temp": (float(np.min(temps)), float(np.max(temps))),
        "mass": (float(np.min(masses)), float(np.max(masses))),
        "charge_time": (float(np.min(chg_times)), float(np.max(chg_times))),
        "usable_energy": (float(np.min(energies)), float(np.max(energies))),
        "cycle_life": (float(np.min(lives)), float(np.max(lives))),
    }

    def normalize(val: np.ndarray, key: str) -> np.ndarray:
        v_min, v_max = bounds[key]
        if v_max <= v_min:
            return np.zeros_like(val)
        return (val - v_min) / (v_max - v_min)

    # Objectives to minimize (0 is best, 1 is worst)
    norm_cost = normalize(costs, "cost")
    norm_temp = normalize(temps, "peak_temp")
    norm_mass = normalize(masses, "mass")
    norm_chg = normalize(chg_times, "charge_time")
    norm_energy = 1.0 - normalize(energies, "usable_energy")  # Maximize energy -> minimize (1 - norm)
    norm_life = 1.0 - normalize(lives, "cycle_life")          # Maximize life -> minimize (1 - norm)

    # Penalty for failing hard requirements
    hard_penalties = np.zeros(len(results))
    for idx, r in enumerate(results):
        penalty = 0.0
        # R-01 (46-54V)
        if not r.requirements["R-01"].passed:
            penalty += 10.0
        # R-02 (<=60V)
        if not r.requirements["R-02"].passed:
            penalty += 20.0
        # R-03 (>=2000 Wh)
        if not r.requirements["R-03"].passed:
            penalty += 5.0
        # Critical findings penalty
        crit_count = sum(1 for f in r.findings if f.severity == "critical")
        penalty += crit_count * 15.0
        hard_penalties[idx] = penalty

    scalar_scores = (
        weights["cost"] * norm_cost
        + weights["peak_temp"] * norm_temp
        + weights["mass"] * norm_mass
        + weights["charge_time"] * norm_chg
        + weights["usable_energy"] * norm_energy
        + weights["cycle_life"] * norm_life
        + hard_penalties
    )

    optimum_index = int(np.argmin(scalar_scores))

    # Multi-objective matrix for Pareto extraction: [Cost, Peak Temp, -Usable Energy]
    obj_matrix = np.column_stack([norm_cost, norm_temp, norm_energy])
    _, pareto_indices = extract_pareto_front(obj_matrix)

    eval_time_s = round(time.perf_counter() - t0, 2)

    exhaustive_res = ExhaustiveResults(
        designs=feasible_designs,
        results=results,
        objective_matrix=obj_matrix,
        scalar_scores=scalar_scores,
        optimum_index=optimum_index,
        pareto_indices=pareto_indices,
        bounds=bounds,
        eval_time_s=eval_time_s,
    )

    if max_designs is None:
        _EXHAUSTIVE_CACHE = exhaustive_res

    return exhaustive_res


def compute_scalar_score(
    res: EvaluationResult,
    bounds: Dict[str, Tuple[float, float]],
    weights: Optional[Dict[str, float]] = None,
) -> float:
    """Compute normalized scalar score matching exhaustive.py formulation."""
    if weights is None:
        weights = {
            "cost": 0.25,
            "peak_temp": 0.20,
            "mass": 0.15,
            "charge_time": 0.15,
            "usable_energy": 0.15,
            "cycle_life": 0.10,
        }

    def norm(val: float, key: str) -> float:
        v_min, v_max = bounds[key]
        if v_max <= v_min:
            return 0.0
        return float(np.clip((val - v_min) / (v_max - v_min), 0.0, 1.0))

    norm_cost = norm(res.bom_cost_USD, "cost")
    norm_temp = norm(res.peak_temp_C, "peak_temp")
    norm_mass = norm(res.pack_mass_kg, "mass")
    norm_chg = norm(res.charge_time_min, "charge_time")
    norm_energy = 1.0 - norm(res.usable_energy_Wh, "usable_energy")
    norm_life = 1.0 - norm(float(res.estimated_cycle_life), "cycle_life")

    penalty = 0.0
    if not res.requirements["R-01"].passed:
        penalty += 10.0
    if not res.requirements["R-02"].passed:
        penalty += 20.0
    if not res.requirements["R-03"].passed:
        penalty += 5.0
    crit_count = sum(1 for f in res.findings if f.severity == "critical")
    penalty += crit_count * 15.0

    return (
        weights["cost"] * norm_cost
        + weights["peak_temp"] * norm_temp
        + weights["mass"] * norm_mass
        + weights["charge_time"] * norm_chg
        + weights["usable_energy"] * norm_energy
        + weights["cycle_life"] * norm_life
        + penalty
    )
