"""Page 8: Multidisciplinary Safety and Conflict Detection."""

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

import streamlit as st
import pandas as pd
from app.theme import (
    apply_theme, render_sidebar_scenario, page_header, finding_card,
    PRIMARY, SECONDARY, ACCENT, FAIL_COLOR, WARN_COLOR, INFO_COLOR,
    PASS_COLOR, BG_CARD, BORDER, TEXT_SECONDARY, TEXT_MUTED
)
from core.data_loader import load_cells
from core.schemas import Scenario
from models.evaluate import evaluate
from optimize.space import get_baseline_designs

apply_theme()
render_sidebar_scenario()

page_header(
    "Multidisciplinary Safety & Conflict Detection",
    "Automated rule engine detecting interface incompatibilities, ELV breaches (>60V DC), thermal runaway risks, and sensing gaps.",
    "🛡️"
)

scenario = st.session_state.get("scenario", Scenario())
cells = load_cells()
baselines = get_baseline_designs()

@st.cache_data(ttl=300, show_spinner=False)
def _collect_findings():
    _cells = load_cells()
    _baselines = get_baseline_designs()
    _scenario = Scenario()
    all_findings = []
    for name, d in _baselines.items():
        res = evaluate(d, _scenario, fast=True, cell=_cells[d.cell_id])
        for f in res.findings:
            all_findings.append({
                "Design": name,
                "Finding ID": f.id,
                "Severity": f.severity.upper(),
                "Subsystem": f.subsystem,
                "Issue Title": f.title,
                "Explanation": f.explanation,
                "Remediation": f.suggested_fix,
            })
    return all_findings

with st.spinner("Running conflict detection engine..."):
    all_findings = _collect_findings()

df_find = pd.DataFrame(all_findings)

# ── Summary strip ─────────────────────────────────────────────────────────────
n_crit = sum(1 for f in all_findings if f["Severity"] == "CRITICAL")
n_warn = sum(1 for f in all_findings if f["Severity"] == "WARNING")
n_info = sum(1 for f in all_findings if f["Severity"] == "INFO")

s1, s2, s3, s4 = st.columns(4)
with s1:
    st.markdown(f'<div style="background:rgba(255,76,76,0.08); border:1px solid rgba(255,76,76,0.3); border-radius:10px; padding:1rem; text-align:center;"><div style="font-size:1.8rem; font-weight:800; color:{FAIL_COLOR};">{n_crit}</div><div style="font-size:0.75rem; color:{TEXT_MUTED}; text-transform:uppercase; letter-spacing:0.06em;">Critical Issues</div></div>', unsafe_allow_html=True)
with s2:
    st.markdown(f'<div style="background:rgba(255,167,38,0.08); border:1px solid rgba(255,167,38,0.3); border-radius:10px; padding:1rem; text-align:center;"><div style="font-size:1.8rem; font-weight:800; color:{WARN_COLOR};">{n_warn}</div><div style="font-size:0.75rem; color:{TEXT_MUTED}; text-transform:uppercase; letter-spacing:0.06em;">Warnings</div></div>', unsafe_allow_html=True)
with s3:
    st.markdown(f'<div style="background:rgba(66,165,245,0.08); border:1px solid rgba(66,165,245,0.3); border-radius:10px; padding:1rem; text-align:center;"><div style="font-size:1.8rem; font-weight:800; color:{INFO_COLOR};">{n_info}</div><div style="font-size:0.75rem; color:{TEXT_MUTED}; text-transform:uppercase; letter-spacing:0.06em;">Info</div></div>', unsafe_allow_html=True)
with s4:
    st.markdown(f'<div style="background:rgba(0,168,107,0.08); border:1px solid rgba(0,168,107,0.3); border-radius:10px; padding:1rem; text-align:center;"><div style="font-size:1.8rem; font-weight:800; color:{PRIMARY};">{len(baselines)}</div><div style="font-size:0.75rem; color:{TEXT_MUTED}; text-transform:uppercase; letter-spacing:0.06em;">Designs Scanned</div></div>', unsafe_allow_html=True)

st.markdown("<div style='height:0.75rem'></div>", unsafe_allow_html=True)

# ── Filters ───────────────────────────────────────────────────────────────────
with st.container(border=True):
    col_f1, col_f2, col_f3 = st.columns([1, 1, 1])
    with col_f1:
        sev_filter = st.multiselect("Filter by Severity", ["CRITICAL", "WARNING", "INFO"], default=["CRITICAL", "WARNING", "INFO"])
    with col_f2:
        subsystems = list(df_find["Subsystem"].unique()) if len(df_find) > 0 else []
        sub_filter = st.multiselect("Filter by Subsystem", options=subsystems, default=subsystems)
    with col_f3:
        design_filter = st.multiselect("Filter by Design", options=list(baselines.keys()), default=list(baselines.keys()))

if len(df_find) > 0:
    df_filtered = df_find[
        df_find["Severity"].isin(sev_filter) &
        df_find["Subsystem"].isin(sub_filter) &
        df_find["Design"].isin(design_filter)
    ]

    st.markdown(f"<div style='font-size:0.85rem; color:{TEXT_SECONDARY}; margin-bottom:0.75rem;'>Showing <b>{len(df_filtered)}</b> findings matching filters</div>", unsafe_allow_html=True)

    for idx, row in df_filtered.iterrows():
        finding_card(
            severity=row["Severity"],
            title=f"[{row['Design']}] {row['Issue Title']}",
            subsystem=row["Subsystem"],
            explanation=row["Explanation"],
            fix=row["Remediation"],
        )
        st.caption(f"Rule ID: {row['Finding ID']}")
else:
    st.success("✅ No safety findings detected across all baseline designs.")

st.markdown("<div style='height:0.5rem'></div>", unsafe_allow_html=True)

# ── Findings Table ────────────────────────────────────────────────────────────
with st.expander("📊 View All Findings as Table"):
    if len(df_find) > 0:
        st.dataframe(df_find, width="stretch")
    else:
        st.write("No findings.")
