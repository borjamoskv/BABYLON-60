"""Trusted subprocess fixtures test supervision; these do not attest OS confinement."""

from __future__ import annotations

import asyncio
import contextlib
import os
import signal
import subprocess
import sys

import pytest

from babylon60.kernel import mcp_sandbox_validator as backend

REAL_CREATE_SUBPROCESS_EXEC = asyncio.create_subprocess_exec

@pytest.mark.asyncio
async def test_oversized_input_is_rejected_before_process_creation(tmp_path, monkeypatch):
    async def forbidden(*_args, **_kwargs):
        raise AssertionError("process launched before input bound was checked")

    monkeypatch.setattr(backend.asyncio, "create_subprocess_exec", forbidden)
    with pytest.raises(ValueError, match="input"):
        await backend._run_confined(tmp_path / "unused", sys.executable, "unused", tmp_path, 1,
                                    b"x" * (backend.MAX_BYTES + 1))


def fixture_launcher(monkeypatch, source: str):
    """Run a fixed trusted fixture with production pipe/session options."""
    processes = []

    async def launch(*_args, **kwargs):
        process = await REAL_CREATE_SUBPROCESS_EXEC(sys.executable, "-I", "-c", source, **kwargs)
        processes.append(process)
        return process

    monkeypatch.setattr(backend.asyncio, "create_subprocess_exec", launch)
    monkeypatch.setattr(backend, "_resident_bytes", lambda _pid: 0)
    return processes


def running(pid: int) -> bool:
    """A zombie is stopped, although its parent/init may not have reaped it yet."""
    result = subprocess.run(["/bin/ps", "-p", str(pid), "-o", "stat="], capture_output=True, text=True)
    return result.returncode == 0 and bool(result.stdout.strip()) and not result.stdout.strip().startswith("Z")


@pytest.mark.asyncio
async def test_successful_leader_exit_still_terminates_descendant_group(tmp_path, monkeypatch):
    marker = tmp_path / "survived"
    child = f"import time; from pathlib import Path; time.sleep(1); Path({str(marker)!r}).write_text('escaped'); time.sleep(20)"
    source = (
        "import subprocess,sys\n"
        f"p=subprocess.Popen([sys.executable,'-I','-c',{child!r}],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)\n"
        "print(p.pid,flush=True)\n"
    )
    processes = fixture_launcher(monkeypatch, source)
    descendant = None
    try:
        rc, out, _ = await backend._run_confined(tmp_path / "unused", sys.executable, "unused", tmp_path, 3)
        assert rc == 0
        descendant = int(out.strip())
        for _ in range(50):
            if not running(descendant):
                break
            await asyncio.sleep(0.01)
        assert not running(descendant), "descendant remained alive after successful leader exit"
        assert not marker.exists()
        assert processes[0].returncode == 0
    finally:
        for process in processes:
            with contextlib.suppress(ProcessLookupError):
                os.killpg(process.pid, signal.SIGKILL)
        if descendant is not None:
            with contextlib.suppress(ProcessLookupError):
                os.kill(descendant, signal.SIGKILL)


@pytest.mark.asyncio
@pytest.mark.parametrize("stream", [1, 2])
async def test_parent_enforces_output_budget_and_reaps_process(tmp_path, monkeypatch, stream):
    processes = fixture_launcher(monkeypatch, f"import os,time; os.write({stream},b'x'*2000000); time.sleep(20)")
    with pytest.raises(ValueError, match="output"):
        await backend._run_confined(tmp_path / "unused", sys.executable, "unused", tmp_path, 3,
                                    max_output_bytes=4096)
    assert processes[0].returncode is not None
    assert not running(processes[0].pid)


@pytest.mark.asyncio
@pytest.mark.parametrize("budget,value", [
    ("max_input_bytes", 0), ("max_input_bytes", True),
    ("max_output_bytes", 0), ("max_output_bytes", 8 * 1024 * 1024 + 1),
    ("max_memory_bytes", 1), ("max_memory_bytes", 1024 * 1024 * 1024 + 1),
])
async def test_invalid_budgets_rejected_before_launch(tmp_path, monkeypatch, budget, value):
    async def forbidden(*_args, **_kwargs):
        raise AssertionError("process launched with invalid budgets")

    monkeypatch.setattr(backend.asyncio, "create_subprocess_exec", forbidden)
    with pytest.raises(ValueError):
        await backend._run_confined(tmp_path / "unused", sys.executable, "unused", tmp_path, 1,
                                    **{budget: value})


@pytest.mark.asyncio
@pytest.mark.parametrize("timeout", [0, -1, float("nan"), float("inf"), True, 31])
async def test_invalid_timeout_rejected_before_launch(tmp_path, monkeypatch, timeout):
    async def forbidden(*_args, **_kwargs):
        raise AssertionError("process launched with invalid timeout")

    monkeypatch.setattr(backend.asyncio, "create_subprocess_exec", forbidden)
    with pytest.raises(ValueError):
        await backend._run_confined(tmp_path / "unused", sys.executable, "unused", tmp_path, timeout)


@pytest.mark.asyncio
async def test_repeated_cancellation_waits_for_cleanup(tmp_path, monkeypatch):
    processes = fixture_launcher(monkeypatch, "import time; time.sleep(20)")
    task = asyncio.create_task(backend._run_confined(tmp_path / "unused", sys.executable, "unused", tmp_path, 3))
    while not processes:
        await asyncio.sleep(0.001)
    task.cancel()
    await asyncio.sleep(0)
    task.cancel()
    with pytest.raises(asyncio.CancelledError):
        await task
    assert processes[0].returncode is not None
    assert not running(processes[0].pid)


@pytest.mark.asyncio
async def test_memory_cutoff_and_timeout_reap_child(tmp_path, monkeypatch):
    for over_memory in (True, False):
        processes = fixture_launcher(monkeypatch, "import time; time.sleep(20)")
        monkeypatch.setattr(backend, "_resident_bytes", lambda _pid: 64 * 1024 * 1024 if over_memory else 0)
        error = ValueError if over_memory else asyncio.TimeoutError
        with pytest.raises(error):
            await backend._run_confined(tmp_path / "unused", sys.executable, "unused", tmp_path, 0.1,
                                        max_memory_bytes=32 * 1024 * 1024)
        assert processes[0].returncode is not None
        assert not running(processes[0].pid)
