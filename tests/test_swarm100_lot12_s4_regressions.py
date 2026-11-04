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


@pytest.mark.parametrize("operation", ["enqueue", "pop", "list", "clear"])
def test_queue_all_operations_reject_links(tmp_path, monkeypatch, operation):
    host = load("scripts/c5_cli/moskv_native_host.py", "lot12_queue_links")
    target = tmp_path / "target"
    target.write_text('["private"]')
    target.chmod(0o600)
    queue = tmp_path / "queue.json"
    queue.symlink_to(target)
    monkeypatch.setattr(host, "QUEUE_FILE", queue)
    calls = {"enqueue": lambda: host.enqueue_prompt("new"), "pop": host.get_next_prompt,
             "list": host.queued_prompts, "clear": host.clear_prompt_queue}
    with pytest.raises(OSError):
        calls[operation]()
    assert target.read_text() == '["private"]'
    assert queue.is_symlink()


@pytest.mark.parametrize("kind", ["hardlink", "fifo", "public", "directory", "malformed", "schema"])
def test_queue_rejects_unsafe_existing_objects(tmp_path, monkeypatch, kind):
    host = load("scripts/c5_cli/moskv_native_host.py", "lot12_queue_bad")
    queue = tmp_path / "queue.json"
    if kind == "hardlink":
        victim = tmp_path / "victim"
        victim.write_text("[]")
        victim.chmod(0o600)
        queue.hardlink_to(victim)
    elif kind == "fifo":
        os.mkfifo(queue, 0o600)
    elif kind == "directory":
        queue.mkdir()
    else:
        queue.write_text({"public": "[]", "malformed": "[bad", "schema": '[{"prompt": "x"}]'}[kind])
        queue.chmod(0o644 if kind == "public" else 0o600)
    monkeypatch.setattr(host, "QUEUE_FILE", queue)
    before = queue.read_bytes() if kind not in {"directory", "fifo"} else None
    with pytest.raises((OSError, ValueError)):
        host.enqueue_prompt("replacement")
    if before is not None:
        assert queue.read_bytes() == before


def test_queue_rejects_symlinked_parent(tmp_path, monkeypatch):
    host = load("scripts/c5_cli/moskv_native_host.py", "lot12_queue_parent")
    target = tmp_path / "private"
    target.mkdir(mode=0o700)
    link = tmp_path / "alias"
    link.symlink_to(target, target_is_directory=True)
    monkeypatch.setattr(host, "QUEUE_FILE", link / "queue.json")
    with pytest.raises(OSError):
        host.enqueue_prompt("injected")
    assert list(target.iterdir()) == []


def test_queue_private_default_and_fifo(tmp_path):
    host = load("scripts/c5_cli/moskv_native_host.py", "lot12_queue_default")
    assert host.QUEUE_FILE == Path.home() / ".babylon60/native_host_queue/prompts.json"
    assert host.get_next_prompt() == host.DEFAULT_PROMPT
    assert host.enqueue_prompt("α") == 1
    assert host.enqueue_prompt("β") == 2
    assert host.queued_prompts() == ["α", "β"]
    assert host.QUEUE_FILE.stat().st_mode & 0o777 == 0o600
    assert host.QUEUE_FILE.parent.stat().st_mode & 0o777 == 0o700
    assert host.get_next_prompt() == "α"
    host.clear_prompt_queue()
    assert host.get_next_prompt() == host.DEFAULT_PROMPT


def test_queue_independent_instances_serialize_warmup_and_bursts(tmp_path, monkeypatch):
    from concurrent.futures import ThreadPoolExecutor
    hosts = [load("scripts/c5_cli/moskv_native_host.py", f"lot12_queue_concurrent_{i}") for i in range(4)]
    for host in hosts:
        monkeypatch.setattr(host, "QUEUE_FILE", tmp_path / "queue.json")
    with ThreadPoolExecutor(max_workers=8) as executor:
        for round_index, count in enumerate([8, 8, 64, 64, 64]):
            expected = {f"{round_index}:{i}" for i in range(count)}
            futures = [executor.submit(hosts[i % 4].enqueue_prompt, f"{round_index}:{i}") for i in range(count)]
            assert sorted(f.result(timeout=15) for f in futures) == list(range(1, count + 1))
            popped = [executor.submit(hosts[i % 4].get_next_prompt) for i in range(count)]
            assert {f.result(timeout=15) for f in popped} == expected
            assert hosts[0].queued_prompts() == []


