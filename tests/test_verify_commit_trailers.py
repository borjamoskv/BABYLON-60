"""Unit tests for fail-closed ledger trailer verification, including orphan root projections."""

from __future__ import annotations

import os
from pathlib import Path
import subprocess
import sys

import pytest
import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = REPO_ROOT / "scripts" / "guards" / "verify_commit_trailers.py"
UNREACHABLE_BASE = "9cf71a9293e6e805d81981d26fd3d0d131d28981"
VALID_LEDGER_HEAD = "92ec49ef9c4dbb1b391693a6dcae138e4a3c69e114d9585ca2a6544f1f07e6bd"


def _git_env() -> dict[str, str]:
    env = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}
    env.update(
        {
            "GIT_CONFIG_NOSYSTEM": "1",
            "GIT_CONFIG_GLOBAL": os.devnull,
            "GIT_AUTHOR_NAME": "Test",
            "GIT_AUTHOR_EMAIL": "test@example.invalid",
            "GIT_COMMITTER_NAME": "Test",
            "GIT_COMMITTER_EMAIL": "test@example.invalid",
        }
    )
    return env


def _git(repo: Path, *args: str) -> str:
    return subprocess.run(
        ["git", *args],
        cwd=repo,
        env=_git_env(),
        text=True,
        capture_output=True,
        check=True,
    ).stdout.strip()


def _init_repo(tmp_path: Path) -> Path:
    repo = tmp_path / "repo"
    repo.mkdir()
    _git(repo, "init", "-q", "-b", "main")
    return repo


def _commit_file(repo: Path, name: str, content: str, message: str) -> str:
    (repo / name).write_text(content, encoding="utf-8")
    _git(repo, "add", name)
    _git(repo, "commit", "-q", "--no-gpg-sign", "-m", message)
    return _git(repo, "rev-parse", "HEAD")


def _run_verifier(repo: Path, base: str, head: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(SCRIPT), "--base", base, "--head", head],
        cwd=repo,
        env=_git_env(),
        text=True,
        capture_output=True,
        check=False,
    )


def test_orphan_root_head_with_unreachable_base_verifies_head(tmp_path: Path) -> None:
    repo = _init_repo(tmp_path)
    msg = f"feat(release): bounded public projection\n\nLedger-Head: {VALID_LEDGER_HEAD}\nLedger-Seq: 1462\n"
    head = _commit_file(repo, "README.md", "projection\n", msg)

    result = _run_verifier(repo, UNREACHABLE_BASE, head)
    assert result.returncode == 0, result.stderr
    assert "Verified ledger trailer syntax on 1 introduced commits" in result.stdout


def test_orphan_root_head_without_trailers_fails_closed(tmp_path: Path) -> None:
    repo = _init_repo(tmp_path)
    head = _commit_file(repo, "README.md", "projection\n", "feat(release): missing trailers")

    result = _run_verifier(repo, UNREACHABLE_BASE, head)
    assert result.returncode != 0
    assert "requires exactly one valid Ledger-Head trailer" in result.stderr


@pytest.mark.parametrize("with_trailers", [True, False])
def test_non_root_head_with_missing_base_fails_closed(tmp_path: Path, with_trailers: bool) -> None:
    repo = _init_repo(tmp_path)
    _commit_file(
        repo,
        "a.txt",
        "v1\n",
        f"init\n\nLedger-Head: {VALID_LEDGER_HEAD}\nLedger-Seq: 1\n",
    )
    msg = f"second\n\nLedger-Head: {VALID_LEDGER_HEAD}\nLedger-Seq: 2\n" if with_trailers else "second without trailers"
    head = _commit_file(repo, "b.txt", "v2\n", msg)

    result = _run_verifier(repo, UNREACHABLE_BASE, head)
    assert result.returncode != 0
    assert "is unavailable for non-root head" in result.stderr


def _run_workflow(repo: Path, base: str, head: str) -> subprocess.CompletedProcess[str]:
    workflow = yaml.safe_load((REPO_ROOT / ".github/workflows/verify_ledger.yml").read_text())
    step = next(s for s in workflow["jobs"]["verify-ledger"]["steps"] if "run" in s)
    script = repo / "scripts/guards/verify_commit_trailers.py"
    script.parent.mkdir(parents=True, exist_ok=True)
    script.write_bytes(SCRIPT.read_bytes())
    return subprocess.run(
        ["bash", "-e", "-o", "pipefail", "-c", step["run"]],
        cwd=repo,
        env={**_git_env(), "BASE_SHA": base, "HEAD_SHA": head},
        text=True,
        capture_output=True,
        timeout=15,
        check=False,
    )


@pytest.mark.parametrize("valid_intermediate", [True, False])
def test_workflow_fetches_rewritten_base_and_checks_full_range(tmp_path: Path, valid_intermediate: bool) -> None:
    origin = _init_repo(tmp_path)
    common = _commit_file(origin, "a.txt", "common\n", "Historical baseline without trailers")
    base = _commit_file(origin, "a.txt", "old\n", "Old tip without trailers")
    _git(origin, "checkout", "-q", "-B", "main", common)
    trailers = f"\n\nLedger-Head: {VALID_LEDGER_HEAD}\nLedger-Seq: 2\n"
    _commit_file(origin, "a.txt", "new\n", "Intermediate" + (trailers if valid_intermediate else ""))
    head = _commit_file(origin, "b.txt", "new\n", "New tip" + trailers)
    clone = tmp_path / "clone"
    _git(tmp_path, "clone", "--no-local", "--single-branch", str(origin), str(clone))
    assert _run_verifier(clone, base, head).returncode != 0

    result = _run_workflow(clone, base, head)

    assert _git(clone, "rev-parse", "HEAD") == head
    assert _git(clone, "cat-file", "-t", base) == "commit"
    if valid_intermediate:
        assert result.returncode == 0, result.stderr
        assert "on 2 introduced commits" in result.stdout
    else:
        assert result.returncode != 0
        assert "requires exactly one valid Ledger-Head trailer" in result.stderr


def test_workflow_preserves_root_projection_without_fetch(tmp_path: Path) -> None:
    repo = _init_repo(tmp_path)
    head = _commit_file(repo, "a.txt", "root\n", f"Root\n\nLedger-Head: {VALID_LEDGER_HEAD}\nLedger-Seq: 1\n")
    # There is deliberately no origin: a valid orphan projection needs no fetch.
    result = _run_workflow(repo, UNREACHABLE_BASE, head)
    assert result.returncode == 0, result.stderr
    assert "on 1 introduced commits" in result.stdout
