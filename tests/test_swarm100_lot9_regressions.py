"""Monitor Git fixes: actual Git only in owned fixtures, producers controlled."""

import importlib.util
import os
from pathlib import Path
import shutil
import socket
import subprocess
import sys
from types import SimpleNamespace

import pytest

ROOT = Path(__file__).absolute().parents[1]
SOURCE = ROOT / "scripts/c5_thermo/c5_exergy_optimizer_monitor.py"
ERRORS = (RuntimeError, subprocess.SubprocessError, SystemExit)


@pytest.fixture
def repo(tmp_path, monkeypatch):
    root = tmp_path / "monitor repository with spaces"
    root.mkdir()
    home = tmp_path / "home"
    home.mkdir()
    for key in list(os.environ):
        if key.startswith("GIT_"):
            monkeypatch.delenv(key)
    for key, value in dict(
        HOME=str(home),
        XDG_CONFIG_HOME=str(home / "xdg"),
        GIT_CONFIG_NOSYSTEM="1",
        GIT_CONFIG_GLOBAL=str(home / "empty"),
        GIT_TERMINAL_PROMPT="0",
    ).items():
        monkeypatch.setenv(key, value)

    def git(*args, check=True):
        return subprocess.run(["git", *args], cwd=root, capture_output=True, check=check, timeout=10)

    git("init", "-b", "main")
    git("config", "user.name", "Monitor Fixture")
    git("config", "user.email", "fixture@example.invalid")
    git("config", "commit.gpgsign", "false")
    status = root / "STATUS.md"
    status.write_text("# Fixture Status\n\nHistorical `[PENDING]` entry\n")
    (root / "unrelated.txt").write_text("initial unrelated\n")
    actual = root / "scripts/c5_thermo/c5_exergy_optimizer_monitor.py"
    actual.parent.mkdir(parents=True)
    actual.write_text("fixture source marker; never execute")
    git("add", "--", "STATUS.md", "unrelated.txt", "scripts/c5_thermo/c5_exergy_optimizer_monitor.py")
    git("commit", "-m", "Fixture initial state")
    copied = tmp_path / "fixture_monitor.py"
    shutil.copyfile(SOURCE, copied)
    spec = importlib.util.spec_from_file_location("lot9_monitor_fixture", copied)
    module = importlib.util.module_from_spec(spec)
    monkeypatch.setitem(sys.modules, spec.name, module)
    spec.loader.exec_module(module)
    monkeypatch.setattr(module, "ROOT_DIR", root)
    monkeypatch.setattr(module, "STATUS_FILE", status)
    monkeypatch.setattr(
        module,
        "audit_git_entropy",
        lambda: dict(head="fixture", branch="main", commits=1, last_tag="NONE", dirty_count=1, dirty_files=[]),
    )
    monkeypatch.setattr(module, "audit_db_census", lambda: {})
    monkeypatch.setattr(module, "audit_ruff", lambda: dict(total_errors=0, fixable=0))
    monkeypatch.setattr(module, "audit_tests", lambda: dict(test_files=0, status="FIXTURE_ONLY", passed=0))

    def forbidden(*args, **kwargs):
        raise AssertionError("network or database call forbidden in monitor fixture")

    monkeypatch.setattr(socket.socket, "connect", forbidden)
    monkeypatch.setattr(socket.socket, "connect_ex", forbidden)
    monkeypatch.setattr(socket, "getaddrinfo", forbidden)
    monkeypatch.setattr(module.sqlite3, "connect", forbidden)

    def head():
        return git("rev-parse", "HEAD").stdout.strip()

    def index():
        return (root / ".git/index").read_bytes()

    def hook(name, body):
        target = root / ".git/hooks" / name
        target.write_text("#!/bin/sh\n" + body + "\n")
        target.chmod(0o700)

    def mutate():
        status.write_text(status.read_text() + "generated fixture status\n")

    def legacy():
        path = root / "scripts/c5_exergy_optimizer_monitor.py"
        path.write_text("obsolete fixture path\n")
        git("add", "--", str(path.relative_to(root)))
        git("commit", "-m", "Fixture obsolete path exists")

    return SimpleNamespace(
        root=root,
        module=module,
        git=git,
        head=head,
        index=index,
        hook=hook,
        mutate=mutate,
        status=status,
        legacy=legacy,
    )