def test_queue_failed_file_sync_preserves_previous_bytes(tmp_path, monkeypatch):
    host = load("scripts/c5_cli/moskv_native_host.py", "lot12_queue_sync")
    monkeypatch.setattr(host, "QUEUE_FILE", tmp_path / "queue.json")
    host.enqueue_prompt("first")
    before = host.QUEUE_FILE.read_bytes()
    def fail_sync(fd):
        raise OSError("fixture fsync failure")
    monkeypatch.setattr(host.os, "fsync", fail_sync)
    with pytest.raises(OSError):
        host.enqueue_prompt("second")
    assert host.QUEUE_FILE.read_bytes() == before
    assert not list(tmp_path.glob(".queue-*.json"))


def test_purge_root_and_native_sources_preserved(tmp_path, monkeypatch):
    purge = load("01_KISH_ENGINE/babylon60/cortex/cortex_purge_anergy.py", "lot12_purge_root")
    assert Path(purge.PROJECT_ROOT) == ROOT
    monkeypatch.setattr(purge, "PROJECT_ROOT", str(tmp_path))
    for key in ["ARCHIVE_SCRIPTS", "ARCHIVE_DATA", "ARCHIVE_DBS"]:
        monkeypatch.setattr(purge, key, str(tmp_path / key))
    keep = ["__init__.py", "plugin.py", "plugin.pyc", "plugin.so", "plugin.pyd"]
    for name in keep:
        (tmp_path / name).write_bytes(b"module fixture")
    (tmp_path / "sample.json").write_text('{"sample": true}')
    target = tmp_path / "neighbor.txt"
    target.write_text("untouched")
    (tmp_path / "link.json").symlink_to(target)
    purge.ensure_dirs()
    count, _, actions = purge.categorize_and_move()
    assert count == 1
    assert actions[0]["file"] == "sample.json"
    assert all((tmp_path / name).read_bytes() == b"module fixture" for name in keep)
    assert (tmp_path / "link.json").is_symlink()
    assert target.read_text() == "untouched"


def test_purge_existing_archive_is_not_overwritten(tmp_path, monkeypatch):
    purge = load("01_KISH_ENGINE/babylon60/cortex/cortex_purge_anergy.py", "lot12_purge_collision")
    monkeypatch.setattr(purge, "PROJECT_ROOT", str(tmp_path))
    for key in ["ARCHIVE_SCRIPTS", "ARCHIVE_DATA", "ARCHIVE_DBS"]:
        monkeypatch.setattr(purge, key, str(tmp_path / key))
    purge.ensure_dirs()
    (tmp_path / "sample.json").write_text("source")
    destination = Path(purge.ARCHIVE_DATA) / "sample.json"
    destination.write_text("old")
    with pytest.raises(FileExistsError):
        purge.categorize_and_move()
    assert destination.read_text() == "old"
    assert (tmp_path / "sample.json").read_text() == "source"


def test_rewrite_clean_preflight_bundle_contains_local_history(tmp_path, monkeypatch):
    rewrite = load("scripts/c5_git_utils/rewrite_commits.py", "lot12_rewrite_bundle")
    repo = make_repo(tmp_path)
    head = git(repo, "rev-parse", "HEAD")
    monkeypatch.chdir(repo)
    backup = rewrite._ensure_main()
    assert backup.is_file()
    assert f"{head} HEAD" in git(repo, "bundle", "list-heads", str(backup))
    assert git(repo, "rev-parse", "HEAD") == head
    assert (repo / "tracked.txt").read_text() == "local commit"
    clone = tmp_path / "recovered"
    git(tmp_path, "clone", str(backup), str(clone))
    assert git(clone, "rev-parse", "HEAD") == head
    assert (clone / "tracked.txt").read_text() == "local commit"


@pytest.mark.parametrize("kind", ["untracked", "staged", "branch"])
def test_rewrite_rejects_other_unpreserved_states(tmp_path, monkeypatch, kind):
    rewrite = load("scripts/c5_git_utils/rewrite_commits.py", "lot12_rewrite_rejections")
    repo = make_repo(tmp_path)
    head = git(repo, "rev-parse", "HEAD")
    if kind == "untracked":
        (repo / "new.txt").write_text("new work")
    elif kind == "staged":
        (repo / "tracked.txt").write_text("staged work")
        git(repo, "add", "tracked.txt")
    else:
        git(repo, "checkout", "-b", "feature")
    before = git(repo, "status", "--porcelain=v1", "--untracked-files=all")
    monkeypatch.chdir(repo)
    with pytest.raises(RuntimeError):
        rewrite._ensure_main()
    assert git(repo, "rev-parse", "HEAD") == head
    assert git(repo, "status", "--porcelain=v1", "--untracked-files=all") == before
    assert not (repo / ".git/rewrite-backups").exists()


