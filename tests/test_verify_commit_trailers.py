"""Unit tests for fail-closed ledger trailer verification, including orphan root projections."""

from __future__ import annotations

import os
from pathlib import Path
import subprocess
import sys

import pytest

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
