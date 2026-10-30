"""PackForge Streamlit Web Application Package."""

import sys
from pathlib import Path

# Ensure project root is always in sys.path
_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

