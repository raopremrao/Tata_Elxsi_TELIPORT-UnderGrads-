"""Hardware-Portable QUBO Exporter for Q-Pack.

Exports QUBO formulations as dimod BinaryQuadraticModel (BQM) representations
and JSON coordinate files for execution on D-Wave annealers or gate-model QAOA.
"""

from __future__ import annotations
import json
from pathlib import Path
from typing import Dict, Any, Tuple
import numpy as np

try:
    import dimod
    HAS_DIMOD = True
except ImportError:
    HAS_DIMOD = False

from optimize.qubo_build import QUBOPackage, TOTAL_QUBITS


def qubo_to_dict(qubo: QUBOPackage) -> Dict[Tuple[int, int], float]:
    """Convert QUBO matrix Q to upper-triangular dictionary format."""
    Q = qubo.Q
    K = TOTAL_QUBITS
    qubo_dict = {}

    for i in range(K):
        for j in range(i, K):
            val = float(Q[i, j])
            if abs(val) > 1e-6:
                qubo_dict[(i, j)] = round(val, 4)

    return qubo_dict


def export_qubo_json(qubo: QUBOPackage, output_path: str = "outputs/qubo_model.json") -> str:
    """Export QUBO matrix and metadata to JSON file."""
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)

    qubo_dict = qubo_to_dict(qubo)

    payload = {
        "metadata": {
            "total_qubits": TOTAL_QUBITS,
            "penalty_P": qubo.penalty_P,
            "r2_surrogate_fidelity": qubo.r2_score,
            "spearman_correlation": qubo.spearman_corr,
            "top_k_overlap": qubo.top_k_overlap,
        },
        "qubo_couplings": [
            {"i": i, "j": j, "weight": val}
            for (i, j), val in qubo_dict.items()
        ],
        "linear_biases": {str(i): float(qubo.Q[i, i]) for i in range(TOTAL_QUBITS)},
    }

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)

    return output_path


def export_to_dimod_bqm(qubo: QUBOPackage) -> Any:
    """Construct a dimod.BinaryQuadraticModel instance if dimod is installed."""
    if not HAS_DIMOD:
        return None

    qubo_dict = qubo_to_dict(qubo)
    return dimod.BinaryQuadraticModel.from_qubo(qubo_dict)

