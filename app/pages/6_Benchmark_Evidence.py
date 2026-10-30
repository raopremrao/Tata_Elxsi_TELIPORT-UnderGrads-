"""Page 6: Multi-Seed Benchmark Evidence and Honest Verdict."""

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

import json
from pathlib import Path
import streamlit as st
import pandas as pd
import plotly.express as px
from app.theme import (
    apply_theme, render_sidebar_scenario, page_header, apply_plotly_theme,
    PLOTLY_TEMPLATE, PRIMARY, SECONDARY, ACCENT, PASS_COLOR, FAIL_COLOR,
    BG_CARD, BORDER, TEXT_SECONDARY, TEXT_MUTED
)
from optimize.benchmark import run_benchmark_suite

apply_theme()
render_sidebar_scenario()

page_header(
    "Multi-Seed Benchmark Evidence & Statistical Verdict",
    "Rigorous 30-seed comparison of QUBO-SA, NSGA-II, Integer SA, and Random Search against Exhaustive Ground Truth.",
    "📈"
)

bench_dir = Path("outputs/benchmark")
summary_file = bench_dir / "benchmark_summary.json"
seeds_file   = bench_dir / "benchmark_seeds.csv"
verdict_file = bench_dir / "VERDICT.md"

if not summary_file.exists():
    with st.status("🔬 Running 30-seed benchmark harness (first run only)...", expanded=True) as status:
        st.write("Evaluating QUBO-SA, NSGA-II, Integer SA, and Random Search across 30 seeds...")
        run_benchmark_suite(n_seeds=30, output_dir=str(bench_dir))
        status.update(label="Benchmark complete!", state="complete", expanded=False)

with open(summary_file, "r", encoding="utf-8") as f:
    summary = json.load(f)
df_seeds = pd.read_csv(seeds_file)

# Re-run control
col_run, col_meta = st.columns([1, 3])
with col_run:
    if st.button("🔄 Re-run Benchmark Suite", width="stretch"):
        with st.spinner("Re-evaluating 30 seeds — this takes ~30 seconds..."):
            run_benchmark_suite(n_seeds=30, output_dir=str(bench_dir))
            st.rerun()
with col_meta:
    st.info(
        f"Loaded: **{summary['metadata']['n_seeds']} Seeds** evaluated over "
        f"**{summary['metadata']['design_space_size']} Feasible Configurations**. "
        f"All numbers reflect real computed values — no inflated claims."
    )

st.markdown("<div style='height:0.5rem'></div>", unsafe_allow_html=True)

# ── Per-Solver KPI Cards ──────────────────────────────────────────────────────
solvers_data  = summary["solvers"]
solver_names  = ["QUBO_SA", "NSGA_II", "Integer_SA", "Random_Search"]
display_names = ["QUBO + SA", "NSGA-II", "Integer SA", "Random Search"]
solver_colors = [PRIMARY, SECONDARY, ACCENT, "#AB47BC"]

k_cols = st.columns(4)
for idx, s in enumerate(solver_names):
    with k_cols[idx]:
        data = solvers_data[s]
        gap_color = PRIMARY if data["optimality_gap_median_pct"] < 2.0 else (ACCENT if data["optimality_gap_median_pct"] < 5.0 else FAIL_COLOR)
        st.markdown(
            f"""
            <div style="background:{BG_CARD}; border:1px solid {BORDER}; border-top:3px solid {solver_colors[idx]};
                        border-radius:12px; padding:1.25rem; margin-bottom:0.5rem;">
                <div style="font-size:0.85rem; font-weight:700; color:{solver_colors[idx]}; margin-bottom:0.75rem;">{display_names[idx]}</div>
                <div style="display:grid; gap:0.5rem;">
                    <div>
                        <div style="font-size:1.5rem; font-weight:800; color:{gap_color};">{data['optimality_gap_median_pct']:.2f}%</div>
                        <div style="font-size:0.7rem; color:{TEXT_MUTED};">Median Optimality Gap</div>
                    </div>
                    <div style="font-size:0.82rem; color:{TEXT_SECONDARY};">
                        ✅ {data['success_rate_pct']:.1f}% Success Rate<br>
                        ⏱ {data['runtime_mean_s']:.3f}s Mean Runtime<br>
                        🔢 {data['evaluations_mean']} Simulator Calls
                    </div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

st.markdown("<div style='height:0.5rem'></div>", unsafe_allow_html=True)

# ── Charts ────────────────────────────────────────────────────────────────────
col_box, col_bar = st.columns(2, gap="large")

with col_box:
    with st.container(border=True):
        st.markdown(f"<div style='font-size:0.85rem; font-weight:700; color:{PRIMARY}; margin-bottom:0.5rem;'>📦 Optimality Gap Distribution across Seeds</div>", unsafe_allow_html=True)
        fig_box = px.box(
            df_seeds,
            x="solver",
            y="optimality_gap_pct",
            color="solver",
            points="all",
            title="Optimality Gap (%) relative to Ground Truth",
            template=PLOTLY_TEMPLATE,
            log_y=True,
            color_discrete_map={
                "QUBO_SA": PRIMARY, "NSGA_II": SECONDARY, "Integer_SA": ACCENT, "Random_Search": "#AB47BC"
            },
        )
        fig_box = apply_plotly_theme(fig_box)
        st.plotly_chart(fig_box, width="stretch")

with col_bar:
    with st.container(border=True):
        st.markdown(f"<div style='font-size:0.85rem; font-weight:700; color:{PRIMARY}; margin-bottom:0.5rem;'>⏱️ Computational Budget: Wall-Clock vs Simulator Calls</div>", unsafe_allow_html=True)
        plot_df = pd.DataFrame([
            {"Solver": display_names[i], "Runtime (s)": solvers_data[s]["runtime_mean_s"], "Simulator Calls": solvers_data[s]["evaluations_mean"]}
            for i, s in enumerate(solver_names)
        ])
        fig_bar = px.bar(
            plot_df,
            x="Solver",
            y="Runtime (s)",
            color="Simulator Calls",
            title="Mean Runtime and Simulator Call Budget",
            template=PLOTLY_TEMPLATE,
            color_continuous_scale="Viridis",
            text_auto=True,
        )
        fig_bar = apply_plotly_theme(fig_bar)
        st.plotly_chart(fig_bar, width="stretch")

# ── Honest Verdict ────────────────────────────────────────────────────────────
st.markdown("<div style='height:0.5rem'></div>", unsafe_allow_html=True)
with st.container(border=True):
    st.markdown(f"<div style='font-size:0.85rem; font-weight:700; color:{PRIMARY}; margin-bottom:0.75rem;'>⚖️ Formal Scientific Honesty Verdict</div>", unsafe_allow_html=True)
    if verdict_file.exists():
        st.markdown(verdict_file.read_text(encoding="utf-8"))
    else:
        st.caption("Verdict file not yet generated — run the benchmark first.")
