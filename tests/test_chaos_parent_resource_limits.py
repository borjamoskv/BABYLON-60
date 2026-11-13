"""Bound worker-controlled bytes in the parent, outside the native-code worker.

These are real Darwin-provider regressions. A returned status remains a worker
observation and never serves as authorization or cryptographic attestation.
"""

import asyncio
import os
import sys

import pytest

from babylon60.cortex import cortex_chaos_monad as chaos


pytestmark = pytest.mark.skipif(sys.platform != "darwin", reason="Actual read-only provider supports Darwin only")
MIB = 1024 * 1024


@pytest.fixture
def real_processes(monkeypatch: pytest.MonkeyPatch) -> list[asyncio.subprocess.Process]:
    original = asyncio.create_subprocess_exec
    observed: list[asyncio.subprocess.Process] = []

    async def record(*args, **kwargs):
        process = await original(*args, **kwargs)
        observed.append(process)
        return process

    monkeypatch.setattr(asyncio, "create_subprocess_exec", record)
    return observed


def assert_reaped(processes: list[asyncio.subprocess.Process]) -> None:
    assert len(processes) == 1
    process = processes[0]
    assert process.returncode is not None
    with pytest.raises(ProcessLookupError):
        os.kill(process.pid, 0)


def assert_output_rejected(result: chaos.ScittResult) -> None:
    assert result["status"] == "RuntimeError"
    assert result["stdout"] == ""
    assert result["error"] == "Execution output exceeded parent byte budget"
    assert result["scitt_receipt"] == {}


def native_write_source(payload_expression: str, fd: int = 1, *, spin: bool = False) -> str:
    ending = "while True: pass" if spin else "lib.exit(0)"
    return (
        "import numpy as np\n"
        "lib = np.ctypeslib.ctypes.CDLL(None)\n"
        f"payload = {payload_expression}\n"
        f"lib.write({fd}, payload, len(payload))\n"
        f"{ending}\n"
    )


@pytest.mark.asyncio
@pytest.mark.parametrize("fd", [1, 2])
async def test_parent_stops_native_stream_overflow_and_reaps(
    real_processes: list[asyncio.subprocess.Process], fd: int
) -> None:
    source = native_write_source(f"b'X' * ({2 * MIB} + 1)", fd, spin=True)
    result = await asyncio.wait_for(chaos.run_chaos_monad(source, timeout_ms=5000), timeout=8)
    assert_output_rejected(result)
    assert_reaped(real_processes)


@pytest.mark.asyncio
async def test_both_native_streams_are_drained_with_a_budget(
    real_processes: list[asyncio.subprocess.Process],
) -> None:
    source = """import numpy as np
lib = np.ctypeslib.ctypes.CDLL(None)
block = b'X' * 4096
for i in range(600):
    lib.write(1, block, len(block))
    lib.write(2, block, len(block))
while True: pass
"""
    result = await asyncio.wait_for(chaos.run_chaos_monad(source, timeout_ms=5000), timeout=8)
    assert_output_rejected(result)
    assert_reaped(real_processes)


@pytest.mark.asyncio
@pytest.mark.parametrize("field", ["stdout", "error"])
@pytest.mark.parametrize("text_expression", [f"b'B' * ({MIB} + 1)", f"('é' * ({MIB // 2} + 1)).encode('utf-8')"])
async def test_decoded_text_is_bounded_by_utf8_bytes(
    real_processes: list[asyncio.subprocess.Process], field: str, text_expression: str
) -> None:
    if field == "stdout":
        prefix = b'{"status":"Success","stdout":"'
        suffix = b'","error":""}'
    else:
        prefix = b'{"status":"RuntimeError","stdout":"","error":"'
        suffix = b'"}'
    # The raw envelope remains below 2 MiB; each decoded field exceeds 1 MiB.
    source = native_write_source(f"{prefix!r} + {text_expression} + {suffix!r}")
    result = await chaos.run_chaos_monad(source, timeout_ms=5000)
    assert_output_rejected(result)
    assert_reaped(real_processes)


@pytest.mark.asyncio
async def test_oversized_exception_is_not_returned_to_parent_callers(
    real_processes: list[asyncio.subprocess.Process],
) -> None:
    result = await chaos.run_chaos_monad(f"assert False, 'E' * {2 * MIB}", timeout_ms=5000)
    assert_output_rejected(result)
    assert_reaped(real_processes)


@pytest.mark.asyncio
@pytest.mark.parametrize("payload", [
    b'{"status":"Success","stdout":"","error":"","authority":true}',
    b'{"status":"Success","stdout":""}',
    b'{"status":"AUTHORIZED","stdout":"","error":""}',
    b'{"status":"Success","stdout":123,"error":""}',
    b'{"status":"Success","stdout":"","error":"\\ud800"}',
    b'{"status":"Success","stdout":"","error":"contradictory worker status"}',
    b'{"status":"Success","stdout":' + b'[' * 1500 + b'0' + b']' * 1500 + b',"error":""}',
    b'\xff',
])
async def test_invalid_worker_schema_is_rejected(
    real_processes: list[asyncio.subprocess.Process], payload: bytes
) -> None:
    result = await chaos.run_chaos_monad(native_write_source(repr(payload)), timeout_ms=5000)
    assert result["status"] == "RuntimeError"
    assert result["stdout"] == ""
    assert result["error"] == "Invalid OS-confined execution response"
    assert result["scitt_receipt"] == {}
    assert_reaped(real_processes)


@pytest.mark.asyncio
async def test_exact_text_budget_is_returned_as_an_untrusted_observation(
    real_processes: list[asyncio.subprocess.Process],
) -> None:
    prefix = b'{"status":"Success","stdout":"'
    suffix = b'","error":""}'
    source = native_write_source(f"{prefix!r} + b'B' * {MIB} + {suffix!r}")
    result = await chaos.run_chaos_monad(source, timeout_ms=5000)
    assert result["status"] == "Success"
    assert len(result["stdout"].encode("utf-8")) == MIB
    assert result["error"] == ""
    assert result["scitt_receipt"] == {}
    assert_reaped(real_processes)


@pytest.mark.asyncio
async def test_timeout_reaps_the_actual_worker(real_processes: list[asyncio.subprocess.Process]) -> None:
    result = await chaos.run_chaos_monad("while True: pass", timeout_ms=100)
    assert result["status"] == "Timeout_Entropy_Death"
    assert result["stdout"] == ""
    assert result["scitt_receipt"] == {}
    assert_reaped(real_processes)


@pytest.mark.asyncio
async def test_cancellation_reaps_the_actual_worker(real_processes: list[asyncio.subprocess.Process]) -> None:
    task = asyncio.create_task(chaos.run_chaos_monad("while True: pass", timeout_ms=5000))

    async def wait_for_spawn() -> None:
        while not real_processes:
            assert not task.done(), "The real confinement provider did not start"
            await asyncio.sleep(0.01)

    try:
        await asyncio.wait_for(wait_for_spawn(), timeout=5)
        task.cancel()
        with pytest.raises(asyncio.CancelledError):
            await asyncio.wait_for(task, timeout=5)
    finally:
        if not task.done():
            task.cancel()
            await asyncio.gather(task, return_exceptions=True)
    assert_reaped(real_processes)
