"""Independent confined S4 adversarial checks; never runs real providers or Git rewrite."""

from __future__ import annotations
import importlib.util
import os
from pathlib import Path
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
import pytest

ROOT = Path(__file__).absolute().parents[5]


def load(relative, name):
    spec = importlib.util.spec_from_file_location(name, ROOT / relative)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture(autouse=True)
def confined(tmp_path, monkeypatch):
    home = tmp_path / "home"
    home.mkdir()
    monkeypatch.setenv("HOME", str(home))
    monkeypatch.setenv("BABYLON60_SIGNING_SEED", "00" * 32)
    monkeypatch.delenv("CORTEX_VAULT_KEY", raising=False)


def test_queue_lock_link_and_corrupt_queue_preserved(tmp_path, monkeypatch):
    host = load("scripts/c5_cli/moskv_native_host.py", "review_s4_host")
    private = tmp_path / "private"
    private.mkdir(mode=0o700)
    victim = tmp_path / "victim"
    victim.write_text("unchanged")
    victim.chmod(0o600)
    (private / ".queue.lock").symlink_to(victim)
    monkeypatch.setattr(host, "QUEUE_FILE", private / "prompts.json")
    with pytest.raises(OSError):
        host.enqueue_prompt("reject")
    assert victim.read_text() == "unchanged"
    (private / ".queue.lock").unlink()
    host.QUEUE_FILE.write_text("{bad")
    host.QUEUE_FILE.chmod(0o600)
    with pytest.raises(ValueError):
        host.clear_prompt_queue()
    assert host.QUEUE_FILE.read_text() == "{bad"


def test_queue_concurrent_instances_and_real_importable_package(tmp_path, monkeypatch):
    hosts = [load("scripts/c5_cli/moskv_native_host.py", "review_s4_host_" + str(i)) for i in range(3)]
    for host in hosts:
        monkeypatch.setattr(host, "QUEUE_FILE", tmp_path / "prompts.json")
    with ThreadPoolExecutor(max_workers=6) as pool:
        for n in (6, 6, 50):
            values = {str(i) for i in range(n)}
            assert sorted(pool.map(lambda i: hosts[i % 3].enqueue_prompt(str(i)), range(n))) == list(range(1, n + 1))
            assert set(pool.map(lambda i: hosts[i % 3].get_next_prompt(), range(n))) == values
    assert hosts[0].queued_prompts() == []
    purge = load("01_KISH_ENGINE/babylon60/cortex/cortex_purge_anergy.py", "review_s4_purge")
    package = tmp_path / "pkg"
    package.mkdir()
    (package / "__init__.py").write_text("from .plugin import VALUE\n")
    (package / "plugin.py").write_text("VALUE = 1729\n")
    for key in ("PROJECT_ROOT",):
        monkeypatch.setattr(purge, key, str(package))
    for key in ("ARCHIVE_SCRIPTS", "ARCHIVE_DATA", "ARCHIVE_DBS"):
        monkeypatch.setattr(purge, key, str(package / ".archive" / key))
    purge.ensure_dirs()
    purge.categorize_and_move()
    spec = importlib.util.spec_from_file_location(
        "review_kept_package", package / "__init__.py", submodule_search_locations=[str(package)]
    )
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    assert module.VALUE == 1729


def git(repo, *args):
    return (
        subprocess.check_output(
            ["git", "-c", "commit.gpgsign=false", "-c", "core.hooksPath=/dev/null", *args],
            cwd=repo,
            stderr=subprocess.DEVNULL,
        )
        .decode()
        .strip()
    )


def test_rewrite_verified_bundle_restores_stash_branch_and_head(tmp_path, monkeypatch):
    repo = tmp_path / "repo"
    repo.mkdir()
    git(repo, "init", "-b", "main")
    git(repo, "config", "user.name", "Fixture")
    git(repo, "config", "user.email", "fixture@example.invalid")
    (repo / "data").write_text("one")
    git(repo, "add", "data")
    git(repo, "commit", "-m", "one")
    git(repo, "branch", "side")
    (repo / "data").write_text("stashed work")
    git(repo, "stash", "push", "-m", "saved")
    (repo / "data").write_text("two")
    git(repo, "commit", "-am", "two")
    head = git(repo, "rev-parse", "HEAD")
    stash = git(repo, "rev-parse", "refs/stash")
    side = git(repo, "rev-parse", "side")
    rewrite = load("scripts/c5_git_utils/rewrite_commits.py", "review_s4_rewrite")
    monkeypatch.chdir(repo)
    backup = rewrite._ensure_main()
    clone = tmp_path / "clone"
    git(tmp_path, "clone", str(backup), str(clone))
    assert git(clone, "rev-parse", "HEAD") == head
    assert (clone / "data").read_text() == "two"
    heads = git(repo, "bundle", "list-heads", str(backup))
    assert stash + " refs/stash" in heads and side + " refs/heads/side" in heads
    assert backup.stat().st_mode & 0o777 == 0o600


