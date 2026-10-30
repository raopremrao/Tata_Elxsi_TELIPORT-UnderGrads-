"""Page 9: End-to-End Requirements Traceability Engine."""

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

import streamlit as st
import pandas as pd
import networkx as nx
import plotly.graph_objects as go
from app.theme import (
    apply_theme, render_sidebar_scenario, page_header, apply_plotly_theme,
    PLOTLY_TEMPLATE, PRIMARY, SECONDARY, ACCENT, PASS_COLOR, FAIL_COLOR, WARN_COLOR,
    BG_CARD, BORDER, TEXT_SECONDARY, TEXT_MUTED
)
from core.schemas import Scenario
from core.data_loader import load_cells
from models.evaluate import evaluate
from optimize.space import get_baseline_designs
from analysis.traceability import (
    build_traceability_graph,
    generate_traceability_matrix,
    generate_design_dossier,
)

apply_theme()
render_sidebar_scenario()

page_header(
    "End-to-End Requirements Traceability",
    "Trace how high-level specifications (R-01 → R-12) map to components, engineering assumptions, physics models, and empirical test evidence.",
    "🔗"
)

scenario = st.session_state.get("scenario", Scenario())
cells = load_cells()
baselines = get_baseline_designs()

# Design selector
col_sel, col_stat = st.columns([1, 2], gap="large")
with col_sel:
    selected_design_name = st.selectbox(
        "Select Target Pack Architecture",
        options=list(baselines.keys()),
        index=1,  # Default: Design A
    )

selected_design = baselines[selected_design_name]

@st.cache_data(ttl=300, show_spinner=False)
def _evaluate_for_trace(design_name):
    _cells = load_cells()
    _baselines = get_baseline_designs()
    d = _baselines[design_name]
    return evaluate(d, Scenario(), fast=True, cell=_cells[d.cell_id])

with st.spinner("Generating traceability model..."):
    res = _evaluate_for_trace(selected_design_name)