def test_c0438_git_error_is_not_empty_success(repo):
    with pytest.raises(subprocess.CalledProcessError):
        repo.module._git(["rev-parse", "--verify", "refs/heads/fixture-absent"])


def test_c0438_signing_configuration_is_not_overridden(repo):
    recorder = repo.root / "signer-recorder.sh"
    recorder.write_text("#!/bin/sh\necho called >> signer-calls.log\nexit 1\n")
    recorder.chmod(0o700)
    repo.git("config", "gpg.program", str(recorder))
    repo.git("config", "user.signingkey", "SYNTHETIC-NO-KEY")
    repo.git("config", "commit.gpgsign", "true")
    repo.mutate()
    before = repo.head()
    with pytest.raises(subprocess.CalledProcessError):
        repo.module._git(["commit", "--only", "-m", "Fixture signer rejection", "--", "STATUS.md"])
    assert (repo.root / "signer-calls.log").read_text().splitlines() == ["called"]
    assert repo.head() == before


def test_c0438_prepared_unrelated_index_is_rejected(repo):
    (repo.root / "unrelated.txt").write_text("prepared unrelated\n")
    repo.git("add", "--", "unrelated.txt")
    repo.mutate()
    head, index = repo.head(), repo.index()
    with pytest.raises(ERRORS):
        repo.module.git_sentinel_commit("a" * 64)
    assert repo.head() == head and repo.index() == index


def test_c0438_obsolete_source_path_cannot_hide_failed_commit(repo):
    repo.mutate()
    before = repo.head()
    value = repo.module.git_sentinel_commit("a" * 64)
    assert repo.head() != before
    assert value.encode() == repo.head()
    assert repo.git("diff-tree", "--no-commit-id", "--name-only", "-r", "-z", "HEAD").stdout == b"STATUS.md\0"


def test_c0438_hook_failure_is_not_bypassed(repo):
    repo.legacy()
    repo.mutate()
    repo.hook("pre-commit", "echo called >> hook-calls.log\nexit 1")
    head, index = repo.head(), repo.index()
    with pytest.raises(ERRORS):
        repo.module.git_sentinel_commit("a" * 64)
    assert repo.head() == head and repo.index() == index
    assert (repo.root / "hook-calls.log").read_text().splitlines() == ["called"]


def test_c0438_consumer_rejection_never_prints_complete(repo, capsys):
    repo.legacy()
    repo.hook("commit-msg", "exit 1")
    head, index = repo.head(), repo.index()
    with pytest.raises(ERRORS):
        repo.module.c5_real_colapso()
    assert "EXERGY_OPTIMIZER COMPLETE" not in capsys.readouterr().out
    assert repo.head() == head and repo.index() == index


def test_c0438_consumer_makes_one_commit_and_preserves_historical_pending(repo, capsys):
    repo.legacy()
    before = int(repo.git("rev-list", "--count", "HEAD").stdout)
    repo.module.c5_real_colapso()
    assert int(repo.git("rev-list", "--count", "HEAD").stdout) == before + 1
    assert "Historical `[PENDING]` entry" in repo.status.read_text()
    assert repo.head().decode() in capsys.readouterr().out


def test_c0438_noop_is_not_returned_as_new_commit(repo):
    head, index = repo.head(), repo.index()
    assert repo.module.git_sentinel_commit("a" * 64) is None
    assert repo.head() == head and repo.index() == index


