# ============================================================================
# BABYLON-60 v4.0 Sovereign Hardened
# █ KERNEL NATIVE MODULES SUITE | STATE: C5-REAL | AESTHETIC: INDUSTRIAL_NOIR_2026
# ============================================================================
"""
test_kernel_native_modules.py — Automated verification for native CDP, Kimi, and Sync modules.
"""

import io
import json
from unittest.mock import Mock

import pytest
from babylon60.kernel.browser_cdp_engine import BrowserEngine
from babylon60.kernel.kimi_client import KimiClient
from babylon60.kernel.quantum_sync import QuantumSyncEngine


def test_browser_cdp_engine_init() -> None:
    engine = BrowserEngine(headless=True, remote_debugging_port=9222)
    _binary = engine.find_chrome_binary()
    # Should evaluate without throwing exception
    assert engine.port == 9222
    assert engine.headless is True


def test_kimi_client_unconfigured_contract(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("KIMI_API_KEY", raising=False)
    monkeypatch.delenv("MOONSHOT_API_KEY", raising=False)
    transport = Mock(side_effect=AssertionError("Unconfigured clients must not make network requests"))
    monkeypatch.setattr("urllib.request.urlopen", transport)
    client = KimiClient(api_key=None)
    assert client.is_configured() is False
    res = client.query("Hello")
    assert res["success"] is False
    assert "remediation" in res
    transport.assert_not_called()


def test_kimi_client_configured_uses_intercepted_transport(monkeypatch: pytest.MonkeyPatch) -> None:
    response = {"choices": [{"message": {"content": "Isolated response"}}], "usage": {"total_tokens": 3}}
    transport = Mock(return_value=io.BytesIO(json.dumps(response).encode()))
    monkeypatch.setattr("urllib.request.urlopen", transport)
    client = KimiClient(api_key="audit-test-only-not-credential")

    assert client.is_configured() is True
    result = client.query("Hello")

    assert result["success"] is True
    assert result["content"] == "Isolated response"
    assert result["usage"] == {"total_tokens": 3}
    transport.assert_called_once()
    request = transport.call_args.args[0]
    assert request.full_url == f"{client.BASE_URL}/chat/completions"
    assert request.method == "POST"
    assert request.get_header("Authorization") == "Bearer audit-test-only-not-credential"
    assert json.loads(request.data)["messages"] == [{"role": "user", "content": "Hello"}]


def test_quantum_sync_engine_status() -> None:
    engine = QuantumSyncEngine()
    status = engine.check_vcs_status()
    assert "is_git" in status
    assert "is_jj" in status
    assert "jj_installed" in status
    assert "git_installed" in status


@pytest.mark.asyncio
async def test_async_browser_launch_check() -> None:
    engine = BrowserEngine(headless=True)
    # Binary test check stub
    assert engine.process is None
