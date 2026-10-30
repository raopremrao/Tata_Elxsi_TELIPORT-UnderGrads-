"""Page 4: Multi-Design Comparison (Design 0 vs A vs B vs Q)."""

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from app.theme import (
    apply_theme, render_sidebar_scenario, page_header, apply_plotly_theme,
    PLOTLY_TEMPLATE, PRIMARY, SECONDARY, ACCENT, PASS_COLOR, FAIL_COLOR, WARN_COLOR,
    BG_CARD, BORDER, TEXT_SECONDARY, TEXT_MUTED
)
from core.data_loader import load_cells
from core.schemas import PackDesign, Scenario
from models.evaluate import evaluate
from optimize.space import get_baseline_designs
from optimize.exhaustive import run_exhaustive_search

apply_theme()
render_sidebar_scenario()

page_header(
    "Compare Alternative Pack Architectures",
    "Side-by-side trade-off evaluation: Design 0 (Baseline), Design A (Engineer's Choice), Design B (LFP Safety), Design Q (Optimizer).",
    "⚖️"
)

cells = load_cells()
scenario = st.session_state.get("scenario", Scenario())
baselines = get_baseline_designs()

@st.cache_data(ttl=600)
def _get_all_results(_scenario_key):
    _cells = load_cells()
    _baselines = get_baseline_designs()
    _scenario = Scenario()
    exh = run_exhaustive_search(_scenario)
    dq_raw = exh.optimal_design
    design_q = PackDesign(
        name="Design Q (Optimizer)",
        cell_id=dq_raw.cell_id,
        ns=dq_raw.ns,
        np=dq_raw.np,
        cooling=dq_raw.cooling,
        bms_tier=dq_raw.bms_tier,
        cell_spacing_mm=dq_raw.cell_spacing_mm,
    )
    all_designs = {
        "Design 0": _baselines["Design 0"],
        "Design A": _baselines["Design A"],
        "Design B": _baselines["Design B"],
        "Design Q": design_q,
    }
    results = {n: evaluate(d, _scenario, fast=True, cell=_cells[d.cell_id]) for n, d in all_designs.items()}
    return results, _cells

with st.spinner("Evaluating all 4 architectures..."):
    results, _cells_ref = _get_all_results("default")

colors = {"Design 0": "#EF5350", "Design A": "#42A5F5", "Design B": "#FFA726", "Design Q": PASS_COLOR}

