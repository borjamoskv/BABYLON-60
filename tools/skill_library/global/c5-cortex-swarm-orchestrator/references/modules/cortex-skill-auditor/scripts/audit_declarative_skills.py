#!/usr/bin/env python3
"""Portable entry point for the independent declarative checker."""
from pathlib import Path
import runpy
for parent in Path(__file__).absolute().parents:
    for relative in ["_skill_checks/declarative.py", "checks/declarative.py"]:
        checker = parent / relative
        if checker.is_file():
            runpy.run_path(str(checker), run_name="__main__")
            raise SystemExit(0)
raise SystemExit("Independent checker missing; regenerate the distribution")