def test_rewrite_failed_backup_stops_before_mutating_main(tmp_path, monkeypatch):
    rewrite = load("scripts/c5_git_utils/rewrite_commits.py", "lot12_rewrite_backup_fail")
    repo = make_repo(tmp_path)
    head = git(repo, "rev-parse", "HEAD")
    monkeypatch.chdir(repo)
    original_run = rewrite.subprocess.run
    def run(command, *args, **kwargs):
        if command[:3] == ["git", "bundle", "create"]:
            raise subprocess.CalledProcessError(1, command)
        return original_run(command, *args, **kwargs)
    monkeypatch.setattr(rewrite.subprocess, "run", run)
    called = []
    monkeypatch.setattr(rewrite, "_create_callback", lambda: called.append("callback"))
    monkeypatch.setattr(rewrite, "_run_filter_repo", lambda backup: called.append("filter"))
    with pytest.raises(subprocess.CalledProcessError):
        rewrite.main()
    assert called == []
    assert git(repo, "rev-parse", "HEAD") == head


@pytest.mark.parametrize("name", ["evilbabylon60.com", "babylon60.com.evil.invalid", "sub.babylon60.com", None, "", "babylon60.com.."])
def test_icloud_does_not_delete_similar_or_missing_names(monkeypatch, name):
    deploy = load("scripts/c5_icloud_deploy.py", "lot12_icloud_names")
    monkeypatch.setenv("CLOUDFLARE_API_TOKEN", "synthetic-token")
    monkeypatch.setenv("APPLE_DOMAIN_CODE", "apple-domain=fixture")
    deleted = []
    def request(method, url, token, data=None):
        if method == "GET" and url.startswith("/zones?"):
            return {"result": [{"id": "zone", "name": "babylon60.com"}]}
        if method == "GET":
            return {"result": [{"id": "neighbor", "name": name, "type": "MX", "content": "mail.invalid"}]}
        if method == "DELETE":
            deleted.append(url)
        return {"success": True}
    monkeypatch.setattr(deploy, "request_cf", request)
    deploy.main()
    assert deleted == []


def test_installer_backup_is_private_and_links_are_idempotent(tmp_path):
    fixture, home = run_installer(tmp_path)
    backups = list(fixture.glob(".babylon60-rule-backup.*"))
    assert len(backups) == 1
    assert backups[0].stat().st_mode & 0o777 == 0o700
    assert (backups[0] / "CLAUDE.md").read_text() == "operator instructions"
    assert (backups[0] / ".github/copilot-instructions.md").read_text() == "copilot operator instructions"
    before = {str(p.relative_to(fixture)): p.read_bytes() for p in backups[0].rglob("*") if p.is_file()}
    env = {**os.environ, "HOME": str(home)}
    result = subprocess.run(["bash", str(fixture / "tools/install_shield.sh")], cwd=fixture, env=env,
                            capture_output=True, text=True, timeout=15)
    assert result.returncode == 0
    assert len(list(fixture.glob(".babylon60-rule-backup.*"))) == 1
    assert {str(p.relative_to(fixture)): p.read_bytes() for p in backups[0].rglob("*") if p.is_file()} == before


@pytest.mark.parametrize("change", ["dirty", "untracked", "commit", "corrupt-backup"])
def test_rewrite_rechecks_state_before_filter_dispatch(tmp_path, monkeypatch, change):
    rewrite = load("scripts/c5_git_utils/rewrite_commits.py", "lot12_rewrite_before_dispatch")
    repo = make_repo(tmp_path)
    monkeypatch.chdir(repo)
    backup = rewrite._ensure_main()
    if change == "dirty":
        (repo / "tracked.txt").write_text("new user work")
    elif change == "untracked":
        (repo / "new.txt").write_text("new user work")
    elif change == "commit":
        (repo / "tracked.txt").write_text("new commit")
        git(repo, "commit", "-am", "new fixture commit")
    else:
        backup.write_bytes(b"invalid bundle")
    head = git(repo, "rev-parse", "HEAD")
    files_before = {p.name: p.read_bytes() for p in repo.iterdir() if p.is_file()}
    with pytest.raises((RuntimeError, subprocess.CalledProcessError)):
        rewrite._run_filter_repo(backup)
    assert git(repo, "rev-parse", "HEAD") == head
    assert {p.name: p.read_bytes() for p in repo.iterdir() if p.is_file()} == files_before


