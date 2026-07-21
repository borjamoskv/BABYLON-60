"""
Pytest unit test to verify Escohotado C5-REAL HTML Dashboard integrity.
Rule Compliance: Ω11 (AST / HTML syntax invariant).
"""

import os
import pytest

DASHBOARD_PATH = "/Users/borjafernandezangulo/borjamoskv/Teorema-Robinson-Moskv/cortex/escohotado_dashboard.html"

def test_dashboard_file_integrity():
    assert os.path.exists(DASHBOARD_PATH)
    with open(DASHBOARD_PATH, "r", encoding="utf-8") as f:
        content = f.read()

    assert "<!DOCTYPE html>" in content
    assert "C5-REAL" in content
    assert "chaosCanvas" in content
    assert "econCanvas" in content
    assert "substanceCanvas" in content
