"""Page 3: Interactive Pack Design Studio."""

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

import streamlit as st
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from app.theme import (
    apply_theme, render_sidebar_scenario, page_header, kpi_card, finding_card,
    apply_plotly_theme, PLOTLY_TEMPLATE,
    PRIMARY, SECONDARY, ACCENT, FAIL_COLOR, WARN_COLOR, INFO_COLOR,
    PASS_COLOR, BG_CARD, BORDER, TEXT_SECONDARY, TEXT_MUTED
)
from core.data_loader import load_cells
from core.schemas import PackDesign, CoolingType, BMSTier, Scenario
from models.evaluate import evaluate

apply_theme()
render_sidebar_scenario()

page_header(
    "Interactive Pack Design Studio",
    "Configure series/parallel groupings, cooling topologies, and BMS tiers with live multidisciplinary simulation.",
    "🛠️"
)

cells = load_cells()
scenario = st.session_state.get("scenario", Scenario())

# ── Design Controls ───────────────────────────────────────────────────────────
with st.container(border=True):
    st.markdown(f"<div style='font-size:0.8rem; font-weight:700; color:{PRIMARY}; text-transform:uppercase; letter-spacing:0.06em; margin-bottom:0.75rem;'>🔧 Design Configuration</div>", unsafe_allow_html=True)
    c_cell, c_ns, c_np, c_cool, c_bms, c_sp = st.columns(6)

    with c_cell:
        cell_id = st.selectbox("Battery Cell", options=list(cells.keys()), format_func=lambda x: cells[x].model)
    with c_ns:
        ns = st.slider("Series (ns)", min_value=12, max_value=17, value=14)
    with c_np:
        np_val = st.slider("Parallel (np)", min_value=1, max_value=8, value=4)
    with c_cool:
        cooling = st.selectbox("Cooling", options=list(CoolingType), format_func=lambda x: x.value.replace("_", " ").title())
    with c_bms:
        bms = st.selectbox("BMS Tier", options=list(BMSTier), format_func=lambda x: x.value.title())
    with c_sp:
        spacing = st.selectbox("Cell Spacing", options=[1.0, 2.0, 4.0], format_func=lambda x: f"{x} mm")

design = PackDesign(
    name="Studio Candidate",
    cell_id=cell_id,
    ns=ns,
    np=np_val,
    cooling=cooling,
    bms_tier=bms,
    cell_spacing_mm=spacing,
)

# ── ELV Safety Gate ───────────────────────────────────────────────────────────
nominal_v = ns * cells[cell_id].nominal_voltage_V
if nominal_v > 60.0:
    st.error(f"⛔ **ELV Breach**: Nominal pack voltage {nominal_v:.1f} V exceeds 60 V DC regulatory limit (R-01). Reduce series count.")
    st.stop()

# ── Fast Simulation (always on) ───────────────────────────────────────────────
with st.spinner("Running fast simulation..."):
    res_fast = evaluate(design, scenario, fast=True, cell=cells[cell_id])

st.markdown("<div style='height:0.5rem'></div>", unsafe_allow_html=True)

# ── KPI Cards ─────────────────────────────────────────────────────────────────
st.markdown(f"<div style='font-size:0.8rem; font-weight:700; color:{TEXT_MUTED}; text-transform:uppercase; letter-spacing:0.06em; margin-bottom:0.6rem;'>Live Performance KPIs</div>", unsafe_allow_html=True)
k1, k2, k3, k4, k5, k6 = st.columns(6)

with k1:
    kpi_card("Nominal Voltage", f"{res_fast.nominal_voltage_V:.1f}", "V", res_fast.requirements["R-01"].passed)
with k2:
    kpi_card("Usable Energy", f"{res_fast.usable_energy_Wh:.0f}", "Wh", res_fast.requirements["R-03"].passed)
with k3:
    kpi_card("Peak Temp", f"{res_fast.peak_temp_C:.1f}", "°C", res_fast.requirements["R-05"].passed)
with k4:
    kpi_card("Charge Time", f"{res_fast.charge_time_min:.1f}", "min", res_fast.requirements["R-06"].passed)
with k5:
    kpi_card("Pack Mass", f"{res_fast.pack_mass_kg:.1f}", "kg", res_fast.requirements["R-07"].passed)
with k6:
    n_pass = sum(1 for r in res_fast.requirements.values() if r.passed)
    kpi_card("Requirements", f"{n_pass} / 12", "", n_pass >= 10)

st.markdown("<div style='height:0.75rem'></div>", unsafe_allow_html=True)

# ── Full Physics Simulation (on demand) ───────────────────────────────────────
with st.container(border=True):
    col_btn, col_info = st.columns([1, 3])
    with col_btn:
        run_full = st.button("🔬 Run Full Physics Simulation", type="primary", width="stretch")
    with col_info:
        st.caption("Full simulation includes transient thermal ODE (solve_ivp) with drive-cycle thermal curves. May take 2–5 seconds.")

if "full_sim_result" not in st.session_state or run_full:
    if run_full:
        with st.spinner("Running full physics simulation (transient ODE)..."):
            st.session_state["full_sim_result"] = evaluate(design, scenario, fast=False, cell=cells[cell_id])
            st.session_state["full_sim_design_key"] = (cell_id, ns, np_val, cooling, bms, spacing)
        st.success("Full simulation complete!")

