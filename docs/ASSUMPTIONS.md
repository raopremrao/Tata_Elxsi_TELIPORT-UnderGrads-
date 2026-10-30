# Q-Pack Engineering Assumptions & Parameter Registry

This document records every parameter not directly derived from official manufacturer datasheets, as mandated by Section 5 of the specification. Every assumption carries a unique ID ($A\text{-}01 \dots A\text{-}15$), numerical baseline, uncertainty range, physical rationale, and linked models.

---

## Assumptions Table

| Assumption ID | Parameter Name | Baseline Value | Uncertainty Range | Units | Physical Rationale / Source Reference | Subsystem Models |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **A-01** | `busbar_resistance_per_cell` | 0.15 | 0.08 - 0.25 | $\text{m}\Omega$ | Laser-welded nickel-copper composite busbars and terminal contact resistance. | `electrical.py` |
| **A-02** | `ocv_soc_curve` | Empirical 11-point | $\pm 2.5\%$ voltage | $\text{V}(\text{SoC})$ | Standard literature OCV-SoC curves for NMC (3.6V nom) and LFP (3.2V nom). | `electrical.py` |
| **A-03** | `inverter_efficiency` | 0.95 | 0.92 - 0.97 | ratio | Average round-trip inverter and DC-DC auxiliary conversion efficiency. | `electrical.py` |
| **A-04** | `cell_specific_heat_cp` | 950.0 | 850 - 1050 | $\text{J}/(\text{kg}\cdot\text{K})$ | Typical specific heat capacity for 18650 / 21700 cylindrical cells (Doughty et al.). | `thermal.py` |
| **A-05a** | `h_eff_passive` | 10.0 | 8.0 - 15.0 | $\text{W}/(\text{m}^2\cdot\text{K})$ | Natural buoyancy-driven air convection from vertical chassis-mounted module. | `thermal.py` |
| **A-05b** | `h_eff_forced_air` | 35.0 | 25.0 - 50.0 | $\text{W}/(\text{m}^2\cdot\text{K})$ | Dual brushless axial fan forced airflow through 2mm inter-cell channels. | `thermal.py` |
| **A-05c** | `h_eff_cold_plate` | 150.0 | 120.0 - 200.0 | $\text{W}/(\text{m}^2\cdot\text{K})$ | Aluminum bottom cold plate with circulating 50/50 ethylene glycol / water loop. | `thermal.py` |
| **A-06** | `thermal_gradient_factor` | 0.25 | 0.15 - 0.35 | ratio | Ratio of core-to-surface temperature rise based on cell grid thermal conductivity. | `thermal.py` |
| **A-07** | `cv_tail_tau_min` | 18.0 | 12.0 - 25.0 | $\text{min}$ | Exponential decay time constant for CC-CV charging phase from 70% to 80% SoC. | `charging.py` |
| **A-08** | `thermal_derating_threshold` | 45.0 | 40.0 - 50.0 | $^\circ\text{C}$ | BMS charge current derating slope: -10% charge current per $^\circ\text{C}$ above threshold. | `charging.py` |
| **A-09** | `enclosure_mass_fraction` | 0.18 | 0.14 - 0.22 | ratio | Structural mass of enclosure, compression brackets, and fasteners vs cell mass. | `mechanical.py` |
| **A-10** | `enclosure_cost_per_kg` | 14.0 | 10.0 - 18.0 | $\text{USD}/\text{kg}$ | High-pressure die-cast aluminum / flame-retardant PC-ABS blend enclosure cost. | `cost.py` |
| **A-11** | `packing_efficiency_factor` | 0.72 | 0.65 - 0.78 | ratio | Volumetric packing density of staggered cylindrical cells within rectangular module. | `mechanical.py` |
| **A-12** | `arrhenius_activation_temp` | 4500.0 | 3800 - 5200 | $\text{K}$ | Empirical activation energy for SEI layer growth and capacity fade ($E_a / R$). | `ageing.py` |
| **A-13** | `cell_capacity_sigma` | 0.02 | 0.01 - 0.03 | ratio | Manufacturing batch variation standard deviation for cell nominal capacity ($\pm 2\%$). | `variation.py` |
| **A-14** | `cell_resistance_sigma` | 0.08 | 0.05 - 0.12 | ratio | Manufacturing batch variation standard deviation for cell DC resistance ($\pm 8\%$). | `variation.py` |
| **A-15** | `weakest_series_cutoff` | True | Boolean | flag | Pack terminates discharge when the minimum series group reaches cell cutoff voltage. | `variation.py` |

---

## Sensitivity & Propagation Notice
All values above are surfaced in the Q-Pack Sensitivity Analysis module (`analysis/sensitivity.py`) and can be perturbed across their specified uncertainty ranges to assess stability of the recommended design.

