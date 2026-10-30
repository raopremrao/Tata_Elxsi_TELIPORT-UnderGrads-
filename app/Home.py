"""PackForge: Reusable Digital Platform for Designing Battery Energy Systems.
Tata Elxsi TELIPORT Season 4 — Case Study 2.
"""

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

import streamlit as st
from app.theme import (
    apply_theme, render_sidebar_scenario, hero_banner,
    PRIMARY, SECONDARY, ACCENT, TEXT_SECONDARY, TEXT_MUTED,
    BG_CARD, BORDER, PASS_COLOR
)
from core.data_loader import load_cells, load_requirements
from optimize.space import get_baseline_designs
from models.evaluate import evaluate
from core.schemas import Scenario

st.set_page_config(
    page_title="PackForge | Battery Energy System Platform",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)

apply_theme()
render_sidebar_scenario()

# ── Sidebar: data health ──────────────────────────────────────────────────────
cells = load_cells()
unverified_count = sum(1 for c in cells.values() if not c.verified)
if unverified_count > 0:
    st.sidebar.warning(f"⚠️ {unverified_count} cell(s) have unverified datasheets.")
st.sidebar.caption("Navigate the pages using the menu above to explore PackForge capabilities.")

# ── Hero Banner ───────────────────────────────────────────────────────────────
hero_banner()

# ── Platform Stats Strip ──────────────────────────────────────────────────────
s1, s2, s3, s4, s5 = st.columns(5)
stat_style = f"background:{BG_CARD}; border:1px solid {BORDER}; border-radius:10px; padding:1rem; text-align:center;"
num_style = f"font-size:1.7rem; font-weight:800; color:{PRIMARY};"
lbl_style = f"font-size:0.7rem; color:{TEXT_MUTED}; text-transform:uppercase; letter-spacing:0.06em;"
with s1:
    st.markdown(f'<div style="{stat_style}"><div style="{num_style}">1053</div><div style="{lbl_style}">Feasible Designs Evaluated</div></div>', unsafe_allow_html=True)
with s2:
    st.markdown(f'<div style="{stat_style}"><div style="{num_style}">28</div><div style="{lbl_style}">QUBO Qubits (Binary Variables)</div></div>', unsafe_allow_html=True)
with s3:
    st.markdown(f'<div style="{stat_style}"><div style="{num_style}">30</div><div style="{lbl_style}">Benchmark Seeds (Honest)</div></div>', unsafe_allow_html=True)
with s4:
    st.markdown(f'<div style="{stat_style}"><div style="{num_style}">12</div><div style="{lbl_style}">System Requirements Traced</div></div>', unsafe_allow_html=True)
with s5:
    st.markdown(f'<div style="{stat_style}"><div style="{num_style}">10</div><div style="{lbl_style}">Safety Conflict Checks</div></div>', unsafe_allow_html=True)

st.markdown("<div style='height:1.5rem'></div>", unsafe_allow_html=True)

# ── Feature Cards ─────────────────────────────────────────────────────────────
st.markdown(f"""
<div style="font-size:1rem; font-weight:700; color:{TEXT_SECONDARY}; text-transform:uppercase;
            letter-spacing:0.08em; margin-bottom:1rem;">Platform Capabilities</div>
""", unsafe_allow_html=True)

fc1, fc2, fc3 = st.columns(3)
card_style = f"background:{BG_CARD}; border:1px solid {BORDER}; border-radius:14px; padding:1.5rem 1.4rem; height:100%;"
title_style = f"font-size:1rem; font-weight:700; color:#E6EDF3; margin:0.6rem 0 0.5rem 0;"
body_style  = f"font-size:0.855rem; color:{TEXT_SECONDARY}; line-height:1.65;"

with fc1:
    st.markdown(f"""
    <div style="{card_style}; border-top:3px solid {PRIMARY};">
        <div style="font-size:1.8rem;">🔬</div>
        <div style="{title_style}">Multi-Disciplinary Physics</div>
        <div style="{body_style}">
            <b>Electrical</b> — Chemistry-specific OCV-SoC curves, busbar resistance, terminal voltage sag.<br><br>
            <b>Thermal</b> — Lumped ODE with 2D spatial cell conduction heatmaps.<br><br>
            <b>Packaging</b> — Granular mass summation, 3D envelope, itemized BOM cost.<br><br>
            <b>Reliability</b> — Monte Carlo manufacturing variation (N=500) and empirical ageing.
        </div>
    </div>
    """, unsafe_allow_html=True)

