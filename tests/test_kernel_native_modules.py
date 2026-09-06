# ============================================================================
# BABYLON-60 v4.0 Sovereign Hardened
# █ KERNEL NATIVE MODULES SUITE | STATE: C5-REAL | AESTHETIC: INDUSTRIAL_NOIR_2026
# ============================================================================
"""
test_kernel_native_modules.py — Automated verification for native CDP, Kimi, and Sync modules.
"""

import pytest
from src.kernel.browser_cdp_engine import BrowserEngine
from src.kernel.kimi_client import KimiClient
from src.kernel.quantum_sync import QuantumSyncEngine

def test_browser_cdp_engine_init():
    engine = BrowserEngine(headless=True, remote_debugging_port=9222)
    binary = engine.find_chrome_binary()
    # Should evaluate without throwing exception
    assert engine.port == 9222
    assert engine.headless is True

def test_kimi_client_unconfigured_contract():
    client = KimiClient(api_key=None)
    assert client.is_configured() is False or client.api_key is not None
    res = client.query("Hello")
    if not client.is_configured():
        assert res["success"] is False
        assert "remediation" in res

def test_quantum_sync_engine_status():
    engine = QuantumSyncEngine()
    status = engine.check_vcs_status()
    assert "is_git" in status
    assert "is_jj" in status
    assert "jj_installed" in status
    assert "git_installed" in status

@pytest.mark.asyncio
async def test_async_browser_launch_check():
    engine = BrowserEngine(headless=True)
    # Binary test check stub
    assert engine.process is None
