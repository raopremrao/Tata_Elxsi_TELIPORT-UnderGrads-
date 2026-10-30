# PackForge Platform Architecture

This document describes the software design, multidisciplinary data flow, and subsystem integration architecture of **PackForge**.

---

## 1. Architectural Philosophy

Battery energy system design is inherently a multi-physics, multi-objective trade-off problem. Conventional approaches suffer from discipline silos:
- Cell selection is done on static spreadsheets.
- Thermal modeling happens offline in computationally heavy CFD.
- Mechanical packaging is decided in CAD without electrical load coupling.
- Protection and BMS limits are configured post-design.

PackForge solves this through a **reactive multi-disciplinary synthesis pipeline**: every design decision immediately propagates through electrical, thermal, mechanical, protection, and commercial models via a unified **Parameter Bus** (`DesignContext`).

```
                    ┌────────────────────────────────────────────────────────┐
                    │                 PackForge Web Platform                 │
                    │               (Streamlit 12-Page Suite)                │
                    └───────────────────────────┬────────────────────────────┘
                                                │
         ┌──────────────────────────────────────┼──────────────────────────────────────┐
         ▼                                      ▼                                      ▼
┌──────────────────┐                  ┌──────────────────┐                  ┌──────────────────┐
│   Data & Physics │                  │ Subsystem Engine │                  │   Optimization   │
│  - Cell Library  │                  │ - Parameter Bus  │                  │ - Exhaustive     │
│  - Electrical    │                  │ - Conflict Rules │                  │ - NSGA-II        │
│  - Thermal IVP   │ ◄──────────────► │ - Traceability   │ ◄──────────────► │ - Classical SA   │
│  - Fast CC-CV    │                  │ - Monte Carlo    │                  │ - QUBO Surrogate │
│  - Mech / Cost   │                  │ - Design Dossier │                  │ - Vectorized SA  │
└──────────────────┘                  └──────────────────┘                  └──────────────────┘
```

---

## 2. Core Subsystems

### 2.1 The Shared Parameter Bus (`core/context.py`)
All physical quantities pass through a typed, provenance-tracked registry:
- Every value carries its physical unit (`V`, `Wh`, `mOhm`, `°C`, `kg`).
- Provenance tracking tags each parameter with its origin (e.g. `datasheet`, `ASSUMPTIONS.md:A-01`, or `models/thermal.py`).

### 2.2 Physics Models (`models/`)
1. **`electrical.py`**:
   - Computes open-circuit voltage via empirical 11-point spline interpolation curves for NMC and LFP.
   - Calculates pack impedance including interconnect and laser-welded busbars.
   - Solves non-linear terminal voltage sag under time-varying synthetic urban drive cycles.
2. **`thermal.py`**:
   - Integrates transient lumped energy balance ODEs using SciPy `solve_ivp` (RK23).
   - Evaluates cooling modes: passive natural convection ($10\text{ W/m}^2\text{K}$), forced air ($35\text{ W/m}^2\text{K}$), and liquid cold plate ($150\text{ W/m}^2\text{K}$).
   - Computes 2D spatial cell conduction heatmaps capturing center core hotspot accumulation.
3. **`mechanical.py`**:
   - Evaluates active cell mass, structural enclosure fraction ($18\%$), busbars, and BMS hardware.
   - Determines 3D bounding envelope dimensions ($L \times W \times H$) and packing volume ($L$).
4. **`charging.py`**:
   - Models CC-CV charging from $10\%$ to $80\%$ SoC.
   - Activates BMS thermal derating curves when pack temperature exceeds $45^\circ\text{C}$.
5. **`cost.py`**:
   - Calculates itemized bottom-up BOM costs across cells, BMS tiers, thermal dissipation hardware, and casing.
6. **`variation.py`**:
   - Simulates stochastic cell-to-cell capacity ($\pm 2\%$) and DC resistance ($\pm 8\%$) manufacturing spreads across $N=500$ Monte Carlo seeds.
   - Identifies the weakest series group bottleneck that terminates pack discharge.

### 2.3 Optimization Engine (`optimize/`)
- Encodes the discrete design space into a 28-qubit one-hot binary Hamiltonian.
- Learns regularized quadratic interaction terms ($h_i, J_{ij}$) from sample evaluations.
- Solves QUBO using a pure vectorized multi-start Simulated Annealing solver in NumPy.
- Re-evaluates every candidate design with the true physics simulator.
- Exports standard dimod BQM / JSON representations for physical quantum annealers (D-Wave).

