"""Residual cleanup checks: owned temporary filesystem, Git and SQLite only."""

import importlib.util
import os
from pathlib import Path
import shutil
import socket
import sqlite3
import subprocess
import sys
from types import SimpleNamespace

import pytest

ROOT = Path(__file__).absolute().parents[1]
SOURCE = ROOT / "scripts/c5_verifiers/purge_residuals.py"


@pytest.fixture
def fixture(tmp_path, monkeypatch):
    root = tmp_path / "owned workspace"
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
    (root / "README.md").write_text("owned fixture\n")
    copied = tmp_path / "fixture_purge.py"
    shutil.copyfile(SOURCE, copied)
    spec = importlib.util.spec_from_file_location("lot10_purge_fixture", copied)
    module = importlib.util.module_from_spec(spec)
    monkeypatch.setitem(sys.modules, spec.name, module)
    spec.loader.exec_module(module)
    monkeypatch.setattr(module, "REPO_ROOT", root)
    verifier_calls = []
    monkeypatch.setitem(
        sys.modules,
        "verify_agent_ontological_value",
        SimpleNamespace(verify_va=lambda: verifier_calls.append("fixture only")),
    )

    def forbidden(*args, **kwargs):
        raise AssertionError("network forbidden in residual-purge fixture")

    monkeypatch.setattr(socket.socket, "connect", forbidden)
    monkeypatch.setattr(socket.socket, "connect_ex", forbidden)
    monkeypatch.setattr(socket, "getaddrinfo", forbidden)
    return SimpleNamespace(root=root, module=module, git=git, verifier_calls=verifier_calls, tmp=tmp_path)


@pytest.mark.parametrize("name", ["index.lock", "packed-refs.lock"])
def test_c0574_preserves_open_git_lock_inode_and_contents(fixture, name):
    lock = fixture.root / ".git" / name
    descriptor = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    try:
        os.write(descriptor, b"owned active fixture lock")
        os.utime(lock, (42, 42))  # Old timestamp does not grant deletion authority.
        before = lock.stat()
        fixture.module.purge_repository_residuals()
        assert lock.exists()
        assert (lock.stat().st_dev, lock.stat().st_ino) == (before.st_dev, before.st_ino)
        assert lock.read_bytes() == b"owned active fixture lock"
    finally:
        os.close(descriptor)


def test_c0574_preserves_git_exclusion_while_lock_descriptor_is_open(fixture):
    lock = fixture.root / ".git/index.lock"
    descriptor = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    try:
        before = fixture.git("add", "--", "README.md", check=False)
        assert before.returncode != 0
        fixture.module.purge_repository_residuals()
        after = fixture.git("add", "--", "README.md", check=False)
        assert after.returncode != 0, "lock deletion let a competing Git update succeed"
        assert lock.exists()
    finally:
        os.close(descriptor)


def test_c0575_preserves_live_sqlite_database_wal_and_shm(fixture):
    scratch = fixture.root / "scratch"
    scratch.mkdir()
    database = scratch / "active.db"
    connection = sqlite3.connect(database)
    try:
        connection.execute("PRAGMA journal_mode=WAL")
        connection.execute("PRAGMA synchronous=FULL")
        connection.execute("CREATE TABLE fixture(value TEXT)")
        connection.execute("INSERT INTO fixture VALUES ('owned temporary data')")
        connection.commit()
        paths = [database, Path(str(database) + "-wal"), Path(str(database) + "-shm")]
        before = {path: (path.stat().st_ino, path.read_bytes()) for path in paths}
        fixture.module.purge_repository_residuals()
        for path, (inode, content) in before.items():
            assert path.exists(), path.name
            assert path.stat().st_ino == inode and path.read_bytes() == content
        assert connection.execute("SELECT value FROM fixture").fetchone() == ("owned temporary data",)
    finally:
        connection.close()


@pytest.mark.parametrize("name", ["keep.db.backup", "notes.db.txt", "foreign.db-wal"])
def test_c0575_preserves_unowned_database_lookalikes(fixture, name):
    scratch = fixture.root / "scratch"
    scratch.mkdir()
    target = scratch / name
    target.write_bytes(b"owned fixture sentinel, not disposable by extension")
    before = target.stat().st_ino
    fixture.module.purge_repository_residuals()
    assert target.exists() and target.stat().st_ino == before
    assert target.read_bytes() == b"owned fixture sentinel, not disposable by extension"


def test_c0575_cache_directory_is_not_authority_to_delete_database(fixture):
    cache = fixture.root / ".pytest_cache"
    cache.mkdir()
    database = cache / "active.db"
    database.write_bytes(b"owned fixture data requiring preservation")
    fixture.module.purge_repository_residuals()
    assert database.exists() and database.read_bytes() == b"owned fixture data requiring preservation"


