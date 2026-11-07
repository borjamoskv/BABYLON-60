"""Generated code must never run while OS confinement is unavailable."""

import asyncio
import subprocess
import sys
from pathlib import Path
from unittest.mock import Mock

import pytest

from babylon60.kernel import mcp_sandbox_validator as sandbox
from babylon60.kernel.mcp_deductive_engine import McpCandidateContract
from babylon60.kernel.mcp_sandbox_validator import McpSandboxValidator
from babylon60.kernel.mcp_scaffolder import McpCodeScaffolder


@pytest.mark.parametrize("entry", ["validate", "execute", "sync", "sync_in_loop"])
@pytest.mark.parametrize("artifact", ["file", "missing", "symlink"])
def test_denial_never_launches_or_deletes(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, entry: str, artifact: str
) -> None:
    def unavailable() -> tuple[str, str]:
        raise RuntimeError("Backend unavailable for this unit test")

    monkeypatch.setattr(sandbox, "_runtime", unavailable)
    launch = Mock(side_effect=AssertionError("Generated code must not start"))
    monkeypatch.setattr(asyncio, "create_subprocess_exec", launch)
    monkeypatch.setattr(asyncio, "create_subprocess_shell", launch)
    monkeypatch.setattr(subprocess, "Popen", launch)
    # Neither configuration claims nor benign-looking source enable execution.
    monkeypatch.setenv("BABYLON_MCP_SANDBOX_VERIFIED", "1")
    target = tmp_path / "reviewable.py"
    target.write_text("raise RuntimeError('must never execute')\n")
    script = target
    if artifact == "missing":
        script = tmp_path / "absent.py"
    elif artifact == "symlink":
        script = tmp_path / "link.py"
        script.symlink_to(target)
    candidate = McpCandidateContract("probe", "probe", "Confinement regression")
    validator = McpSandboxValidator()
    if entry == "validate":
        result = asyncio.run(validator.validate_mcp_server(str(script), candidate))
    elif entry == "execute":
        result = asyncio.run(validator.execute_and_detonate_mcp(str(script), candidate, {}))
    elif entry == "sync":
        result = validator.execute_and_detonate_mcp_sync(str(script), candidate, {})
    else:

        async def invoke() -> dict[str, object]:
            return validator.execute_and_detonate_mcp_sync(str(script), candidate, {})

        result = asyncio.run(invoke())
    assert result["status"] == "ERROR"
    assert result["is_valid"] is False
    assert result["error_code"] == "OS_ISOLATION_UNAVAILABLE"
    assert "tool_output" not in result
    launch.assert_not_called()
    assert target.read_text() == "raise RuntimeError('must never execute')\n"
    if artifact == "symlink":
        assert script.is_symlink()
    elif artifact == "missing":
        assert not script.exists()


def test_ast_acceptance_does_not_authorize_execution() -> None:
    # Validate source only: this body is never evaluated or materialized as a script.
    body = "from pathlib import Path\nreturn Path('/not-accessed').read_text()"
    McpCodeScaffolder.validate_implementation_ast(body)
    candidate = McpCandidateContract("probe", "probe", "AST is not confinement", implementation_body=body)
    result = McpSandboxValidator().execute_and_detonate_mcp_sync("/not-opened.py", candidate, {})
    assert result["is_valid"] is False
    assert result["error_code"] == "OS_ISOLATION_UNAVAILABLE"


def test_unsupported_os_cannot_enable_backend(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(sys, "platform", "linux")
    monkeypatch.setenv("BABYLON_MCP_SANDBOX_VERIFIED", "1")
    result = McpSandboxValidator().execute_and_detonate_mcp_sync(
        "/not-opened.py", McpCandidateContract("p", "p", "p"), {}
    )
    assert result["error_code"] == "OS_ISOLATION_UNAVAILABLE"
    assert "macOS Seatbelt is required" in str(result["reason"])
