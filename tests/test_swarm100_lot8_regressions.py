"""Git Sentinel regressions in owned temporary repositories only."""

import hashlib
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
SOURCE = ROOT / "scripts/c5_cortex/cortex_objectives_transducer.py"
ALLOWED = {"cortex/ontology/babylon60_objectives.yaml", "PROJECT.md"}
ERRORS = (RuntimeError, subprocess.SubprocessError, SystemExit)


@pytest.fixture
def repo(tmp_path, monkeypatch):
    home = tmp_path / "home"
    home.mkdir()
    root = tmp_path / "repository with spaces"
    root.mkdir()
    for key in list(os.environ):
        if key.startswith("GIT_"):
            monkeypatch.delenv(key)
    for key, value in dict(
        HOME=str(home),
        XDG_CONFIG_HOME=str(home / "xdg"),
        GIT_CONFIG_NOSYSTEM="1",
        GIT_CONFIG_GLOBAL=str(home / "empty-gitconfig"),
        GIT_TERMINAL_PROMPT="0",
    ).items():
        monkeypatch.setenv(key, value)

    def git(*args, check=True):
        return subprocess.run(["git", *args], cwd=root, capture_output=True, check=check, timeout=10)

    git("init", "-b", "main")
    git("config", "user.name", "Fixture Author")
    git("config", "user.email", "fixture@example.invalid")
    git("config", "commit.gpgsign", "false")
    yaml = root / "cortex/ontology/babylon60_objectives.yaml"
    yaml.parent.mkdir(parents=True)
    yaml.write_text("objectives: []\n")
    (root / "PROJECT.md").write_text("# Fixture project\n")
    (root / "unrelated.txt").write_text("initial unrelated data\n")
    git("add", "--", *sorted(ALLOWED), "unrelated.txt")
    git("commit", "-m", "Fixture initial commit")
    copied = tmp_path / "fixture_objectives.py"
    shutil.copyfile(SOURCE, copied)
    spec = importlib.util.spec_from_file_location("lot8_objectives_fixture", copied)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    monkeypatch.setitem(sys.modules, spec.name, module)
    spec.loader.exec_module(module)
    monkeypatch.setattr(module, "WORKSPACE_DIR", root)
    monkeypatch.setattr(module, "YAML_STATE_PATH", yaml)
    monkeypatch.setattr(module, "PROJECT_MD_PATH", root / "PROJECT.md")

    def forbidden(*args, **kwargs):
        raise AssertionError("network or process-kill forbidden in fixture")

    monkeypatch.setattr(socket.socket, "connect", forbidden)
    monkeypatch.setattr(socket.socket, "connect_ex", forbidden)
    monkeypatch.setattr(socket, "getaddrinfo", forbidden)
    monkeypatch.setattr(module.os, "kill", forbidden)

    def head():
        return git("rev-parse", "HEAD").stdout.strip()

    def index():
        return (root / ".git/index").read_bytes()

    def changed():
        return set(
            git("diff-tree", "--no-commit-id", "--name-only", "-r", "-z", "HEAD")
            .stdout.decode()
            .strip("\0")
            .split("\0")
        )

    def hook(name, body):
        target = root / ".git/hooks" / name
        target.write_text("#!/bin/sh\n" + body + "\n")
        target.chmod(0o700)
        return target

    def mutate():
        yaml.write_text("objectives:\n- id: OBJ-FIXTURE\n")

    return SimpleNamespace(
        root=root, module=module, git=git, head=head, index=index, changed=changed, hook=hook, mutate=mutate, yaml=yaml
    )


@pytest.mark.parametrize("name", ["pre-commit", "commit-msg"])
def test_c0499_hook_rejection_is_never_bypassed(repo, name):
    repo.mutate()
    repo.hook(name, "echo invocation >> hook-calls.log\nexit 1")
    before_head, before_index = repo.head(), repo.index()
    with pytest.raises(ERRORS):
        repo.module.run_git_sentinel("Fixture rejected mutation")
    assert repo.head() == before_head
    assert repo.index() == before_index
    assert (repo.root / "hook-calls.log").read_text().splitlines() == ["invocation"]


