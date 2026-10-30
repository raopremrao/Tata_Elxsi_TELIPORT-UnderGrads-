# Q-Pack Official Computed Results Summary

Generated automatically by `reports/make_report.py`. All values are computed directly from the physics simulator and benchmark data.

## 1. Headline Numbers
- **Design 0 (Starting Baseline)**: Usable Energy **247.9 Wh**, Peak Temp **560.9 °C**, BOM Cost **$128.18**, Mass **1.9 kg**.
- **Design A (Engineer's Choice)**: Usable Energy **878.0 Wh**, Peak Temp **67.9 °C**, BOM Cost **$392.20**, Mass **6.2 kg**.
- **Design B (LFP Safety-First)**: Usable Energy **771.8 Wh**, Peak Temp **48.3 °C**, BOM Cost **$386.35**, Mass **9.1 kg**.
- **Design Q (Optimizer Recommendation)**: Usable Energy **2110.5 Wh**, Peak Temp **37.9 °C**, BOM Cost **$831.98**, Mass **21.1 kg**.

## 2. Surrogate Model Fidelity
- Quadratic Surrogate $R^2$: **0.918**
- Spearman Rank Correlation: **0.937**
- Top-10 Overlap with True Simulator: **60%**

## 3. Claims Allowed on Presentation Slides
- "QUBO-SA reproduces ground-truth optimal design within 2.1% median optimality gap across 30 random seeds."
- "The learned quadratic surrogate captures 91.8% of simulator variance ($R^2=0.918$), enabling sub-50ms multi-objective re-solving."
- "Design Q improves usable energy by +751.4% over the starting baseline while staying safely below the 60V ELV limit."
- "All reported candidate pack performance metrics are verified through full physics re-evaluation, avoiding surrogate drift."
