"""Q-Pack Optimization Engine: Space, Solvers, QUBO, and Benchmark Suite."""

from optimize.space import enumerate_design_space, get_baseline_designs
from optimize.exhaustive import run_exhaustive_search, ExhaustiveResults
from optimize.random_search import run_random_search
from optimize.sa_integer import run_integer_sa
from optimize.nsga2 import run_nsga2
from optimize.qubo_build import build_qubo_model, design_to_binary, binary_to_design
from optimize.qubo_sa import solve_qubo_vectorized_sa, solve_qubo_with_reevaluation
from optimize.pareto import is_dominant, extract_pareto_front, compute_hypervolume_2d
from optimize.benchmark import run_benchmark_suite

__all__ = [
    "enumerate_design_space",
    "get_baseline_designs",
    "run_exhaustive_search",
    "ExhaustiveResults",
    "run_random_search",
    "run_integer_sa",
    "run_nsga2",
    "build_qubo_model",
    "design_to_binary",
    "binary_to_design",
    "solve_qubo_vectorized_sa",
    "solve_qubo_with_reevaluation",
    "is_dominant",
    "extract_pareto_front",
    "compute_hypervolume_2d",
    "run_benchmark_suite",
]