def test_dns_only_normalized_exact_apex_policy(monkeypatch):
    mod = load("scripts/c5_icloud_deploy.py", "review_s4_dns")
    monkeypatch.setenv("CLOUDFLARE_API_TOKEN", "fixture-only")
    monkeypatch.setenv("APPLE_DOMAIN_CODE", "fixture-only")
    removed = []
    records = [
        dict(id="apexmx", name="BABYLON60.COM.", type="MX", content="mail.invalid"),
        dict(id="apexspf", name="babylon60.com", type="TXT", content="V=SPF1 -all"),
        dict(id="neighbor", name="a.babylon60.com", type="MX", content="mail.invalid"),
        dict(id="spfmarker", name="babylon60.com", type="TXT", content="prefix v=spf1 -all"),
    ]

    def request(method, url, token, data=None):
        if url.startswith("/zones?"):
            return {"result": [{"id": "fixture"}]}
        if method == "GET":
            return {"result": records}
        if method == "DELETE":
            removed.append(url.rsplit("/", 1)[-1])
        return {"success": True}

    monkeypatch.setattr(mod, "request_cf", request)
    mod.main()
    assert removed == ["apexmx", "apexspf"]


def test_dns_http_error_aborts_before_other_operations(monkeypatch):
    import io
    import urllib.error

    mod = load("scripts/c5_icloud_deploy.py", "review_s4_dns_error")
    calls = []

    def error(*args, **kwargs):
        calls.append(args[0].method)
        raise urllib.error.HTTPError(
            "https://fixture.invalid", 403, "fixture refusal", {}, io.BytesIO(b"fixture refusal")
        )

    monkeypatch.setattr(mod.urllib.request, "urlopen", error)
    with pytest.raises(SystemExit) as exc:
        mod.request_cf("GET", "/zones?name=babylon60.com", "fixture-only")
    assert exc.value.code == 1
    assert calls == ["GET"]


def test_rewrite_rejects_backup_directory_link_before_history_mutation(tmp_path, monkeypatch):
    repo = tmp_path / "repo"
    repo.mkdir()
    git(repo, "init", "-b", "main")
    git(repo, "config", "user.name", "Fixture")
    git(repo, "config", "user.email", "fixture@example.invalid")
    (repo / "data").write_text("keep")
    git(repo, "add", "data")
    git(repo, "commit", "-m", "keep")
    head = git(repo, "rev-parse", "HEAD")
    external = tmp_path / "outside"
    external.mkdir(mode=0o700)
    (repo / ".git/rewrite-backups").symlink_to(external, target_is_directory=True)
    rewrite = load("scripts/c5_git_utils/rewrite_commits.py", "review_s4_rewrite_unsafe")
    monkeypatch.chdir(repo)
    with pytest.raises(OSError):
        rewrite._ensure_main()
    assert git(repo, "rev-parse", "HEAD") == head
    assert (repo / "data").read_text() == "keep"
    assert list(external.iterdir()) == []


def installer(tmp_path, github_link=False):
    fixture = tmp_path / "fixture"
    fixture.mkdir()
    tools = fixture / "tools"
    tools.mkdir()
    home = tmp_path / "install_home"
    home.mkdir()
    (fixture / ".babylon60rules").write_text("canonical")
    (fixture / "CLAUDE.md").write_text("original workspace instruction")
    external = tmp_path / "external"
    external.mkdir()
    if github_link:
        (external / "copilot-instructions.md").write_text("external original instruction")
        (fixture / ".github").symlink_to(external, target_is_directory=True)
    else:
        (fixture / ".github").mkdir()
        (fixture / ".github/copilot-instructions.md").write_text("original copilot")
    script = tools / "install_shield.sh"
    script.write_text(
        (ROOT / "tools/install_shield.sh")
        .read_text()
        .replace('LOCK_DIR="/tmp/babylon_shield_install.lock"', 'LOCK_DIR="' + str(tmp_path / "install-lock") + '"')
    )
    run = subprocess.run(
        ["bash", str(script)],
        cwd=fixture,
        env={**os.environ, "HOME": str(home)},
        capture_output=True,
        text=True,
        timeout=15,
    )
    return fixture, external, run


def test_installer_preserves_bytes_and_symlink_identity(tmp_path):
    fixture, _, run = installer(tmp_path)
    assert run.returncode == 0, run.stderr
    backups = list(fixture.glob(".babylon60-rule-backup.*"))
    assert len(backups) == 1
    assert (backups[0] / "CLAUDE.md").read_text() == "original workspace instruction"
    assert (backups[0] / ".github/copilot-instructions.md").read_text() == "original copilot"
    assert os.readlink(fixture / "CLAUDE.md") == ".babylon60rules"


def test_installer_refuses_symlinked_copilot_directory(tmp_path):
    _, external, run = installer(tmp_path, github_link=True)
    target = external / "copilot-instructions.md"
    assert target.is_file() and not target.is_symlink(), "installer moved external instruction through .github symlink"
    assert target.read_text() == "external original instruction"
    assert run.returncode != 0, "installer must reject parent symlink before external instruction mutation"
