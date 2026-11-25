"""Real macOS OS-boundary checks using only private temporary artifacts."""

import asyncio
import sys
from pathlib import Path

from blake3 import blake3
import pytest

from babylon60.kernel.mcp_deductive_engine import McpCandidateContract
from babylon60.kernel.mcp_sandbox_validator import McpSandboxValidator
from babylon60.kernel.mcp_scaffolder import McpCodeScaffolder

pytestmark = pytest.mark.skipif(sys.platform != "darwin", reason="Real Seatbelt backend requires macOS")


def test_real_protocol_and_confinement_evidence(tmp_path: Path) -> None:
    contract = McpCandidateContract("probe", "probe", "Arithmetic", implementation_body="return 2 + 2")
    script = McpCodeScaffolder(str(tmp_path)).scaffold_fastmcp_python(contract)
    result = McpSandboxValidator().execute_and_detonate_mcp_sync(script, contract, {})
    assert result["is_valid"] is True, result
    output = result["tool_output"]
    assert isinstance(output, dict) and output["result"] == 4
    assert result["code_hash"] == blake3(Path(script).read_bytes()).hexdigest()
    evidence = result["isolation_evidence"]
    assert isinstance(evidence, dict) and all(evidence.values())
    assert result["isolation_backend"] == "macos-seatbelt"
    assert Path(script).exists()  # Executor owns only its private copy.


def test_ast_bypass_cannot_read_external_file(tmp_path: Path) -> None:
    canary = tmp_path / "secret"
    canary.write_text("private-canary")
    body = f"from pathlib import Path\nreturn Path({str(canary)!r}).read_text()"
    contract = McpCandidateContract("probe", "probe", "Denied read", implementation_body=body)
    script = McpCodeScaffolder(str(tmp_path)).scaffold_fastmcp_python(contract)
    result = McpSandboxValidator().execute_and_detonate_mcp_sync(script, contract, {})
    assert result["is_valid"] is False
    assert result["error_code"] == "TOOL_ERROR", result
    assert canary.read_text() == "private-canary"
    assert "private-canary" not in str(result)


@pytest.mark.parametrize("source", ["while True: pass", "import os\nwhile True: os.write(1, b'x' * 65536)"])
def test_timeout_and_output_limits(tmp_path: Path, source: str) -> None:
    script = tmp_path / "limits.py"
    script.write_text(source)
    contract = McpCandidateContract("probe", "probe", "Bounded resources")
    result = McpSandboxValidator().execute_and_detonate_mcp_sync(str(script), contract, {}, timeout_seconds=1)
    assert result["is_valid"] is False
    assert result["error_code"] in ("TIMEOUT", "EXECUTION_FAILED", "OS_ISOLATION_UNAVAILABLE"), result
    if "os.write" in source:
        assert "output exceeds" in str(result["reason"])


def test_source_symlink_rejected(tmp_path: Path) -> None:
    target = tmp_path / "source.py"
    target.write_text("raise AssertionError('must not run')")
    link = tmp_path / "link.py"
    link.symlink_to(target)
    result = McpSandboxValidator().execute_and_detonate_mcp_sync(str(link), McpCandidateContract("p", "p", "p"), {})
    assert result["is_valid"] is False
    assert link.is_symlink()


def test_sync_api_inside_active_loop(tmp_path: Path) -> None:
    contract = McpCandidateContract("probe", "probe", "loop", implementation_body="return 7")
    script = McpCodeScaffolder(str(tmp_path)).scaffold_fastmcp_python(contract)

    async def invoke() -> dict[str, object]:
        return McpSandboxValidator().execute_and_detonate_mcp_sync(script, contract, {})

    result = asyncio.run(invoke())
    assert result["is_valid"] is True, result
    output = result["tool_output"]
    assert isinstance(output, dict) and output["result"] == 7


def test_scaffolder_rejects_path_escape(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="basename"):
        McpCodeScaffolder(str(tmp_path)).scaffold_fastmcp_python(McpCandidateContract("p", "p", "p"), "../escape.py")


def test_failed_probe_never_dispatches_candidate(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    from babylon60.kernel import mcp_sandbox_validator as backend

    calls: list[str] = []

    async def failed_probe(script: Path, *args: object, **kwargs: object) -> tuple[int, bytes, bytes]:
        calls.append(script.name)
        return 1, b"{}", b"sandbox policy rejected"

    monkeypatch.setattr(backend, "_run_confined", failed_probe)
    script = tmp_path / "source.py"
    script.write_text("raise AssertionError('candidate must not run')")
    result = McpSandboxValidator().execute_and_detonate_mcp_sync(str(script), McpCandidateContract("p", "p", "p"), {})
    assert result["is_valid"] is False
    assert calls == ["probe.py"]


def test_original_replacement_does_not_change_pinned_execution(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    from babylon60.kernel import mcp_sandbox_validator as backend

    contract = McpCandidateContract("probe", "probe", "Pinned copy", implementation_body="return 4")
    script = Path(McpCodeScaffolder(str(tmp_path)).scaffold_fastmcp_python(contract))
    expected_hash = blake3(script.read_bytes()).hexdigest()
    original_run = backend._run_confined

    async def replace_after_probe(
        source: Path, executable: str, profile: str, work: Path, timeout: float, stdin: bytes = b""
    ) -> tuple[int, bytes, bytes]:
        outcome = await original_run(source, executable, profile, work, timeout, stdin)
        script.write_text("raise AssertionError('replacement must not run')")
        return outcome

    monkeypatch.setattr(backend, "_run_confined", replace_after_probe)
    result = McpSandboxValidator().execute_and_detonate_mcp_sync(str(script), contract, {})
    assert result["is_valid"] is True, result
    output = result["tool_output"]
    assert isinstance(output, dict) and output["result"] == 4
    assert result["code_hash"] == expected_hash
