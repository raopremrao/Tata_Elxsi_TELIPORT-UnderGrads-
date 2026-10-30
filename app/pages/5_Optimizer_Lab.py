"""Page 5: Optimizer Lab (QUBO, NSGA-II, and Pareto Analysis)."""

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

import streamlit as st
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from app.theme import (
    apply_theme, render_sidebar_scenario, page_header, apply_plotly_theme,
    PLOTLY_TEMPLATE, PRIMARY, SECONDARY, ACCENT, PASS_COLOR, FAIL_COLOR,
    BG_CARD, BORDER, TEXT_SECONDARY, TEXT_MUTED
)
from core.data_loader import load_cells
from core.schemas import Scenario
from optimize.exhaustive import run_exhaustive_search, ExhaustiveResults
from optimize.qubo_build import build_qubo_model, TOTAL_QUBITS, CELL_LIST, NS_LIST, NP_LIST
from optimize.qubo_sa import solve_qubo_with_reevaluation

apply_theme()
render_sidebar_scenario()

page_header(
    "Optimizer Lab: Quantum-Inspired Synthesis",
    "Run QUBO-SA, evaluate surrogate fidelity (R², Spearman), and explore the non-dominated Pareto frontier against Ground Truth.",
    "🧪"
)

scenario = st.session_state.get("scenario", Scenario())
cells = load_cells()

# ── Controls ──────────────────────────────────────────────────────────────────
with st.container(border=True):
    st.markdown(f"<div style='font-size:0.8rem; font-weight:700; color:{PRIMARY}; text-transform:uppercase; letter-spacing:0.06em; margin-bottom:0.75rem;'>🎛️ Solver Configuration</div>", unsafe_allow_html=True)
    c_solver, c_reads, c_sweeps = st.columns(3)
    with c_solver:
        solver_choice = st.selectbox(
            "Optimization Algorithm",
            ["QUBO + Vectorized SA (Quantum-Inspired)", "NSGA-II (pymoo Evolutionary)", "Random Search Baseline"],
        )
    with c_reads:
        n_reads = st.slider("Parallel Reads (Vectorized Chains)", min_value=20, max_value=200, value=80, step=20)
    with c_sweeps:
        n_sweeps = st.slider("Annealing Sweeps per Read", min_value=50, max_value=400, value=150, step=50)

    st.markdown(f"<div style='font-size:0.8rem; font-weight:600; color:{TEXT_SECONDARY}; margin:0.75rem 0 0.5rem;'>⚖️ Objective Weights (Scalarization)</div>", unsafe_allow_html=True)
    w_c1, w_c2, w_c3, w_c4, w_c5, w_c6 = st.columns(6)
    with w_c1:
        w_cost = st.slider("Cost", 0.0, 1.0, 0.25, 0.05)
    with w_c2:
        w_temp = st.slider("Peak Temp", 0.0, 1.0, 0.20, 0.05)
    with w_c3:
        w_mass = st.slider("Pack Mass", 0.0, 1.0, 0.15, 0.05)
    with w_c4:
        w_chg = st.slider("Charge Time", 0.0, 1.0, 0.15, 0.05)
    with w_c5:
        w_energy = st.slider("Usable Energy", 0.0, 1.0, 0.15, 0.05)
    with w_c6:
        w_life = st.slider("Cycle Life", 0.0, 1.0, 0.10, 0.05)

weights = {
    "cost": w_cost, "peak_temp": w_temp, "mass": w_mass,
    "charge_time": w_chg, "usable_energy": w_energy, "cycle_life": w_life,
}

# ── Cached Heavy Computations ─────────────────────────────────────────────────
@st.cache_data(ttl=600, show_spinner=False)
def _run_exhaustive(_weights_key):
    return run_exhaustive_search(Scenario(), _weights_key)

@st.cache_data(ttl=600, show_spinner=False)
def _build_qubo(_exh_id, _weights_key):
    exh = _run_exhaustive(_weights_key)
    sample_rng = np.random.default_rng(42)
    sample_idx = sample_rng.choice(len(exh.designs), size=min(500, len(exh.designs)), replace=False)
    sample_designs = [exh.designs[i] for i in sample_idx]
    sample_scores = exh.scalar_scores[sample_idx]
    return build_qubo_model(sample_designs, sample_scores)

@st.cache_data(ttl=600, show_spinner=False)
def _solve_qubo(_qubo_key, _weights_key, _n_reads, _n_sweeps):
    exh = _run_exhaustive(_weights_key)
    qubo_model = _build_qubo(_qubo_key, _weights_key)
    best_design, best_res, candidates = solve_qubo_with_reevaluation(
        qubo=qubo_model,
        scenario=Scenario(),
        bounds=exh.bounds,
        weights=weights,
        n_reads=_n_reads,
        n_sweeps=_n_sweeps,
        seed=42,
    )
    return best_design, best_res, candidates, exh, qubo_model

weights_key = tuple(sorted(weights.items()))
qubo_key = str(weights_key)