res = st.session_state.get("full_sim_result", res_fast)

# ── Visualizations ────────────────────────────────────────────────────────────
col_heat, col_transient, col_bom = st.columns([1.2, 1.2, 1.0], gap="medium")

with col_heat:
    with st.container(border=True):
        st.markdown(f"<div style='font-size:0.85rem; font-weight:700; color:{PRIMARY}; margin-bottom:0.5rem;'>🔥 2D Layout Thermal Heatmap</div>", unsafe_allow_html=True)
        total_cells = design.ns * design.np
        cols_n = int(np.ceil(np.sqrt(total_cells * 1.5)))
        rows_n = int(np.ceil(total_cells / cols_n))
        grid = np.zeros((rows_n, cols_n))
        cy, cx = (rows_n - 1) / 2.0, (cols_n - 1) / 2.0
        max_r = max(1.0, np.sqrt(cx**2 + cy**2))
        for r in range(rows_n):
            for c in range(cols_n):
                dist = np.sqrt((r - cy) ** 2 + (c - cx) ** 2)
                grid[r, c] = res.peak_temp_C - res.temp_gradient_C * (dist / max_r) ** 2

        fig_heat = px.imshow(
            grid,
            color_continuous_scale="Inferno",
            labels=dict(x="Cell Columns", y="Cell Rows", color="Temp (°C)"),
            title=f"Hotspot: {res.peak_temp_C:.1f}°C  ΔT={res.temp_gradient_C:.1f}°C",
            template=PLOTLY_TEMPLATE,
            aspect="auto",
        )
        fig_heat = apply_plotly_theme(fig_heat)
        st.plotly_chart(fig_heat, width="stretch")

with col_transient:
    with st.container(border=True):
        st.markdown(f"<div style='font-size:0.85rem; font-weight:700; color:{PRIMARY}; margin-bottom:0.5rem;'>⏱️ Drive Cycle Thermal Rise</div>", unsafe_allow_html=True)
        if res.time_series and "temp_C" in res.time_series:
            time_m = [t / 60.0 for t in res.time_series["time_s"]]
            fig_temp = go.Figure()
            fig_temp.add_trace(go.Scatter(
                x=time_m, y=res.time_series["temp_C"],
                mode="lines", name="Pack Temp",
                line=dict(color=ACCENT, width=2.5),
                fill="tozeroy",
                fillcolor="rgba(255,122,0,0.07)",
            ))
            fig_temp.add_hline(y=45.0, line_dash="dash", line_color=FAIL_COLOR, annotation_text="Limit 45°C (R-05)")
            fig_temp.update_layout(
                title="Temperature vs Time (30-min Urban Drive Cycle)",
                xaxis_title="Time (minutes)",
                yaxis_title="Temperature (°C)",
                template=PLOTLY_TEMPLATE,
            )
            fig_temp = apply_plotly_theme(fig_temp)
            st.plotly_chart(fig_temp, width="stretch")
        else:
            st.info("Click **Run Full Physics Simulation** above to generate the transient thermal curve.")

with col_bom:
    with st.container(border=True):
        st.markdown(f"<div style='font-size:0.85rem; font-weight:700; color:{PRIMARY}; margin-bottom:0.5rem;'>💰 BOM Cost Breakdown</div>", unsafe_allow_html=True)
        fig_bom = px.pie(
            names=list(res.itemized_cost_USD.keys()),
            values=list(res.itemized_cost_USD.values()),
            hole=0.5,
            title=f"Total: ${res.bom_cost_USD:.2f}",
            template=PLOTLY_TEMPLATE,
            color_discrete_sequence=[PRIMARY, SECONDARY, ACCENT, PASS_COLOR, WARN_COLOR, INFO_COLOR, "#AB47BC"],
        )
        fig_bom = apply_plotly_theme(fig_bom)
        fig_bom.update_traces(textposition="inside", textinfo="percent+label")
        st.plotly_chart(fig_bom, width="stretch")

st.markdown("<div style='height:0.5rem'></div>", unsafe_allow_html=True)

# ── Findings ──────────────────────────────────────────────────────────────────
with st.container(border=True):
    n_crit = sum(1 for f in res.findings if f.severity == "critical")
    n_warn = sum(1 for f in res.findings if f.severity == "warning")
    st.markdown(
        f"<div style='font-size:0.85rem; font-weight:700; color:#E6EDF3; margin-bottom:0.75rem;'>"
        f"⚠️ Subsystem Findings &nbsp;"
        f"<span style='background:rgba(255,76,76,0.15); color:{FAIL_COLOR}; padding:2px 8px; border-radius:8px; font-size:0.75rem;'>{n_crit} Critical</span> &nbsp;"
        f"<span style='background:rgba(255,167,38,0.15); color:{WARN_COLOR}; padding:2px 8px; border-radius:8px; font-size:0.75rem;'>{n_warn} Warning</span>"
        f"</div>",
        unsafe_allow_html=True,
    )
    if res.findings:
        for f in res.findings:
            finding_card(f.severity, f.title, f.subsystem, f.explanation, f.suggested_fix)
    else:
        st.success("✅ Zero active conflicts or safety violations detected for this design.")