passed_count = sum(1 for r in res.requirements.values() if r.passed)
with col_stat:
    st.markdown(
        f"""
        <div style="background:{BG_CARD}; border:1px solid {BORDER}; border-radius:10px; padding:0.9rem 1.2rem; margin-top:0.3rem;">
            <div style="font-size:0.75rem; color:{TEXT_MUTED}; text-transform:uppercase; letter-spacing:0.06em;">Compliance Summary</div>
            <div style="font-size:1.1rem; font-weight:700; color:#E6EDF3; margin-top:2px;">
                {selected_design_name} ({selected_design.ns}S{selected_design.np}P {cells[selected_design.cell_id].model}):
                <span style="color:{PASS_COLOR if passed_count >= 10 else FAIL_COLOR};"> {passed_count} / 12 Requirements Met</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

st.markdown("<div style='height:0.5rem'></div>", unsafe_allow_html=True)

tab_matrix, tab_graph, tab_dossier = st.tabs([
    "📋 Requirements Compliance Matrix",
    "🕸️ Interactive Dependency Graph",
    "📑 Formal Design Dossier",
])

with tab_matrix:
    with st.container(border=True):
        st.markdown(f"<div style='font-size:0.85rem; font-weight:700; color:{PRIMARY}; margin-bottom:0.75rem;'>System Requirements Verification Matrix — {selected_design_name}</div>", unsafe_allow_html=True)
        df_matrix = generate_traceability_matrix(res)
        st.dataframe(df_matrix, width="stretch", height=460)
        st.caption("Each requirement tracks its mapped engineering component, underlying physics model, and verification verdict.")

with tab_graph:
    with st.container(border=True):
        st.markdown(f"<div style='font-size:0.85rem; font-weight:700; color:{PRIMARY}; margin-bottom:0.5rem;'>NetworkX System Architecture Graph — Requirement & Dependency Flows</div>", unsafe_allow_html=True)
        
        # Build graph
        g = build_traceability_graph(res)
        pos = nx.spring_layout(g, seed=42, k=0.9, iterations=50)

        edge_x = []
        edge_y = []
        for edge in g.edges():
            if edge[0] in pos and edge[1] in pos:
                x0, y0 = pos[edge[0]]
                x1, y1 = pos[edge[1]]
                edge_x.extend([x0, x1, None])
                edge_y.extend([y0, y1, None])

        edge_trace = go.Scatter(
            x=edge_x, y=edge_y,
            line=dict(width=1.2, color="rgba(139, 148, 158, 0.35)"),
            hoverinfo="none",
            mode="lines"
        )

        node_x = []
        node_y = []
        node_text = []
        node_hover = []
        node_color = []

        type_colors = {
            "Requirement": ACCENT,
            "Component": PRIMARY,
            "Assumption": WARN_COLOR,
            "Model": SECONDARY,
            "Evidence": "#AB47BC",
        }

        for node in g.nodes():
            x, y = pos[node]
            node_x.append(x)
            node_y.append(y)
            data = g.nodes[node]
            n_type = data.get("node_type", "Unknown")
            desc = data.get("description", "")
            node_text.append(str(node))
            node_hover.append(f"<b>{node}</b><br>Type: {n_type}<br>{desc}")
            node_color.append(type_colors.get(n_type, "#90A4AE"))

        node_trace = go.Scatter(
            x=node_x, y=node_y,
            mode="markers+text",
            hoverinfo="text",
            text=node_text,
            textposition="top center",
            textfont=dict(size=10, color="#E6EDF3"),
            hovertext=node_hover,
            marker=dict(size=16, color=node_color, line=dict(width=1.5, color="#FFFFFF"))
        )

        fig_g = go.Figure(data=[edge_trace, node_trace])
        fig_g.update_layout(
            showlegend=False,
            hovermode="closest",
            margin=dict(b=20, l=20, r=20, t=20),
            xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
            yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
            template=PLOTLY_TEMPLATE,
        )
        fig_g = apply_plotly_theme(fig_g)
        st.plotly_chart(fig_g, width="stretch")

        # Color legend
        st.markdown(
            f"""
            <div style="display:flex; gap:1rem; flex-wrap:wrap; margin-top:0.5rem; font-size:0.75rem;">
                <div><span style="display:inline-block; width:10px; height:10px; border-radius:50%; background:{ACCENT}; margin-right:4px;"></span> Requirement</div>
                <div><span style="display:inline-block; width:10px; height:10px; border-radius:50%; background:{PRIMARY}; margin-right:4px;"></span> Component</div>
                <div><span style="display:inline-block; width:10px; height:10px; border-radius:50%; background:{WARN_COLOR}; margin-right:4px;"></span> Assumption</div>
                <div><span style="display:inline-block; width:10px; height:10px; border-radius:50%; background:{SECONDARY}; margin-right:4px;"></span> Physics Model</div>
                <div><span style="display:inline-block; width:10px; height:10px; border-radius:50%; background:#AB47BC; margin-right:4px;"></span> Test Evidence</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

with tab_dossier:
    with st.container(border=True):
        st.markdown(f"<div style='font-size:0.85rem; font-weight:700; color:{PRIMARY}; margin-bottom:0.75rem;'>Official System Design Dossier — {selected_design_name}</div>", unsafe_allow_html=True)
        dossier = generate_design_dossier(res)
        
        col_d1, col_d2 = st.columns(2)
        with col_d1:
            st.markdown(f"**Architecture**: `{dossier.get('architecture', selected_design_name)}`")
            st.markdown(f"**Cell**: `{cells[selected_design.cell_id].model}` ({cells[selected_design.cell_id].chemistry.value})")
            st.markdown(f"**Configuration**: `{selected_design.ns}S {selected_design.np}P` ({selected_design.ns * selected_design.np} cells total)")
            st.markdown(f"**Cooling**: `{selected_design.cooling.value.title()}`")
            st.markdown(f"**BMS Tier**: `{selected_design.bms_tier.value.title()}`")
        with col_d2:
            st.markdown(f"**Pack Mass**: `{res.pack_mass_kg:.2f} kg`")
            st.markdown(f"**BOM Cost**: `${res.bom_cost_USD:.2f}`")
            st.markdown(f"**Usable Energy**: `{res.usable_energy_Wh:.1f} Wh`")
            st.markdown(f"**Peak Temperature**: `{res.peak_temp_C:.1f} °C`")
            st.markdown(f"**Estimated Cycle Life**: `{res.estimated_cycle_life} cycles`")
        
        st.markdown("<div style='height:0.5rem'></div>", unsafe_allow_html=True)
        with st.expander("🔍 View Raw JSON Dossier"):
            st.json(dossier)
