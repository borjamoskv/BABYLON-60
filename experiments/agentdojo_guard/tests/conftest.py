"""Test configuration exposing ``src/b60_guard`` without altering pyproject.toml."""

from __future__ import annotations

import sys
from pathlib import Path

SRC_DIR = Path(__file__).absolute().parents[1] / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))
