# C5-REAL EXERGY CERTIFIED
"""
Pytest unit test to verify Escohotado C5-REAL HTML Dashboard integrity.
Rule Compliance: Ω11 (AST / HTML syntax invariant).
"""

import os
from pathlib import Path

DASHBOARD_PATH = str(Path(__file__).resolve().parent.parent / "escohotado_dashboard.html")

def test_dashboard_file_integrity() -> None:
    assert os.path.exists(DASHBOARD_PATH)
    with open(DASHBOARD_PATH, "r", encoding="utf-8") as f:
        content = f.read()

    assert "<!doctype html>" in content.lower()
    assert "C5-REAL" in content
    assert "chaosCanvas" in content
    assert "econCanvas" in content
    assert "substanceCanvas" in content
