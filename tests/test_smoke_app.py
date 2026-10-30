"""Smoke test for Q-Pack Streamlit pages and assets."""

import importlib.util
from pathlib import Path


def test_streamlit_pages_importable():
    """Verify that all Streamlit app pages are valid Python and import without errors."""
    app_dir = Path(__file__).resolve().parent.parent / "app"
    home_file = app_dir / "Home.py"
    assert home_file.exists(), "Home.py missing!"

    # Find all subpages
    page_files = sorted(list((app_dir / "pages").glob("*.py")))
    assert len(page_files) == 11, f"Expected 11 subpages, found {len(page_files)}"

    all_files = [home_file] + page_files
    for f in all_files:
        spec = importlib.util.spec_from_file_location(f.stem, f)
        assert spec is not None, f"Failed to load spec for {f.name}"
        # Compiling code verifies zero syntax or indentation errors
        with open(f, "r", encoding="utf-8") as py_file:
            code = py_file.read()
            compile(code, str(f), "exec")