@pytest.mark.parametrize("kind", ["tracked", "untracked"])
def test_c0500_only_declared_outputs_are_committed(repo, kind):
    repo.mutate()
    other = repo.root / ("unrelated.txt" if kind == "tracked" else "private-untracked.txt")
    other.write_text("unrelated data must remain outside the commit\n")
    value = repo.module.run_git_sentinel("Fixture narrow mutation")
    assert value.encode() == repo.head()
    assert repo.changed() == {"cortex/ontology/babylon60_objectives.yaml"}
    assert other.read_text() == "unrelated data must remain outside the commit\n"


def test_c0500_yaml_consumer_does_not_commit_unrelated_project_edit(repo):
    project = repo.root / "PROJECT.md"
    project.write_text("unrelated project edit\n")
    args = SimpleNamespace(title="Fixture", description="Fixture objective", exergy=0.0)
    repo.module.cmd_add_objective(args)
    assert repo.changed() == {"cortex/ontology/babylon60_objectives.yaml"}
    assert project.read_text() == "unrelated project edit\n"


@pytest.mark.parametrize("target", ["unrelated.txt", "cortex/ontology/babylon60_objectives.yaml"])
def test_c0500_prepared_index_is_rejected_without_changes(repo, target):
    path = repo.root / target
    path.write_text("prepared content\n")
    repo.git("add", "--", target)
    repo.mutate()
    before_head, before_index = repo.head(), repo.index()
    with pytest.raises(ERRORS):
        repo.module.run_git_sentinel("Fixture must not include prepared work")
    assert repo.head() == before_head
    assert repo.index() == before_index
    assert hashlib.sha256(repo.index()).digest() == hashlib.sha256(before_index).digest()


def test_clean_commit_runs_both_normal_hooks_once(repo):
    repo.mutate()
    (repo.root / "PROJECT.md").write_text("# Generated fixture project\n")
    repo.hook("pre-commit", "echo pre >> normal-hook-calls.log\nexit 0")
    repo.hook("commit-msg", "echo msg >> normal-hook-calls.log\nexit 0")
    result = repo.module.run_git_sentinel("Fixture both generated outputs", paths=(repo.yaml, repo.root / "PROJECT.md"))
    assert result.encode() == repo.head()
    assert repo.changed() == ALLOWED
    assert (repo.root / "normal-hook-calls.log").read_text().splitlines() == ["pre", "msg"]
    assert repo.git("diff", "--cached", "--name-only", "-z").stdout == b""


def test_noop_returns_existing_head_without_hook_or_index_write(repo):
    repo.hook("pre-commit", "echo forbidden > should-not-exist\nexit 1")
    head, index = repo.head(), repo.index()
    assert repo.module.run_git_sentinel("Fixture no changes").encode() == head
    assert repo.head() == head and repo.index() == index
    assert not (repo.root / "should-not-exist").exists()


def test_hook_diagnostic_nothing_to_commit_is_not_success(repo):
    repo.mutate()
    repo.hook("pre-commit", 'echo "nothing to commit" >&2\nexit 1')
    head, index = repo.head(), repo.index()
    with pytest.raises(subprocess.CalledProcessError):
        repo.module.run_git_sentinel("Fixture diagnostic is not a verdict")
    assert repo.head() == head and repo.index() == index


def test_non_hook_git_error_is_not_retried_or_treated_as_noop(repo):
    repo.mutate()
    repo.git("config", "user.useConfigOnly", "true")
    repo.git("config", "--unset", "user.email")
    head, index = repo.head(), repo.index()
    with pytest.raises(subprocess.CalledProcessError):
        repo.module.run_git_sentinel("Fixture invalid identity")
    assert repo.head() == head and repo.index() == index


def test_existing_index_lock_is_preserved(repo):
    repo.mutate()
    lock = repo.root / ".git/index.lock"
    lock.write_bytes(b"owned by another operation")
    head, index = repo.head(), repo.index()
    with pytest.raises(ERRORS):
        repo.module.run_git_sentinel("Fixture must not remove another lock")
    assert repo.head() == head and repo.index() == index
    assert lock.read_bytes() == b"owned by another operation"


