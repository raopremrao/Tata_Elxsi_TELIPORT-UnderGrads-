"""Pareto Utilities: Dominance, Non-Dominated Sorting, Hypervolume, and Generational Distance."""

from __future__ import annotations
from typing import List, Tuple
import numpy as np


def is_dominant(a: np.ndarray, b: np.ndarray) -> bool:
    """Return True if vector a dominates vector b (all objectives minimized)."""
    return bool(np.all(a <= b) and np.any(a < b))


def extract_pareto_front(objectives: np.ndarray) -> Tuple[np.ndarray, List[int]]:
    """Extract non-dominated Pareto front indices from objective matrix (N, M).

    Returns:
        (pareto_objectives, pareto_indices)
    """
    n = len(objectives)
    pareto_indices = []

    for i in range(n):
        dominated = False
        for j in range(n):
            if i != j and is_dominant(objectives[j], objectives[i]):
                dominated = True
                break
        if not dominated:
            pareto_indices.append(i)

    return objectives[pareto_indices], pareto_indices


def compute_hypervolume_2d(front: np.ndarray, ref_point: np.ndarray) -> float:
    """Compute 2D hypervolume bounded by reference point for minimization.

    front: shape (K, 2)
    ref_point: shape (2,)
    """
    if len(front) == 0:
        return 0.0

    # Filter points that exceed the reference point
    valid = np.all(front <= ref_point, axis=1)
    pts = front[valid]
    if len(pts) == 0:
        return 0.0

    # Sort by first objective
    order = np.argsort(pts[:, 0])
    pts_sorted = pts[order]

    hv = 0.0
    current_y = ref_point[1]

    for p in pts_sorted:
        dx = ref_point[0] - p[0]
        dy = max(0.0, current_y - p[1])
        hv += dx * dy
        current_y = min(current_y, p[1])

    return float(hv)


def compute_generational_distance(front: np.ndarray, true_front: np.ndarray) -> float:
    """Compute generational distance (average Euclidean distance to closest true Pareto point)."""
    if len(front) == 0 or len(true_front) == 0:
        return 1.0

    distances = []
    for p in front:
        dists = np.linalg.norm(true_front - p, axis=1)
        distances.append(np.min(dists))

    return float(np.mean(distances))