def test_normal_hooks_run_once_and_source_edits_remain_outside_commit(repo):
    repo.mutate()
    actual = repo.root / "scripts/c5_thermo/c5_exergy_optimizer_monitor.py"
    actual.write_text("unrelated source edit\n")
    (repo.root / "untracked.txt").write_text("private fixture data\n")
    repo.hook("pre-commit", "echo pre >> normal-hooks.log\nexit 0")
    repo.hook("prepare-commit-msg", "echo prepare >> normal-hooks.log\nexit 0")
    repo.hook("commit-msg", "echo msg >> normal-hooks.log\nexit 0")
    value = repo.module.git_sentinel_commit("a" * 64)
    assert value.encode() == repo.head()
    assert repo.git("diff-tree", "--no-commit-id", "--name-only", "-r", "-z", "HEAD").stdout == b"STATUS.md\0"
    assert (repo.root / "normal-hooks.log").read_text().splitlines() == ["pre", "prepare", "msg"]
    assert actual.read_text() == "unrelated source edit\n"
    assert (repo.root / "untracked.txt").read_text() == "private fixture data\n"


def test_noop_does_not_invoke_hook(repo):
    repo.hook("pre-commit", "echo forbidden > hook-should-not-run\nexit 1")
    head, index = repo.head(), repo.index()
    assert repo.module.git_sentinel_commit("a" * 64) is None
    assert repo.head() == head and repo.index() == index
    assert not (repo.root / "hook-should-not-run").exists()


def test_consumer_noop_is_explicit_not_complete(repo, monkeypatch, capsys):
    monkeypatch.setattr(repo.module, "append_mutation", lambda *args: None)
    head, index = repo.head(), repo.index()
    repo.module.c5_real_colapso()
    output = capsys.readouterr().out
    assert "NO_CHANGE" in output and "EXERGY_OPTIMIZER COMPLETE" not in output
    assert repo.head() == head and repo.index() == index


def test_consumer_respects_signer_failure(repo, capsys):
    signer = repo.root / "signer-recorder.sh"
    signer.write_text("#!/bin/sh\necho called >> consumer-signer.log\nexit 1\n")
    signer.chmod(0o700)
    repo.git("config", "gpg.program", str(signer))
    repo.git("config", "user.signingkey", "SYNTHETIC-NO-KEY")
    repo.git("config", "commit.gpgsign", "true")
    head, index = repo.head(), repo.index()
    with pytest.raises(subprocess.CalledProcessError):
        repo.module.c5_real_colapso()
    assert "EXERGY_OPTIMIZER COMPLETE" not in capsys.readouterr().out
    assert repo.head() == head and repo.index() == index
    assert (repo.root / "consumer-signer.log").read_text().splitlines() == ["called"]


@pytest.mark.parametrize("kind", ["unrelated", "partial-status", "intent-to-add", "assume-unchanged", "skip-worktree"])
def test_consumer_preflight_precedes_every_producer(repo, monkeypatch, kind):
    if kind == "unrelated":
        (repo.root / "unrelated.txt").write_text("prepared data\n")
        repo.git("add", "--", "unrelated.txt")
    elif kind == "partial-status":
        repo.mutate()
        repo.git("add", "--", "STATUS.md")
        repo.mutate()
    elif kind == "intent-to-add":
        (repo.root / "intent.txt").write_text("intent data\n")
        repo.git("add", "--intent-to-add", "--", "intent.txt")
    else:
        repo.git("update-index", "--" + kind, "--", "unrelated.txt")

    def forbidden(*args, **kwargs):
        raise AssertionError("producer executed before preflight acceptance")

    for name in [
        "audit_git_entropy",
        "audit_db_census",
        "audit_ruff",
        "audit_tests",
        "crystallize_status",
        "append_mutation",
    ]:
        monkeypatch.setattr(repo.module, name, forbidden)
    head, index, contents = repo.head(), repo.index(), repo.status.read_bytes()
    with pytest.raises(RuntimeError):
        repo.module.c5_real_colapso()
    assert repo.head() == head and repo.index() == index and repo.status.read_bytes() == contents