@pytest.mark.parametrize("flag", ["--assume-unchanged", "--skip-worktree", "intent-to-add"])
def test_special_index_preparation_is_rejected_byte_for_byte(repo, flag):
    if flag == "intent-to-add":
        target = repo.root / "intent-only.txt"
        target.write_text("intent must be preserved")
        repo.git("add", "--intent-to-add", "--", target.name)
    else:
        repo.git("update-index", flag, "--", "unrelated.txt")
    repo.mutate()
    head, index = repo.head(), repo.index()
    with pytest.raises(RuntimeError):
        repo.module.run_git_sentinel("Fixture special index")
    assert repo.head() == head and repo.index() == index


@pytest.mark.parametrize(
    "marker", ["MERGE_HEAD", "CHERRY_PICK_HEAD", "REVERT_HEAD", "rebase-merge", "rebase-apply", "sequencer"]
)
def test_in_progress_git_operation_is_not_committed(repo, marker):
    repo.mutate()
    path = repo.root / ".git" / marker
    if marker.endswith("HEAD"):
        path.write_bytes(repo.head() + b"\n")
    else:
        path.mkdir()
    head, index = repo.head(), repo.index()
    with pytest.raises(RuntimeError):
        repo.module.run_git_sentinel("Fixture active operation")
    assert repo.head() == head and repo.index() == index
    assert path.exists()


@pytest.mark.parametrize(
    "selector",
    [
        "GIT_DIR",
        "GIT_WORK_TREE",
        "GIT_INDEX_FILE",
        "GIT_COMMON_DIR",
        "GIT_NAMESPACE",
        "GIT_OBJECT_DIRECTORY",
        "GIT_ALTERNATE_OBJECT_DIRECTORIES",
        "GIT_CONFIG_COUNT",
        "GIT_CONFIG_PARAMETERS",
        "GIT_CONFIG_KEY_0",
        "GIT_CONFIG_VALUE_0",
    ],
)
def test_ambient_selectors_fail_before_any_git_call(repo, monkeypatch, selector):
    def forbidden(*args, **kwargs):
        raise AssertionError("selector rejection must precede Git")

    with monkeypatch.context() as patch:
        patch.setenv(selector, "fixture-override")
        patch.setattr(repo.module.subprocess, "run", forbidden)
        with pytest.raises(RuntimeError):
            repo.module.run_git_sentinel("Fixture rejected selector")


@pytest.mark.parametrize("variant", ["empty", "duplicate", "outside", "relative", "not-path"])
def test_explicit_paths_cannot_expand_the_output_set(repo, monkeypatch, variant):
    variants = {
        "empty": (),
        "duplicate": (repo.yaml, repo.yaml),
        "outside": (repo.root / "unrelated.txt",),
        "relative": (Path("../operator.txt"),),
        "not-path": ("PROJECT.md",),
    }

    def forbidden(*args, **kwargs):
        raise AssertionError("invalid path selection must precede Git")

    with monkeypatch.context() as patch:
        patch.setattr(repo.module.subprocess, "run", forbidden)
        with pytest.raises(ValueError):
            repo.module.run_git_sentinel("Fixture invalid selection", paths=variants[variant])


@pytest.mark.parametrize("kind", ["missing", "symlink", "directory", "fifo", "parent-symlink"])
def test_non_regular_or_linked_output_is_rejected(repo, kind):
    if kind == "parent-symlink":
        parent = repo.yaml.parent
        moved = repo.root / "owned-other-ontology"
        parent.rename(moved)
        parent.symlink_to(moved, target_is_directory=True)
    else:
        repo.yaml.unlink()
        if kind == "symlink":
            repo.yaml.symlink_to(repo.root / "unrelated.txt")
        elif kind == "directory":
            repo.yaml.mkdir()
        elif kind == "fifo":
            os.mkfifo(repo.yaml)
    head, index = repo.head(), repo.index()
    with pytest.raises((RuntimeError, OSError)):
        repo.module.run_git_sentinel("Fixture invalid output type")
    assert repo.head() == head and repo.index() == index


