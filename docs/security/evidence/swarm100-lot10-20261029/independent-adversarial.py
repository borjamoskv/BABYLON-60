"""Independent scoped-cleanup fixtures; never purge the actual workspace."""
from contextlib import redirect_stdout
import hashlib
from importlib.util import MAGIC_NUMBER
import importlib.util
import io
import json
import marshal
import os
from pathlib import Path
import shutil
import socket
import sqlite3
import subprocess
import sys
import tempfile
from types import SimpleNamespace
from unittest.mock import patch

ROOT = Path(__file__).absolute().parents[4]
SOURCE = ROOT / "scripts/c5_verifiers/purge_residuals.py"
TEST = ROOT / "tests/test_swarm100_lot10_regressions.py"
sys.dont_write_bytecode = True


def hashes():
    return {str(path.relative_to(ROOT)): hashlib.sha256(path.read_bytes()).hexdigest() for path in (SOURCE, TEST)}


def bytecode(flags=0):
    return MAGIC_NUMBER + flags.to_bytes(4, "little") + b"\0" * 8 + marshal.dumps(compile("fixture_value = 1\n", "owned-fixture.py", "exec"))


def image(path):
    stat = path.stat()
    return (stat.st_dev, stat.st_ino, path.read_bytes())


def main():
    before = hashes()
    old_env, old_cwd = dict(os.environ), Path.cwd()
    real_run = subprocess.run
    checks, forbidden_calls = [], []
    fixture_count = [0]

    def forbidden(*args, **kwargs):
        forbidden_calls.append("unexpected verifier/network/process")
        raise AssertionError("Operation outside scoped cleanup fixture")

    try:
        with tempfile.TemporaryDirectory(prefix="lot10-independent-") as temporary:
            boundary = Path(temporary).resolve()
            home = boundary / "home"
            home.mkdir()
            os.environ.clear()
            os.environ.update(HOME=str(home), XDG_CONFIG_HOME=str(home / "xdg"), PATH="/usr/bin:/bin",
                              GIT_CONFIG_GLOBAL=str(home / "empty-config"), GIT_CONFIG_NOSYSTEM="1",
                              GIT_TERMINAL_PROMPT="0", LC_ALL="C", PYTHONDONTWRITEBYTECODE="1")
            os.chdir(boundary)

            class Fixture:
                def __init__(self):
                    fixture_count[0] += 1
                    self.root = boundary / f"owned workspace {fixture_count[0]}"
                    self.root.mkdir()
                    copied = boundary / f"purge-{fixture_count[0]}.py"
                    shutil.copyfile(SOURCE, copied)
                    spec = importlib.util.spec_from_file_location(f"independent_lot10_{fixture_count[0]}", copied)
                    self.module = importlib.util.module_from_spec(spec)
                    sys.modules[spec.name] = self.module
                    spec.loader.exec_module(self.module)
                    self.module.REPO_ROOT = self.root
                    # Isolate filesystem doubles from the stdlib used by fixture cleanup.
                    self.module.os = SimpleNamespace(**{name: getattr(os, name) for name in dir(os) if not name.startswith("__")})

                def run(self):
                    assert self.module.REPO_ROOT.absolute().is_relative_to(boundary)
                    with patch.object(socket.socket, "connect", forbidden), patch.object(socket.socket, "connect_ex", forbidden), \
                            patch.object(socket, "getaddrinfo", forbidden), patch.object(subprocess, "Popen", forbidden), \
                            patch.dict(sys.modules, {"verify_agent_ontological_value": SimpleNamespace(verify_va=forbidden)}):
                        return self.module.purge_repository_residuals()

                def make(self, relative, data):
                    target = self.root / relative
                    target.parent.mkdir(parents=True, exist_ok=True)
                    target.write_bytes(data)
                    return target

                def git(self, *args, check=True):
                    assert self.root.is_relative_to(boundary)
                    assert args[0] in ("init", "add")
                    return real_run(["/usr/bin/git", *args], cwd=self.root, capture_output=True, check=check, timeout=10)

            f = Fixture()
            f.git("init", "-b", "main")
            f.make("README.md", b"owned fixture")
            locks = [f.root / ".git/index.lock", f.root / ".git/packed-refs.lock"]
            descriptors = [os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600) for path in locks]
            try:
                for fd, path in zip(descriptors, locks):
                    os.write(fd, b"active owned lock")
                    os.utime(path, (42, 42))
                snapshots = [image(path) for path in locks]
                assert f.git("add", "--", "README.md", check=False).returncode != 0
                report = f.run()
                assert [image(path) for path in locks] == snapshots
                assert f.git("add", "--", "README.md", check=False).returncode != 0
                assert not report["deleted"] and report["verification"] == "NOT_REQUESTED"
            finally:
                for fd in descriptors:
                    os.close(fd)
            checks.append(dict(name="active_old_git_locks_and_mutual_exclusion_preserved", passed=True, locks=2))

            for location in ("scratch/active.db", "mixed/__pycache__/renamed.pyc"):
                f = Fixture()
                db = f.root / location
                db.parent.mkdir(parents=True)
                connection = sqlite3.connect(db)
                try:
                    connection.execute("PRAGMA journal_mode=WAL")
                    connection.execute("CREATE TABLE owned_fixture(value TEXT)")
                    connection.execute("INSERT INTO owned_fixture VALUES ('preserved')")
                    connection.commit()
                    paths = [db, Path(str(db) + "-wal"), Path(str(db) + "-shm")]
                    initial = [image(path) for path in paths]
                    report = f.run()
                    assert [image(path) for path in paths] == initial
                    assert connection.execute("SELECT value FROM owned_fixture").fetchone() == ("preserved",)
                    assert not report["deleted"]
                finally:
                    connection.close()
            checks.append(dict(name="live_sqlite_wal_shm_preserved_in_scratch_and_misnamed_cache", passed=True, cases=2))

            f = Fixture()
            recognized = [f.make(f"pkg/__pycache__/known{flags}.pyc", bytecode(flags)) for flags in (0, 1, 3)]
            keep = [f.make("outside.pyc", bytecode()), f.make("pkg/__pycache__/truncated.pyc", MAGIC_NUMBER + b"\0" * 12),
                    f.make("pkg/__pycache__/invalid.pyc", bytecode(2)), f.make("pkg/__pycache__/unknown.pyc", b"not bytecode"),
                    f.make("pkg/__pycache__/notes.db.txt", b"preserve database-like name"),
                    f.make("pkg/__pycache__/current.lock.pyc", bytecode()), f.make("pkg/__pycache__/.DS_Store", b"opaque metadata"),
                    f.make(".pytest_cache/__pycache__/owned.pyc", bytecode()), f.make("scratch/__pycache__/owned.pyc", bytecode()),
                    f.make(".venv/__pycache__/owned.pyc", bytecode())]
            initial = [image(path) for path in keep]
            report = f.run()
            assert {item["path"] for item in report["deleted"]} == {str(path.relative_to(f.root)) for path in recognized}
            assert not any(path.exists() for path in recognized)
            assert [image(path) for path in keep] == initial
            assert (f.root / "pkg/__pycache__").is_dir() and report["status"] == "SCOPED_OK"
            checks.append(dict(name="only_recognized_current_bytecode_deleted_precise_report", passed=True, deleted=3, preserved_fixtures=len(keep)))

            f = Fixture()
            outside = boundary / "outside selected root"
            outside.mkdir()
            target = outside / "target.pyc"
            target.write_bytes(bytecode())
            (f.root / "linked_dir").symlink_to(outside, target_is_directory=True)
            cache = f.root / "pkg/__pycache__"
            cache.mkdir(parents=True)
            (cache / "link.pyc").symlink_to(target)
            os.mkfifo(cache / "pipe.pyc")
            shared = cache / "shared.pyc"
            os.link(target, shared)
            before_target = image(target)
            report = f.run()
            assert image(target) == before_target and shared.exists() and (cache / "link.pyc").is_symlink()
            assert not report["deleted"] and report["status"] == "SCOPED_OK"
            checks.append(dict(name="symlinks_fifo_hardlinks_and_external_target_preserved", passed=True))

            f = Fixture()
            candidate = f.make("__pycache__/foreign.pyc", bytecode())
            f.module.os.getuid = lambda: os.getuid() + 1
            report = f.run()
            assert candidate.exists() and not report["deleted"]
            assert any(item["reason"] == "SHARED_OR_FOREIGN_FILE" for item in report["preserved"])
            checks.append(dict(name="foreign_owner_candidate_preserved", passed=True))

            for kind in ("bare", "worktree"):
                f = Fixture()
                metadata = f.root / "arbitrary metadata name"
                (metadata / "__pycache__").mkdir(parents=True)
                (metadata / "HEAD").write_text("synthetic fixture metadata")
                for marker in (("objects", "refs") if kind == "bare" else ("commondir", "gitdir")):
                    (metadata / marker).write_text("synthetic owned marker")
                candidate = metadata / "__pycache__/metadata.pyc"
                candidate.write_bytes(bytecode())
                (f.root / ".git").write_text("gitdir: arbitrary metadata name\n")
                report = f.run()
                assert candidate.exists() and not report["deleted"]
                assert any(item["reason"] == "GIT_METADATA_SUBTREE" for item in report["preserved"])
                f.module.REPO_ROOT = metadata
                assert not f.run()["deleted"] and candidate.exists()
            checks.append(dict(name="git_file_and_alternate_named_metadata_subtrees_preserved", passed=True, cases=2))

            f = Fixture()
            candidate = f.make("__pycache__/denied.pyc", bytecode())

            def deny(*args, **kwargs):
                raise PermissionError("synthetic fixture error")

            f.module.os.unlink = deny
            report = f.run()
            assert candidate.exists() and not report["deleted"] and report["status"] == "ERROR"
            assert any(item["reason"] == "PermissionError" for item in report["errors"])
            output = io.StringIO()
            with redirect_stdout(output):
                assert f.module.main(["--json"]) == 1
            assert json.loads(output.getvalue())["status"] == "ERROR"
            checks.append(dict(name="unlink_failure_reported_without_false_deletion_and_cli_nonzero", passed=True))

            f = Fixture()
            candidate = f.make("__pycache__/changed.pyc", bytecode())
            original_open = f.module.os.open
            switched = []

            def replace_before_open(path, flags, **kwargs):
                if path == "changed.pyc" and not switched:
                    candidate.rename(candidate.with_name("original-preserved.bin"))
                    candidate.write_bytes(b"replacement unowned data")
                    switched.append(True)
                return original_open(path, flags, **kwargs)

            f.module.os.open = replace_before_open
            report = f.run()
            assert switched and candidate.read_bytes() == b"replacement unowned data" and not report["deleted"]
            assert any(item["reason"] == "IDENTITY_CHANGED" for item in report["preserved"])
            checks.append(dict(name="replacement_before_open_preserved_by_identity_check", passed=True))

            f = Fixture()
            candidate = f.make("__pycache__/rewritten.pyc", bytecode())
            original_read = f.module.os.read
            modified = []

            def rewrite_after_read(fd, size):
                data = original_read(fd, size)
                if not modified:
                    candidate.write_bytes(b"SQLite format 3\0modified fixture")
                    modified.append(True)
                return data

            f.module.os.read = rewrite_after_read
            report = f.run()
            assert modified and candidate.read_bytes().startswith(b"SQLite format 3\0") and not report["deleted"]
            assert any(item["reason"] == "IDENTITY_CHANGED" for item in report["preserved"])
            checks.append(dict(name="content_change_after_read_preserved_before_unlink", passed=True))

            for budget in ("MAX_ENTRIES", "MAX_DEPTH"):
                f = Fixture()
                candidate = f.make("__pycache__/budget.pyc", bytecode())
                setattr(f.module, budget, 0)
                report = f.run()
                assert candidate.exists() and report["status"] == "ERROR" and not report["deleted"]
                assert report["errors"]
            checks.append(dict(name="scan_budgets_stop_with_explicit_errors", passed=True, cases=2))

            f = Fixture()
            f.module.REPO_ROOT = f.root / "missing"
            assert f.run()["status"] == "ERROR"
            alias = boundary / "root symlink"
            alias.symlink_to(f.root, target_is_directory=True)
            f.module.REPO_ROOT = alias
            assert f.run()["status"] == "ERROR"
            checks.append(dict(name="missing_and_symlink_roots_fail_closed", passed=True, cases=2))
            assert not forbidden_calls
    finally:
        os.chdir(old_cwd)
        os.environ.clear()
        os.environ.update(old_env)
    after = hashes()
    assert before[str(SOURCE.relative_to(ROOT))] == after[str(SOURCE.relative_to(ROOT))]
    print(json.dumps(dict(reviewer="03", status="PASS", checks=checks, check_count=len(checks), fixtures=fixture_count[0],
                          forbidden_calls=forbidden_calls, source_sha256_before=before, source_sha256_after=after,
                          scope="Only owned temporary roots; open Git locks and live SQLite fixtures; no actual-project purge, operator databases, network, hardware or automatic verifier execution."), indent=2))


if __name__ == "__main__":
    main()
