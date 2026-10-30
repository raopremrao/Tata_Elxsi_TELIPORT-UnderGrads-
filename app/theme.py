"""PackForge UI Design System — Professional Theme, CSS & Plotly Templates."""

import streamlit as st
import plotly.graph_objects as go
import plotly.express as px

# ─── Brand Palette ────────────────────────────────────────────────────────────
PRIMARY     = "#00A86B"   # Clean-tech Emerald Green
SECONDARY   = "#006699"   # Tata Elxsi Deep Blue
ACCENT      = "#FF7A00"   # High-Voltage Energy Orange
PASS_COLOR  = "#00E676"
FAIL_COLOR  = "#FF4C4C"
WARN_COLOR  = "#FFA726"
INFO_COLOR  = "#42A5F5"

BG_BASE     = "#0D1117"
BG_SURFACE  = "#161B22"
BG_CARD     = "#1C2333"
BORDER      = "#30363D"
TEXT_PRIMARY   = "#E6EDF3"
TEXT_SECONDARY = "#8B949E"
TEXT_MUTED     = "#6E7681"

PLOTLY_TEMPLATE = "plotly_dark"

_PLOTLY_LAYOUT_DEFAULTS = dict(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font=dict(family="Inter, sans-serif", color=TEXT_PRIMARY, size=12),
    margin=dict(l=16, r=16, t=40, b=16),
    colorway=[PRIMARY, SECONDARY, ACCENT, PASS_COLOR, WARN_COLOR, INFO_COLOR, "#AB47BC"],
)


def apply_plotly_theme(fig: go.Figure) -> go.Figure:
    """Apply PackForge brand theme to any Plotly figure."""
    fig.update_layout(template=PLOTLY_TEMPLATE, **_PLOTLY_LAYOUT_DEFAULTS)
    fig.update_xaxes(
        gridcolor="rgba(48,54,61,0.8)",
        linecolor=BORDER,
        zerolinecolor="rgba(48,54,61,0.5)",
    )
    fig.update_yaxes(
        gridcolor="rgba(48,54,61,0.8)",
        linecolor=BORDER,
        zerolinecolor="rgba(48,54,61,0.5)",
    )
    return fig