def test_new_untracked_output_requires_explicit_review(repo):
    repo.git("rm", "--", "PROJECT.md")
    repo.git("commit", "-m", "Fixture remove optional output")
    project = repo.root / "PROJECT.md"
    project.write_text("new untracked output\n")
    head, index = repo.head(), repo.index()
    with pytest.raises(RuntimeError):
        repo.module.run_git_sentinel("Fixture no implicit add", paths=(project,))
    assert repo.head() == head and repo.index() == index and project.read_text() == "new untracked output\n"


def test_missing_unselected_project_does_not_block_yaml(repo):
    repo.git("rm", "--", "PROJECT.md")
    repo.git("commit", "-m", "Fixture optional project absent")
    repo.mutate()
    result = repo.module.run_git_sentinel("Fixture YAML alone")
    assert result.encode() == repo.head()
    assert repo.changed() == {"cortex/ontology/babylon60_objectives.yaml"}


@pytest.mark.parametrize("mode", ["sparse", "split", "detached", "unborn", "subdirectory"])
def test_unsupported_repository_states_fail_without_staging(repo, monkeypatch, mode):
    if mode == "sparse":
        repo.git("config", "core.sparseCheckout", "true")
    elif mode == "split":
        repo.git("update-index", "--split-index")
    elif mode == "detached":
        repo.git("checkout", "--detach")
    elif mode == "unborn":
        repo.git("symbolic-ref", "HEAD", "refs/heads/fixture-unborn")
    elif mode == "subdirectory":
        nested = repo.root / "nested"
        nested.mkdir()
        monkeypatch.setattr(repo.module, "WORKSPACE_DIR", nested)
        monkeypatch.setattr(repo.module, "YAML_STATE_PATH", nested / "cortex/ontology/babylon60_objectives.yaml")
    repo.mutate()
    index = repo.index()
    with pytest.raises((RuntimeError, subprocess.SubprocessError)):
        repo.module.run_git_sentinel("Fixture unsupported repository")
    assert repo.index() == index


@pytest.mark.parametrize("consumer", ["cmd_add_objective", "cmd_add_milestone", "cmd_update_status", "cmd_iter"])
def test_consumer_failure_never_prints_success_proof(repo, capsys, consumer):
    state = {"objectives": [{"id": "OBJ-001", "title": "Fixture", "status": "PENDING", "milestones": []}]}
    repo.module.save_state(state)
    repo.git("add", "--", "cortex/ontology/babylon60_objectives.yaml")
    repo.git("commit", "-m", "Fixture objective input")
    repo.hook("pre-commit", "exit 1")
    args = SimpleNamespace(
        title="New fixture",
        description="Synthetic",
        exergy=0.1,
        obj_id="OBJ-001",
        due="2026-10-29",
        hash=None,
        type="objective",
        id="OBJ-001",
        status="DONE",
    )
    head, index = repo.head(), repo.index()
    with pytest.raises(ERRORS):
        getattr(repo.module, consumer)(args)
    captured = capsys.readouterr().out
    assert "Proof:" not in captured and "Claim:" not in captured
    assert repo.head() == head and repo.index() == index


@pytest.mark.parametrize("state_changed,project_changed", [(True, False), (False, True), (True, True)])
def test_iter_commits_only_outputs_its_producers_changed(repo, monkeypatch, state_changed, project_changed):
    monkeypatch.setattr(repo.module, "load_state", lambda: {"objectives": []})

    def save(state):
        if state_changed:
            repo.mutate()
        return state_changed

    def project(state):
        if project_changed:
            (repo.root / "PROJECT.md").write_text("generated project\n")
        return project_changed

    monkeypatch.setattr(repo.module, "save_state", save)
    monkeypatch.setattr(repo.module, "update_project_md", project)
    if not state_changed:
        repo.yaml.write_text("unrelated YAML edit\n")
    if not project_changed:
        (repo.root / "PROJECT.md").write_text("unrelated PROJECT edit\n")
    repo.module.cmd_iter(SimpleNamespace())
    expected = ({"cortex/ontology/babylon60_objectives.yaml"} if state_changed else set()) | (
        {"PROJECT.md"} if project_changed else set()
    )
    assert repo.changed() == expected