# ── Top KPI strip ─────────────────────────────────────────────────────────────
st.markdown(f"<div style='font-size:0.78rem; font-weight:700; color:{TEXT_MUTED}; text-transform:uppercase; letter-spacing:0.07em; margin-bottom:0.5rem;'>Quick Comparison — Key Metrics</div>", unsafe_allow_html=True)
kcols = st.columns(4)
for i, (name, r) in enumerate(results.items()):
    n_pass = sum(1 for req in r.requirements.values() if req.passed)
    with kcols[i]:
        st.markdown(
            f"""
            <div style="background:{BG_CARD}; border:1px solid {BORDER}; border-top:3px solid {colors[name]};
                        border-radius:10px; padding:1rem; text-align:center;">
                <div style="font-size:0.8rem; font-weight:700; color:{colors[name]}; margin-bottom:0.5rem;">{name}</div>
                <div style="font-size:1.4rem; font-weight:800; color:#E6EDF3;">{r.usable_energy_Wh:.0f} Wh</div>
                <div style="font-size:0.75rem; color:{TEXT_MUTED};">Usable Energy</div>
                <div style="margin-top:0.4rem; font-size:0.82rem; color:{TEXT_SECONDARY};">
                    {r.peak_temp_C:.1f}°C &nbsp;|&nbsp; {r.pack_mass_kg:.1f} kg &nbsp;|&nbsp; ${r.bom_cost_USD:.0f}
                </div>
                <div style="margin-top:0.4rem; font-size:0.72rem; color:{'#00E676' if n_pass >= 10 else '#FF4C4C'};">{n_pass}/12 requirements</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

st.markdown("<div style='height:1rem'></div>", unsafe_allow_html=True)

# ── Radar + Narrative ─────────────────────────────────────────────────────────
col_radar, col_summary = st.columns([1.3, 1.0], gap="large")

with col_radar:
    with st.container(border=True):
        st.markdown(f"<div style='font-size:0.85rem; font-weight:700; color:{PRIMARY}; margin-bottom:0.5rem;'>🕸️ 6-Axis Normalized Trade-Off Radar</div>", unsafe_allow_html=True)
        categories = ["Usable Energy", "Thermal Margin", "Mass Efficiency", "Cost Efficiency", "Fast Charge", "Cycle Life"]
        fig_radar = go.Figure()

        for name, r in results.items():
            v_energy = min(1.0, r.usable_energy_Wh / 2500.0)
            v_temp   = max(0.0, 1.0 - (r.peak_temp_C - 35.0) / 30.0)
            v_mass   = max(0.0, 1.0 - r.pack_mass_kg / 25.0)
            v_cost   = max(0.0, 1.0 - r.bom_cost_USD / 600.0)
            v_chg    = max(0.0, 1.0 - r.charge_time_min / 120.0)
            v_life   = min(1.0, r.estimated_cycle_life / 2000.0)
            vals = [v_energy, v_temp, v_mass, v_cost, v_chg, v_life]
            vals.append(vals[0])

            fig_radar.add_trace(go.Scatterpolar(
                r=vals,
                theta=categories + [categories[0]],
                name=name,
                line_color=colors[name],
                fill="toself" if name == "Design Q" else "none",
                opacity=0.25 if name == "Design Q" else 1.0,
                line=dict(width=2.5 if name == "Design Q" else 1.8),
            ))

        fig_radar.update_layout(
            polar=dict(
                radialaxis=dict(visible=True, range=[0, 1], tickfont=dict(size=9), gridcolor="rgba(48,54,61,0.8)"),
                angularaxis=dict(tickfont=dict(size=10)),
                bgcolor="rgba(0,0,0,0)",
            ),
            showlegend=True,
            template=PLOTLY_TEMPLATE,
            legend=dict(orientation="h", yanchor="bottom", y=-0.15, xanchor="center", x=0.5),
        )
        fig_radar = apply_plotly_theme(fig_radar)
        st.plotly_chart(fig_radar, width="stretch")

with col_summary:
    with st.container(border=True):
        st.markdown(f"<div style='font-size:0.85rem; font-weight:700; color:{PRIMARY}; margin-bottom:0.75rem;'>💡 Automated Trade-Off Synthesis</div>", unsafe_allow_html=True)
        d0_r = results["Design 0"]
        dq_r = results["Design Q"]
        da_r = results["Design A"]
        db_r = results["Design B"]

        energy_gain = ((dq_r.usable_energy_Wh - d0_r.usable_energy_Wh) / max(1.0, d0_r.usable_energy_Wh)) * 100.0
        temp_drop   = d0_r.peak_temp_C - dq_r.peak_temp_C

        def _card(name, color, text):
            st.markdown(
                f'<div style="background:{BG_CARD}; border:1px solid {BORDER}; border-left:3px solid {color}; '
                f'border-radius:8px; padding:0.75rem 0.9rem; margin-bottom:0.6rem;">'
                f'<div style="font-size:0.8rem; font-weight:700; color:{color}; margin-bottom:0.2rem;">{name}</div>'
                f'<div style="font-size:0.82rem; color:{TEXT_SECONDARY}; line-height:1.5;">{text}</div>'
                f'</div>',
                unsafe_allow_html=True,
            )

        _card("Design 0 — Baseline", "#EF5350",
              f"Extreme thermal stress ({d0_r.peak_temp_C:.1f}°C) with passive cooling on high-IR 18650 cells. Fails R-03 (energy) and R-05 (thermal).")
        _card("Design A — Engineer's Choice", "#42A5F5",
              f"Balanced 14S4P NMC-21700 with forced air cooling. {da_r.usable_energy_Wh:.0f} Wh usable, {da_r.peak_temp_C:.1f}°C peak temp.")
        _card("Design B — LFP Safety-First", "#FFA726",
              f"LFP chemistry gives excellent thermal stability and 2000+ cycle life, but incurs a {db_r.pack_mass_kg:.1f} kg mass penalty.")
        _card("Design Q — QUBO Optimized ⭐", PASS_COLOR,
              f"+{energy_gain:.1f}% usable energy vs D0, peak temp reduced by {temp_drop:.1f}°C. Best multi-objective trade-off.")

# ── Comparison Table ──────────────────────────────────────────────────────────
st.markdown("<div style='height:0.5rem'></div>", unsafe_allow_html=True)
with st.container(border=True):
    st.markdown(f"<div style='font-size:0.85rem; font-weight:700; color:{PRIMARY}; margin-bottom:0.75rem;'>📊 Detailed Metric Comparison & Deltas vs Design 0</div>", unsafe_allow_html=True)

    metrics_to_show = [
        ("Cell Model",           lambda r: _cells_ref[r.design.cell_id].model,                 ""),
        ("Configuration",        lambda r: f"{r.design.ns}S × {r.design.np}P",                 ""),
        ("Cooling Type",         lambda r: r.design.cooling.value.replace("_"," ").title(),    ""),
        ("Nominal Voltage",      lambda r: r.nominal_voltage_V,                                "V"),
        ("Usable Energy",        lambda r: r.usable_energy_Wh,                                 "Wh"),
        ("Peak Temperature",     lambda r: r.peak_temp_C,                                      "°C"),
        ("Charge Time (10-80%)", lambda r: r.charge_time_min,                                  "min"),
        ("Total Pack Mass",      lambda r: r.pack_mass_kg,                                     "kg"),
        ("BOM Cost",             lambda r: r.bom_cost_USD,                                     "USD"),
        ("Estimated Cycle Life", lambda r: r.estimated_cycle_life,                             "cycles"),
        ("Requirements Met",     lambda r: f"{sum(1 for req in r.requirements.values() if req.passed)} / 12", ""),
    ]

    table_rows = []
    for label, extractor, unit in metrics_to_show:
        row = {"Metric": label}
        val0 = extractor(results["Design 0"])
        row["Design 0 (Base)"] = f"{val0} {unit}".strip() if unit else str(val0)
        for name in ["Design A", "Design B", "Design Q"]:
            val = extractor(results[name])
            if isinstance(val, (int, float)) and isinstance(val0, (int, float)) and val0 != 0:
                delta_pct = ((val - val0) / abs(val0)) * 100.0
                row[name] = f"{val:.1f} {unit}  ({delta_pct:+.1f}%)".strip()
            else:
                row[name] = f"{val} {unit}".strip() if unit else str(val)
        table_rows.append(row)

    st.dataframe(pd.DataFrame(table_rows), width="stretch")