def test_rewrite_backup_parent_symlink_is_rejected(tmp_path, monkeypatch):
    rewrite = load("scripts/c5_git_utils/rewrite_commits.py", "lot12_rewrite_symlink")
    repo = make_repo(tmp_path)
    external = tmp_path / "external"
    external.mkdir()
    (repo / ".git/rewrite-backups").symlink_to(external, target_is_directory=True)
    monkeypatch.chdir(repo)
    with pytest.raises(OSError):
        rewrite._ensure_main()
    assert list(external.iterdir()) == []


@pytest.mark.parametrize("record_type,content,expected", [
    ("MX", "mail.invalid", True), ("TXT", "v=spf1 -all", True),
    ("TXT", "v=spf1", True), ("TXT", "V=SPF1\t-all", True),
    ("TXT", "verification v=spf1 -all", False), ("TXT", "v=spf10 -all", False),
    ("TXT", "apple-domain=already-set", False), ("CNAME", "mail.invalid", False),
])
def test_icloud_exact_apex_policy_and_unrelated_content(monkeypatch, record_type, content, expected):
    deploy = load("scripts/c5_icloud_deploy.py", "lot12_icloud_apex")
    monkeypatch.setenv("CLOUDFLARE_API_TOKEN", "synthetic-token")
    monkeypatch.setenv("APPLE_DOMAIN_CODE", "apple-domain=fixture")
    deleted = []
    def request(method, url, token, data=None):
        if method == "GET" and url.startswith("/zones?"):
            return {"result": [{"id": "zone", "name": "babylon60.com"}]}
        if method == "GET":
            return {"result": [{"id": "record", "name": "BABYLON60.COM.", "type": record_type, "content": content}]}
        if method == "DELETE":
            deleted.append(url)
        return {"success": True}
    monkeypatch.setattr(deploy, "request_cf", request)
    deploy.main()
    assert bool(deleted) is expected



def test_installer_preserves_regular_instruction_bytes_and_modes(tmp_path):
    content = "custom instructions: mañana\nsecond line\n"
    def prepare(fixture):
        (fixture / "CLAUDE.md").chmod(0o640)
        for name in [".cursorrules", ".windsurfrules", ".codexrules", ".clinerules", ".roorules"]:
            (fixture / name).write_text(name + " private text")
    fixture, _ = run_installer(tmp_path, instruction=content, prepare=prepare)
    backup = next(fixture.glob(".babylon60-rule-backup.*"))
    assert (backup / "CLAUDE.md").read_text() == content
    assert (backup / "CLAUDE.md").stat().st_mode & 0o777 == 0o640
    for name in [".cursorrules", ".windsurfrules", ".codexrules", ".clinerules", ".roorules"]:
        assert (backup / name).read_text() == name + " private text"
        assert os.readlink(fixture / name) == ".babylon60rules"
    assert (fixture / ".babylon60rules").read_text() == "canonical fixture rules\n"


def test_installer_preserves_noncanonical_symlink_metadata(tmp_path):
    def prepare(fixture):
        (fixture / "CLAUDE.md").unlink()
        (fixture / "CLAUDE.md").symlink_to("custom-missing.md")
    fixture, _ = run_installer(tmp_path, prepare=prepare)
    backup = next(fixture.glob(".babylon60-rule-backup.*"))
    assert (backup / "CLAUDE.md").is_symlink()
    assert os.readlink(backup / "CLAUDE.md") == "custom-missing.md"
    assert os.readlink(fixture / "CLAUDE.md") == ".babylon60rules"



