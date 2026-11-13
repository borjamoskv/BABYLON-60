"""Exercise native selection against real Git history, including deletion/rename."""

import importlib.util
from pathlib import Path
import subprocess

import pytest


ROOT = Path(__file__).absolute().parents[1]
spec = importlib.util.spec_from_file_location("native_ci_scope", ROOT / "scripts/guards/native_ci_scope.py")
assert spec and spec.loader
scope = importlib.util.module_from_spec(spec)
spec.loader.exec_module(scope)


def git(root: Path, *args: str) -> str:
    return subprocess.check_output(["git", "-C", str(root), *args], text=True).strip()


def commit(root: Path) -> str:
    git(root, "add", ".")
    git(root, "-c", "user.name=Test", "-c", "user.email=test@example.invalid",
        "-c", "commit.gpgsign=false", "commit", "-qm", "fixture")
    return git(root, "rev-parse", "HEAD")


@pytest.mark.parametrize("event_name", ["push", "pull_request"])
def test_docs_skip_but_native_changes_and_deletions_require_execution(tmp_path: Path, event_name: str) -> None:
    git(tmp_path, "init", "-q")
    (tmp_path / "src").mkdir()
    native = tmp_path / "src/kernel.rs"
    native.write_text("baseline")
    base = commit(tmp_path)
    (tmp_path / "README.md").write_text("docs only")
    docs = commit(tmp_path)
    event = {"before": base, "pull_request": {"base": {"sha": base}}}
    assert not scope.requires_native(event_name, event, docs, tmp_path)
    # A rename outside the native subtree still includes the deleted native input.
    native.rename(tmp_path / "archived.txt")
    changed = commit(tmp_path)
    assert scope.requires_native(event_name, event, changed, tmp_path)


@pytest.mark.parametrize("event,base,head", [
    ("workflow_dispatch", "a" * 40, "b" * 40),
    ("push", "0" * 40, "b" * 40),
    ("push", "invalid", "b" * 40),
    ("push", "a" * 40, "b" * 40),
])
def test_unknown_scope_never_suppresses_native_execution(tmp_path: Path, event: str, base: str, head: str) -> None:
    assert scope.requires_native(event, {"before": base}, head, tmp_path)
