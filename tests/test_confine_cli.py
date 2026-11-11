"""``babylon60 run | demo | log`` through the real argument parser."""

from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import sys

import pytest

from babylon60.confine.cli import _strip_separator, executable_grants
from babylon60.confine.launcher import landlock_abi
from babylon60.confine.policy import MIN_LANDLOCK_ABI

ROOT = Path(__file__).absolute().parents[1]
BACKEND = (sys.platform.startswith("linux") and landlock_abi() >= MIN_LANDLOCK_ABI) or sys.platform == "darwin"
needs_backend = pytest.mark.skipif(
    not BACKEND and os.environ.get("BABYLON60_REQUIRE_LANDLOCK") != "1", reason="no confinement backend on this machine"
)


@pytest.fixture
def sandbox(tmp_path: Path) -> dict[str, Path]:
    home = tmp_path / "home"
    (home / ".ssh").mkdir(parents=True)
    (home / ".ssh" / "id_rsa").write_text("B60-CANARY-cli\n")
    (home / "notes.txt").write_text("private\n")
    ws = tmp_path / "ws"
    ws.mkdir()
    (ws / "README.md").write_text("project\n")
    return {"home": home, "ws": ws, "journal": tmp_path / "state" / "journal.db"}


def _cli(sandbox: dict[str, Path], *args: str) -> subprocess.CompletedProcess[str]:
    env = {**os.environ, "HOME": str(sandbox["home"]), "PYTHONPATH": str(ROOT / "01_KISH_ENGINE")}
    return subprocess.run(
        [sys.executable, "-m", "babylon60.cli.main_dispatcher", *args],
        env=env,
        cwd=str(sandbox["ws"]),
        capture_output=True,
        text=True,
        timeout=300,
    )


def _run(sandbox: dict[str, Path], *command: str, options: tuple[str, ...] = ()) -> subprocess.CompletedProcess[str]:
    return _cli(sandbox, "run", "--allow-root", "--journal", str(sandbox["journal"]), *options, "--", *command)


def test_separator_is_stripped_exactly_once() -> None:
    assert _strip_separator(["--", "cat", "x"]) == ["cat", "x"]
    assert _strip_separator(["cat", "--", "x"]) == ["cat", "--", "x"]
    assert _strip_separator(["--", "--", "x"]) == ["--", "x"]
    assert _strip_separator([]) == []


def test_executable_under_home_is_granted_as_one_file(tmp_path: Path) -> None:
    home = tmp_path / "home"
    tool = home / ".tools" / "agent" / "bin" / "agent"
    tool.parent.mkdir(parents=True)
    tool.write_text("#!/bin/sh\n")
    assert executable_grants(str(tool), (str(home),)) == [str(tool)]
    assert executable_grants("/bin/sh", (str(home),)) == []


def test_missing_command_is_a_usage_error(sandbox: dict[str, Path]) -> None:
    result = _cli(sandbox, "run", "--allow-root", "--journal", str(sandbox["journal"]))
    assert result.returncode == 2 and "missing command" in result.stderr


@pytest.mark.skipif(os.geteuid() != 0, reason="root-only refusal path")
def test_root_is_refused_without_explicit_flag(sandbox: dict[str, Path]) -> None:
    result = _cli(sandbox, "run", "--", "true")
    assert result.returncode == 3 and "--allow-root" in result.stderr


@needs_backend
def test_unknown_command_is_127(sandbox: dict[str, Path]) -> None:
    assert _run(sandbox, "babylon60-no-such-command").returncode == 127


@needs_backend
def test_protected_grant_is_refused(sandbox: dict[str, Path]) -> None:
    result = _run(sandbox, "true", options=("--allow-read", str(sandbox["home"] / ".ssh")))
    assert result.returncode == 3 and "protected path" in result.stderr


@needs_backend
def test_home_is_denied_and_workspace_is_readable(sandbox: dict[str, Path]) -> None:
    denied = _run(sandbox, "cat", str(sandbox["home"] / "notes.txt"))
    assert denied.returncode != 0 and denied.stdout == ""
    allowed = _run(sandbox, "cat", "README.md")
    assert allowed.returncode == 0 and allowed.stdout == "project\n"
    log = _cli(sandbox, "log", "--journal", str(sandbox["journal"]), "--json")
    payload = json.loads(log.stdout)
    assert payload["verified"] and [e["kind"] for e in payload["entries"]] == ["run_start", "run_end"] * 2


@needs_backend
def test_hook_changes_are_reported_and_journaled(sandbox: dict[str, Path]) -> None:
    result = _run(sandbox, "sh", "-c", "echo '{}' > .mcp.json")
    assert result.returncode == 0
    assert "outside the sandbox later: .mcp.json" in result.stderr
    log = json.loads(_cli(sandbox, "log", "--journal", str(sandbox["journal"]), "--json").stdout)
    assert log["entries"][-1]["body"]["hooks_changed"] == [".mcp.json"]


@needs_backend
def test_demo_writes_evidence_and_log_verifies(sandbox: dict[str, Path], tmp_path: Path) -> None:
    evidence = tmp_path / "evidence.json"
    result = _cli(sandbox, "demo", "--journal", str(sandbox["journal"]), "--json", str(evidence))
    assert result.returncode == 0, result.stdout + result.stderr
    assert "verdict: BLOCKED" in result.stdout
    document = json.loads(evidence.read_text())
    assert document["schema"] == "babylon60.confine.demo/v1" and document["verdict"] == "BLOCKED"
    log = _cli(sandbox, "log", "--journal", str(sandbox["journal"]))
    assert log.returncode == 0 and "verified" in log.stdout


def test_log_without_journal_is_not_an_error(sandbox: dict[str, Path]) -> None:
    result = _cli(sandbox, "log", "--journal", str(sandbox["journal"]))
    assert result.returncode == 0 and "no journal" in result.stdout
    assert not sandbox["journal"].exists()


@needs_backend
def test_demo_check_verifies_and_rejects_evidence(sandbox: dict[str, Path], tmp_path: Path) -> None:
    evidence = tmp_path / "evidence.json"
    assert _cli(sandbox, "demo", "--journal", str(sandbox["journal"]), "--json", str(evidence)).returncode == 0
    good = _cli(sandbox, "demo", "--check", str(evidence))
    assert good.returncode == 0 and "self digest: ok" in good.stdout and "same as this installation" in good.stdout
    document = json.loads(evidence.read_text())
    document["verdict"] = "EDITED"
    evidence.write_text(json.dumps(document))
    bad = _cli(sandbox, "demo", "--check", str(evidence))
    assert bad.returncode == 1 and "MISMATCH" in bad.stdout