@pytest.mark.parametrize("kind", ["missing", "symlink", "directory", "fifo", "untracked"])
def test_invalid_status_is_rejected_before_producers(repo, monkeypatch, kind):
    if kind == "untracked":
        repo.git("rm", "--cached", "--", "STATUS.md")
        repo.git("commit", "-m", "Fixture STATUS untracked")
    else:
        repo.status.unlink()
        if kind == "symlink":
            repo.status.symlink_to(repo.root / "unrelated.txt")
        elif kind == "directory":
            repo.status.mkdir()
        elif kind == "fifo":
            os.mkfifo(repo.status)

    def forbidden(*args, **kwargs):
        raise AssertionError("invalid STATUS reached producer")

    monkeypatch.setattr(repo.module, "audit_git_entropy", forbidden)
    head, index = repo.head(), repo.index()
    with pytest.raises((RuntimeError, OSError)):
        repo.module.c5_real_colapso()
    assert repo.head() == head and repo.index() == index
    assert (repo.root / "unrelated.txt").read_text() == "initial unrelated\n"


@pytest.mark.parametrize(
    "selector",
    ["GIT_DIR", "GIT_WORK_TREE", "GIT_INDEX_FILE", "GIT_COMMON_DIR", "GIT_CONFIG_COUNT", "GIT_CONFIG_PARAMETERS"],
)
def test_ambient_override_rejected_before_git(repo, monkeypatch, selector):
    def forbidden(*args, **kwargs):
        raise AssertionError("selector reached Git")

    with monkeypatch.context() as patch:
        patch.setenv(selector, "fixture-override")
        patch.setattr(repo.module.subprocess, "run", forbidden)
        with pytest.raises(RuntimeError):
            repo.module._git(["rev-parse", "HEAD"])


@pytest.mark.parametrize("mode", ["merge", "rebase", "split", "sparse", "detached", "subdirectory"])
def test_repository_state_rejected_without_index_write(repo, monkeypatch, mode):
    if mode == "merge":
        (repo.root / ".git/MERGE_HEAD").write_bytes(repo.head() + b"\n")
    elif mode == "rebase":
        (repo.root / ".git/rebase-merge").mkdir()
    elif mode == "split":
        repo.git("update-index", "--split-index")
    elif mode == "sparse":
        repo.git("config", "core.sparseCheckout", "true")
    elif mode == "detached":
        repo.git("checkout", "--detach")
    elif mode == "subdirectory":
        nested = repo.root / "nested"
        nested.mkdir()
        monkeypatch.setattr(repo.module, "ROOT_DIR", nested)
        monkeypatch.setattr(repo.module, "STATUS_FILE", nested / "STATUS.md")
    head, index = repo.head(), repo.index()
    with pytest.raises((RuntimeError, subprocess.SubprocessError)):
        repo.module.c5_real_colapso()
    assert repo.head() == head and repo.index() == index


def test_output_outside_workspace_rejected_before_git(repo, monkeypatch):
    monkeypatch.setattr(repo.module, "STATUS_FILE", repo.root / "other.md")

    def forbidden(*args, **kwargs):
        raise AssertionError("invalid output reached Git")

    monkeypatch.setattr(repo.module.subprocess, "run", forbidden)
    with pytest.raises(ValueError):
        repo.module._git_preflight()


@pytest.mark.parametrize("value", ["", True, "x" * 64, "a" * 63, "a" * 65, None])
def test_invalid_digest_rejected_before_git(repo, monkeypatch, value):
    def forbidden(*args, **kwargs):
        raise AssertionError("invalid digest reached Git")

    monkeypatch.setattr(repo.module.subprocess, "run", forbidden)
    with pytest.raises(ValueError):
        repo.module.git_sentinel_commit(value)


