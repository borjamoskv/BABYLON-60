"""Logical cleanup checks on temporary files; no generated code is executed."""

import os
from pathlib import Path
from unittest.mock import Mock

import pytest

from babylon60.kernel import mcp_lifecycle_manager as lifecycle
from babylon60.kernel.mcp_deductive_engine import McpCandidateContract
from babylon60.kernel.mcp_sandbox_validator import McpSandboxValidator


def _register(manager: lifecycle.McpLifecycleManager, path: Path, name: str, scope: str = "EPH_EPHEMERAL") -> None:
    candidate = McpCandidateContract(name, name, "Isolated cleanup check")
    result = manager.register_mcp(candidate, str(path), scope)
    assert result["status"] == "SUCCESS"


def _deny_unlink(monkeypatch: pytest.MonkeyPatch, path: Path) -> None:
    original = os.unlink

    def deny(target: str, *, dir_fd: int | None = None) -> None:
        if target == str(path):
            raise PermissionError("Isolated unlink refusal")
        original(target, dir_fd=dir_fd)

    monkeypatch.setattr(os, "unlink", deny)
    monkeypatch.setattr(os, "remove", deny)


def test_failed_detonation_preserves_source_and_registry(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    manager = lifecycle.McpLifecycleManager(str(tmp_path / "registry.db"))
    source = tmp_path / "reviewable.py"
    source.write_text("retained source")
    _register(manager, source, "failed")
    _deny_unlink(monkeypatch, source)
    assert manager.detonate_mcp("failed") is False
    assert source.read_text() == "retained source"
    assert [row["server_name"] for row in manager.list_active_mcps()] == ["failed"]


def test_partial_purge_retains_failed_and_permanent_entries(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    manager = lifecycle.McpLifecycleManager(str(tmp_path / "registry.db"))
    for name, scope in (("removed", "EPH_EPHEMERAL"), ("failed", "EPH_EPHEMERAL"), ("permanent", "PERM_SOVEREIGN")):
        source = tmp_path / f"{name}.py"
        source.write_text(name)
        _register(manager, source, name, scope)
    _deny_unlink(monkeypatch, tmp_path / "failed.py")
    assert manager.purge_ephemeral_mcps() == 1
    assert not (tmp_path / "removed.py").exists()
    assert (tmp_path / "failed.py").read_text() == "failed"
    assert (tmp_path / "permanent.py").read_text() == "permanent"
    assert {row["server_name"] for row in manager.list_active_mcps()} == {"failed", "permanent"}


def test_detonation_removes_a_dangling_symlink(tmp_path: Path) -> None:
    manager = lifecycle.McpLifecycleManager(str(tmp_path / "registry.db"))
    source = tmp_path / "dangling.py"
    source.symlink_to(tmp_path / "absent.py")
    _register(manager, source, "dangling")
    assert manager.detonate_mcp("dangling") is True
    assert not os.path.lexists(source)
    assert manager.list_active_mcps() == []


def test_unobservable_path_is_not_certified_as_absent(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    manager = lifecycle.McpLifecycleManager(str(tmp_path / "registry.db"))
    source = tmp_path / "unobservable.py"
    source.write_text("temporary source")
    _register(manager, source, "unobservable")
    original_lstat = os.lstat

    def denied_stat(path: str, *, dir_fd: int | None = None) -> os.stat_result:
        if os.fspath(path) == str(source):
            raise PermissionError("Isolated observation refusal")
        return original_lstat(path, dir_fd=dir_fd)

    monkeypatch.setattr(os, "lstat", denied_stat)
    assert manager.detonate_mcp("unobservable") is False
    assert [row["server_name"] for row in manager.list_active_mcps()] == ["unobservable"]


@pytest.mark.parametrize("fault", ["none", "unlink", "registry"])
def test_bomb_receipt_requires_both_cleanup_surfaces(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, fault: str
) -> None:
    manager = lifecycle.McpLifecycleManager(str(tmp_path / "registry.db"))
    source = tmp_path / "mcp_cleanupbridge_server.py"

    def isolated_execution(
        self: McpSandboxValidator,
        script_path: str,
        candidate: McpCandidateContract,
        call_arguments: dict[str, object],
        timeout_seconds: float = 5.0,
        detonate: bool = True,
    ) -> dict[str, object]:
        if fault == "registry":
            Path(script_path).unlink()
        return {"status": "SUCCESS", "is_valid": True}

    monkeypatch.setattr(McpSandboxValidator, "execute_and_detonate_mcp_sync", isolated_execution)
    if fault == "unlink":
        _deny_unlink(monkeypatch, source)
    elif fault == "registry":
        monkeypatch.setattr(manager, "detonate_mcp", lambda name: False)
    result = manager.synthesize_and_detonate_bomb("Cleanup", "return 1", {}, output_dir=str(tmp_path))
    if fault == "none":
        assert result["status"] == "SUCCESS"
        assert result["is_valid"] is True
        assert result["self_destruct_verified"] is True
        assert result["self_destruct_evidence"] == {"active_path_absent": True, "registry_purged": True}
        assert manager.list_active_mcps() == []
    else:
        assert result["status"] == "ERROR"
        assert result["is_valid"] is False
        assert result["error_code"] == "CLEANUP_FAILED"
        assert result["self_destruct_verified"] is False
        assert result["scope"] == "EPH_EPHEMERAL_PENDING"
        assert len(manager.list_active_mcps()) == 1
    assert source.exists() is (fault == "unlink")


def test_registration_failure_never_launches_generated_code(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    manager = lifecycle.McpLifecycleManager(str(tmp_path / "registry.db"))
    monkeypatch.setattr(manager, "register_mcp", lambda *args, **kwargs: {"status": "ERROR", "reason": "isolated"})
    execute = Mock(side_effect=AssertionError("Unregistered code must not execute"))
    monkeypatch.setattr(McpSandboxValidator, "execute_and_detonate_mcp_sync", execute)
    with pytest.raises(RuntimeError, match="registration failed"):
        manager.synthesize_and_detonate_bomb("Cleanup", "return 1", {}, output_dir=str(tmp_path))
    execute.assert_not_called()
    assert not (tmp_path / "mcp_cleanupbridge_server.py").exists()
