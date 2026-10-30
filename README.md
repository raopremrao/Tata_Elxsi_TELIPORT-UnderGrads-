# Q-Pack ⚡
### Reusable Digital Platform for Designing Battery Energy Systems
**Tata Elxsi TELIPORT Season 4 — Case Study 2**

> *"From cell datasheet to defensible battery design in minutes."*

---

## ⚡ 60-Second Quickstart

```bash
# 1. Setup virtual environment and dependencies
make setup

# 2. Run the full unit and integration test suite
make test

# 3. Execute the multi-seed benchmark harness
make quick-benchmark

# 4. Generate the 300 DPI presentation slide assets
make report

# 5. Launch the interactive Streamlit dashboard
make run
```
Access the web dashboard in your browser at `http://localhost:8501`.

---

## 📌 Executive Overview

Q-Pack is an engineering platform that synthesizes battery pack configurations for **48 V-class light electric mobility** (electric scooters and motorcycles). It replaces fragmented spreadsheets and disconnected CAD/CFD tools with a unified, multi-disciplinary parameter bus coupled with a **quantum-inspired QUBO optimization engine**.

### Core Platform Capabilities
1. **Multi-Disciplinary Synthesis**: Couples electrical voltage sag, lumped thermal ODE (`solve_ivp`), 2D spatial cell conduction heatmaps, CC-CV charging with thermal derating, mechanical mass/dimensions, and itemized BOM costing in a single loop.
2. **Quantum-Inspired QUBO Engine**: Encodes the discrete design space into a 28-qubit binary Hamiltonian with quadratic surrogate learning ($R^2 = 0.918$, Spearman $= 0.937$), solved via vectorized multi-start Simulated Annealing in pure NumPy.
3. **Hardware Portability Without Quantum Claims**: Formulated as standard `dimod.BinaryQuadraticModel` (BQM) exportable to physical D-Wave quantum annealers and gate-model QAOA circuits, benchmarked honestly against classical evolutionary algorithms (NSGA-II) and exhaustive ground truth.
4. **End-to-End Traceability & Conflict Engine**: Tracks 10 automated multidisciplinary conflict rules (ELV > 60V breaches, thermal cooling capacity, sensing gaps) linked through a NetworkX dependency graph.
5. **Manufacturing Reliability**: Propagates stochastic cell-to-cell capacity ($\pm 2\%$) and resistance ($\pm 8\%$) variations through $N=500$ Monte Carlo runs to quantify weakest-group capacity bottlenecks (P5/P50/P95).

---

## 📊 Baseline Architecture Comparison

All values computed directly from the Q-Pack physics engine under the reference 30-minute urban drive cycle:

