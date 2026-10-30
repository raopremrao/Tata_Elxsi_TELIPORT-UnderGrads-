"""Page 2: Battery Cell Library & Ragone Analysis."""

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

import streamlit as st
import pandas as pd
import plotly.express as px
from app.theme import (
    apply_theme, render_sidebar_scenario, page_header,
    apply_plotly_theme, PLOTLY_TEMPLATE,
    PRIMARY, SECONDARY, ACCENT, BG_CARD, BORDER, TEXT_SECONDARY, TEXT_MUTED
)
from core.data_loader import load_cells

apply_theme()
render_sidebar_scenario()

page_header(
    "Battery Cell Library",
    "Verified cell specifications with chemistry-level trade-offs and Ragone density analysis.",
    "🔋"
)

cells = load_cells()

# ── Cell Data Table ───────────────────────────────────────────────────────────
rows = []
for c_id, c in cells.items():
    specific_energy_wh_kg = (c.nominal_voltage_V * c.capacity_Ah) / (c.mass_g / 1000.0)
    specific_power_w_kg = (c.nominal_voltage_V * c.max_continuous_discharge_A) / (c.mass_g / 1000.0)
    rows.append({
        "Model": c.model,
        "Manufacturer": c.manufacturer,
        "Chemistry": c.chemistry.value,
        "Form Factor": c.form_factor,
        "Capacity (Ah)": c.capacity_Ah,
        "Nom Voltage (V)": c.nominal_voltage_V,
        "Max Discharge (A)": c.max_continuous_discharge_A,
        "Int. Resistance (mΩ)": c.internal_resistance_mOhm,
        "Mass (g)": c.mass_g,
        "Unit Cost (USD)": round(c.unit_cost_USD, 2),
        "Cycle Life": c.cycle_life_ref,
        "Sp. Energy (Wh/kg)": round(specific_energy_wh_kg, 1),
        "Sp. Power (W/kg)": round(specific_power_w_kg, 1),
        "Verified": "✅ Verified" if c.verified else "⚠️ Unverified",
    })

df_cells = pd.DataFrame(rows)

with st.container(border=True):
    st.markdown(f"<div style='font-size:0.8rem; font-weight:600; color:{TEXT_SECONDARY}; margin-bottom:0.5rem;'>📊 Full Cell Specifications — {len(df_cells)} cells in library</div>", unsafe_allow_html=True)
    st.dataframe(df_cells, width="stretch")

st.markdown("<div style='height:0.5rem'></div>", unsafe_allow_html=True)

# ── Ragone Plot + Source Details ──────────────────────────────────────────────
col_ragone, col_details = st.columns([2, 1], gap="large")

with col_ragone:
    with st.container(border=True):
        st.markdown(f"<div style='font-size:0.85rem; font-weight:700; color:{PRIMARY}; margin-bottom:0.5rem;'>📈 Ragone Plot — Energy Density vs Power Density</div>", unsafe_allow_html=True)

        # Color map per chemistry
        chem_colors = {"NMC": PRIMARY, "LFP": SECONDARY, "NCA": ACCENT}

        fig = px.scatter(
            df_cells,
            x="Sp. Energy (Wh/kg)",
            y="Sp. Power (W/kg)",
            color="Chemistry",
            size="Capacity (Ah)",
            text="Model",
            template=PLOTLY_TEMPLATE,
            title="Gravimetric Energy Density vs Power Density",
            color_discrete_map=chem_colors,
            size_max=40,
            hover_data=["Manufacturer", "Int. Resistance (mΩ)", "Cycle Life"],
        )
        fig.update_traces(textposition="top center", textfont=dict(size=11))
        fig = apply_plotly_theme(fig)
        fig.update_layout(
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        )
        st.plotly_chart(fig, width="stretch")

with col_details:
    with st.container(border=True):
        st.markdown(f"<div style='font-size:0.85rem; font-weight:700; color:{PRIMARY}; margin-bottom:0.75rem;'>📑 Datasheet Verification</div>", unsafe_allow_html=True)
        for c in cells.values():
            if c.verified:
                badge = f'<span style="background:rgba(0,168,107,0.12); border:1px solid rgba(0,168,107,0.4); color:{PRIMARY}; padding:1px 7px; border-radius:9px; font-size:0.7rem; font-weight:600;">✅ VERIFIED</span>'
            else:
                badge = f'<span style="background:rgba(255,122,0,0.12); border:1px solid rgba(255,122,0,0.4); color:{ACCENT}; padding:1px 7px; border-radius:9px; font-size:0.7rem; font-weight:600;">⚠️ UNVERIFIED</span>'

            st.markdown(
                f'<div style="background:{BG_CARD}; border:1px solid {BORDER}; border-radius:8px; padding:0.75rem; margin-bottom:0.6rem;">'
                f'<div style="font-size:0.875rem; font-weight:700; color:#E6EDF3; margin-bottom:4px;">{c.model}</div>'
                f'<div style="font-size:0.78rem; color:{TEXT_MUTED};">{c.manufacturer} · {c.chemistry.value} · {c.form_factor}</div>'
                f'<div style="margin-top:6px;">{badge}</div>',
                unsafe_allow_html=True,
            )
            if c.source_url.startswith("http"):
                st.markdown(f"[🔗 Official Datasheet]({c.source_url})", unsafe_allow_html=False)
            else:
                st.caption("No official datasheet linked — flagged in conflict engine.")
            if c.notes:
                st.caption(f"_{c.notes}_")
            st.markdown("</div>", unsafe_allow_html=True)
