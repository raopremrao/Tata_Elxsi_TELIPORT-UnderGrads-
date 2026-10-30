"""Page 1: Requirements and Operating Scenario Configuration."""

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

import streamlit as st
import pandas as pd
from app.theme import apply_theme, render_sidebar_scenario, page_header, BG_CARD, BORDER, PRIMARY, TEXT_SECONDARY
from core.data_loader import load_requirements
from core.schemas import Scenario

apply_theme()
render_sidebar_scenario()

page_header(
    "Requirements & Operating Scenario",
    "Configure operational duty cycles, environmental parameters, and explore locked system requirements.",
    "📋"
)

col1, col2 = st.columns([1, 2], gap="large")

with col1:
    with st.container(border=True):
        st.markdown(f"<div style='font-size:0.85rem; font-weight:700; color:{PRIMARY}; text-transform:uppercase; letter-spacing:0.06em; margin-bottom:0.75rem;'>⚙️ Scenario Parameters</div>", unsafe_allow_html=True)
        amb_temp = st.slider("Ambient Temperature (°C)", min_value=15.0, max_value=50.0, value=35.0, step=1.0)
        budget = st.slider("BOM Cost Budget (USD)", min_value=250.0, max_value=800.0, value=450.0, step=25.0)
        max_mass = st.slider("Maximum Pack Mass (kg)", min_value=10.0, max_value=30.0, value=18.0, step=0.5)
        max_vol = st.slider("Maximum Volume (Liters)", min_value=12.0, max_value=40.0, value=22.0, step=1.0)
        mc_iters = st.select_slider("Monte Carlo Iterations", options=[100, 250, 500, 1000], value=500)
        seed = st.number_input("Random Seed", min_value=1, max_value=99999, value=42)

    st.session_state["scenario"] = Scenario(
        ambient_temp_C=amb_temp,
        cost_budget_USD=budget,
        max_mass_kg=max_mass,
        max_volume_L=max_vol,
        mc_iterations=mc_iters,
        seed=seed,
    )
    st.success("✅ Scenario parameters saved to session state.")

    # Active scenario summary
    st.markdown(f"""
    <div style="background:{BG_CARD}; border:1px solid {BORDER}; border-radius:10px; padding:1rem; margin-top:0.5rem;">
        <div style="font-size:0.75rem; color:{TEXT_SECONDARY}; margin-bottom:0.3rem;">Active Scenario Preview</div>
        <div style="font-size:0.85rem; color:#E6EDF3;">
            <b>{amb_temp}°C</b> ambient &nbsp;|&nbsp; <b>${budget:.0f}</b> budget &nbsp;|&nbsp;
            <b>{max_mass} kg</b> max mass &nbsp;|&nbsp; <b>{max_vol} L</b> max vol
        </div>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown(f"<div style='font-size:0.85rem; font-weight:700; color:{PRIMARY}; text-transform:uppercase; letter-spacing:0.06em; margin-bottom:0.75rem;'>📜 System Engineering Requirements (R-01 → R-12)</div>", unsafe_allow_html=True)
    reqs = load_requirements()
    table_data = []
    for r_id, r in sorted(reqs.items()):
        table_data.append({
            "ID": r.id,
            "Requirement": r.text,
            "Target Value": f"{r.target_value} {r.unit}",
            "Verification": r.verification_method,
            "Rationale": r.rationale,
        })
    df_reqs = pd.DataFrame(table_data)
    st.dataframe(df_reqs, width="stretch", height=480)

    st.info("Requirements R-01 through R-12 are locked (derived from Tata Elxsi TELIPORT Case Study 2 specification). All design decisions are verified against these targets.")
