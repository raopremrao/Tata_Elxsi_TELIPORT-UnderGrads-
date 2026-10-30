# Q-Pack ⚡
### Quantum-Inspired Digital Platform for Battery Energy Systems
**Tata Elxsi TELIPORT Season 4 — Case Study 2**  
*Team UnderGrads | VSSUT, Burla*

> *"From cell datasheet to defensible, verified battery pack design in minutes."*

---

## 📋 Table of Contents
- [Project Overview](#-project-overview)
- [Key Features](#-key-features)
- [System Architecture](#-system-architecture)
- [Baseline & Pareto Trade-Off Summary](#-baseline--pareto-trade-off-summary)
- [Installation Steps](#-installation-steps)
- [Run Commands](#-run-commands)
- [Sample Outputs & Verification](#-sample-outputs--verification)
- [Repository Structure](#-repository-structure)
- [Safety & Engineering Disclaimer](#-safety--engineering-disclaimer)

---

## 📌 Project Overview

Designing battery energy systems for light electric mobility (48 V-class urban electric scooters and motorcycles) requires balancing conflicting physical domains: electrical voltage sag, transient heat generation, mechanical envelope constraints, and BOM cost. 

Traditional design workflows rely on disconnected spreadsheets and offline CAD/CFD tools. This creates critical engineering blind spots:
1. **Severe Thermal Overheating**: Spreadsheet-only sizing ignores $I^2R$ resistive heating during 6 kW acceleration bursts.
2. **Regulatory Violations**: Undersized series grouping can trigger Extra Low Voltage (ELV > 60 V DC) regulatory breaches under regenerative braking.
3. **The 2 kWh vs. $450 Cost Conflict**: A $\ge 2\text{ kWh}$ pack requires over 100 automotive-grade cells, making a $\le \$450$ BOM physically impossible under current cell pricing ($>\$750$ with BMS and packaging).

**Q-Pack** solves this by uniting electrochemical, lumped thermal ODE, mechanical packaging, and itemized BOM costing into a **reactive parameter bus**, driven by a **28-qubit Quantum-Inspired QUBO (Quadratic Unconstrained Binary Optimization) Engine** with automated requirements traceability ($R\text{-}01 \to R\text{-}12$).

---

## 🚀 Key Features

* **Closed-Loop Multiphysics Engine**:
  * *Electrochemical*: Chemistry-specific OCV–SoC curves, busbar contact resistance, and dynamic voltage sag under realistic 30-minute Indian urban drive cycles.
  * *Thermal Dynamics*: Lumped transient ODE solver (`scipy.integrate.solve_ivp`) with 2D spatial core-to-surface heat conduction heatmaps.
  * *Packaging & BOM*: Granular mass summation (cells, enclosure, busbars, thermal interface material) and bottom-up itemized costing.
  * *Fast Charging*: Multi-stage CC-CV charging with automatic thermal derating above $40^\circ\text{C}$.

* **Quantum-Inspired QUBO Optimization**:
  * *Hamiltonian Formulation*: Discrete design variables (cell choice, series count, parallel count, cooling mode, BMS tier) encoded into a 28-qubit one-hot binary Hamiltonian.
  * *Surrogate Fidelity*: Quadratic surrogate model achieving $R^2 = 0.918$ and Spearman rank correlation of $0.937$.
  * *Vectorized Simulated Annealing*: Pure NumPy multi-chain parallel solver executing in $<50\text{ ms}$ (zero C-extension lock-in).
  * *Hardware Portability*: Native export to `dimod.BinaryQuadraticModel` (BQM) formatted for D-Wave Advantage quantum annealers and gate-model QAOA pipelines.

* **Systems Engineering & Conflict Rule Engine**:
  * 10 automated multidisciplinary safety and interface checks (AIS-156 / UNECE R136 $<60\text{ V}$ ELV boundary, cell continuous current limits, BMS sensor channels).
  * Interactive NetworkX architecture graph linking high-level specifications ($R\text{-}01 \to R\text{-}12$) directly to equations, test cases, and CAD assumptions.

* **Manufacturing Reliability (Monte Carlo)**:
  * Propagates stochastic cell-to-cell capacity ($\pm 2\%$) and impedance ($\pm 8\%$) manufacturing variations across $N=500$ packs to quantify weakest-cell series group bottlenecks ($P5 / P50 / P95$).

* **Interactive 12-Page Streamlit Web Suite**:
  * Modular design studio, interactive trade-off explorer with parallel coordinates, QUBO lab, and 1-click 300 DPI competition presentation asset generator.

---

## 🏗️ System Architecture

```
┌──────────────────────────────────────────────────────────────────────────────────┐
│                             Q-PACK PLATFORM FLOW                                │
└──────────────────────────────────────────────────────────────────────────────────┘

   [ Verified Inputs ]            [ Multidisciplinary Physics ]          [ Optimization & Rules ]
 ┌──────────────────────┐        ┌────────────────────────────┐        ┌─────────────────────────┐
 │ • Cell Datasheets    │        │ • Electrochemical (OCV-SoC)│        │ • 28-Qubit QUBO Builder │
 │   (NMC, LFP, NCA)    │───────>│ • Lumped ODE (solve_ivp)   │───────>│ • Vectorized NumPy SA   │
 │ • Drive Cycle Profile│        │ • 2D Spatial Conduction    │        │ • NSGA-II Benchmark     │
 │ • Locked Reqs R01-R12│        │ • Itemized BOM Cost & Mass │        │ • 10 Safety Rules       │
 └──────────────────────┘        └────────────────────────────┘        └─────────────────────────┘
                                                │                                   │
                                                ▼                                   ▼
                                 ┌────────────────────────────┐        ┌─────────────────────────┐
                                 │   DesignContext Bus (Rx)   │<───────│ Requirements Traceability│
                                 │   Propagates all states    │        │ Matrix & NetworkX Graph │
                                 └────────────────────────────┘        └─────────────────────────┘
                                                │
                                                ▼
 ┌───────────────────────────────────────────────────────────────────────────────────────────────┐
 │                                   USER INTERACTION & OUTPUTS                                  │
 ├───────────────────────────────────────────────┬───────────────────────────────────────────────┤
 │  12-Page Streamlit Web Application (Port 8501)│  Automated Publication Bundle (outputs/)      │
 │  • Design Studio & Live Heatmap               │  • 300 DPI Presentation Slide Figures         │
 │  • Optimizer Lab & Learned QUBO Matrix        │  • Detailed RESULTS.md & SLIDE_NOTES.md       │
 │  • Monte Carlo Quantiles & Tornado Explorer   │  • D-Wave Advantage BQM Export (.json)        │
 └───────────────────────────────────────────────┴───────────────────────────────────────────────┘
```

---

## 📊 Baseline & Pareto Trade-Off Summary

Evaluated under the standardized 30-minute Indian urban scooter profile (peak 6 kW acceleration, ambient $35^\circ\text{C}$):

| Metric | Design 0 (Baseline) | Design A (Engineer's Choice) | Design B (LFP Safety) | Design Q (QUBO Optimized) | Target Specification |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **Cell Model** | Panasonic NCR18650B | Samsung INR21700-50E | Generic LFP 32700 | Generic LFP 32700 | Verified Datasheet |
| **Configuration** | 13S 2P | 14S 4P | 15S 3P | **15S 8P** | 46.0 – 54.0 V (R-01) |
| **Cooling Method** | Passive Air | Forced Air Fans | Forced Air Fans | **Passive Air** | Convective $h_{\text{eff}}$ |
| **Nominal Voltage** | 46.8 V | 50.8 V | 48.0 V | **48.0 V** | $<60\text{ V}$ ELV Gate (R-02) |
| **Usable Energy** | 247.9 Wh | 878.0 Wh | 771.8 Wh | **2,110.5 Wh** | $\ge 2,000\text{ Wh}$ (R-03) |
| **Peak Operating Temp** | 560.9 °C (Overheating) | 67.9 °C | 48.3 °C | **37.9 °C** | $\le 45.0^\circ\text{C}$ (R-05) |
| **Total Pack Mass** | 1.9 kg | 6.2 kg | 9.1 kg | **21.2 kg** | $\le 18.0\text{ kg}$ (R-07) |
| **BOM Cost** | $128.18 | $392.20 | $386.35 | **$831.98** | $\le \$450.00$ (R-08) |
| **Requirements Met** | 3 / 12 | 8 / 12 | 8 / 12 | **9 / 12 (Max: 10)** | 12 / 12 |

> **Key Systems Engineering Discovery**: In an exhaustive scan of all 1,053 feasible designs, **no configuration satisfies all 12 requirements**. A $\ge 2\text{ kWh}$ pack under $<60\text{ V}$ requires 120 cells ($17.4\text{ kg}$ and $\$540$ in cells alone), making $\le \$450$ BOM and $\le 18\text{ kg}$ mass physically mutually exclusive. Q-Pack captures this Pareto boundary honestly.

---

## 💻 Installation Steps

### Prerequisites
* **Operating System**: Linux (Ubuntu/Debian/Kali), macOS, or Windows (WSL2 recommended)
* **Python**: `Python >= 3.10`
* **Build Tools**: `make`, `git`

### 1. Clone the Repository
```bash
git clone https://github.com/raopremrao/Tata_Elxsi_TELIPORT-UnderGrads-.git
cd Tata_Elxsi_TELIPORT-UnderGrads-
```

### 2. Set Up Virtual Environment & Dependencies
Using `make` (recommended):
```bash
make setup
```

Or manually using `venv` and `pip`:
```bash
python3 -m venv .venv
source .venv/bin/activate    # On Windows: .venv\Scripts\activate
pip install --upgrade pip
pip install -r requirements.txt
```

---

## ⚡ Run Commands

The repository includes a clean `Makefile` providing 1-command verification workflows:

### 1. Run Complete Test Suite (37 Tests)
```bash
make test
```
Executes all electrical, thermal, optimization, schema, and application smoke tests.

### 2. Run Fast Multi-Seed Benchmark
```bash
make quick-benchmark
```
Runs a 3-seed benchmark comparing QUBO-SA, NSGA-II, and Random Search against Exhaustive Ground Truth (1,053 evaluations).

### 3. Run Full 30-Seed Statistical Benchmark
```bash
make benchmark
```
Runs the complete 30-seed validation harness. Outputs results to `outputs/benchmark/`.

### 4. Generate 300 DPI Slide Assets & Presentation Bundle
```bash
make report
```
Generates publication-quality 300 DPI figures, `RESULTS.md`, and `SLIDE_NOTES.md` in `outputs/ppt_assets/`.

### 5. Launch Interactive Web Dashboard
```bash
make run
```
Starts the 12-page Streamlit application on `http://localhost:8501`.

---

## 📈 Sample Outputs & Verification

### Test Suite Execution Output
```text
$ make test
Running test suite...
.venv/bin/python -m pytest tests/ -v
============================= test session starts ==============================
platform linux -- Python 3.14.7, pytest-9.1.1
rootdir: /home/prem/VS Code/Projects/UnderGrads/Tata_Elxsi_TELIPORT-UnderGrads-
collected 37 items

tests/test_benchmark_harness.py::test_benchmark_suite_execution PASSED   [  2%]
tests/test_conflicts.py::test_conflict_rule_01_cell_overcurrent PASSED   [  5%]
tests/test_conflicts.py::test_conflict_rule_02_elv_breach PASSED         [  8%]
tests/test_conflicts.py::test_conflict_rule_03_bms_undersized PASSED     [ 10%]
tests/test_conflicts.py::test_conflict_rule_04_thermal_insufficient PASSED [ 13%]
tests/test_conflicts.py::test_conflict_rule_06_sensing_gap PASSED        [ 16%]
tests/test_conflicts.py::test_conflict_rule_10_unverified_provenance PASSED [ 18%]
tests/test_data_layer.py::test_load_cells PASSED                         [ 21%]
tests/test_data_layer.py::test_load_requirements PASSED                  [ 24%]
tests/test_data_layer.py::test_load_components PASSED                    [ 27%]
tests/test_data_layer.py::test_load_drive_cycle PASSED                   [ 29%]
tests/test_datasheet_crosscheck.py::test_datasheet_discharge_capacity_crosscheck PASSED [ 32%]
tests/test_electrical.py::test_hand_calculated_13s2p PASSED              [ 35%]
tests/test_electrical.py::test_ocv_lookup_bounds PASSED                  [ 37%]
tests/test_evaluate.py::test_mechanical_and_cost PASSED                  [ 40%]
tests/test_evaluate.py::test_charging_derating PASSED                    [ 43%]
tests/test_evaluate.py::test_ageing_trend PASSED                         [ 45%]
tests/test_evaluate.py::test_variation_statistics PASSED                 [ 48%]
tests/test_evaluate.py::test_evaluate_fast_mode_speed_and_caching PASSED [ 51%]
tests/test_optimization_space.py::test_design_space_enumeration PASSED   [ 54%]
tests/test_optimization_space.py::test_baseline_designs_evaluation PASSED [ 56%]
tests/test_optimization_space.py::test_pareto_dominance PASSED           [ 59%]
tests/test_optimization_space.py::test_exhaustive_search_subset PASSED   [ 62%]
tests/test_qubo_engine.py::test_binary_encoding_roundtrip PASSED         [ 64%]
tests/test_qubo_engine.py::test_qubo_build_and_fidelity PASSED           [ 67%]
tests/test_qubo_engine.py::test_vectorized_sa_solver_and_reevaluation PASSED [ 70%]
tests/test_qubo_engine.py::test_qubo_export PASSED                       [ 72%]
tests/test_schemas.py::test_cell_schema_valid PASSED                     [ 75%]
tests/test_schemas.py::test_cell_schema_immutability PASSED              [ 78%]
tests/test_schemas.py::test_pack_design_bounds PASSED                    [ 81%]
tests/test_schemas.py::test_units_conversion PASSED                      [ 83%]
tests/test_schemas.py::test_design_context_bus PASSED                    [ 86%]
tests/test_smoke_app.py::test_streamlit_pages_importable PASSED          [ 89%]
tests/test_thermal.py::test_cooling_monotonicity PASSED                  [ 91%]
tests/test_thermal.py::test_thermal_spatial_gradient PASSED              [ 94%]
tests/test_traceability.py::test_traceability_graph_integrity PASSED     [ 97%]
tests/test_traceability.py::test_traceability_matrix_and_dossier PASSED  [100%]

============================== 37 passed in 4.67s ==============================
```

### Multi-Seed Benchmark Output (30 Seeds Summary)
```text
=== Q-Pack Statistical Benchmark Results (Outputs: outputs/benchmark/) ===
• Design Space Size: 1,053 feasible configurations
• Ground Truth Optimum: generic_lfp_32700_15S8P_passive_standard (Score: 0.3493)
• Surrogate Fit: R² = 0.918, Spearman = 0.937

Solver Performance Comparison:
├── QUBO + Vectorized SA: Median Gap = 2.05% | Runtime = 0.044s | Calls = 537
├── Random Search (100): Median Gap = 11.71% | Runtime = 0.016s | Calls = 100
└── NSGA-II (pymoo):     Median Gap = 1439%  | Runtime = 0.039s | Calls = 99
```

---

## 📁 Repository Structure

```
Tata_Elxsi_TELIPORT-UnderGrads-/
├── app/                        # 12-page Streamlit web platform
│   ├── Home.py                 # Executive overview & baseline comparison
│   ├── theme.py                # Styling, dark CSS, and Plotly templates
│   └── pages/                  # 11 interactive engineering subpages
├── core/                       # Shared schemas, units, and reactive bus
│   ├── schemas.py              # Pydantic v2 data models
│   ├── units.py                # Physical unit conversions
│   ├── context.py              # DesignContext reactive parameter bus
│   └── data_loader.py          # Cached YAML/CSV data loaders
├── models/                     # Multi-disciplinary physics engine
│   ├── electrical.py           # OCV-SoC curves, voltage sag, impedance
│   ├── thermal.py              # Lumped ODE solve_ivp & 2D spatial gradient
│   ├── mechanical.py           # Cell packing density, dimensions, mass
│   ├── charging.py             # CC-CV integration with thermal derating
│   ├── cost.py                 # Bottom-up itemized BOM costing
│   ├── ageing.py               # Empirical cycle life degradation model
│   ├── variation.py            # Monte Carlo weakest-group propagation
│   └── evaluate.py             # Pure unified simulation entry point
├── analysis/                   # Systems engineering & traceability
│   ├── constraints.py          # Requirement compliance evaluator (R-01 to R-12)
│   ├── conflicts.py            # 10 multidisciplinary safety conflict rules
│   ├── traceability.py         # NetworkX graph and compliance matrix
│   └── sensitivity.py          # One-At-A-Time (OAT) tornado sensitivity
├── optimize/                   # Quantum-inspired optimization engine
│   ├── space.py                # Discrete design space enumeration
│   ├── exhaustive.py           # Ground truth evaluator & Pareto extraction
│   ├── qubo_build.py           # 28-qubit one-hot binary Hamiltonian
│   ├── qubo_sa.py              # Pure NumPy vectorized Simulated Annealer
│   ├── export_qubo.py          # D-Wave BQM JSON exporter
│   └── benchmark.py            # Multi-seed comparative benchmark harness
├── reports/                    # Presentation bundle generator
│   └── make_report.py          # 300 DPI figures, RESULTS.md, SLIDE_NOTES.md
├── tests/                      # 37 unit, integration, and smoke tests
├── docs/                       # Comprehensive engineering documentation
│   ├── ARCHITECTURE.md         # Data flow and reactive bus design
│   ├── ASSUMPTIONS.md          # Numerical baseline & uncertainty registry
│   ├── DATA_SOURCES.md         # Official component datasheets & provenance
│   ├── LIMITATIONS.md          # Model fidelity boundaries & physical roadmap
│   ├── QUBO_FORMULATION.md     # Mathematical formulation of the Hamiltonian
│   └── SAFETY.md               # Electrical & thermal laboratory safety protocols
├── outputs/
│   ├── benchmark/              # Raw seed logs and statistical VERDICT.md
│   └── ppt_assets/             # 300 DPI competition slide figures & markdown
├── Makefile                    # Automation workflows (setup, test, run, etc.)
└── requirements.txt            # Production-grade dependencies
```

---

## 🛡️ Safety & Engineering Disclaimer

Q-Pack is a virtual design synthesis and multi-objective optimization platform intended for engineering trade-off exploration. Physical lithium-ion battery prototyping involves severe thermal runaway, chemical off-gassing, and high-energy arc flash hazards. All virtual designs must undergo physical cell-level calorimeter testing and formal **AIS-156 / UNECE R136 / IEC 62619** certification before commercial or vehicle implementation. See [`docs/SAFETY.md`](docs/SAFETY.md) and [`docs/LIMITATIONS.md`](docs/LIMITATIONS.md) for full experimental safety protocols.