def test_report_does_not_certify_zero_entropy(fixture, capsys):
    fixture.module.purge_repository_residuals()
    output = capsys.readouterr().out
    assert "0% ENTROP" not in output
    assert "REPOSITORIO LIBRE" not in output


def bytecode(fixture, relative="pkg/__pycache__/fixture.pyc"):
    import py_compile

    source = fixture.tmp / "owned_fixture_input.py"
    source.write_text("ANSWER = 42\n")
    target = fixture.root / relative
    target.parent.mkdir(parents=True, exist_ok=True)
    py_compile.compile(str(source), cfile=str(target), doraise=True)
    return target


def test_recognized_bytecode_is_deleted_and_report_matches_effect(fixture):
    target = bytecode(fixture)
    parent_inode = target.parent.stat().st_ino
    report = fixture.module.purge_repository_residuals()
    assert not target.exists()
    assert target.parent.stat().st_ino == parent_inode
    assert report["status"] == "SCOPED_OK" and report["errors"] == []
    assert report["deleted"] == [{"path": "pkg/__pycache__/fixture.pyc", "reason": "CURRENT_PYTHON_BYTECODE_HEADER"}]
    assert report["verification"] == "NOT_REQUESTED" and fixture.verifier_calls == []


def test_second_cleanup_is_idempotent(fixture):
    bytecode(fixture)
    first = fixture.module.purge_repository_residuals()
    second = fixture.module.purge_repository_residuals()
    assert len(first["deleted"]) == 1 and second["deleted"] == []
    assert second["status"] == "SCOPED_OK"


@pytest.mark.parametrize(
    "relative",
    [
        "outside.pyc",
        ".DS_Store",
        "pkg/__pycache__/legacy.pyo",
        ".pytest_cache/__pycache__/cached.pyc",
        ".ruff_cache/__pycache__/cached.pyc",
        ".mypy_cache/__pycache__/cached.pyc",
        "scratch/__pycache__/cached.pyc",
        ".venv/__pycache__/cached.pyc",
        "node_modules/__pycache__/cached.pyc",
    ],
)
def test_unknown_or_excluded_cache_data_is_preserved(fixture, relative):
    target = bytecode(fixture, relative)
    before = target.read_bytes()
    report = fixture.module.purge_repository_residuals()
    assert target.read_bytes() == before and report["deleted"] == []


@pytest.mark.parametrize(
    "name",
    [
        "index.lock",
        "packed-refs.lock",
        "module.lock.pyc",
        "cache.db.pyc",
        "cache.db-wal",
        "cache.db-shm",
        "notes.db.backup.pyc",
        "cache.sqlite3.pyc",
        "cache.journal.pyc",
        "foreign-wal",
        "foreign-shm",
        "foreign-journal",
    ],
)
def test_protected_names_survive_even_with_valid_bytecode_header(fixture, name):
    target = bytecode(fixture, "pkg/__pycache__/" + name)
    before = target.read_bytes()
    report = fixture.module.purge_repository_residuals()
    assert target.read_bytes() == before and report["deleted"] == []


@pytest.mark.parametrize("variant", ["empty", "short", "wrong-magic", "bad-flags-2", "bad-flags-4", "header-only"])
def test_unrecognized_bytecode_is_preserved(fixture, variant):
    target = bytecode(fixture)
    valid = target.read_bytes()
    values = {
        "empty": b"",
        "short": valid[:6],
        "wrong-magic": b"NOPE" + valid[4:],
        "bad-flags-2": valid[:4] + (2).to_bytes(4, "little") + valid[8:],
        "bad-flags-4": valid[:4] + (4).to_bytes(4, "little") + valid[8:],
        "header-only": valid[:16],
    }
    target.write_bytes(values[variant])
    report = fixture.module.purge_repository_residuals()
    assert target.read_bytes() == values[variant] and report["deleted"] == []
    assert any(row["reason"] == "UNRECOGNIZED_BYTECODE_HEADER" for row in report["preserved"])


def test_database_disguised_as_bytecode_is_preserved(fixture):
    cache = fixture.root / "pkg/__pycache__"
    cache.mkdir(parents=True)
    target = cache / "ordinary.pyc"
    with sqlite3.connect(target) as connection:
        connection.execute("PRAGMA synchronous=FULL")
        connection.execute("CREATE TABLE fixture(value)")
        connection.execute("INSERT INTO fixture VALUES (42)")
    before = target.read_bytes()
    report = fixture.module.purge_repository_residuals()
    assert target.read_bytes() == before and report["deleted"] == []
    with sqlite3.connect(target) as connection:
        assert connection.execute("SELECT value FROM fixture").fetchone() == (42,)


