"""Dynamic execution without verified OS confinement must never claim attestation."""

import pytest

from babylon60.cortex import cortex_chaos_monad
from babylon60.cortex.cortex_chaos_monad import run_chaos_monad


@pytest.mark.asyncio
async def test_attestation_explicitly_rejects_unavailable_confinement(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(cortex_chaos_monad.sys, "platform", "unsupported")
    result = await run_chaos_monad(
        source_code="print('must not execute')",
        frontier_tick="test-no-confinement",
        timeout_ms=500,
    )
    assert result["status"] == "SecurityError"
    assert "confinement" in result["error"].lower()
    assert result["stdout"] == ""
    assert result["scitt_receipt"] == {}


@pytest.mark.asyncio
@pytest.mark.parametrize("source", ["import os", "open('state', 'w')", "def broken("])
async def test_attestation_rejects_invalid_source_without_a_receipt(source: str) -> None:
    result = await run_chaos_monad(source_code=source, frontier_tick="test-invalid-source")
    assert result["status"] == "SecurityError"
    assert result["error"]
    assert result["stdout"] == ""
    assert result["scitt_receipt"] == {}
