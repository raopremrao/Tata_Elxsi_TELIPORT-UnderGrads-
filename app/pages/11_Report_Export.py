"""Page 11: Report and PPT Asset Bundle Generator."""

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from pathlib import Path
import streamlit as st
from app.theme import (
    apply_theme, render_sidebar_scenario, page_header,
    PRIMARY, SECONDARY, ACCENT, PASS_COLOR, BG_CARD, BORDER,
    TEXT_SECONDARY, TEXT_MUTED
)
from reports.make_report import generate_ppt_asset_bundle

apply_theme()
render_sidebar_scenario()

page_header(
    "Presentation Bundle & Asset Export",
    "Generate 300 DPI competition presentation slide assets, auto-filled RESULTS.md, and the 6-slide evaluation storyline (SLIDE_NOTES.md).",
    "📦"
)

ppt_dir = Path("outputs/ppt_assets")
results_md = Path("outputs/RESULTS.md")
slide_notes_md = Path("outputs/SLIDE_NOTES.md")

# ── Action Banner ─────────────────────────────────────────────────────────────
with st.container(border=True):
    col_btn, col_info = st.columns([1, 2], gap="large")
    with col_btn:
        generate_clicked = st.button("🚀 Generate 300 DPI Slide Assets", type="primary", width="stretch")
    with col_info:
        st.markdown(
            f"""
            <div style="font-size:0.85rem; color:{TEXT_SECONDARY}; line-height:1.6;">
                Assets are saved to <code>outputs/ppt_assets/</code> matching Tata Elxsi hackathon slide deck requirements.
                Includes 300 DPI figures, full evaluation markdown tables, and competition narrative.
            </div>
            """,
            unsafe_allow_html=True,
        )

if generate_clicked:
    with st.status("Rendering high-resolution figures & compiling results...", expanded=True) as status:
        st.write("🎨 Rendering high-res Pareto front and Ragone plot...")
        st.write("📊 Computing benchmark tables and delta matrices...")
        generate_ppt_asset_bundle(output_dir=str(ppt_dir))
        status.update(label="All presentation assets rendered successfully!", state="complete", expanded=False)
    st.success("✅ Complete slide bundle generated and ready for export!")

st.markdown("<div style='height:0.75rem'></div>", unsafe_allow_html=True)

tab_assets, tab_notes, tab_results = st.tabs([
    "📁 Generated Slide Figures & Downloads",
    "📑 6-Slide Presentation Storyline (SLIDE_NOTES.md)",
    "📊 Evaluation Summary (RESULTS.md)",
])

with tab_assets:
    if ppt_dir.exists():
        files = sorted(list(ppt_dir.glob("*")))
        if files:
            st.markdown(f"<div style='font-size:0.85rem; font-weight:700; color:{PRIMARY}; margin-bottom:0.75rem;'>Available Download Assets ({len(files)} files)</div>", unsafe_allow_html=True)
            
            # Display 2 columns of download cards
            c1, c2 = st.columns(2, gap="medium")
            for idx, f in enumerate(files):
                col = c1 if idx % 2 == 0 else c2
                with col:
                    is_image = f.suffix.lower() in [".png", ".jpg", ".jpeg", ".svg"]
                    with st.container(border=True):
                        st.markdown(f"**`{f.name}`**")
                        st.caption(f"Size: {f.stat().st_size / 1024:.1f} KB &nbsp;|&nbsp; Type: {f.suffix.upper()}")
                        
                        if is_image:
                            st.image(str(f), width="stretch")
                        
                        with open(f, "rb") as file_bytes:
                            st.download_button(
                                label=f"⬇️ Download {f.name}",
                                data=file_bytes,
                                file_name=f.name,
                                key=f"dl_{f.name}",
                                width="stretch",
                            )
        else:
            st.info("No files in output directory yet. Click **Generate 300 DPI Slide Assets** above to render.")
    else:
        st.info("Output directory not yet initialized. Click **Generate 300 DPI Slide Assets** above.")

with tab_notes:
    with st.container(border=True):
        if slide_notes_md.exists():
            st.markdown(slide_notes_md.read_text(encoding="utf-8"))
        else:
            st.info("Slide notes will appear here once generated. Click **Generate 300 DPI Slide Assets**.")

with tab_results:
    with st.container(border=True):
        if results_md.exists():
            st.markdown(results_md.read_text(encoding="utf-8"))
        else:
            st.info("Results markdown will appear here once generated. Click **Generate 300 DPI Slide Assets**.")
