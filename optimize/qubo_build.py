"""QUBO Construction, Surrogate Regression, and Binary Encoding for PackForge.

Maps the discrete battery design space into one-hot binary decision variables,
fits a regularized pairwise interaction surrogate Hamiltonian from true simulations,
and enforces one-hot and hard feasibility constraints.
"""

from __future__ import annotations
import itertools
from typing import Dict, List, Tuple, Any, Optional
import numpy as np
from scipy.stats import spearmanr

from core.schemas import PackDesign, CoolingType, BMSTier, ChemistryEnum
from core.data_loader import load_cells
from models.evaluate import evaluate


CELL_LIST = [
    "samsung_inr21700_50e",
    "lg_inr21700_m50lt",
    "samsung_inr21700_40t",
    "panasonic_ncr18650b",
    "generic_lfp_32700",
]
NS_LIST = [12, 13, 14, 15, 16, 17]
NP_LIST = [1, 2, 3, 4, 5, 6, 7, 8]
COOLING_LIST = [CoolingType.PASSIVE, CoolingType.FORCED_AIR, CoolingType.COLD_PLATE]
BMS_LIST = [BMSTier.BASIC, BMSTier.STANDARD, BMSTier.ADVANCED]
SPACING_LIST = [1.0, 2.0, 4.0]

# Variable offsets for one-hot encoding
OFFSETS = {
    "cell": (0, len(CELL_LIST)),
    "ns": (len(CELL_LIST), len(CELL_LIST) + len(NS_LIST)),
    "np": (len(CELL_LIST) + len(NS_LIST), len(CELL_LIST) + len(NS_LIST) + len(NP_LIST)),
    "cooling": (
        len(CELL_LIST) + len(NS_LIST) + len(NP_LIST),
        len(CELL_LIST) + len(NS_LIST) + len(NP_LIST) + len(COOLING_LIST),
    ),
    "bms": (
        len(CELL_LIST) + len(NS_LIST) + len(NP_LIST) + len(COOLING_LIST),
        len(CELL_LIST) + len(NS_LIST) + len(NP_LIST) + len(COOLING_LIST) + len(BMS_LIST),
    ),
    "spacing": (
        len(CELL_LIST) + len(NS_LIST) + len(NP_LIST) + len(COOLING_LIST) + len(BMS_LIST),
        len(CELL_LIST) + len(NS_LIST) + len(NP_LIST) + len(COOLING_LIST) + len(BMS_LIST) + len(SPACING_LIST),
    ),
}

TOTAL_QUBITS = OFFSETS["spacing"][1]  # 5 + 6 + 8 + 3 + 3 + 3 = 28 variables


def design_to_binary(design: PackDesign) -> np.ndarray:
    """Encode a PackDesign into a length-28 binary vector."""
    x = np.zeros(TOTAL_QUBITS, dtype=float)
    if design.cell_id in CELL_LIST:
        x[OFFSETS["cell"][0] + CELL_LIST.index(design.cell_id)] = 1.0
    if design.ns in NS_LIST:
        x[OFFSETS["ns"][0] + NS_LIST.index(design.ns)] = 1.0
    if design.np in NP_LIST:
        x[OFFSETS["np"][0] + NP_LIST.index(design.np)] = 1.0
    if design.cooling in COOLING_LIST:
        x[OFFSETS["cooling"][0] + COOLING_LIST.index(design.cooling)] = 1.0
    if design.bms_tier in BMS_LIST:
        x[OFFSETS["bms"][0] + BMS_LIST.index(design.bms_tier)] = 1.0
    if design.cell_spacing_mm in SPACING_LIST:
        x[OFFSETS["spacing"][0] + SPACING_LIST.index(design.cell_spacing_mm)] = 1.0
    return x


def binary_to_design(x: np.ndarray, name: str = "QUBO Candidate") -> PackDesign:
    """Decode a binary vector into a PackDesign, repairing any non-one-hot states."""
    # Repair logic: argmax within each slice
    cell_idx = int(np.argmax(x[OFFSETS["cell"][0] : OFFSETS["cell"][1]]))
    ns_idx = int(np.argmax(x[OFFSETS["ns"][0] : OFFSETS["ns"][1]]))
    np_idx = int(np.argmax(x[OFFSETS["np"][0] : OFFSETS["np"][1]]))
    cool_idx = int(np.argmax(x[OFFSETS["cooling"][0] : OFFSETS["cooling"][1]]))
    bms_idx = int(np.argmax(x[OFFSETS["bms"][0] : OFFSETS["bms"][1]]))
    sp_idx = int(np.argmax(x[OFFSETS["spacing"][0] : OFFSETS["spacing"][1]]))

    return PackDesign(
        name=name,
        cell_id=CELL_LIST[cell_idx],
        ns=NS_LIST[ns_idx],
        np=NP_LIST[np_idx],
        cooling=COOLING_LIST[cool_idx],
        bms_tier=BMS_LIST[bms_idx],
        cell_spacing_mm=SPACING_LIST[sp_idx],
    )


