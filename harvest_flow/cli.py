from __future__ import annotations

import sys
from pathlib import Path

from app import main as run_engine


def engine_main() -> None:
    run_engine()


def dashboard_main() -> None:
    import streamlit.web.cli as stcli

    dashboard_path = Path(__file__).resolve().parent.parent / "dashboard.py"
    passthrough_args = sys.argv[1:]
    sys.argv = ["streamlit", "run", str(dashboard_path), *passthrough_args]
    stcli.main()