with fc2:
    st.markdown(f"""
    <div style="{card_style}; border-top:3px solid {SECONDARY};">
        <div style="font-size:1.8rem;">⚛️</div>
        <div style="{title_style}">Quantum-Inspired Engine</div>
        <div style="{body_style}">
            <b>QUBO Mapping</b> — 28-qubit one-hot Hamiltonian with quadratic surrogate learning (R² &gt; 0.90).<br><br>
            <b>Vectorized SA</b> — Multi-start parallel Simulated Annealing in pure NumPy.<br><br>
            <b>Hardware Portability</b> — Direct export to D-Wave Advantage BQM and gate-model QAOA pipelines.<br><br>
            <b>Honest Benchmarking</b> — 30 random seeds vs Exhaustive Ground Truth &amp; NSGA-II.
        </div>
    </div>
    """, unsafe_allow_html=True)

with fc3:
    st.markdown(f"""
    <div style="{card_style}; border-top:3px solid {ACCENT};">
        <div style="font-size:1.8rem;">🛡️</div>
        <div style="{title_style}">Traceability &amp; Verification</div>
        <div style="{body_style}">
            <b>Rule Engine</b> — 10 multidisciplinary failure checks (ELV breach, thermal runaway, sensing gaps).<br><br>
            <b>NetworkX Graph</b> — End-to-end evidence linking Requirements R-01→R-12 to tests and models.<br><br>
            <b>Automated Dossiers</b> — 1-click generation of 300 DPI slides and auto-filled results markdown.
        </div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("<div style='height:1.75rem'></div>", unsafe_allow_html=True)

# ── Baseline Overview Table ───────────────────────────────────────────────────
st.markdown(f"""
<div style="font-size:1rem; font-weight:700; color:{TEXT_SECONDARY}; text-transform:uppercase;
            letter-spacing:0.08em; margin-bottom:0.75rem;">Standard Baseline Configurations</div>
""", unsafe_allow_html=True)

@st.cache_data(ttl=600)
def _compute_baselines():
    _cells = load_cells()
    _baselines = get_baseline_designs()
    _scenario = Scenario()
    rows = []
    for name, d in _baselines.items():
        res = evaluate(d, _scenario, fast=True, cell=_cells[d.cell_id])
        n_pass = sum(1 for r in res.requirements.values() if r.passed)
        rows.append({
            "Design": name,
            "Cell": _cells[d.cell_id].model,
            "Chemistry": _cells[d.cell_id].chemistry.value,
            "Config": f"{d.ns}S × {d.np}P",
            "Cooling": d.cooling.value.replace("_", " ").title(),
            "Usable Energy (Wh)": round(res.usable_energy_Wh, 1),
            "Peak Temp (°C)": round(res.peak_temp_C, 1),
            "Pack Mass (kg)": round(res.pack_mass_kg, 1),
            "BOM Cost (USD)": round(res.bom_cost_USD, 2),
            "Req. Met": f"{n_pass} / 12",
        })
    return rows, _cells

with st.spinner("Computing baseline designs..."):
    baseline_rows, _cells_ref = _compute_baselines()

st.dataframe(baseline_rows, width="stretch")

st.markdown("<div style='height:1rem'></div>", unsafe_allow_html=True)

# ── CTA / Quick Start ─────────────────────────────────────────────────────────
st.markdown(f"""
<div style="background:linear-gradient(135deg,rgba(0,168,107,0.08),rgba(0,102,153,0.08));
            border:1px solid {BORDER}; border-radius:12px; padding:1.5rem 1.75rem;">
    <div style="font-size:1rem; font-weight:700; color:#E6EDF3; margin-bottom:0.4rem;">🚀 Quick Start Guide</div>
    <div style="font-size:0.875rem; color:{TEXT_SECONDARY}; line-height:1.7;">
        <b>1. Requirements Scenario</b> — Set operational constraints (voltage, mass, cost budget).<br>
        <b>2. Cell Library</b> — Browse all candidate cells on the Ragone plot.<br>
        <b>3. Design Studio</b> — Interactively configure your pack and watch live simulation results.<br>
        <b>4. Optimizer Lab</b> — Run QUBO-SA and compare against NSGA-II on the Pareto front.<br>
        <b>5. Benchmark Evidence</b> — Review 30-seed statistical comparison with ground truth.<br>
        <b>6. Traceability</b> — Inspect the full R-01→R-12 evidence chain in the NetworkX graph.
    </div>
</div>
""", unsafe_allow_html=True)
