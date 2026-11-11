"""``babylon60 run | demo | log`` through the real argument parser."""

from __future__ import annotations

import json
import os
from pathlib import Path
import secrets
import subprocess
import sys

import pytest

from babylon60.confine.cli import _strip_separator, executable_grants, outside_grants_hint
from babylon60.confine.launcher import landlock_abi
from babylon60.confine.policy import MIN_LANDLOCK_ABI, build_policy

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
    assert document["schema"] == "babylon60.confine.demo/v2" and document["verdict"] == "BLOCKED"
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
    assert "not a signature" in good.stdout  # anyone who edits the document can recompute its digest
    document = json.loads(evidence.read_text())
    document["verdict"] = "EDITED"
    evidence.write_text(json.dumps(document))
    bad = _cli(sandbox, "demo", "--check", str(evidence))
    assert bad.returncode == 1 and "MISMATCH" in bad.stdout


@needs_backend
def test_each_run_gets_a_private_tmpdir_that_is_removed(sandbox: dict[str, Path]) -> None:
    script = (
        'import os, sys, tempfile; d = os.environ["TMPDIR"]; print(d); '
        'open(os.path.join(d, "scratch"), "w").write("ok"); '
        'p = "/tmp/b60-shared-" + str(os.getpid())\n'
        "try:\n    open(p, 'w').close(); print('tmp writable')\n"
        "except OSError as e:\n    print('tmp denied', e.errno)"
    )
    result = _run(sandbox, sys.executable, "-I", "-S", "-c", script)
    assert result.returncode == 0, result.stderr
    private, outcome = result.stdout.splitlines()
    assert os.path.basename(private).startswith("babylon60-run-") and not os.path.exists(private)
    assert outcome.startswith("tmp denied") if sys.platform.startswith("linux") else outcome


@needs_backend
def test_permission_changes_on_protected_paths_are_reported_and_journaled(sandbox: dict[str, Path]) -> None:
    key = sandbox["home"] / ".ssh" / "id_rsa"
    key.chmod(0o600)
    result = _run(sandbox, "chmod", "644", str(key))
    if sys.platform == "darwin":  # Seatbelt denies metadata writes in the home
        assert result.returncode != 0 and "permissions or ownership changed" not in result.stderr
        return
    assert result.returncode == 0, result.stderr  # Landlock (ABI <= 7) does not mediate chmod: a declared limit
    assert "permissions or ownership changed" in result.stderr and "id_rsa" in result.stderr
    log = json.loads(_cli(sandbox, "log", "--journal", str(sandbox["journal"]), "--json").stdout)
    assert any("id_rsa" in line for line in log["entries"][-1]["body"]["metadata_changed"])


def test_a_journal_with_another_hard_link_is_refused(sandbox: dict[str, Path], tmp_path: Path) -> None:
    sandbox["journal"].parent.mkdir(parents=True)
    sandbox["journal"].write_bytes(b"")
    os.link(sandbox["journal"], sandbox["ws"] / "journal-alias.db")
    result = _run(sandbox, "true")
    assert result.returncode == 3 and "hard links" in result.stderr


@needs_backend
def test_policy_warnings_reach_stderr(sandbox: dict[str, Path], tmp_path: Path) -> None:
    os.link(sandbox["home"] / ".ssh" / "id_rsa", tmp_path / "outside-alias")
    result = _run(sandbox, "true")
    assert result.returncode == 0, result.stderr
    assert "babylon60 run: warning:" in result.stderr and "links" in result.stderr


@needs_backend
@pytest.mark.skipif(not sys.platform.startswith("linux"), reason="Landlock scoping is Linux-only")
def test_signals_outside_the_sandbox_follow_the_landlock_abi_and_are_journaled(sandbox: dict[str, Path]) -> None:
    outside = subprocess.Popen(["sleep", "120"])
    try:
        script = (
            "import os, sys\n"
            "try:\n    os.kill(int(sys.argv[1]), 0); print('signal sent')\n"
            "except PermissionError:\n    print('signal refused')"
        )
        result = _run(sandbox, sys.executable, "-I", "-S", "-c", script, str(outside.pid))
    finally:
        outside.kill()
        outside.wait()
    assert result.returncode == 0, result.stderr
    scoped = landlock_abi() >= 6  # LANDLOCK_SCOPE_SIGNAL
    assert result.stdout.strip() == ("signal refused" if scoped else "signal sent")
    assert ("does not scope signals" in result.stderr) == (not scoped)  # an older kernel is a declared limit
    log = json.loads(_cli(sandbox, "log", "--journal", str(sandbox["journal"]), "--json").stdout)
    assert log["entries"][-1]["body"]["landlock_scoped"] == (3 if scoped else 0)


