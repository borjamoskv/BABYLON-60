# C5-REAL EXERGY CERTIFIED
"""Unit test suite for detect_sim.py synthetic artifact detector."""

import json
import pytest
from pathlib import Path
from scripts.detect_sim import scan_text, analyze_hex


def test_detect_synthetic_hex_pattern():
    synthetic_hex = "f2a8b29c1d9e3a4b5c6d7e8f9a0b1c2d3e4f5a6b7c8d9e0f1a2b3c4d5e6f7a8b"
    analysis = analyze_hex(synthetic_hex)
    assert analysis["suspect"] is True
    assert "MONOTONIC_BYTES" in str(analysis["flags"]) or "NIBBLE_RUNS" in str(analysis["flags"])


def test_detect_sim_scan_text():
    text = """
    SHA256: f2a8b29c1d9e3a4b5c6d7e8f9a0b1c2d3e4f5a6b7c8d9e0f1a2b3c4d5e6f7a8b
    Commit: [master 4f2a1b9]
    Ran command: python3 test.py
    ATP SAVED: +85000
    """
    findings = scan_text(text)
    assert len(findings["synthetic_hashes"]) > 0
    assert len(findings["unbacked_claims"]) > 0
    assert len(findings["sourceless_metrics"]) > 0
