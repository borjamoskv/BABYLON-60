"""
Unit and Integration Tests for BABYLON-60 C5-REAL Native Commands Module.
Vector: INV_C5_17 / INV_C5_21 / INV_C5_22
"""

import pytest

from babylon60.commands import (
    run_autodidact,
    run_ethos,
    run_itera,
    run_logos,
    run_mythos,
    run_purge,
    run_seal,
    run_ship,
    run_swarm,
    run_ultrathink,
    run_verify,
)


def test_logos_transduction():
    payload = run_logos("Test Operator Intent")
    assert "LOGOS_COLLAPSED_INVARIANT" in payload

def test_ethos_zk_mask():
    valid = run_ethos("CLAIM: VALID_INVARIANT")
    assert valid is True
    
    invalid = run_ethos("CLAIM: INVALID_FLOAT_12.5")
    assert invalid is False

def test_mythos_compression():
    run_mythos() # Should complete without exception

def test_verify_ledger():
    # Verify execution path
    result = run_verify()
    assert isinstance(result, bool)

def test_itera_loop():
    run_itera(steps=1) # Run single step iteration test

def test_purge_protocol():
    run_purge() # Execute kinetic purge test

def test_browser_diagnostics():
    from babylon60.commands.browser import run_browser
    # We test it against a lightweight internal payload or public mock
    res = run_browser("http://example.com", extract_dom=True)
    assert res["status"] == "success"
    assert res["bytes_extracted"] > 0