def test_interleaved_index_change_during_preflight_is_preserved(repo, monkeypatch):
    repo.mutate()
    (repo.root / "unrelated.txt").write_text("another actor prepared this\n")
    original = subprocess.run
    actor_index: list[bytes] = []

    def run(command, **kwargs):
        result = original(command, **kwargs)
        if command[:4] == ["git", "--literal-pathspecs", "diff", "--name-only"] and not actor_index:
            original(["git", "add", "--", "unrelated.txt"], cwd=repo.root, check=True, capture_output=True)
            actor_index.append(repo.index())
        return result

    monkeypatch.setattr(repo.module.subprocess, "run", run)
    head = repo.head()
    with pytest.raises(RuntimeError):
        repo.module.run_git_sentinel("Fixture interleaving")
    assert actor_index and repo.index() == actor_index[0] and repo.head() == head


def test_last_moment_staging_cannot_expand_only_commit(repo, monkeypatch):
    repo.mutate()
    (repo.root / "unrelated.txt").write_text("late staging by another actor\n")
    original = subprocess.run
    events = []

    def run(command, **kwargs):
        if command[:3] == ["git", "--literal-pathspecs", "commit"]:
            original(["git", "add", "--", "unrelated.txt"], cwd=repo.root, check=True, capture_output=True)
            events.append("actor staged")
        return original(command, **kwargs)

    monkeypatch.setattr(repo.module.subprocess, "run", run)
    result = repo.module.run_git_sentinel("Fixture last moment staging")
    assert events == ["actor staged"] and result.encode() == repo.head()
    assert repo.changed() == {"cortex/ontology/babylon60_objectives.yaml"}
    assert repo.git("diff", "--cached", "--name-only", "-z").stdout == b"unrelated.txt\0"


def test_binary_unrelated_edits_remain_outside_commit(repo):
    name = "binary-Ω.dat"  # macOS filenames require valid UTF-8; contents remain arbitrary bytes.
    binary = repo.root / name
    binary.write_bytes(b"\x00\xffinitial")
    repo.git("add", "--", name)
    repo.git("commit", "-m", "Fixture binary baseline")
    binary.write_bytes(b"\x00\xfemodified")
    repo.mutate()
    repo.module.run_git_sentinel("Fixture binary-safe Git inspection")
    assert repo.changed() == {"cortex/ontology/babylon60_objectives.yaml"}
    assert binary.read_bytes() == b"\x00\xfemodified"


def test_bounded_repeated_commits_preserve_narrow_scope(repo):
    # One warmup then eight sequential mutations, not a performance/parallelism claim.
    for number in range(9):
        repo.yaml.write_text(f"objectives: [fixture-{number}]\n")
        value = repo.module.run_git_sentinel(f"Fixture repetition {number}")
        assert value.encode() == repo.head()
        assert repo.changed() == {"cortex/ontology/babylon60_objectives.yaml"}


def test_linked_worktree_uses_its_own_index_and_head(repo, monkeypatch):
    linked = repo.root.parent / "linked fixture worktree"
    repo.git("worktree", "add", "-b", "fixture-linked", str(linked))
    original_head, original_index = repo.head(), repo.index()
    yaml = linked / "cortex/ontology/babylon60_objectives.yaml"
    monkeypatch.setattr(repo.module, "WORKSPACE_DIR", linked)
    monkeypatch.setattr(repo.module, "YAML_STATE_PATH", yaml)
    monkeypatch.setattr(repo.module, "PROJECT_MD_PATH", linked / "PROJECT.md")
    yaml.write_text("objectives: [linked-fixture]\n")
    value = repo.module.run_git_sentinel("Fixture linked worktree")
    observed = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=linked, capture_output=True, check=True, timeout=10
    ).stdout.strip()
    assert value.encode() == observed and observed != original_head
    assert repo.head() == original_head and repo.index() == original_index
