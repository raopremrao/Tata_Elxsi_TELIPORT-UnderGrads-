"""Page 7: Trade-Off Explorer & Sensitivity Analysis."""

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

import streamlit as st
import pandas as pd
import plotly.express as px
from app.theme import (
    apply_theme, render_sidebar_scenario, page_header, apply_plotly_theme,
    PLOTLY_TEMPLATE, PRIMARY, SECONDARY, ACCENT, PASS_COLOR,
    BG_CARD, BORDER, TEXT_SECONDARY, TEXT_MUTED
)
from core.schemas import Scenario
from optimize.exhaustive import run_exhaustive_search, ExhaustiveResults
from analysis.sensitivity import run_oat_sensitivity
from optimize.space import get_baseline_designs

apply_theme()
render_sidebar_scenario()

page_header(
    "Multi-Dimensional Trade-Off Explorer",
    "Navigate Pareto frontiers via parallel coordinates and evaluate assumption uncertainty via tornado sensitivity analysis.",
    "🧭"
)

scenario = st.session_state.get("scenario", Scenario())

@st.cache_data(ttl=600, show_spinner=False)
def _cached_exh():
    return run_exhaustive_search(Scenario())

with st.spinner("Loading design space..."):
    exh: ExhaustiveResults = _cached_exh()

# ── Parallel Coordinates ──────────────────────────────────────────────────────
with st.container(border=True):
    st.markdown(f"<div style='font-size:0.85rem; font-weight:700; color:{PRIMARY}; margin-bottom:0.5rem;'>🌐 Parallel Coordinates: Design Variable Coupling to System KPIs</div>", unsafe_allow_html=True)
    df_parallel = pd.DataFrame({
        "Cell Series":      [d.ns for d in exh.designs],
        "Cell Parallel":    [d.np for d in exh.designs],
        "Nom Voltage (V)":  [r.nominal_voltage_V for r in exh.results],
        "Usable Energy (Wh)": [r.usable_energy_Wh for r in exh.results],
        "Peak Temp (°C)":   [r.peak_temp_C for r in exh.results],
        "Pack Mass (kg)":   [r.pack_mass_kg for r in exh.results],
        "BOM Cost ($)":     [r.bom_cost_USD for r in exh.results],
    })
    fig_par = px.parallel_coordinates(
        df_parallel,
        color="Usable Energy (Wh)",
        color_continuous_scale="Viridis",
        title=f"Coupled Subsystem Interactions Across {len(exh.designs)} Feasible Designs",
        template=PLOTLY_TEMPLATE,
    )
    fig_par = apply_plotly_theme(fig_par)
    st.plotly_chart(fig_par, width="stretch")
    st.caption("Drag axis ranges to filter and highlight specific design families. Color encodes usable energy — drag to isolate high-energy designs.")

st.markdown("<div style='height:0.5rem'></div>", unsafe_allow_html=True)

# ── Tornado Sensitivity ───────────────────────────────────────────────────────
col_sens, col_expl = st.columns([1.5, 1.0], gap="large")

with col_sens:
    with st.container(border=True):
        st.markdown(f"<div style='font-size:0.85rem; font-weight:700; color:{PRIMARY}; margin-bottom:0.5rem;'>🌪️ Tornado Sensitivity Analysis: Assumption Uncertainty</div>", unsafe_allow_html=True)
        metric_choice = st.selectbox(
            "Select Sensitivity Target Metric",
            ["peak_temp_C", "bom_cost_USD", "pack_mass_kg"],
            format_func=lambda x: x.replace("_", " ").title(),
        )
        baselines = get_baseline_designs()
        target_design = baselines["Design A"]
        df_sens = run_oat_sensitivity(target_design, scenario, target_metric=metric_choice)

        fig_tornado = px.bar(
            df_sens,
            x="Swing",
            y="Parameter",
            orientation="h",
            color="Swing",
            color_continuous_scale="Teal",
            title=f"One-At-A-Time Parameter Swing on: {metric_choice.replace('_',' ').title()}",
            template=PLOTLY_TEMPLATE,
        )
        fig_tornado = apply_plotly_theme(fig_tornado)
        fig_tornado.update_layout(yaxis=dict(categoryorder="total ascending"))
        st.plotly_chart(fig_tornado, width="stretch")
        st.caption("⚠️ OAT sensitivity approximation — assumes linear response. Non-linear coupling effects not captured.")

with col_expl:
    with st.container(border=True):
        st.markdown(f"<div style='font-size:0.85rem; font-weight:700; color:{PRIMARY}; margin-bottom:0.75rem;'>📌 Key Sensitivity Insights</div>", unsafe_allow_html=True)

        def _insight(icon, title, text, color=TEXT_SECONDARY):
            st.markdown(
                f'<div style="background:{BG_CARD}; border:1px solid {BORDER}; border-radius:8px; padding:0.75rem; margin-bottom:0.6rem;">'
                f'<div style="font-size:0.85rem; font-weight:700; color:#E6EDF3; margin-bottom:0.2rem;">{icon} {title}</div>'
                f'<div style="font-size:0.82rem; color:{color}; line-height:1.55;">{text}</div>'
                f'</div>',
                unsafe_allow_html=True,
            )

        _insight("🌡️", "Cooling HTC (h_eff, A-05)",
                 "Exerts the single largest leverage on peak cell temperature (±2.8°C swing). Liquid cooling vs passive ~8°C delta.")
        _insight("💰", "Enclosure Cost ($/kg, A-10)",
                 "Dominates non-cell BOM cost variations (±$7.50 delta). Structural aluminum vs polycarbonate is key decision.")
        _insight("⚡", "Busbar Resistance (A-01)",
                 "Increases I²R heat dissipation during high-power 6 kW bursts. Low-resistance copper busbars justified for >5P configs.")
        _insight("🔋", "Cell Capacity Spread (σ, A-08)",
                 "1% extra capacity spread → ~0.9% reduction in weakest-group usable energy. Critical for large parallel groups.")

        st.info("All sensitivities computed by perturbing Design A (14S4P NMC-21700) assumptions ±10% from nominal.")
