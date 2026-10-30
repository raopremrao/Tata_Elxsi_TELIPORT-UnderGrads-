# PackForge Quantum-Inspired Optimization: QUBO Formulation

This document outlines the mathematical derivation, binary encoding, quadratic surrogate regression, penalty formulations, and hardware portability pipeline implemented in `optimize/qubo_build.py` and `optimize/qubo_sa.py`.

---

## 1. Problem Formulation as a QUBO

Quadratic Unconstrained Binary Optimization (QUBO) seeks to find a binary vector $x \in \{0, 1\}^K$ that minimizes an objective function of the form:
$$E(x) = x^T Q x = \sum_{i=1}^K h_i x_i + \sum_{1 \le i < j \le K} J_{ij} x_i x_j$$
Where:
- $h_i = Q_{ii}$ represents the linear bias on qubit $i$.
- $J_{ij} = Q_{ij} + Q_{ji}$ represents the quadratic coupling between qubits $i$ and $j$.

---

## 2. One-Hot Categorical Encoding ($K = 28$ Qubits)

The discrete battery pack design space consists of 6 categorical parameter groups:

| Group Name | Discrete Choices | Number of Bits | Bit Indices |
| :--- | :--- | :---: | :---: |
| **Cell ID** | Samsung 50E, LG M50LT, Samsung 40T, Panasonic 18650B, Generic LFP 32700 | 5 | 0 to 4 |
| **Series Count ($n_s$)** | 12, 13, 14, 15, 16, 17 | 6 | 5 to 10 |
| **Parallel Count ($n_p$)** | 1, 2, 3, 4, 5, 6, 7, 8 | 8 | 11 to 18 |
| **Cooling Method** | Passive, Forced Air, Cold Plate | 3 | 19 to 21 |
| **BMS Tier** | Basic, Standard, Advanced | 3 | 22 to 24 |
| **Cell Spacing** | 1.0 mm, 2.0 mm, 4.0 mm | 3 | 25 to 27 |
| **Total Qubits** | | **28** | **0 to 27** |

---

## 3. Constraint Penalties

### 3.1 One-Hot Group Constraints
Each group $g$ must select exactly one option: $\sum_{i \in g} x_i = 1$. This is enforced via quadratic penalty:
$$P \left( \sum_{i \in g} x_i - 1 \right)^2 = P \left( \sum_{i \in g} x_i^2 + 2 \sum_{i < j \in g} x_i x_j - 2 \sum_{i \in g} x_i + 1 \right)$$
Since $x_i \in \{0, 1\}$, $x_i^2 = x_i$:
$$= -P \sum_{i \in g} x_i + 2P \sum_{i < j \in g} x_i x_j + P$$
Thus:
- Linear bias adjustment: $Q_{ii} \mathrel{+}= -P$ for $i \in g$.
- Quadratic coupling adjustment: $Q_{ij} \mathrel{+}= 2P$ for $i < j \in g$.
We set $P = 15.0$, calibrated against normalized simulator objectives.

### 3.2 Hard Feasibility Pairwise Penalties ($M_{ij}$)
Certain parameter combinations are provably invalid by first principles:
- **Voltage Violations**: $n_s \times V_{\text{cell,max}} > 60.0\text{ V}$ (breaches extra-low voltage boundary) or nominal voltage $< 44.0\text{ V}$.
- **Extreme Overcurrent**: Low $n_p$ with low-pulse cells (e.g. Panasonic 18650 at $n_p = 1$ under $6.0\text{ kW}$ peak load).
For every such incompatible pair $(i, j)$, a large quadratic penalty $M = 50.0$ is added:
$$Q_{ij} \mathrel{+}= M, \quad Q_{ji} \mathrel{+}= M$$

---

## 4. Quadratic Surrogate Learning

The true battery simulator involves non-linear ODE integrations (`solve_ivp`), terminal voltage sag quadratics, and exponential charging tails. To encode this into QUBO:
1. We evaluate $N = 2,000 \dots 5,000$ feasible designs with the fast simulator.
2. We construct linear features $x_i$ and selected pairwise interaction terms $x_i x_j$ between distinct groups (e.g. $\text{Cell} \times \text{Cooling}$, $n_s \times n_p$, $\text{Cooling} \times \text{Spacing}$).
3. Regularized Ridge regression fits coefficients $h_i$ and $J_{ij}$.
4. Model fidelity ($R^2$, Spearman rank correlation, top-10 overlap) is computed on a held-out test split.

---

## 5. Vectorized Multi-Start Simulated Annealing

To avoid external C-extension build failures, PackForge implements a pure vectorized NumPy simulated annealer:
- Tracks $N_{\text{reads}} = 100$ parallel Markov chains using 2D matrix broadcasting.
- Geometric cooling schedule: $T_{k+1} = \alpha T_k$ from $T_0$ to $T_{\text{final}} = 0.05$.
- Single-bit flip energy difference is computed vectorially in $\mathcal{O}(K)$ per candidate:
  $$\Delta E = \Delta x_i \cdot \left( 2 (Q x)_i + Q_{ii} \Delta x_i \right)$$
- Metropolis criterion: $P_{\text{accept}} = \min(1, \exp(-\Delta E / T))$.
- After annealing, candidates are repaired (argmax per group) and **re-evaluated with the true physics simulator**.

---

## 6. Hardware Portability to D-Wave and QAOA

The generated QUBO matrix $Q$ exports seamlessly via `optimize/export_qubo.py` to:
1. `dimod.BinaryQuadraticModel`: Ready for direct submission to D-Wave Advantage quantum annealers via `dwave-system` / Leap API.
2. Standard JSON / COO matrices: Compatible with QAOA (Quantum Approximate Optimization Algorithm) circuits on IBM Quantum or Amazon Braket.

