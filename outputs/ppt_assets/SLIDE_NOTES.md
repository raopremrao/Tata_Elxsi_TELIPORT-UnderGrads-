# Tata Elxsi Hackathon: 6-Slide Pitch Storyline

Mapped directly to the TELIPORT Season 4 evaluation weights (Problem Understanding 15%, Feasibility 20%, Engineering Quality 15%, Prototype/Evidence 15%, Innovation 10%, Business 10%).

---

### Slide 1: Problem Understanding & Locked Architecture (15%)
- **Headline**: Balancing coupled electro-thermal trade-offs for 48V electric two-wheelers.
- **Story**: Designing a battery pack requires balancing conflicting physics: increasing capacity boosts range but causes thermal runaway risks, mass penalties, and cost overruns.
- **Visual**: `outputs/ppt_assets/radar_comparison.png`

---

### Slide 2: The Multi-Disciplinary Physics Engine (15%)
- **Headline**: High-fidelity subsystem models with a shared parameter bus.
- **Story**: Rather than isolated spreadsheets, Q-Pack couples OCV-SoC voltage sag, lumped ODE thermal conduction (`solve_ivp`), CC-CV fast charging, and bottom-up BOM costing into a single reactive loop.
- **Visual**: `outputs/ppt_assets/thermal_heatmap.png`

---

### Slide 3: Quantum-Inspired Optimization Engine (20%)
- **Headline**: Mapping pack design to a 28-qubit QUBO with honest benchmarking.
- **Story**: We encode the discrete design space into binary one-hot decision variables with pairwise quadratic surrogates ($R^2 > 0.90$). Solved via vectorized NumPy SA with direct export to D-Wave quantum annealers.
- **Visual**: `outputs/ppt_assets/qubo_heatmap.png`

---

### Slide 4: Empirical Validation & Benchmark Evidence (15%)
- **Headline**: 30-Seed validation against exhaustive ground truth.
- **Story**: QUBO-SA achieves a 2.05% median optimality gap across 30 seeds. We state our limitations honestly: evolutionary search is more sample-efficient for single runs, but QUBO enables instant (<10ms) weight sweeps and hardware portability.
- **Visual**: `outputs/ppt_assets/pareto_front.png`

---

### Slide 5: Traceability, Safety, and Conflict Rule Engine (15%)
- **Headline**: Catching interface conflicts before hardware prototypes.
- **Story**: 10 automated engineering rules catch ELV breaches (>60V), thermal bottlenecks, and sensing coverage gaps, linked through an end-to-end NetworkX dependency graph.
- **Visual**: `outputs/ppt_assets/traceability_matrix.png`

---

### Slide 6: Manufacturing Variation & Commercial Viability (20%)
- **Headline**: Stochastic Monte Carlo propagation and final BOM recommendation.
- **Story**: We demonstrate how manufacturing spreads propagate to weakest-group capacity bottlenecks (P5/P50/P95). Recommended Design Q satisfies all 12 requirements under $450 BOM.
- **Visual**: `outputs/ppt_assets/monte_carlo_distribution.png`
