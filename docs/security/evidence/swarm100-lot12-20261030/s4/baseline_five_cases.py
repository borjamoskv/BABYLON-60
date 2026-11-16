"""Isolated regressions for the five file/Git findings in SWARM100 lot 12."""
from __future__ import annotations

import importlib.util
import os
from pathlib import Path
import subprocess
import sys

import pytest

ROOT = Path(__file__).absolute().parents[1]


def load(relative: str, name: str):
    spec = importlib.util.spec_from_file_location(name, ROOT / relative)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture(autouse=True)
def isolated_environment(tmp_path, monkeypatch):
    home = tmp_path / "home"
    home.mkdir()
    monkeypatch.setenv("HOME", str(home))
    monkeypatch.setenv("BABYLON60_SIGNING_SEED", "00" * 32)
    for key in ("CLOUDFLARE_API_TOKEN", "APPLE_DOMAIN_CODE", "CORTEX_VAULT_KEY"):
        monkeypatch.delenv(key, raising=False)
    import dotenv
    monkeypatch.setattr(dotenv, "load_dotenv", lambda *a, **k: False)
    monkeypatch.setattr(dotenv, "dotenv_values", lambda *a, **k: {})


def git(directory: Path, *args: str) -> str:
    result = subprocess.run(["git", "-c", "commit.gpgsign=false", "-c", "core.hooksPath=/dev/null", *args],
                            cwd=directory, check=True, capture_output=True)
    return result.stdout.decode().strip()


def make_repo(tmp_path: Path) -> Path:
    repo = tmp_path / "repo"
    repo.mkdir()
    git(repo, "init", "-b", "main")
    git(repo, "config", "user.name", "Fixture")
    git(repo, "config", "user.email", "fixture@example.invalid")
    (repo / "tracked.txt").write_text("original")
    git(repo, "add", "tracked.txt")
    git(repo, "commit", "-m", "fixture origin")
    git(repo, "update-ref", "refs/remotes/origin/main", "HEAD")
    (repo / "tracked.txt").write_text("local commit")
    git(repo, "commit", "-am", "fixture local")
    return repo


def test_c0435_queue_rejects_symlink_without_changing_target(tmp_path, monkeypatch):
    host = load("scripts/c5_cli/moskv_native_host.py", "lot12_s4_native")
    victim = tmp_path / "victim.txt"
    victim.write_text('["preserve"]')
    queue = tmp_path / "queue.json"
    queue.symlink_to(victim)
    monkeypatch.setattr(host, "QUEUE_FILE", queue)
    try:
        host.enqueue_prompt("injected")
    except (OSError, ValueError):
        pass
    assert victim.read_text() == '["preserve"]'


def test_c0298_purge_preserves_importable_python(tmp_path, monkeypatch):
    purge = load("01_KISH_ENGINE/babylon60/cortex/cortex_purge_anergy.py", "lot12_s4_purge")
    package = tmp_path / "package"
    package.mkdir()
    (package / "__init__.py").write_text("VALUE = 41\n")
    (package / "gemini_labs_nexus.py").write_text("VALUE = 42\n")
    archive = package / ".archive"
    monkeypatch.setattr(purge, "PROJECT_ROOT", str(package))
    for name in ("ARCHIVE_SCRIPTS", "ARCHIVE_DATA", "ARCHIVE_DBS"):
        monkeypatch.setattr(purge, name, str(archive / name.lower()))
    purge.ensure_dirs()
    purge.categorize_and_move()
    assert (package / "__init__.py").is_file()
    assert (package / "gemini_labs_nexus.py").is_file()
    for filename, value in [("__init__.py", 41), ("gemini_labs_nexus.py", 42)]:
        spec = importlib.util.spec_from_file_location("fixture_importable", package / filename)
        assert spec is not None and spec.loader is not None
        imported = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(imported)
        assert imported.VALUE == value


def test_c0437_dirty_work_and_local_commits_survive_preflight(tmp_path, monkeypatch):
    rewrite = load("scripts/c5_git_utils/rewrite_commits.py", "lot12_s4_rewrite")
    repo = make_repo(tmp_path)
    head = git(repo, "rev-parse", "HEAD")
    (repo / "tracked.txt").write_text("uncommitted work")
    monkeypatch.chdir(repo)
    try:
        rewrite._ensure_main()
    except (RuntimeError, subprocess.CalledProcessError):
        pass
    assert (repo / "tracked.txt").read_text() == "uncommitted work"
    assert git(repo, "rev-parse", "HEAD") == head


def test_c0448_icloud_preserves_neighbor_records(monkeypatch):
    deploy = load("scripts/c5_icloud_deploy.py", "lot12_s4_icloud")
    monkeypatch.setenv("CLOUDFLARE_API_TOKEN", "synthetic-token")
    monkeypatch.setenv("APPLE_DOMAIN_CODE", "apple-domain=fixture")
    removed = []
    records = [
        {"id": "apex", "name": "babylon60.com", "type": "MX", "content": "old.example.invalid"},
        {"id": "neighbor-mx", "name": "neighbor.babylon60.com", "type": "MX", "content": "mail.example.invalid"},
        {"id": "neighbor-spf", "name": "neighbor.babylon60.com", "type": "TXT", "content": "v=spf1 -all"},
    ]
    def request(method, url, token, data=None):
        if method == "GET" and url.startswith("/zones?"):
            return {"result": [{"id": "fixture-zone", "name": "babylon60.com"}]}
        if method == "GET":
            return {"result": records}
        if method == "DELETE":
            removed.append(url.rsplit("/", 1)[-1])
        return {"success": True, "result": {}}
    monkeypatch.setattr(deploy, "request_cf", request)
    deploy.main()
    assert removed == ["apex"]


def run_installer(tmp_path: Path, instruction: str = "operator instructions", prepare=None, expect_success=True):
    fixture = tmp_path / "fixture"
    tools = fixture / "tools"
    tools.mkdir(parents=True)
    home = tmp_path / "isolated-home"
    home.mkdir()
    (fixture / ".babylon60rules").write_text("canonical fixture rules\n")
    (fixture / "CLAUDE.md").write_text(instruction)
    (fixture / ".github").mkdir()
    (fixture / ".github/copilot-instructions.md").write_text("copilot operator instructions")
    if prepare is not None:
        prepare(fixture)
    text = (ROOT / "tools/install_shield.sh").read_text()
    # Only the shared installer lock is relocated; all tested rule migration executes unchanged.
    text = text.replace('LOCK_DIR="/tmp/babylon_shield_install.lock"',
                        'LOCK_DIR="' + str(tmp_path / "fixture-lock") + '"')
    script = tools / "install_shield.sh"
    script.write_text(text)
    env = {**os.environ, "HOME": str(home)}
    result = subprocess.run(["bash", str(script)], cwd=fixture, env=env, capture_output=True, text=True, timeout=15)
    assert (result.returncode == 0) is expect_success, result.stderr
    return fixture, home


def test_c0490_installer_preserves_previous_instructions(tmp_path):
    fixture, _ = run_installer(tmp_path)
    preserved = [p.read_text() for p in fixture.rglob("*") if p.is_file() and not p.is_symlink()
                 and p.name != "install_shield.sh"]
    assert "operator instructions" in preserved
    assert "copilot operator instructions" in preserved
    assert (fixture / "CLAUDE.md").is_symlink()
