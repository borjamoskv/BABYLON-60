"""Lot 8 independent fixtures: real Git confined to owned temporary repositories."""
from __future__ import annotations

from contextlib import redirect_stdout
import hashlib
import importlib.util
import io
import json
import os
from pathlib import Path
import shutil
import socket
import subprocess
import sys
import tempfile
from types import SimpleNamespace
from unittest.mock import patch

ROOT = Path(__file__).absolute().parents[4]
SOURCE = ROOT / "scripts/c5_cortex/cortex_objectives_transducer.py"
SHARED_TEST = ROOT / "tests/test_swarm100_lot8_regressions.py"
YAML = "cortex/ontology/babylon60_objectives.yaml"
GIT = "/usr/bin/git"
sys.dont_write_bytecode = True


def hashes():
    return {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in (SOURCE, SHARED_TEST)}


def expect_error(callback):
    try:
        callback()
    except (RuntimeError, ValueError, OSError, subprocess.SubprocessError) as error:
        return type(error).__name__
    raise AssertionError("Operation unexpectedly returned success")


def main():
    before = hashes()
    original_env, original_cwd = dict(os.environ), Path.cwd()
    checks, limits, calls = [], [], []
    real_run = subprocess.run
    counter = [0]

    def forbidden(*args, **kwargs):
        raise AssertionError("Network/process kill forbidden")

    try:
        with tempfile.TemporaryDirectory(prefix="lot8-independent-") as owned:
            boundary = Path(owned).resolve()
            home = boundary / "home"
            home.mkdir()
            os.environ.clear()
            os.environ.update(HOME=str(home), XDG_CONFIG_HOME=str(home / "xdg"), PATH="/usr/bin:/bin",
                              GIT_CONFIG_NOSYSTEM="1", GIT_CONFIG_GLOBAL=str(home / "empty-config"),
                              GIT_TERMINAL_PROMPT="0", LC_ALL="C", PYTHONDONTWRITEBYTECODE="1")
            os.chdir(boundary)

            def confined_run(command, **kwargs):
                cwd = Path(kwargs["cwd"]).resolve()
                assert cwd.is_relative_to(boundary) and cwd != boundary
                assert command[0] in ("git", GIT)
                argv = list(command)
                argv[0] = GIT
                stripped = [arg for arg in argv[1:] if arg != "--literal-pathspecs"]
                assert stripped[0] in {"init", "config", "add", "commit", "rev-parse", "symbolic-ref", "ls-files",
                                       "diff", "diff-tree", "rev-list", "show", "update-index", "update-ref"}
                assert not any(arg in {"--no-verify", "push", "fetch", "pull", "clone", "reset", "clean"} for arg in argv)
                selected_env = kwargs.get("env", os.environ)
                assert selected_env["HOME"] == str(home) and selected_env["GIT_CONFIG_NOSYSTEM"] == "1"
                assert selected_env["GIT_CONFIG_GLOBAL"] == str(home / "empty-config")
                calls.append(stripped[0])
                kwargs["timeout"] = 10
                return real_run(argv, **kwargs)

            class Fixture:
                def __init__(self):
                    counter[0] += 1
                    self.root = boundary / f"fixture repo {counter[0]}"
                    self.root.mkdir()
                    self.git("init", "-b", "main")
                    self.git("config", "user.name", "Independent Fixture")
                    self.git("config", "user.email", "fixture@example.invalid")
                    self.git("config", "commit.gpgsign", "false")
                    self.yaml = self.root / YAML
                    self.yaml.parent.mkdir(parents=True)
                    self.yaml.write_text("objectives: []\n")
                    (self.root / "PROJECT.md").write_text("# Initial fixture\n")
                    (self.root / "foreign.txt").write_text("initial foreign\n")
                    self.git("add", "--", YAML, "PROJECT.md", "foreign.txt")
                    self.git("commit", "-m", "Initial fixture")
                    copied = boundary / f"fixture-{counter[0]}.py"
                    shutil.copyfile(SOURCE, copied)
                    spec = importlib.util.spec_from_file_location(f"independent_lot8_{counter[0]}", copied)
                    self.module = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(self.module)
                    self.module.WORKSPACE_DIR = self.root
                    self.module.YAML_STATE_PATH = self.yaml
                    self.module.PROJECT_MD_PATH = self.root / "PROJECT.md"
                    self.module.subprocess = SimpleNamespace(run=confined_run, CalledProcessError=subprocess.CalledProcessError,
                                                             SubprocessError=subprocess.SubprocessError)

                def git(self, *args):
                    return confined_run([GIT, *args], cwd=self.root, capture_output=True, check=True)

                def head(self):
                    return self.git("rev-parse", "HEAD").stdout.strip()

                def index(self):
                    return (self.root / ".git/index").read_bytes()

                def hook(self, name, body):
                    target = self.root / ".git/hooks" / name
                    target.write_text("#!/bin/sh\n" + body + "\n")
                    target.chmod(0o700)

                def mutate(self):
                    self.yaml.write_text("objectives:\n- id: OBJ-INDEPENDENT\n")

                def run(self, paths=None):
                    return self.module.run_git_sentinel("Independent fixture mutation", **({"paths": paths} if paths else {}))

                def changed(self):
                    return set(filter(None, self.git("diff-tree", "--no-commit-id", "--name-only", "-r", "-z", "HEAD").stdout.split(b"\0")))

            with patch.object(socket.socket, "connect", forbidden), patch.object(socket.socket, "connect_ex", forbidden), \
                    patch.object(socket, "getaddrinfo", forbidden), patch.object(os, "kill", forbidden):
                f = Fixture()
                f.mutate()
                for path in ("PROJECT.md", "foreign.txt", "untracked.txt"):
                    (f.root / path).write_text("preserve operator fixture edit\n")
                initial = f.head()
                result = f.run()
                assert result.encode() == f.head() and f.head() != initial
                assert f.changed() == {YAML.encode()}
                assert f.git("diff", "--cached", "--name-only").stdout == b""
                assert all((f.root / name).read_text() == "preserve operator fixture edit\n" for name in ("PROJECT.md", "foreign.txt", "untracked.txt"))
                checks.append(dict(name="only_yaml_excludes_other_worktree_files", passed=True))

                for hook in ("pre-commit", "prepare-commit-msg", "commit-msg"):
                    f = Fixture()
                    f.mutate()
                    f.hook(hook, "echo called >> hook.log\nexit 7")
                    initial, index = f.head(), f.index()
                    expect_error(f.run)
                    assert f.head() == initial and f.index() == index
                    assert (f.root / "hook.log").read_text().splitlines() == ["called"]
                checks.append(dict(name="three_rejecting_hooks_once_preserve_head_and_index", passed=True, cases=3))

                f = Fixture()
                f.mutate()
                (f.root / "PROJECT.md").write_text("# Changed selected project\n")
                for hook in ("pre-commit", "prepare-commit-msg", "commit-msg", "post-commit"):
                    f.hook(hook, f"echo {hook} >> hook.log\nexit 0")
                f.run((f.yaml, f.root / "PROJECT.md"))
                assert f.changed() == {YAML.encode(), b"PROJECT.md"}
                assert (f.root / "hook.log").read_text().splitlines() == ["pre-commit", "prepare-commit-msg", "commit-msg", "post-commit"]
                checks.append(dict(name="declared_two_file_commit_runs_all_normal_hooks", passed=True))

                f = Fixture()
                (f.root / "foreign.txt").write_text("unrelated dirty only\n")
                f.hook("pre-commit", "echo unexpected >> hook.log\nexit 1")
                initial, index = f.head(), f.index()
                assert f.run().encode() == initial and f.index() == index and not (f.root / "hook.log").exists()
                checks.append(dict(name="no_op_returns_observed_existing_head_without_commit", passed=True))

                for kind in ("foreign-staged", "selected-partially-staged", "intent-to-add", "assume-unchanged", "skip-worktree"):
                    f = Fixture()
                    f.mutate()
                    if kind == "foreign-staged":
                        (f.root / "foreign.txt").write_text("prepared foreign\n")
                        f.git("add", "--", "foreign.txt")
                    elif kind == "selected-partially-staged":
                        f.git("add", "--", YAML)
                        f.yaml.write_text("subsequent unstaged selected fixture\n")
                    elif kind == "intent-to-add":
                        (f.root / "intent.txt").write_text("intent fixture\n")
                        f.git("add", "-N", "--", "intent.txt")
                    else:
                        f.git("update-index", "--" + kind, "foreign.txt")
                    initial, index = f.head(), f.index()
                    expect_error(f.run)
                    assert f.head() == initial and f.index() == index
                checks.append(dict(name="prepared_or_special_index_rejected_byte_identically", passed=True, cases=5))

                for kind in ("symlink", "fifo", "untracked", "parent-symlink"):
                    f = Fixture()
                    if kind in ("symlink", "fifo"):
                        f.yaml.unlink()
                        if kind == "symlink":
                            f.yaml.symlink_to(f.root / "foreign.txt")
                        else:
                            os.mkfifo(f.yaml)
                    elif kind == "untracked":
                        # Point a new clean repository's config at a declared path absent from its index.
                        f.git("update-index", "--force-remove", "--", YAML)
                        f.git("commit", "-m", "Fixture remove tracked output")
                    else:
                        target = f.root / "renamed-ontology"
                        f.yaml.parent.rename(target)
                        (f.root / "cortex/ontology").symlink_to(target, target_is_directory=True)
                    initial, index = f.head(), f.index()
                    expect_error(f.run)
                    assert f.head() == initial and f.index() == index
                checks.append(dict(name="unsupported_output_types_or_untracked_paths_rejected", passed=True, cases=4))

                f = Fixture()
                f.mutate()
                initial, index = f.head(), f.index()
                baseline_calls = len(calls)
                with patch.dict(os.environ, {"GIT_INDEX_FILE": str(f.root / "alternate.index")}):
                    expect_error(f.run)
                assert len(calls) == baseline_calls and f.index() == index and f.head() == initial
                for paths in ((f.root / "foreign.txt",), (f.root / "PROJECT.md", f.root / "../escape")):
                    expect_error(lambda: f.run(paths))
                assert f.index() == index
                checks.append(dict(name="ambient_index_selector_and_nonallowlisted_paths_rejected_before_git", passed=True))

                f = Fixture()
                f.mutate()
                commit_calls = []
                initial, index = f.head(), f.index()

                def fail_commit(command, **kwargs):
                    if "commit" in command:
                        commit_calls.append(command)
                        return subprocess.CompletedProcess(command, 23, b"synthetic git failure", b"synthetic error")
                    return confined_run(command, **kwargs)

                f.module.subprocess.run = fail_commit
                expect_error(f.run)
                assert len(commit_calls) == 1 and f.head() == initial and f.index() == index
                checks.append(dict(name="nonhook_git_error_no_retry_no_staging", passed=True))

                f = Fixture()
                f.mutate()
                (f.root / "foreign.txt").write_text("concurrent prepared foreign\n")
                staged = []

                def stage_foreign_before_commit(command, **kwargs):
                    if "commit" in command:
                        f.git("add", "--", "foreign.txt")
                        staged.append(f.git("show", ":foreign.txt").stdout)
                    return confined_run(command, **kwargs)

                f.module.subprocess.run = stage_foreign_before_commit
                f.run()
                assert staged == [b"concurrent prepared foreign\n"]
                assert f.changed() == {YAML.encode()}
                assert f.git("show", ":foreign.txt").stdout == staged[0]
                assert f.git("diff", "--cached", "--name-only").stdout == b"foreign.txt\n"
                checks.append(dict(name="concurrent_foreign_staging_excluded_and_preserved", passed=True))

                f = Fixture()
                f.mutate()
                expected_worktree = f.yaml.read_bytes()
                competing_staged = b"competing selected staged bytes\n"

                def stage_selected_before_commit(command, **kwargs):
                    if "commit" in command:
                        f.yaml.write_bytes(competing_staged)
                        f.git("add", "--", YAML)
                        f.yaml.write_bytes(expected_worktree)
                    return confined_run(command, **kwargs)

                f.module.subprocess.run = stage_selected_before_commit
                result = f.run()
                actual_index = f.git("show", ":" + YAML).stdout
                assert actual_index == expected_worktree and actual_index != competing_staged
                limits.append(dict(name="concurrent_same_output_staging_window", observed=True,
                                   detail="Another writer staging a selected path after final preflight loses that staged version when --only commits current worktree. No global transaction or same-output concurrency guarantee.",
                                   returned_hash_matches_head=result.encode() == f.head()))

                f = Fixture()
                f.mutate()
                (f.root / "foreign.txt").write_text("hook staged foreign\n")
                f.hook("pre-commit", "git add -- foreign.txt\nexit 0")
                initial = f.head()
                expect_error(f.run)
                assert f.head() != initial and b"foreign.txt" in f.changed()
                limits.append(dict(name="trusted_hook_can_widen_commit_before_postvalidation", observed=True,
                                   detail="Hook using git add stages an extra route in Git temporary index. Helper rejects postvalidation without undoing the already created commit; hooks are not sandboxed."))

                f = Fixture()
                args = SimpleNamespace(title="Independent", description="Owned fixture", exergy=0.0)
                f.hook("pre-commit", "exit 1")
                initial = f.head()
                output = io.StringIO()
                with redirect_stdout(output):
                    expect_error(lambda: f.module.cmd_add_objective(args))
                assert not output.getvalue() and f.head() == initial
                assert "Independent" in f.yaml.read_text()
                checks.append(dict(name="consumer_propagates_failure_without_success_claim", passed=True,
                                   limitation="Generated YAML stays modified; persistence rollback is outside this lot."))
                os.chdir(boundary)
    finally:
        os.chdir(original_cwd)
        os.environ.clear()
        os.environ.update(original_env)
    after = hashes()
    assert before["scripts/c5_cortex/cortex_objectives_transducer.py"] == after["scripts/c5_cortex/cortex_objectives_transducer.py"]
    print(json.dumps(dict(reviewer="03", status="PASS_WITH_OBSERVED_LIMITATIONS", source_sha256_before=before,
                          source_sha256_after=after, checks=checks, check_count=len(checks), limitations=limits,
                          git_scope="Only owned temporary repositories, isolated HOME/global/system config, synthetic author, signing disabled; no network/native protected runtime.",
                          temporary_repositories=counter[0], git_commands=len(calls)), indent=2))


if __name__ == "__main__":
    main()
