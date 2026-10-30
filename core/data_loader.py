"""Data loader utilities for Q-Pack.

Loads and validates YAML and CSV data into frozen Pydantic schemas.
"""

from functools import lru_cache
from pathlib import Path
from typing import Dict, Any
import yaml
import pandas as pd

from core.schemas import Cell, Requirement


DATA_DIR = Path(__file__).resolve().parent.parent / "data"


@lru_cache(maxsize=1)
def load_cells(yaml_path: str = str(DATA_DIR / "cells.yaml")) -> Dict[str, Cell]:
    """Load cell library from YAML into a dictionary of Cell models."""
    with open(yaml_path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)

    cells = {}
    for entry in data.get("cells", []):
        cell = Cell(**entry)
        cells[cell.id] = cell
    return cells


@lru_cache(maxsize=1)
def load_requirements(yaml_path: str = str(DATA_DIR / "requirements.yaml")) -> Dict[str, Requirement]:
    """Load engineering requirements from YAML."""
    with open(yaml_path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)

    reqs = {}
    for entry in data.get("requirements", []):
        req = Requirement(**entry)
        reqs[req.id] = req
    return reqs


@lru_cache(maxsize=1)
def load_components(yaml_path: str = str(DATA_DIR / "components.yaml")) -> Dict[str, Any]:
    """Load BMS, cooling, and mechanical hardware specifications."""
    with open(yaml_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


@lru_cache(maxsize=1)
def load_drive_cycle(csv_path: str = str(DATA_DIR / "drive_cycle_urban.csv")) -> pd.DataFrame:
    """Load reference urban drive cycle power profile."""
    df = pd.read_csv(csv_path)
    return df

