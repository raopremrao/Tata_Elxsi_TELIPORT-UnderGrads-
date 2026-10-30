"""NSGA-II Multi-Objective Evolutionary Optimizer for PackForge."""

from __future__ import annotations
import time
from typing import List, Tuple, Dict, Any, Optional
import numpy as np

try:
    from pymoo.core.problem import ElementwiseProblem
    from pymoo.algorithms.moo.nsga2 import NSGA2
    from pymoo.operators.sampling.rnd import IntegerRandomSampling
    from pymoo.operators.crossover.sbx import SBX
    from pymoo.operators.mutation.pm import PM
    from pymoo.optimize import minimize
    HAS_PYMOO = True
except ImportError:
    HAS_PYMOO = False

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


def run_nsga2(
    scenario: Scenario,
    pop_size: int = 20,
    n_gen: int = 5,
    seed: int = 42,
) -> Tuple[List[PackDesign], List[EvaluationResult], float, int]:
    """Execute NSGA-II multi-objective optimization.

    Objectives minimized: [BOM Cost, Peak Temp, -Usable Energy]
    """
    t0 = time.perf_counter()
    cells = load_cells()
    eval_count = 0

    if not HAS_PYMOO:
        # Fallback to simple random Pareto sampling if pymoo is absent
        from optimize.random_search import run_random_search
        d, r, rt, ev = run_random_search(scenario, {}, budget=pop_size * n_gen, seed=seed)
        return [d], [r], rt, ev

    class BatteryOptimizationProblem(ElementwiseProblem):
        def __init__(self):
            super().__init__(
                n_var=6,
                n_obj=3,
                n_ieq_constr=2,
                xl=np.array([0, 0, 0, 0, 0, 0]),
                xu=np.array([
                    len(CELL_LIST) - 1,
                    len(NS_LIST) - 1,
                    len(NP_LIST) - 1,
                    len(COOLING_LIST) - 1,
                    len(BMS_LIST) - 1,
                    len(SPACING_LIST) - 1,
                ]),
            )
            self.eval_records = []

        def _evaluate(self, x, out, *args, **kwargs):
            nonlocal eval_count
            eval_count += 1

            design = PackDesign(
                name="NSGA-II Candidate",
                cell_id=CELL_LIST[int(x[0])],
                ns=NS_LIST[int(x[1])],
                np=NP_LIST[int(x[2])],
                cooling=COOLING_LIST[int(x[3])],
                bms_tier=BMS_LIST[int(x[4])],
                cell_spacing_mm=SPACING_LIST[int(x[5])],
            )

            res = evaluate(design, scenario, fast=True, cell=cells[design.cell_id])
            self.eval_records.append((design, res))

            # Objectives to minimize: Cost, Peak Temp, -Usable Energy
            f1 = res.bom_cost_USD
            f2 = res.peak_temp_C
            f3 = -res.usable_energy_Wh

            # Constraints: ELV V_max <= 60V, Peak current margin
            g1 = res.max_voltage_V - 60.0
            g2 = res.max_cell_current_peak_A - cells[design.cell_id].max_pulse_discharge_A

            out["F"] = [f1, f2, f3]
            out["G"] = [g1, g2]

    problem = BatteryOptimizationProblem()
    algorithm = NSGA2(
        pop_size=pop_size,
        sampling=IntegerRandomSampling(),
        crossover=SBX(prob=0.9, eta=15, vtype=float),
        mutation=PM(eta=20, vtype=float),
        eliminate_duplicates=True,
    )

    res = minimize(
        problem,
        algorithm,
        ("n_gen", n_gen),
        seed=seed,
        verbose=False,
    )

    runtime_s = time.perf_counter() - t0

    # Extract non-dominated front designs
    front_designs = [d for d, r in problem.eval_records[-pop_size:]]
    front_results = [r for d, r in problem.eval_records[-pop_size:]]

    return front_designs, front_results, runtime_s, eval_count