class QUBOPackage:
    def __init__(
        self,
        Q: np.ndarray,
        h: np.ndarray,
        J: np.ndarray,
        r2_score: float,
        spearman_corr: float,
        top_k_overlap: float,
        penalty_P: float,
    ):
        self.Q = Q
        self.h = h
        self.J = J
        self.r2_score = r2_score
        self.spearman_corr = spearman_corr
        self.top_k_overlap = top_k_overlap
        self.penalty_P = penalty_P


def build_qubo_model(
    sample_designs: List[PackDesign],
    sample_scores: np.ndarray,
    penalty_P: float = 15.0,
    penalty_M: float = 50.0,
) -> QUBOPackage:
    """Fit quadratic surrogate parameters h and J and assemble QUBO matrix Q."""
    n_samples = len(sample_designs)
    K = TOTAL_QUBITS

    # Construct one-hot feature vectors: linear (K) and pairwise interaction terms
    # To prevent overfitting, select interactions between distinct groups
    group_pairs = [
        ("cell", "ns"),
        ("cell", "np"),
        ("cell", "cooling"),
        ("ns", "np"),
        ("ns", "cooling"),
        ("cooling", "spacing"),
    ]

    pair_indices: List[Tuple[int, int]] = []
    for g1, g2 in group_pairs:
        s1, e1 = OFFSETS[g1]
        s2, e2 = OFFSETS[g2]
        for i in range(s1, e1):
            for j in range(s2, e2):
                pair_indices.append((i, j))

    n_features = K + len(pair_indices)
    X = np.zeros((n_samples, n_features), dtype=float)

    for idx, d in enumerate(sample_designs):
        x_bin = design_to_binary(d)
        X[idx, :K] = x_bin
        for p_idx, (i, j) in enumerate(pair_indices):
            X[idx, K + p_idx] = x_bin[i] * x_bin[j]

    # Split into train / test sets (80 / 20)
    split = int(0.80 * n_samples)
    X_train, X_test = X[:split], X[split:]
    y_train, y_test = sample_scores[:split], sample_scores[split:]

    # Regularized Ridge regression in pure NumPy: w = (X^T X + alpha * I)^(-1) X^T y
    alpha_ridge = 1.0
    xtx = X_train.T @ X_train
    a_mat = xtx + alpha_ridge * np.eye(X_train.shape[1])
    weights = np.linalg.solve(a_mat, X_train.T @ y_train)

    # Fidelity metrics on held-out set
    y_pred = X_test @ weights
    ss_tot = np.sum((y_test - np.mean(y_test)) ** 2)
    ss_res = np.sum((y_test - y_pred) ** 2)
    r2 = float(1.0 - (ss_res / max(1e-6, ss_tot)))
    r2 = max(0.0, r2)

    spearman, _ = spearmanr(y_test, y_pred)
    spearman = float(spearman)

    # Top-10 overlap
    k = min(10, len(y_test))
    top_true = set(np.argsort(y_test)[:k])
    top_pred = set(np.argsort(y_pred)[:k])
    top_overlap = float(len(top_true.intersection(top_pred)) / k)

    # Map regression coefficients to linear h and quadratic J
    h = weights[:K].copy()
    J = np.zeros((K, K), dtype=float)

    for p_idx, (i, j) in enumerate(pair_indices):
        coeff = weights[K + p_idx]
        J[i, j] += coeff / 2.0
        J[j, i] += coeff / 2.0

    # Assemble QUBO matrix Q: E(x) = x^T Q x
    # Note: for binary x_i in {0,1}, x_i^2 = x_i, so linear terms go on diagonal
    Q = J.copy()
    for i in range(K):
        Q[i, i] += h[i]

    # Add One-Hot Constraint Penalties: P * (sum_{i in g} x_i - 1)^2
    # = P * (-sum x_i + 2 * sum_{i < j} x_i x_j) + const
    for group_name, (start, end) in OFFSETS.items():
        for i in range(start, end):
            Q[i, i] -= penalty_P
            for j in range(i + 1, end):
                Q[i, j] += 2.0 * penalty_P
                Q[j, i] += 2.0 * penalty_P

    # Add Hard Feasibility Penalties (M) for provably infeasible variable pairs
    cells = load_cells()
    for c_idx, cell_id in enumerate(CELL_LIST):
        cell = cells[cell_id]
        c_bit = OFFSETS["cell"][0] + c_idx
        # Check series counts that violate 60V ELV limit
        for ns_idx, ns_val in enumerate(NS_LIST):
            ns_bit = OFFSETS["ns"][0] + ns_idx
            if (ns_val * cell.max_voltage_V) > 60.0 or (ns_val * cell.nominal_voltage_V) < 44.0:
                Q[c_bit, ns_bit] += penalty_M
                Q[ns_bit, c_bit] += penalty_M

        # Check parallel counts that cause severe cell overcurrent at peak
        for np_idx, np_val in enumerate(NP_LIST):
            np_bit = OFFSETS["np"][0] + np_idx
            if (136.0 / np_val) > (cell.max_pulse_discharge_A * 1.15):
                Q[c_bit, np_bit] += penalty_M
                Q[np_bit, c_bit] += penalty_M

    return QUBOPackage(
        Q=Q,
        h=h,
        J=J,
        r2_score=round(r2, 3),
        spearman_corr=round(spearman, 3),
        top_k_overlap=round(top_overlap, 3),
        penalty_P=penalty_P,
    )
