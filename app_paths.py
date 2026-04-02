"""Central paths so CLI, Streamlit, and imports resolve data files consistently."""
from __future__ import annotations

import os

ROOT = os.path.dirname(os.path.abspath(__file__))


def data_path(filename: str) -> str:
    return os.path.join(ROOT, filename)