def test_hardlink_bytecode_is_preserved(fixture):
    target = bytecode(fixture)
    alias = fixture.tmp / "owned-hardlink.pyc"
    os.link(target, alias)
    before = alias.read_bytes()
    report = fixture.module.purge_repository_residuals()
    assert target.exists() and alias.read_bytes() == before and report["deleted"] == []
    assert any(row["reason"] == "SHARED_OR_FOREIGN_FILE" for row in report["preserved"])


def test_foreign_owner_policy_preserves_candidate(fixture, monkeypatch):
    target = bytecode(fixture)
    actual = os.getuid()
    monkeypatch.setattr(fixture.module.os, "getuid", lambda: actual + 1)
    report = fixture.module.purge_repository_residuals()
    assert target.exists() and report["deleted"] == []


@pytest.mark.parametrize("kind", ["file-symlink", "cache-symlink", "directory-symlink", "fifo"])
def test_symlinks_and_special_files_are_preserved_without_following(fixture, kind):
    outside = fixture.tmp / "outside-owned"
    outside.mkdir()
    sentinel = outside / "do-not-delete.pyc"
    sentinel.write_bytes(b"owned external data")
    if kind == "file-symlink":
        cache = fixture.root / "__pycache__"
        cache.mkdir()
        target = cache / "linked.pyc"
        target.symlink_to(sentinel)
    elif kind == "cache-symlink":
        target = fixture.root / "__pycache__"
        target.symlink_to(outside, target_is_directory=True)
    elif kind == "directory-symlink":
        target = fixture.root / "linked"
        target.symlink_to(outside, target_is_directory=True)
    else:
        cache = fixture.root / "__pycache__"
        cache.mkdir()
        target = cache / "pipe.pyc"
        os.mkfifo(target)
    report = fixture.module.purge_repository_residuals()
    assert os.path.lexists(target) and sentinel.read_bytes() == b"owned external data"
    assert report["deleted"] == []


def test_symlink_root_fails_without_purging_target(fixture, monkeypatch):
    target = bytecode(fixture)
    link = fixture.tmp / "linked-root"
    link.symlink_to(fixture.root, target_is_directory=True)
    monkeypatch.setattr(fixture.module, "REPO_ROOT", link)
    report = fixture.module.purge_repository_residuals()
    assert report["status"] == "ERROR" and report["deleted"] == [] and target.exists()


@pytest.mark.parametrize("kind", ["bare-shape", "worktree-shape", "actual-gitdir"])
def test_metadata_roots_with_alternative_names_are_excluded(fixture, monkeypatch, kind):
    if kind == "actual-gitdir":
        selected = fixture.root / ".git"
        target = bytecode(fixture, ".git/hooks/__pycache__/cached.pyc")
    else:
        selected = fixture.root / "alternate-metadata"
        selected.mkdir()
        (selected / "HEAD").write_text("ref: refs/heads/main\n")
        if kind == "bare-shape":
            (selected / "objects").mkdir()
            (selected / "refs").mkdir()
        else:
            (selected / "commondir").write_text("../outside-metadata\n")
            (selected / "gitdir").write_text("../worktree/.git\n")
        target = bytecode(fixture, "alternate-metadata/hooks/__pycache__/cached.pyc")
    monkeypatch.setattr(fixture.module, "REPO_ROOT", selected)
    before = target.read_bytes()
    report = fixture.module.purge_repository_residuals()
    assert target.read_bytes() == before and report["deleted"] == []
    assert report["preserved"] == [{"path": ".", "reason": "GIT_METADATA_SUBTREE"}]


def test_nested_metadata_and_worktree_pointer_are_preserved(fixture):
    (fixture.root / ".git").rename(fixture.root / "metadata-store")
    (fixture.root / ".git").write_text("gitdir: metadata-store\n")
    target = bytecode(fixture, "metadata-store/hooks/__pycache__/cached.pyc")
    before = target.read_bytes()
    report = fixture.module.purge_repository_residuals()
    assert target.read_bytes() == before and report["deleted"] == []
    assert (fixture.root / ".git").read_text() == "gitdir: metadata-store\n"


def test_linked_worktree_does_not_follow_external_common_dir(fixture, monkeypatch):
    fixture.git("config", "user.name", "Cleanup Fixture")
    fixture.git("config", "user.email", "fixture@example.invalid")
    fixture.git("config", "commit.gpgsign", "false")
    fixture.git("add", "--", "README.md")
    fixture.git("commit", "-m", "Fixture initial state")
    linked = fixture.tmp / "linked fixture worktree"
    fixture.git("worktree", "add", "-b", "fixture-cleanup-linked", str(linked))
    lock = fixture.root / ".git/packed-refs.lock"
    lock.write_bytes(b"external common-dir lock")
    target = bytecode(fixture)
    moved = linked / "__pycache__/fixture.pyc"
    moved.parent.mkdir()
    target.rename(moved)
    monkeypatch.setattr(fixture.module, "REPO_ROOT", linked)
    report = fixture.module.purge_repository_residuals()
    assert not moved.exists() and len(report["deleted"]) == 1
    assert lock.read_bytes() == b"external common-dir lock"
    assert (linked / ".git").is_file()