| Architectural Metric | Design 0 (Starting Baseline) | Design A (Engineer's Choice) | Design B (LFP Safety-First) | Design Q (Optimizer Recommendation) | Target Requirement |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **Cell Selection** | Panasonic NCR18650B | Samsung INR21700-50E | Generic LFP 32700 | Generic LFP 32700 | Datasheet Verified |
| **Configuration** | 13S 2P | 14S 4P | 15S 3P | 15S 8P | 46V - 54V (R-01) |
| **Cooling Method** | Passive Air | Forced Air Fans | Forced Air Fans | Passive Air | Convection HTC |
| **Nominal Pack Voltage** | 46.8 V | 50.8 V | 48.0 V | 48.0 V | 46.0 - 54.0 V (R-01) |
| **Usable Pack Energy** | 247.9 Wh | 878.0 Wh | 771.8 Wh | **2,110.5 Wh** | $\ge 2,000\text{ Wh}$ (R-03) |
| **Peak Operating Temp** | 560.9 °C (Thermal Runaway) | 67.9 °C | 48.3 °C | **37.9 °C** | $\le 45.0\ ^\circ\text{C}$ (R-05) |
| **Total Pack Mass** | 1.9 kg | 6.2 kg | 9.1 kg | 21.2 kg | $\le 18.0\text{ kg}$ (R-07) |
| **BOM Cost** | $128.18 | $392.20 | $386.35 | $831.98 | $\le \$450$ (R-08) |
| **Requirements Satisfied**| 3 / 12 | 8 / 12 | 8 / 12 | **9 / 12** | 12 / 12 |

---

## 🔬 Multi-Seed Benchmark Summary (30 Seeds)

Evaluated against Exhaustive Ground Truth (1,053 feasible designs) and baseline solvers:

| Solver Algorithm | Median Optimality Gap (%) | Success Rate (≤1% Gap) | Mean Runtime (s) | True Simulator Evaluations | Primary Value Proposition |
| :--- | :---: | :---: | :---: | :---: | :--- |
| **Exhaustive Ground Truth** | **0.00%** | **100.0%** | 2.03 s | 1,053 calls | Exact reference baseline & true Pareto front. |
| **QUBO + Vectorized SA** | **2.05%** | **40.0%** | 0.044 s | 500 (fit) + 37 (re-eval) | **Hardware-portable to D-Wave; <10ms instant re-solve across weights.** |
| **NSGA-II (Evolutionary)** | 1439.28% | 0.0% | 0.039 s | 99 calls | Multi-objective genetic search (frequently stuck in infeasible bounds). |
| **Random Search Baseline** | 11.71% | 3.3% | 0.016 s | 100 calls | Budget-matched uniform sampling. |

> **Scientific Honesty Statement**: Evolutionary search is more sample-efficient for static one-time optimization. QUBO's advantage lies in its physical coupling interpretability ($J_{ij}$), instantaneous weight re-solving (<10 ms), and hardware portability to physical quantum annealers.

---

## 📁 Repository Structure

```
q-pack/
├── app/                        # 12-page Streamlit web platform
│   ├── Home.py                 # Executive overview & 1-click demo
│   ├── theme.py                # Styling, CSS, and Plotly color templates
│   └── pages/                  # 11 interactive subpages
├── core/                       # Shared schemas, units, and parameter bus
│   ├── schemas.py              # Pydantic v2 data models
│   ├── units.py                # Physical unit conversion functions
│   ├── context.py              # DesignContext reactive parameter bus
│   └── data_loader.py          # Cached YAML/CSV loader
├── models/                     # Multi-disciplinary physics engine
│   ├── electrical.py           # OCV-SoC curves, voltage sag, impedance
│   ├── thermal.py              # Lumped ODE solve_ivp & 2D spatial gradient
│   ├── mechanical.py           # Packing density, dimensions, mass
│   ├── charging.py             # CC-CV integration with thermal derating
│   ├── cost.py                 # Bottom-up itemized BOM costing
│   ├── ageing.py               # Empirical cycle life surrogate
│   ├── variation.py            # Monte Carlo weakest-group propagation
│   └── evaluate.py             # Pure unified simulation entry point
├── analysis/                   # Constraints, conflicts, and traceability
│   ├── constraints.py          # Requirement compliance evaluator (R-01 to R-12)
│   ├── conflicts.py            # 10 multidisciplinary safety/interface rules
│   ├── traceability.py         # NetworkX graph and compliance matrix
│   └── sensitivity.py          # OAT parameter sensitivity (tornado chart)
├── optimize/                   # Quantum-inspired optimization engine
│   ├── space.py                # Discrete design space enumeration
│   ├── exhaustive.py           # Ground truth evaluator & Pareto extraction
│   ├── qubo_build.py           # 28-qubit one-hot binary Hamiltonian
│   ├── qubo_sa.py              # Pure NumPy vectorized Simulated Annealer
│   ├── export_qubo.py          # D-Wave BQM JSON exporter
│   ├── benchmark.py            # Multi-seed comparative benchmark harness
│   └── pareto.py               # Hypervolume and dominance utilities
├── reports/                    # Presentation asset generator
│   └── make_report.py          # 300 DPI figures, RESULTS.md, SLIDE_NOTES.md
├── tests/                      # 37 unit, integration, and smoke tests
├── docs/                       # Comprehensive technical documentation
│   ├── ARCHITECTURE.md
│   ├── ASSUMPTIONS.md
│   ├── LIMITATIONS.md
│   ├── QUBO_FORMULATION.md
│   ├── DATA_SOURCES.md
│   └── SAFETY.md
└── outputs/
    ├── benchmark/              # Raw seed logs and VERDICT.md
    └── ppt_assets/             # 300 DPI slide images and summary JSON
```

---

## 🛡️ License & Safety Disclaimer
Q-Pack is a virtual trade-off exploration tool. Designing physical lithium-ion systems involves significant electrical and thermal hazards. See [`docs/SAFETY.md`](file:///home/prem/VS%20Code/Projects/UnderGrads/docs/SAFETY.md) and [`docs/LIMITATIONS.md`](file:///home/prem/VS%20Code/Projects/UnderGrads/docs/LIMITATIONS.md) before attempting physical experimentation.

