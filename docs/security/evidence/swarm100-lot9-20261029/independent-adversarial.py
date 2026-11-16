"""Independent Lot 9 Git checks, owned temporary repositories and audit doubles only."""
from contextlib import redirect_stdout
import hashlib
import importlib.util
import io
import json
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
SOURCE = ROOT / "scripts/c5_thermo/c5_exergy_optimizer_monitor.py"
TEST = ROOT / "tests/test_swarm100_lot9_regressions.py"
GIT = "/usr/bin/git"
sys.dont_write_bytecode = True


def hashes():
    return {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in (SOURCE, TEST)}


def rejected(callback):
    try:
        callback()
    except (RuntimeError, ValueError, OSError, subprocess.SubprocessError) as error:
        return type(error).__name__
    raise AssertionError("Unexpected success")


def main():
    before = hashes()
    old_env, old_cwd = dict(os.environ), Path.cwd()
    real_run = subprocess.run
    checks, commands = [], []
    sequence = [0]

    def forbidden(*args, **kwargs):
        raise AssertionError("Database/network/kill forbidden in independent fixture")

    try:
        with tempfile.TemporaryDirectory(prefix="lot9-independent-") as temporary:
            boundary = Path(temporary).resolve()
            home = boundary / "home"
            home.mkdir()
            os.environ.clear()
            os.environ.update(HOME=str(home), XDG_CONFIG_HOME=str(home / "xdg"), PATH="/usr/bin:/bin",
                              GIT_CONFIG_GLOBAL=str(home / "empty-config"), GIT_CONFIG_NOSYSTEM="1",
                              GIT_TERMINAL_PROMPT="0", LC_ALL="C", PYTHONDONTWRITEBYTECODE="1")
            os.chdir(boundary)

            def guarded_run(command, **kwargs):
                cwd = Path(kwargs["cwd"]).resolve()
                assert cwd.is_relative_to(boundary) and cwd != boundary
                assert command[0] in ("git", GIT)
                args = [arg for arg in command[1:] if arg != "--literal-pathspecs"]
                assert args[0] in {"init", "config", "add", "commit", "rev-parse", "symbolic-ref", "ls-files", "diff",
                                   "diff-tree", "rev-list", "show", "update-index", "update-ref"}
                assert not any(arg in {"--no-verify", "--amend", "reset", "push", "fetch", "pull", "clone", "clean"} for arg in args)
                env = kwargs.get("env", os.environ)
                assert env["HOME"] == str(home) and env["GIT_CONFIG_NOSYSTEM"] == "1"
                assert env["GIT_CONFIG_GLOBAL"] == str(home / "empty-config")
                commands.append(args)
                kwargs["timeout"] = 10
                return real_run([GIT, *command[1:]], **kwargs)

            class Fixture:
                def __init__(self):
                    sequence[0] += 1
                    self.root = boundary / f"monitor fixture {sequence[0]}"
                    self.root.mkdir()
                    self.git("init", "-b", "main")
                    self.git("config", "user.name", "Independent Monitor Fixture")
                    self.git("config", "user.email", "fixture@example.invalid")
                    self.git("config", "commit.gpgsign", "false")
                    self.status = self.root / "STATUS.md"
                    self.status.write_text("# Fixture status\nHistorical `[PENDING]` marker\n")
                    (self.root / "foreign.txt").write_text("foreign original\n")
                    self.git("add", "--", "STATUS.md", "foreign.txt")
                    self.git("commit", "-m", "Initial fixture")
                    copied = boundary / f"monitor-{sequence[0]}.py"
                    shutil.copyfile(SOURCE, copied)
                    spec = importlib.util.spec_from_file_location(f"lot9_independent_{sequence[0]}", copied)
                    self.module = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(self.module)
                    self.module.ROOT_DIR = self.root
                    self.module.STATUS_FILE = self.status
                    self.module.subprocess = SimpleNamespace(run=guarded_run, CalledProcessError=subprocess.CalledProcessError)
                    self.module.audit_git_entropy = lambda: dict(head="FIXTURE", branch="main", commits=1, last_tag="NONE", dirty_count=0, dirty_files=[])
                    self.module.audit_db_census = lambda: {}
                    self.module.audit_ruff = lambda: dict(total_errors=0, fixable=0)
                    self.module.audit_tests = lambda: dict(test_files=0, status="FIXTURE_ONLY", passed=0)

                def git(self, *args):
                    return guarded_run([GIT, *args], cwd=self.root, capture_output=True, check=True)

                def head(self):
                    return self.git("rev-parse", "HEAD").stdout.strip()

                def index(self):
                    return (self.root / ".git/index").read_bytes()

                def mutate(self):
                    self.status.write_text(self.status.read_text() + "independent generated row\n")

                def commit(self):
                    return self.module.git_sentinel_commit("a" * 64)

                def hook(self, name, content):
                    path = self.root / ".git/hooks" / name
                    path.write_text("#!/bin/sh\n" + content + "\n")
                    path.chmod(0o700)

                def caller(self):
                    output = io.StringIO()
                    with redirect_stdout(output):
                        self.module.c5_real_colapso()
                    return output.getvalue()

            with patch.object(socket.socket, "connect", forbidden), patch.object(socket.socket, "connect_ex", forbidden), \
                    patch.object(socket, "getaddrinfo", forbidden), patch.object(sqlite3, "connect", forbidden), patch.object(os, "kill", forbidden):
                f = Fixture()
                assert rejected(lambda: f.module._git(["rev-parse", "--verify", "refs/heads/absent-fixture"])) == "CalledProcessError"
                original = f.module.subprocess.run
                f.module.subprocess.run = lambda command, **kwargs: subprocess.CompletedProcess(command, 0, b"\xff\x00\n", b"")
                assert f.module._git_bytes(["show", "HEAD"]) == b"\xff\x00\n"
                f.module.subprocess.run = original
                checks.append(dict(name="git_errors_propagate_and_raw_bytes_preserved", passed=True))

                f = Fixture()
                f.mutate()
                (f.root / "foreign.txt").write_text("unrelated tracked dirty\n")
                (f.root / "untracked.bin").write_bytes(b"\x00\xffprivate")
                before_head = f.head()
                result = f.commit()
                assert result.encode() == f.head() and f.head() != before_head
                assert f.git("diff-tree", "--no-commit-id", "--name-only", "-r", "-z", "HEAD").stdout == b"STATUS.md\0"
                assert (f.root / "foreign.txt").read_text() == "unrelated tracked dirty\n"
                assert (f.root / "untracked.bin").read_bytes() == b"\x00\xffprivate"
                checks.append(dict(name="status_only_without_obsolete_source_or_foreign_capture", passed=True))

                for name in ("pre-commit", "prepare-commit-msg", "commit-msg"):
                    f = Fixture()
                    f.mutate()
                    f.hook(name, "echo called >> hook.log\nexit 4")
                    head, index = f.head(), f.index()
                    rejected(f.commit)
                    assert f.head() == head and f.index() == index
                    assert (f.root / "hook.log").read_text().splitlines() == ["called"]
                checks.append(dict(name="three_hook_rejections_preserve_index_and_head_once", passed=True, cases=3))

                for selected in (False, True):
                    f = Fixture()
                    target = f.status if selected else f.root / "foreign.txt"
                    target.write_text("prepared fixture data\n")
                    f.git("add", "--", target.name)
                    head, index, status = f.head(), f.index(), f.status.read_bytes()
                    for name in ("audit_git_entropy", "audit_db_census", "audit_ruff", "audit_tests", "crystallize_status", "append_mutation"):
                        setattr(f.module, name, forbidden)
                    output = io.StringIO()
                    with redirect_stdout(output):
                        rejected(f.module.c5_real_colapso)
                    assert not output.getvalue() and f.head() == head and f.index() == index and f.status.read_bytes() == status
                checks.append(dict(name="initial_preflight_rejects_before_all_audits_or_writes", passed=True, cases=2))

                f = Fixture()
                signer = f.root / "signer-recorder.sh"
                signer.write_text("#!/bin/sh\necho signer >> signer.log\nexit 1\n")
                signer.chmod(0o700)
                f.git("config", "gpg.program", str(signer))
                f.git("config", "user.signingkey", "SYNTHETIC-NO-KEY")
                f.git("config", "commit.gpgsign", "true")
                head, index = f.head(), f.index()
                output = io.StringIO()
                with redirect_stdout(output):
                    rejected(f.module.c5_real_colapso)
                assert "COMPLETE" not in output.getvalue() and "Collapse:" not in output.getvalue()
                assert f.head() == head and f.index() == index
                assert (f.root / "signer.log").read_text().splitlines() == ["signer"]
                checks.append(dict(name="caller_respects_signing_config_without_real_key_or_false_success", passed=True))

                f = Fixture()
                for name in ("pre-commit", "prepare-commit-msg", "commit-msg", "post-commit"):
                    f.hook(name, f"echo {name} >> hook.log\nexit 0")
                count = int(f.git("rev-list", "--count", "HEAD").stdout)
                output = f.caller()
                assert int(f.git("rev-list", "--count", "HEAD").stdout) == count + 1
                assert "Historical `[PENDING]` marker" in f.status.read_text()
                assert f.status.read_text().count("COMMIT_REFERENCE_IN_STDOUT") == 1
                assert f.head().decode() in output and f.head().decode() not in f.status.read_text()
                assert "EXERGY_OPTIMIZER COMPLETE" in output
                assert (f.root / "hook.log").read_text().splitlines() == ["pre-commit", "prepare-commit-msg", "commit-msg", "post-commit"]
                checks.append(dict(name="caller_single_commit_no_amend_no_historical_rewrite", passed=True))

                f = Fixture()
                head, index = f.head(), f.index()
                f.hook("pre-commit", "echo wrong >> unexpected-hook.log\nexit 1")
                assert f.commit() is None
                f.module.crystallize_status = lambda report: "b" * 64
                f.module.append_mutation = lambda *args: None
                output = f.caller()
                assert "NO_CHANGE" in output and "COMPLETE" not in output and "Collapse:" not in output
                assert f.head() == head and f.index() == index and not (f.root / "unexpected-hook.log").exists()
                checks.append(dict(name="noop_none_and_caller_no_change_without_commit_proof", passed=True))

                f = Fixture()
                baseline = f.module._git_preflight()
                f.mutate()
                (f.root / "foreign.txt").write_text("prepared during audits\n")
                f.git("add", "--", "foreign.txt")
                head, index = f.head(), f.index()
                rejected(lambda: f.module.git_sentinel_commit("a" * 64, baseline=baseline))
                assert f.head() == head and f.index() == index
                checks.append(dict(name="audit_interval_external_staging_rejected_and_preserved", passed=True))

                f = Fixture()
                f.mutate()
                (f.root / "foreign.txt").write_text("late foreign preparation\n")
                events = []

                def interleaved_run(command, **kwargs):
                    if "commit" in command:
                        f.git("add", "--", "foreign.txt")
                        events.append("prepared")
                    return guarded_run(command, **kwargs)

                f.module.subprocess.run = interleaved_run
                result = f.commit()
                assert events == ["prepared"] and result.encode() == f.head()
                assert f.git("diff-tree", "--no-commit-id", "--name-only", "-r", "-z", "HEAD").stdout == b"STATUS.md\0"
                assert f.git("diff", "--cached", "--name-only", "-z").stdout == b"foreign.txt\0"
                assert f.git("show", ":foreign.txt").stdout == b"late foreign preparation\n"
                checks.append(dict(name="last_moment_foreign_staging_preserved_and_excluded", passed=True))

                for mode in ("symlink", "fifo", "override"):
                    f = Fixture()
                    head, index = f.head(), f.index()
                    if mode == "override":
                        f.module.STATUS_FILE = f.root / "foreign.txt"
                    else:
                        f.status.unlink()
                        if mode == "symlink":
                            f.status.symlink_to(f.root / "foreign.txt")
                        else:
                            os.mkfifo(f.status)
                    rejected(f.module._git_preflight)
                    assert f.head() == head and f.index() == index
                checks.append(dict(name="status_type_and_path_override_rejected", passed=True, cases=3))
    finally:
        os.chdir(old_cwd)
        os.environ.clear()
        os.environ.update(old_env)
    after = hashes()
    assert before[str(SOURCE.relative_to(ROOT))] == after[str(SOURCE.relative_to(ROOT))]
    print(json.dumps(dict(reviewer="03", status="PASS", checks=checks, check_count=len(checks), temporary_repositories=sequence[0],
                          git_command_count=len(commands), source_sha256_before=before, source_sha256_after=after,
                          scope="Real Git and benign hooks/signing recorder in owned temporary repos only; all census/linter/test audits replaced; SQLite/network/process kill blocked; no real keys or protected runtime."), indent=2))


if __name__ == "__main__":
    main()