def apply_theme():
    """Inject PackForge global CSS into the Streamlit page."""
    st.markdown(
        f"""
        <style>
        /* ── Google Font ─────────────────────────────────── */
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');

        /* ── Global Reset ────────────────────────────────── */
        html, body, [class*="css"] {{
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
        }}

        /* ── Main Content Area ───────────────────────────── */
        .main .block-container {{
            padding-top: 1.5rem;
            padding-bottom: 3rem;
            max-width: 1400px;
        }}

        /* ── Hero Header ─────────────────────────────────── */
        .pf-hero {{
            background: linear-gradient(135deg, {BG_SURFACE} 0%, #0d2137 50%, #0d1a0f 100%);
            border: 1px solid {BORDER};
            border-radius: 16px;
            padding: 2.5rem 2rem;
            margin-bottom: 1.5rem;
            position: relative;
            overflow: hidden;
        }}
        .pf-hero::before {{
            content: '';
            position: absolute;
            top: -50%;
            right: -10%;
            width: 400px;
            height: 400px;
            background: radial-gradient(circle, rgba(0,168,107,0.12) 0%, transparent 70%);
            border-radius: 50%;
        }}
        .pf-hero-title {{
            font-size: 3rem;
            font-weight: 800;
            background: linear-gradient(90deg, {PRIMARY} 0%, {SECONDARY} 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            letter-spacing: -0.02em;
            line-height: 1.1;
            margin: 0 0 0.5rem 0;
        }}
        .pf-hero-subtitle {{
            font-size: 1.1rem;
            color: {TEXT_SECONDARY};
            font-weight: 400;
            margin: 0 0 1rem 0;
            max-width: 700px;
        }}
        .pf-hero-tag {{
            display: inline-block;
            background: rgba(0,168,107,0.15);
            border: 1px solid rgba(0,168,107,0.4);
            color: {PRIMARY};
            padding: 4px 12px;
            border-radius: 20px;
            font-size: 0.75rem;
            font-weight: 600;
            letter-spacing: 0.05em;
            text-transform: uppercase;
            margin-right: 8px;
        }}

        /* ── Section Header ──────────────────────────────── */
        .pf-section-header {{
            display: flex;
            align-items: center;
            gap: 10px;
            margin: 1.5rem 0 1rem 0;
            padding-bottom: 0.5rem;
            border-bottom: 1px solid {BORDER};
        }}
        .pf-section-title {{
            font-size: 1.15rem;
            font-weight: 700;
            color: {TEXT_PRIMARY};
            margin: 0;
        }}
        .pf-section-badge {{
            background: rgba(0,168,107,0.15);
            color: {PRIMARY};
            padding: 2px 10px;
            border-radius: 12px;
            font-size: 0.75rem;
            font-weight: 600;
        }}

        /* ── KPI / Metric Cards ──────────────────────────── */
        .pf-kpi-card {{
            background: {BG_CARD};
            border: 1px solid {BORDER};
            border-radius: 12px;
            padding: 1.25rem 1.2rem;
            position: relative;
            overflow: hidden;
            transition: transform 0.15s ease, box-shadow 0.15s ease;
        }}
        .pf-kpi-card:hover {{
            transform: translateY(-2px);
            box-shadow: 0 8px 24px rgba(0,0,0,0.4);
        }}
        .pf-kpi-card-accent {{
            position: absolute;
            top: 0; left: 0; right: 0;
            height: 3px;
            background: linear-gradient(90deg, {PRIMARY}, {SECONDARY});
        }}
        .pf-kpi-label {{
            font-size: 0.7rem;
            font-weight: 600;
            color: {TEXT_MUTED};
            text-transform: uppercase;
            letter-spacing: 0.08em;
            margin-bottom: 0.35rem;
        }}
        .pf-kpi-value {{
            font-size: 1.8rem;
            font-weight: 700;
            color: {TEXT_PRIMARY};
            line-height: 1.1;
            margin-bottom: 0.2rem;
        }}
        .pf-kpi-unit {{
            font-size: 0.85rem;
            font-weight: 400;
            color: {TEXT_SECONDARY};
        }}
        .pf-kpi-badge-pass {{
            display: inline-block;
            background: rgba(0,230,118,0.12);
            border: 1px solid rgba(0,230,118,0.35);
            color: {PASS_COLOR};
            padding: 1px 8px;
            border-radius: 10px;
            font-size: 0.7rem;
            font-weight: 700;
        }}
        .pf-kpi-badge-fail {{
            display: inline-block;
            background: rgba(255,76,76,0.12);
            border: 1px solid rgba(255,76,76,0.35);
            color: {FAIL_COLOR};
            padding: 1px 8px;
            border-radius: 10px;
            font-size: 0.7rem;
            font-weight: 700;
        }}
        .pf-kpi-badge-warn {{
            display: inline-block;
            background: rgba(255,167,38,0.12);
            border: 1px solid rgba(255,167,38,0.35);
            color: {WARN_COLOR};
            padding: 1px 8px;
            border-radius: 10px;
            font-size: 0.7rem;
            font-weight: 700;
        }}

        /* ── Feature Cards (Home page) ───────────────────── */
        .pf-feature-card {{
            background: {BG_CARD};
            border: 1px solid {BORDER};
            border-radius: 12px;
            padding: 1.5rem;
            height: 100%;
            transition: border-color 0.2s ease;
        }}
        .pf-feature-card:hover {{
            border-color: {PRIMARY};
        }}
        .pf-feature-icon {{
            font-size: 2rem;
            margin-bottom: 0.75rem;
        }}
        .pf-feature-title {{
            font-size: 1rem;
            font-weight: 700;
            color: {TEXT_PRIMARY};
            margin-bottom: 0.5rem;
        }}
        .pf-feature-text {{
            font-size: 0.875rem;
            color: {TEXT_SECONDARY};
            line-height: 1.6;
        }}

        /* ── Finding / Alert Boxes ───────────────────────── */
        .pf-finding-critical {{
            background: rgba(255,76,76,0.06);
            border: 1px solid rgba(255,76,76,0.3);
            border-left: 4px solid {FAIL_COLOR};
            border-radius: 8px;
            padding: 1rem 1.25rem;
            margin-bottom: 0.75rem;
        }}
        .pf-finding-warning {{
            background: rgba(255,167,38,0.06);
            border: 1px solid rgba(255,167,38,0.3);
            border-left: 4px solid {WARN_COLOR};
            border-radius: 8px;
            padding: 1rem 1.25rem;
            margin-bottom: 0.75rem;
        }}
        .pf-finding-info {{
            background: rgba(66,165,245,0.06);
            border: 1px solid rgba(66,165,245,0.3);
            border-left: 4px solid {INFO_COLOR};
            border-radius: 8px;
            padding: 1rem 1.25rem;
            margin-bottom: 0.75rem;
        }}
        .pf-finding-title {{
            font-size: 0.9rem;
            font-weight: 700;
            margin-bottom: 0.35rem;
        }}
        .pf-finding-body {{
            font-size: 0.85rem;
            color: {TEXT_SECONDARY};
            line-height: 1.55;
        }}
        .pf-finding-fix {{
            font-size: 0.8rem;
            color: {PASS_COLOR};
            margin-top: 0.5rem;
            font-weight: 500;
        }}

        /* ── Sidebar ─────────────────────────────────────── */
        [data-testid="stSidebar"] {{
            background: {BG_SURFACE} !important;
            border-right: 1px solid {BORDER} !important;
        }}
        [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p {{
            color: {TEXT_SECONDARY};
        }}

        /* ── Page Title ──────────────────────────────────── */
        .pf-page-title {{
            font-size: 1.8rem;
            font-weight: 800;
            color: {TEXT_PRIMARY};
            margin-bottom: 0.25rem;
            letter-spacing: -0.02em;
        }}
        .pf-page-subtitle {{
            font-size: 0.9rem;
            color: {TEXT_SECONDARY};
            margin-bottom: 1.25rem;
        }}

        /* ── Divider ─────────────────────────────────────── */
        .pf-divider {{
            height: 1px;
            background: {BORDER};
            margin: 1.5rem 0;
            border: none;
        }}

        /* ── Unverified chip ─────────────────────────────── */
        .pf-chip-unverified {{
            background: rgba(255,122,0,0.12);
            border: 1px solid rgba(255,122,0,0.4);
            color: {ACCENT};
            padding: 3px 10px;
            border-radius: 12px;
            font-size: 0.75rem;
            font-weight: 600;
            display: inline-block;
        }}
        .pf-chip-verified {{
            background: rgba(0,168,107,0.12);
            border: 1px solid rgba(0,168,107,0.4);
            color: {PRIMARY};
            padding: 3px 10px;
            border-radius: 12px;
            font-size: 0.75rem;
            font-weight: 600;
            display: inline-block;
        }}

        /* ── Stat grid (horizontal KPI strip) ────────────── */
        .pf-stat-strip {{
            display: flex;
            gap: 1rem;
            flex-wrap: wrap;
            margin: 1rem 0;
        }}
        .pf-stat-item {{
            flex: 1 1 120px;
            background: {BG_CARD};
            border: 1px solid {BORDER};
            border-radius: 10px;
            padding: 0.8rem 1rem;
            text-align: center;
        }}
        .pf-stat-num {{
            font-size: 1.6rem;
            font-weight: 700;
            color: {PRIMARY};
        }}
        .pf-stat-label {{
            font-size: 0.72rem;
            color: {TEXT_MUTED};
            text-transform: uppercase;
            letter-spacing: 0.06em;
        }}

        /* ── Tabs ────────────────────────────────────────── */
        [data-testid="stTabs"] [data-baseweb="tab"] {{
            font-weight: 600;
            font-size: 0.875rem;
        }}

        /* ── Buttons ─────────────────────────────────────── */
        [data-testid="stButton"] button[kind="primary"] {{
            background: linear-gradient(135deg, {PRIMARY} 0%, #00875A 100%);
            border: none;
            font-weight: 600;
        }}

        /* ── Dataframe ───────────────────────────────────── */
        [data-testid="stDataFrame"] {{
            border: 1px solid {BORDER} !important;
            border-radius: 8px;
            overflow: hidden;
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_sidebar_scenario(scenario_name: str = "48V Urban Two-Wheeler"):
    """Render PackForge branded sidebar with active scenario badge."""
    st.sidebar.markdown(
        f"""
        <div style="padding: 0.5rem 0 1rem 0;">
            <div style="font-size:1.35rem; font-weight:800; background:linear-gradient(90deg,{PRIMARY},{SECONDARY});
                        -webkit-background-clip:text; -webkit-text-fill-color:transparent; background-clip:text;">
                ⚡ PackForge
            </div>
            <div style="font-size:0.72rem; color:{TEXT_MUTED}; font-weight:500; letter-spacing:0.05em; text-transform:uppercase;">
                TELIPORT Season 4 · Case Study 2
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.sidebar.markdown(
        f"""
        <div style="background:rgba(0,168,107,0.1); border:1px solid rgba(0,168,107,0.3);
                    border-radius:8px; padding:0.6rem 0.8rem; margin-bottom:0.75rem;">
            <div style="font-size:0.68rem; color:{TEXT_MUTED}; text-transform:uppercase; letter-spacing:0.06em; font-weight:600;">Active Scenario</div>
            <div style="font-size:0.88rem; color:{PRIMARY}; font-weight:700; margin-top:2px;">{scenario_name}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def page_header(title: str, subtitle: str = "", icon: str = ""):
    """Render a consistent PackForge page header."""
    icon_html = f'<span style="margin-right:0.4rem;">{icon}</span>' if icon else ""
    st.markdown(
        f"""
        <div style="margin-bottom:1.25rem;">
            <div class="pf-page-title">{icon_html}{title}</div>
            {f'<div class="pf-page-subtitle">{subtitle}</div>' if subtitle else ""}
        </div>
        """,
        unsafe_allow_html=True,
    )


def kpi_card(title: str, value: str, unit: str = "", passed: bool | None = None, delta: str = ""):
    """Render a single professional KPI card via st.markdown."""
    if passed is True:
        badge = '<span class="pf-kpi-badge-pass">PASS</span>'
    elif passed is False:
        badge = '<span class="pf-kpi-badge-fail">FAIL</span>'
    else:
        badge = ""

    delta_html = f'<div style="font-size:0.75rem; color:{TEXT_MUTED}; margin-top:0.15rem;">{delta}</div>' if delta else ""

    st.markdown(
        f"""
        <div class="pf-kpi-card">
            <div class="pf-kpi-card-accent"></div>
            <div class="pf-kpi-label">{title}</div>
            <div class="pf-kpi-value">{value}<span class="pf-kpi-unit"> {unit}</span></div>
            {badge}
            {delta_html}
        </div>
        """,
        unsafe_allow_html=True,
    )


def finding_card(severity: str, title: str, subsystem: str, explanation: str, fix: str):
    """Render a finding/conflict card with appropriate severity styling."""
    sev = severity.lower()
    css_class = {
        "critical": "pf-finding-critical",
        "warning": "pf-finding-warning",
    }.get(sev, "pf-finding-info")
    color = {
        "critical": FAIL_COLOR,
        "warning": WARN_COLOR,
    }.get(sev, INFO_COLOR)
    badge_bg = {
        "critical": "rgba(255,76,76,0.15)",
        "warning": "rgba(255,167,38,0.15)",
    }.get(sev, "rgba(66,165,245,0.15)")

    st.markdown(
        f"""
        <div class="{css_class}">
            <div class="pf-finding-title" style="color:{color};">
                <span style="background:{badge_bg}; padding:1px 8px; border-radius:8px; font-size:0.7rem; margin-right:6px;">{severity.upper()}</span>
                {title}
                <span style="font-size:0.75rem; color:{TEXT_MUTED}; font-weight:400; margin-left:8px;">— {subsystem}</span>
            </div>
            <div class="pf-finding-body">{explanation}</div>
            <div class="pf-finding-fix">✦ Remediation: {fix}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def hero_banner():
    """Render the PackForge home hero section."""
    st.markdown(
        f"""
        <div class="pf-hero">
            <div style="margin-bottom:0.75rem;">
                <span class="pf-hero-tag">Tata Elxsi TELIPORT S4</span>
                <span class="pf-hero-tag" style="background:rgba(0,102,153,0.15); border-color:rgba(0,102,153,0.4); color:{SECONDARY};">Case Study 2</span>
                <span class="pf-hero-tag" style="background:rgba(255,122,0,0.12); border-color:rgba(255,122,0,0.4); color:{ACCENT};">Battery Energy Systems</span>
            </div>
            <div class="pf-hero-title">PackForge</div>
            <div class="pf-hero-subtitle">
                From Cell Datasheet to Defensible Battery Design in Minutes.<br>
                Multiphysics simulation · Quantum-Inspired QUBO Optimization · Full Traceability.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