with st.status("⚡ Running QUBO-SA Optimizer...", expanded=True) as status:
    st.write("📊 Evaluating exhaustive ground truth (1053 designs)...")
    best_design, best_res, candidates, exh, qubo_model = _solve_qubo(qubo_key, weights_key, n_reads, n_sweeps)
    st.write("✅ QUBO surrogate trained & SA annealing complete.")
    status.update(label="Optimization complete!", state="complete", expanded=False)

# ── Metrics Banner ────────────────────────────────────────────────────────────
st.markdown("<div style='height:0.5rem'></div>", unsafe_allow_html=True)
m1, m2, m3, m4 = st.columns(4)
try:
    opt_gap = max(0.0, (exh.scalar_scores[exh.designs.index(best_design)] - exh.scalar_scores[exh.optimum_index]) / max(1e-9, exh.scalar_scores[exh.optimum_index]) * 100.0) if best_design in exh.designs else 0.0
except (ValueError, ZeroDivisionError):
    opt_gap = 0.0

with m1:
    st.metric("Surrogate Fidelity (R²)", f"{qubo_model.r2_score:.3f}", delta=None)
with m2:
    st.metric("Spearman Rank Correlation", f"{qubo_model.spearman_corr:.3f}")
with m3:
    st.metric("Top-10 Overlap", f"{qubo_model.top_k_overlap * 100:.0f}%")
with m4:
    st.metric("Optimality Gap vs Ground Truth", f"{opt_gap:.2f}%")

st.markdown("<div style='height:0.5rem'></div>", unsafe_allow_html=True)

# ── Pareto Front + QUBO Matrix ────────────────────────────────────────────────
col_pareto, col_matrix = st.columns([1.3, 1.0], gap="large")

with col_pareto:
    with st.container(border=True):
        st.markdown(f"<div style='font-size:0.85rem; font-weight:700; color:{PRIMARY}; margin-bottom:0.5rem;'>🎯 Pareto Frontier: Ground Truth vs Discovered Designs</div>", unsafe_allow_html=True)
        df_all = pd.DataFrame({
            "BOM Cost ($)":       [r.bom_cost_USD for r in exh.results],
            "Usable Energy (Wh)": [r.usable_energy_Wh for r in exh.results],
            "Peak Temp (°C)":     [r.peak_temp_C for r in exh.results],
            "Design Name":        [d.name for d in exh.designs],
            "Type":               ["Feasible Design" for _ in exh.designs],
        })
        for idx in exh.pareto_indices:
            df_all.loc[idx, "Type"] = "Ground Truth Pareto Front"

        fig_pareto = px.scatter(
            df_all,
            x="BOM Cost ($)",
            y="Usable Energy (Wh)",
            color="Peak Temp (°C)",
            symbol="Type",
            hover_name="Design Name",
            title="Cost vs Usable Energy (Color: Peak Temp)",
            template=PLOTLY_TEMPLATE,
            color_continuous_scale="Plasma",
            opacity=0.7,
        )
        fig_pareto.add_trace(go.Scatter(
            x=[best_res.bom_cost_USD],
            y=[best_res.usable_energy_Wh],
            mode="markers",
            marker=dict(size=18, color=PASS_COLOR, symbol="star", line=dict(color="#FFFFFF", width=2)),
            name=f"QUBO Selected: {best_design.name}",
        ))
        fig_pareto = apply_plotly_theme(fig_pareto)
        st.plotly_chart(fig_pareto, width="stretch")

with col_matrix:
    with st.container(border=True):
        st.markdown(f"<div style='font-size:0.85rem; font-weight:700; color:{PRIMARY}; margin-bottom:0.5rem;'>🧲 Learned QUBO Coupling Matrix (J_ij)</div>", unsafe_allow_html=True)
        Q_crop = qubo_model.Q[:15, :15]
        fig_q = px.imshow(
            Q_crop,
            labels=dict(x="Qubit j", y="Qubit i", color="Weight"),
            title="Pairwise Coupling Strengths (Qubits 0–14)",
            color_continuous_scale="RdBu_r",
            template=PLOTLY_TEMPLATE,
            aspect="auto",
        )
        fig_q = apply_plotly_theme(fig_q)
        st.plotly_chart(fig_q, width="stretch")
        st.caption("Strong positive off-diagonal terms represent high penalties (one-hot or hard physical constraints).")

# ── QUBO Design Space Stats ───────────────────────────────────────────────────
st.markdown("<div style='height:0.5rem'></div>", unsafe_allow_html=True)
with st.container(border=True):
    st.markdown(f"<div style='font-size:0.8rem; font-weight:700; color:{TEXT_SECONDARY}; margin-bottom:0.5rem;'>📐 QUBO Problem Specification</div>", unsafe_allow_html=True)
    q1, q2, q3, q4 = st.columns(4)
    with q1:
        st.metric("Total Qubits", f"{TOTAL_QUBITS}")
    with q2:
        st.metric("Cell Variables", f"{len(CELL_LIST)}")
    with q3:
        st.metric("Series Options", f"{len(NS_LIST)}")
    with q4:
        st.metric("Parallel Options", f"{len(NP_LIST)}")