def test_queue_serializes_independent_processes(tmp_path, monkeypatch):
    host = load("scripts/c5_cli/moskv_native_host.py", "lot12_queue_processes")
    queue = tmp_path / "queue.json"
    monkeypatch.setattr(host, "QUEUE_FILE", queue)
    code = """import importlib.util,sys
spec=importlib.util.spec_from_file_location('fixture_native',sys.argv[1])
m=importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)
from pathlib import Path
m.QUEUE_FILE=Path(sys.argv[2])
for i in range(16):m.enqueue_prompt(sys.argv[3]+':'+str(i))
"""
    workers = [subprocess.Popen([sys.executable, "-c", code, str(ROOT / "scripts/c5_cli/moskv_native_host.py"),
                                 str(queue), str(index)], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
               for index in range(4)]
    try:
        for worker in workers:
            _, stderr = worker.communicate(timeout=20)
            assert worker.returncode == 0, stderr
    finally:
        for worker in workers:
            if worker.poll() is None:
                worker.kill()
                worker.wait()
    expected = {f"{worker}:{item}" for worker in range(4) for item in range(16)}
    assert set(host.queued_prompts()) == expected
    assert len(host.queued_prompts()) == 64
    assert {host.get_next_prompt() for _ in range(64)} == expected
    assert host.queued_prompts() == []



@pytest.mark.parametrize("kind", ["external-symlink", "dangling-symlink", "regular-file"])
def test_installer_rejects_unsafe_copilot_parent_before_mutating_instructions(tmp_path, kind):
    external = tmp_path / "external"
    external.mkdir()
    (external / "copilot-instructions.md").write_text("external instructions")
    def prepare(fixture):
        (fixture / ".github/copilot-instructions.md").unlink()
        (fixture / ".github").rmdir()
        if kind == "regular-file":
            (fixture / ".github").write_text("existing non-directory")
        else:
            target = "../external" if kind == "external-symlink" else "../missing"
            (fixture / ".github").symlink_to(target, target_is_directory=True)
    fixture, home = run_installer(tmp_path, prepare=prepare, expect_success=False)
    assert (external / "copilot-instructions.md").read_text() == "external instructions"
    assert not (external / "copilot-instructions.md").is_symlink()
    assert (fixture / "CLAUDE.md").read_text() == "operator instructions"
    assert not (fixture / "CLAUDE.md").is_symlink()
    assert not (fixture / ".cursorrules").exists()
    assert not (home / ".babylon/shield").exists()



def test_queue_cold_start_barrier_keeps_every_accepted_prompt(tmp_path, monkeypatch):
    from concurrent.futures import ThreadPoolExecutor
    from threading import Barrier
    hosts = [load("scripts/c5_cli/moskv_native_host.py", f"lot12_queue_cold_{i}") for i in range(3)]
    for round_index in range(12):
        directory = tmp_path / f"cold-{round_index}"
        directory.mkdir(mode=0o700)
        queue = directory / "queue.json"
        for host in hosts:
            monkeypatch.setattr(host, "QUEUE_FILE", queue)
        start = Barrier(6)
        def enqueue(index):
            start.wait(timeout=10)
            return hosts[index % 3].enqueue_prompt(str(index))
        with ThreadPoolExecutor(max_workers=6) as executor:
            counts = list(executor.map(enqueue, range(6)))
        assert sorted(counts) == list(range(1, 7))
        assert set(hosts[0].queued_prompts()) == {str(i) for i in range(6)}
        assert (directory / ".queue.lock").stat().st_nlink == 1


def test_queue_lock_creation_retries_only_transient_missing_name(tmp_path, monkeypatch):
    host = load("scripts/c5_cli/moskv_native_host.py", "lot12_queue_lock_retry")
    monkeypatch.setattr(host, "QUEUE_FILE", tmp_path / "queue.json")
    original_open = host.os.open
    attempts = []
    def open_file(path, flags, *args, **kwargs):
        if path == ".queue.lock":
            attempts.append(flags)
            if len(attempts) <= 2:
                raise FileNotFoundError("fixture concurrent cold start")
        return original_open(path, flags, *args, **kwargs)
    monkeypatch.setattr(host.os, "open", open_file)
    assert host.enqueue_prompt("accepted") == 1
    assert len(attempts) == 3
    assert all(flags & os.O_EXCL for flags in attempts)


def test_queue_lock_creation_retry_is_bounded(tmp_path, monkeypatch):
    host = load("scripts/c5_cli/moskv_native_host.py", "lot12_queue_lock_bound")
    monkeypatch.setattr(host, "QUEUE_FILE", tmp_path / "queue.json")
    original_open = host.os.open
    attempts = []
    def open_file(path, flags, *args, **kwargs):
        if path == ".queue.lock":
            attempts.append(flags)
            raise FileNotFoundError("fixture missing name persists")
        return original_open(path, flags, *args, **kwargs)
    monkeypatch.setattr(host.os, "open", open_file)
    with pytest.raises(RuntimeError, match="bounded"):
        host.enqueue_prompt("not accepted")
    assert len(attempts) == 8
    assert not host.QUEUE_FILE.exists()
