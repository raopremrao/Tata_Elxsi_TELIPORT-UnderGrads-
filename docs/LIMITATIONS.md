# PackForge Prototype Limitations & Production Roadmap

In strict compliance with the project's scientific honesty guidelines, this document explicitly lists what the PackForge prototype models, what it does **not** model, and the experimental qualification required before physical production.

---

## 1. Prototype Modeling Scope & Current Limitations

| Engineering Discipline | Current Prototype Implementation | Scope Limitation (What is NOT Modeled) |
| :--- | :--- | :--- |
| **Fluid & Thermal Dynamics** | Lumped ODE thermal capacitance model with effective $h_{\text{eff}}$ convection and 2D analytic conduction gradient. | **No 3D CFD / FEA**: Does not simulate local turbulent airflow vortices, boundary layer separation, or localized dead zones in complex geometries. |
| **Safety & Abuse Dynamics** | Static threshold checking (overvoltage, overcurrent, high-temperature cutoff) and conflict rules. | **No Thermal Runaway / Abuse**: Does not simulate internal dendritic short-circuiting, nail penetration, venting gas dynamics, or cell-to-cell thermal propagation. |
| **Cell Degradation (Ageing)** | Semi-empirical surrogate based on Arrhenius temperature acceleration and C-rate severity scaling. | **Not Experimentally Validated**: Calendar ageing, SEI layer impedance growth, lithium plating at low temperatures, and mechanical fatigue are surrogates. |
| **Operational Duty Cycle** | 30-minute 1 Hz synthetic urban commute profile with 6 kW peak bursts and 2.5 kW cruising. | **Synthetic**: Does not capture real-world elevation gradients, ambient solar radiation loads, or regenerative braking transients. |
| **Commercial Costing** | Parametric bottom-up BOM estimation using typical cell tier pricing and enclosure mass fractions. | **Indicative**: Does not include factory tooling amortization, NRE (non-recurring engineering), import tariffs, or assembly labor costs. |

---

## 2. Requirements for Production & Hardware Deployment

Before committing any PackForge candidate design to automotive tooling or pilot production:

1. **Cell Characterization Testing**:
   - Comprehensive electrochemical impedance spectroscopy (EIS) across temperature (-10°C to +55°C) and State-of-Charge (0% to 100%).
   - Multi-channel cycling to validate high-current CC-CV charge acceptance without lithium deposition.
2. **Automotive Regulatory Certification**:
   - **AIS-156 / AIS-038 (Rev 2)**: Mandatory Indian EV battery safety standards including thermal propagation tests, drop tests, and water ingress (IP67).
   - **UN 38.3**: Transport safety testing for lithium batteries (altitude simulation, thermal test, vibration, shock, external short circuit).
   - **IEC 62619 / ISO 26262**: Functional safety validation of BMS hardware and software fail-safes (ASIL-C).
3. **Hardware-in-the-Loop (HIL) Simulation**:
   - Validation of BMS microcontroller firmware against high-fidelity battery emulator hardware before connecting live cells.

