"""Execution denial requires an independent absence-of-effect witness."""

import asyncio
import json
import subprocess
import sys
from pathlib import Path
from unittest.mock import AsyncMock

import pytest

from babylon60.cortex import cortex_chaos_monad as chaos
from babylon60.cortex.cortex_chaos_monad import run_chaos_monad


@pytest.mark.asyncio
async def test_unconfined_option_cannot_start_a_process(monkeypatch: pytest.MonkeyPatch) -> None:
    spawn = AsyncMock(side_effect=AssertionError("Unconfined subprocess must never start"))
    monkeypatch.setattr(asyncio, "create_subprocess_exec", spawn)
    result = await run_chaos_monad("print('inert')", use_seatbelt=False)
    assert result["status"] == "SecurityError"
    assert result["stdout"] == ""
    assert result["scitt_receipt"] == {}
    spawn.assert_not_called()


@pytest.mark.asyncio
async def test_external_file_canary_is_unchanged(tmp_path: Path) -> None:
    outside_file = tmp_path / "outside-canary.txt"
    outside_file.write_text("UNCHANGED_AUDIT_CANARY\n")
    before = outside_file.read_bytes()
    source = f"import numpy as np\nnp.savetxt({str(outside_file)!r}, [6060])"
    result = await run_chaos_monad(source, timeout_ms=5000)
    assert outside_file.read_bytes() == before
    assert result["status"] in {"SecurityError", "RuntimeError"}
    assert result["scitt_receipt"] == {}


@pytest.mark.asyncio
async def test_unavailable_backend_returns_explicit_denial_without_receipt(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(chaos.sys, "platform", "unsupported")
    result = await run_chaos_monad("print('inert')")
    assert result["status"] == "SecurityError"
    assert "confinement backend" in result["error"]
    assert result["stdout"] == ""
    assert result["scitt_receipt"] == {}


@pytest.mark.asyncio
async def test_missing_backend_denies_before_process_start(monkeypatch: pytest.MonkeyPatch) -> None:
    spawn = AsyncMock(side_effect=AssertionError("No fallback process may start"))
    monkeypatch.setattr(asyncio, "create_subprocess_exec", spawn)
    monkeypatch.setattr(chaos.os, "access", lambda *args: False)
    result = await run_chaos_monad("print('inert')")
    assert result["status"] == "SecurityError"
    assert result["scitt_receipt"] == {}
    spawn.assert_not_called()


@pytest.mark.asyncio
async def test_unverified_python_installation_denies_before_process_start(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    spawn = AsyncMock(side_effect=AssertionError("No fallback process may start"))
    monkeypatch.setattr(asyncio, "create_subprocess_exec", spawn)
    monkeypatch.setattr(chaos.sys, "platform", "darwin")
    monkeypatch.setattr(chaos.sys, "base_prefix", str(tmp_path))
    result = await run_chaos_monad("print('inert')")
    assert result["status"] == "SecurityError"
    assert "confinement" in result["error"]
    spawn.assert_not_called()


@pytest.mark.asyncio
@pytest.mark.skipif(sys.platform != "darwin", reason="Read-only execution provider supports Darwin only")
@pytest.mark.parametrize("source, expected", [
    ("print(60 * 60)", "3600"),
    ("import numpy as np\nprint(np.sum([1, 2, 3]))", "6"),
])
async def test_supported_backend_executes_without_claiming_attestation(source: str, expected: str) -> None:
    result = await run_chaos_monad(source, timeout_ms=5000)
    assert result["status"] == "Success", result
    assert result["stdout"].strip() == expected
    assert result["scitt_receipt"] == {}


@pytest.mark.skipif(sys.platform != "darwin", reason="Read-only execution provider supports Darwin only")
def test_os_provider_denies_host_data_network_and_fork(tmp_path: Path) -> None:
    """Trusted probe tests the actual OS policy independently of the AST filter."""
    canary = tmp_path / "private-canary.txt"
    canary.write_text("UNCHANGED")
    alias = Path("/System/Volumes/Data") / str(canary).lstrip("/")
    source = f"""
import json, os, socket
results = {{}}
for label, path, mode in [
    ('read', {str(canary)!r}, 'r'), ('write', {str(canary)!r}, 'w'),
    ('alias_read', {str(alias)!r}, 'r')
]:
    try:
        with open(path, mode) as handle:
            if mode == 'w':
                handle.write('CHANGED')
        results[label] = 'ALLOWED'
    except PermissionError:
        results[label] = 'DENIED'
try:
    sock = socket.socket()
    sock.settimeout(0.25)
    sock.connect(('127.0.0.1', 9))
    results['connect'] = 'ALLOWED'
except PermissionError:
    results['connect'] = 'DENIED'
finally:
    sock.close()
try:
    pid = os.fork()
    if pid == 0:
        os._exit(0)
    os.waitpid(pid, 0)
    results['fork'] = 'ALLOWED'
except PermissionError:
    results['fork'] = 'DENIED'
print(json.dumps(results))
"""
    command = chaos._sandbox_command()
    command[-1] = source
    result = subprocess.run(command, cwd="/", env={}, capture_output=True, text=True, timeout=10, check=False)
    assert canary.read_text() == "UNCHANGED"
    assert result.returncode == 0, result.stderr
    assert json.loads(result.stdout) == dict.fromkeys(["read", "write", "alias_read", "connect", "fork"], "DENIED")