@needs_backend
@pytest.mark.skipif(not sys.platform.startswith("linux"), reason="Seatbelt allows paths outside the homes")
def test_a_command_outside_every_grant_gets_a_hint_and_runs_once_granted(
    sandbox: dict[str, Path], tmp_path: Path
) -> None:
    tools = tmp_path / "tools" / "bin"
    tools.mkdir(parents=True)
    tool = tools / "tool"
    tool.write_text("#!/bin/sh\necho tool ran\n")
    tool.chmod(0o755)
    refused = _run(sandbox, str(tool))
    assert refused.returncode == 126, refused.stderr  # Landlock refuses execve; before, only "Permission denied"
    assert f"outside every granted path; to allow it, pass --allow-read {tools}" in refused.stderr
    granted = _run(sandbox, str(tool), options=("--allow-read", str(tools)))
    assert granted.returncode == 0 and granted.stdout == "tool ran\n", granted.stderr
    assert "outside every granted path" not in granted.stderr


def _policy(tmp_path: Path) -> tuple[tuple[str, ...], object]:
    ws = tmp_path / "ws"
    ws.mkdir(exist_ok=True)
    homes = (str(tmp_path / "home"),)
    return homes, build_policy(ws, homes=list(homes))


def _executable(path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("#!/bin/sh\necho hi\n")
    path.chmod(0o755)
    return path


def test_the_hint_names_the_whole_npm_install_or_venv(tmp_path: Path) -> None:
    homes, policy = _policy(tmp_path)
    modules = tmp_path / "npm" / "node_modules"
    entry = _executable(modules / "@scope" / "agent" / "bin" / "cli.js")
    (modules / ".bin").mkdir()
    (modules / ".bin" / "agent").symlink_to(entry)
    hint = outside_grants_hint(str(modules / ".bin" / "agent"), homes, policy)  # type: ignore[arg-type]
    assert hint is not None and hint.endswith(f"--allow-read {modules}"), hint
    venv = tmp_path / "venv"
    tool = _executable(venv / "bin" / "tool")
    (venv / "pyvenv.cfg").write_text("home = /usr/bin\n")
    hint = outside_grants_hint(str(tool), homes, policy)  # type: ignore[arg-type]
    assert hint is not None and hint.endswith(f"--allow-read {venv}"), hint
    inside = _executable(tmp_path / "ws" / "bin" / "tool")
    assert outside_grants_hint(str(inside), homes, policy) is None  # type: ignore[arg-type]


def test_the_hint_never_suggests_granting_a_shared_directory(tmp_path: Path) -> None:
    homes, policy = _policy(tmp_path)
    shared = tmp_path / "shared"
    shared.mkdir()
    shared.chmod(0o1777)
    hint = outside_grants_hint(str(_executable(shared / "tool")), homes, policy)  # type: ignore[arg-type]
    assert hint is not None and "--allow-read" in hint and f"--allow-read {shared}" not in hint, hint
    assert "copy it to a directory of your own" in hint


@needs_backend
@pytest.mark.skipif(
    not sys.platform.startswith("linux"), reason="reads the launcher's /proc/<pid>/environ from outside"
)
def test_run_reexecutes_itself_without_the_withheld_variables(sandbox: dict[str, Path]) -> None:
    """macOS lets the agent read its launcher's exec-time environment (KERN_PROCARGS2): nothing withheld stays there."""
    token = "B60-CANARY-" + secrets.token_hex(8)
    script = (
        "import os, sys; print(os.getppid(), 'BABYLON60_RUN_WITHHELD' in os.environ, flush=True); sys.stdin.readline()"
    )
    env = {**os.environ, "HOME": str(sandbox["home"]), "PYTHONPATH": str(ROOT / "01_KISH_ENGINE"), "GH_TOKEN": token}
    argv = [sys.executable, "-m", "babylon60.cli.main_dispatcher", "run", "--allow-root"]
    argv += ["--journal", str(sandbox["journal"]), "--", sys.executable, "-I", "-S", "-c", script]
    process = subprocess.Popen(
        argv, env=env, cwd=str(sandbox["ws"]), stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE
    )
    try:
        assert process.stdout is not None and process.stdin is not None
        launcher_pid, leaked_marker = process.stdout.readline().split()
        environ = Path(f"/proc/{int(launcher_pid)}/environ").read_bytes()  # read from outside the sandbox
        # The newline goes through communicate(): Python 3.12 refuses communicate() on a stdin closed beforehand.
        _out, err = process.communicate(b"\n", timeout=120)
    finally:
        if process.poll() is None:
            process.kill()
            process.wait()
    assert process.returncode == 0, err
    assert token.encode() not in environ and b"GH_TOKEN=" not in environ, "the launcher still holds the withheld value"
    assert b"GH_TOKEN" in err and leaked_marker == b"False"  # still reported; the internal list never reaches the agent
    log = json.loads(_cli(sandbox, "log", "--journal", str(sandbox["journal"]), "--json").stdout)
    assert "GH_TOKEN" in log["entries"][0]["body"]["env_removed"]