def test_unlink_failure_is_reported_without_false_deletion(fixture, monkeypatch):
    target = bytecode(fixture)

    def denied(*args, **kwargs):
        raise PermissionError("owned fixture denied")

    with monkeypatch.context() as patch:
        patch.setattr(fixture.module.os, "unlink", denied)
        report = fixture.module.purge_repository_residuals()
    assert target.exists() and report["deleted"] == [] and report["status"] == "ERROR"
    assert report["errors"] == [{"path": "pkg/__pycache__/fixture.pyc", "reason": "PermissionError"}]


def test_scan_failure_is_reported_and_main_returns_nonzero(fixture, monkeypatch, capsys):
    target = bytecode(fixture)

    def denied(*args, **kwargs):
        raise PermissionError("owned fixture denied")

    with monkeypatch.context() as patch:
        patch.setattr(fixture.module.os, "scandir", denied)
        status = fixture.module.main(["--json"])
    import json

    report = json.loads(capsys.readouterr().out)
    assert status == 1 and report["status"] == "ERROR" and report["deleted"] == [] and target.exists()


@pytest.mark.parametrize("limit", ["MAX_ENTRIES", "MAX_DEPTH"])
def test_traversal_budget_error_does_not_claim_complete_cleanup(fixture, monkeypatch, limit):
    target = bytecode(fixture)
    monkeypatch.setattr(fixture.module, limit, 0)
    report = fixture.module.purge_repository_residuals()
    assert report["status"] == "ERROR" and report["deleted"] == [] and target.exists()


def test_file_replaced_by_symlink_before_open_is_not_followed(fixture, monkeypatch):
    target = bytecode(fixture)
    outside = fixture.tmp / "owned-external-data"
    outside.write_bytes(b"external data")
    original = os.open
    seen = []

    def opening(path, flags, *args, **kwargs):
        if path == "fixture.pyc" and kwargs.get("dir_fd") is not None and not seen:
            target.unlink()
            target.symlink_to(outside)
            seen.append(True)
        return original(path, flags, *args, **kwargs)

    with monkeypatch.context() as patch:
        patch.setattr(fixture.module.os, "open", opening)
        report = fixture.module.purge_repository_residuals()
    assert seen and target.is_symlink() and outside.read_bytes() == b"external data"
    assert report["deleted"] == [] and report["errors"]


def test_content_mutation_during_read_is_preserved(fixture, monkeypatch):
    target = bytecode(fixture)
    original = os.read
    seen = []

    def reading(descriptor, size):
        value = original(descriptor, size)
        if size == 17 and not seen:
            target.write_bytes(b"concurrent owned fixture mutation")
            seen.append(True)
        return value

    with monkeypatch.context() as patch:
        patch.setattr(fixture.module.os, "read", reading)
        report = fixture.module.purge_repository_residuals()
    assert target.read_bytes() == b"concurrent owned fixture mutation"
    assert report["deleted"] == [] and any(row["reason"] == "IDENTITY_CHANGED" for row in report["preserved"])


def test_api_does_not_invoke_other_verifier(fixture):
    bytecode(fixture)
    report = fixture.module.purge_repository_residuals()
    assert fixture.verifier_calls == [] and report["verification"] == "NOT_REQUESTED"


@pytest.mark.parametrize("json_output", [False, True])
def test_cli_runs_only_copied_script_in_owned_root(fixture, json_output):
    target = bytecode(fixture)
    copied = fixture.root / "scripts/c5_verifiers/purge_residuals.py"
    copied.parent.mkdir(parents=True)
    shutil.copyfile(SOURCE, copied)
    result = subprocess.run(
        [sys.executable, str(copied), *(["--json"] if json_output else [])],
        cwd=fixture.root,
        env={"HOME": str(fixture.tmp / "home"), "PATH": "/usr/bin:/bin"},
        capture_output=True,
        timeout=10,
    )
    assert result.returncode == 0 and not target.exists(), result.stderr
    assert b"0% ENTROP" not in result.stdout and b"REPOSITORIO LIBRE" not in result.stdout
    if json_output:
        import json

        report = json.loads(result.stdout)
        assert report["schema"] == "babylon60.residual-cleanup.v2" and report["status"] == "SCOPED_OK"
        assert len(report["deleted"]) == 1 and report["verification"] == "NOT_REQUESTED"
    else:
        assert b"Deleted files: 1" in result.stdout