def test_index_change_during_producers_is_preserved(repo, monkeypatch, capsys):
    original = repo.module.append_mutation
    actor_index = []

    def append(*args):
        original(*args)
        (repo.root / "unrelated.txt").write_text("another actor staged this\n")
        repo.git("add", "--", "unrelated.txt")
        actor_index.append(repo.index())

    monkeypatch.setattr(repo.module, "append_mutation", append)
    head = repo.head()
    with pytest.raises(RuntimeError):
        repo.module.c5_real_colapso()
    assert repo.head() == head and repo.index() == actor_index[0]
    assert "EXERGY_OPTIMIZER COMPLETE" not in capsys.readouterr().out


def test_head_change_during_audit_is_preserved(repo, monkeypatch, capsys):
    original = repo.module.audit_tests
    actor_head = []

    def audit():
        (repo.root / "unrelated.txt").write_text("another actor committed this\n")
        repo.git("add", "--", "unrelated.txt")
        repo.git("commit", "-m", "Fixture concurrent actor commit")
        actor_head.append(repo.head())
        return original()

    monkeypatch.setattr(repo.module, "audit_tests", audit)
    with pytest.raises(RuntimeError):
        repo.module.c5_real_colapso()
    assert repo.head() == actor_head[0]
    assert "EXERGY_OPTIMIZER COMPLETE" not in capsys.readouterr().out


def test_staging_unrelated_path_just_before_commit_is_not_consumed(repo, monkeypatch):
    repo.mutate()
    (repo.root / "unrelated.txt").write_text("late unrelated staging\n")
    original = subprocess.run
    seen = []

    def run(command, **kwargs):
        if command[:3] == ["git", "--literal-pathspecs", "commit"]:
            original(["git", "add", "--", "unrelated.txt"], cwd=repo.root, capture_output=True, check=True)
            seen.append(True)
        return original(command, **kwargs)

    monkeypatch.setattr(repo.module.subprocess, "run", run)
    value = repo.module.git_sentinel_commit("a" * 64)
    assert seen == [True] and value.encode() == repo.head()
    assert repo.git("diff-tree", "--no-commit-id", "--name-only", "-r", "-z", "HEAD").stdout == b"STATUS.md\0"
    assert repo.git("diff", "--cached", "--name-only", "-z").stdout == b"unrelated.txt\0"


def test_git_metadata_wrapper_survives_binary_diff(repo):
    repo.status.write_bytes(b"\x00\xffbinary STATUS fixture")
    output = repo.module._git_bytes(["diff", "--binary", "HEAD", "--", "STATUS.md"])
    assert isinstance(output, bytes) and b"STATUS.md" in output
    text = repo.module._git(["diff", "HEAD", "--", "STATUS.md"])
    assert isinstance(text, str)
    value = repo.module.git_sentinel_commit("a" * 64)
    assert value.encode() == repo.head()
    assert repo.git("show", "HEAD:STATUS.md").stdout == b"\x00\xffbinary STATUS fixture"


def test_linked_worktree_changes_only_its_own_status(repo, monkeypatch):
    linked = repo.root.parent / "linked monitor fixture"
    repo.git("worktree", "add", "-b", "fixture-monitor-linked", str(linked))
    head, index = repo.head(), repo.index()
    monkeypatch.setattr(repo.module, "ROOT_DIR", linked)
    monkeypatch.setattr(repo.module, "STATUS_FILE", linked / "STATUS.md")
    (linked / "STATUS.md").write_text("linked STATUS fixture\n")
    value = repo.module.git_sentinel_commit("a" * 64)
    observed = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=linked, capture_output=True, check=True, timeout=10
    ).stdout.strip()
    assert value.encode() == observed and observed != head
    assert repo.head() == head and repo.index() == index


def test_bounded_sequential_commits_keep_status_scope(repo):
    # Warmup plus four sequential fixtures; no timing/concurrency certification.
    for number in range(5):
        repo.status.write_text(f"generated STATUS {number}\n")
        value = repo.module.git_sentinel_commit("a" * 64)
        assert value.encode() == repo.head()
        assert repo.git("diff-tree", "--no-commit-id", "--name-only", "-r", "-z", "HEAD").stdout == b"STATUS.md\0"
