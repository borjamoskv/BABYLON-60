"""C0005 regression: verify_execution.sh must not report a clean repo with untracked files.

Runs the script inside a throwaway git repository; the real repository is not touched.
"""

import os
import re
import subprocess
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "c5_verifiers" / "verify_execution.sh"


def _git(repo: Path, *args: str) -> None:
    env = {
        **os.environ,
        "GIT_CONFIG_GLOBAL": os.devnull,
        "GIT_CONFIG_SYSTEM": os.devnull,
        "GIT_AUTHOR_NAME": "fixture",
        "GIT_AUTHOR_EMAIL": "fixture@example.invalid",
        "GIT_COMMITTER_NAME": "fixture",
        "GIT_COMMITTER_EMAIL": "fixture@example.invalid",
    }
    subprocess.run(["git", *args], cwd=repo, check=True, capture_output=True, env=env)


def _repo(tmp_path: Path) -> Path:
    repo = tmp_path / "repo"
    repo.mkdir()
    _git(repo, "init", "-q")
    (repo / "tracked file.txt").write_text("contenido\n", encoding="utf-8")
    (repo / ".gitignore").write_text("ignored.log\n", encoding="utf-8")
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", "inicial")
    return repo


def _run(repo: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(["bash", str(SCRIPT)], cwd=repo, capture_output=True, text=True)


def test_clean_repo_passes_and_hashes_files_with_spaces(tmp_path):
    result = _run(_repo(tmp_path))
    assert result.returncode == 0, result.stdout + result.stderr
    assert "tracked file.txt" in result.stdout


def test_untracked_file_is_reported_and_fails(tmp_path):
    repo = _repo(tmp_path)
    (repo / "nuevo_sin_versionar.py").write_text("print('x')\n", encoding="utf-8")
    result = _run(repo)
    assert result.returncode != 0, "C0005: repo con archivo no versionado declarado limpio"
    assert "nuevo_sin_versionar.py" in result.stdout + result.stderr


def test_gitignored_file_stays_outside_the_contract(tmp_path):
    repo = _repo(tmp_path)
    (repo / "ignored.log").write_text("ruido\n", encoding="utf-8")
    assert _run(repo).returncode == 0


def test_file_hidden_by_info_exclude_is_reported(tmp_path):
    repo = _repo(tmp_path)
    (repo / ".git" / "info").mkdir(parents=True, exist_ok=True)
    (repo / ".git" / "info" / "exclude").write_text("oculto.py\n", encoding="utf-8")
    (repo / "oculto.py").write_text("x = 1\n", encoding="utf-8")
    result = _run(repo)
    assert result.returncode != 0, "C0005: archivo oculto por .git/info/exclude declarado limpio"
    assert "oculto.py" in result.stdout + result.stderr


def test_file_hidden_by_core_excludes_file_is_reported(tmp_path):
    repo = _repo(tmp_path)
    excludes = tmp_path / "excludes"
    excludes.write_text("tambien_oculto.py\n", encoding="utf-8")
    _git(repo, "config", "core.excludesFile", str(excludes))
    (repo / "tambien_oculto.py").write_text("x = 1\n", encoding="utf-8")
    assert _run(repo).returncode != 0, "C0005: archivo oculto por core.excludesFile declarado limpio"


def test_skip_worktree_change_is_reported(tmp_path):
    repo = _repo(tmp_path)
    _git(repo, "update-index", "--skip-worktree", "tracked file.txt")
    (repo / "tracked file.txt").write_text("cambiado\n", encoding="utf-8")
    result = _run(repo)
    assert result.returncode != 0, "C0005: cambio oculto con skip-worktree declarado limpio"


def test_run_from_subdirectory_still_hashes_commit_files(tmp_path):
    repo = _repo(tmp_path)
    sub = repo / "sub"
    sub.mkdir()
    result = subprocess.run(["bash", str(SCRIPT)], cwd=sub, capture_output=True, text=True)
    assert result.returncode == 0, result.stdout + result.stderr
    assert re.search(r"[0-9a-f]{64}\s+tracked file\.txt", result.stdout), "C0005: sin hash desde subdirectorio"
