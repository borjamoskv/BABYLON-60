"""
Unit & Integration Tests for BABYLON-60 Zero-Secret Gate & DevSecOps Attestation.
Verifies pre-commit hook installation, .gitleaks.toml configuration integrity,
active working tree cleanliness, canary leak interception, and Zero-Trust scaffold.
"""

from contextlib import ExitStack
import errno
import json
import os
import shutil
import stat
import subprocess
import tomllib
from pathlib import Path
import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent


def copy_git_candidates(source: Path, destination: Path) -> None:
    """Copy current Git candidates without following links or reading ignored private files."""
    files = subprocess.run(
        ["git", "-C", str(source), "ls-files", "--cached", "--others", "--exclude-standard", "-z"],
        check=True,
        capture_output=True,
    ).stdout.split(b"\0")
    for raw_path in files:
        if not raw_path:
            continue
        relative = Path(os.fsdecode(raw_path))
        if relative.is_absolute() or ".." in relative.parts:
            raise ValueError("Git candidate must remain within the source tree")
        try:
            with ExitStack() as descriptors:
                directory = os.open(source, os.O_RDONLY | os.O_DIRECTORY)
                descriptors.callback(os.close, directory)
                for part in relative.parts[:-1]:
                    directory = os.open(part, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=directory)
                    descriptors.callback(os.close, directory)
                descriptor = os.open(relative.name, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=directory)
                if not stat.S_ISREG(os.fstat(descriptor).st_mode):
                    os.close(descriptor)
                    continue
                with os.fdopen(descriptor, "rb") as stream:
                    target = destination / relative
                    target.parent.mkdir(parents=True, exist_ok=True)
                    with target.open("wb") as output:
                        shutil.copyfileobj(stream, output)
        except FileNotFoundError:
            # A tracked deletion has no current contents to publish.
            continue
        except OSError as error:
            if error.errno in (errno.ELOOP, errno.ENOTDIR):
                continue
            raise


def test_gitleaks_config_syntax() -> None:
    """Ensures .gitleaks.toml is present and valid TOML."""
    config_path = REPO_ROOT / ".gitleaks.toml"
    assert config_path.exists(), ".gitleaks.toml must exist in repo root"
    content = config_path.read_text(encoding="utf-8")
    data = tomllib.loads(content)
    assert "allowlist" in data, "Must specify allowlist section"
    assert "paths" in data["allowlist"], "Must define allowlisted paths"
    assert "regexes" in data["allowlist"], "Must define allowlisted regexes"


def test_pre_commit_hook_installed() -> None:
    """Ensures git pre-commit hook is active, executable, and enforces gitleaks protect."""
    hook_path = REPO_ROOT / ".git" / "hooks" / "pre-commit"
    if not (REPO_ROOT / ".git").is_dir():
        pytest.skip("Not a git repository directory")
    if not hook_path.exists() and (os.environ.get("CI") or os.environ.get("GITHUB_ACTIONS")):
        pytest.skip("CI environment clone does not provision local git hooks by default")
    assert hook_path.exists(), ".git/hooks/pre-commit must be installed"
    assert os.access(str(hook_path), os.X_OK), "pre-commit hook must be executable"
    content = hook_path.read_text(encoding="utf-8")
    assert "gitleaks protect --staged" in content, "pre-commit hook must enforce gitleaks protect"


@pytest.mark.skipif(not shutil.which("gitleaks"), reason="gitleaks binary not installed")
def test_active_working_tree_zero_secrets(tmp_path: Path) -> None:
    """Check tracked and nonignored untracked contents intended for publication."""
    tree = tmp_path / "candidates"
    tree.mkdir()
    copy_git_candidates(REPO_ROOT, tree)
    cmd = [
        "gitleaks",
        "detect",
        "--config",
        str(REPO_ROOT / ".gitleaks.toml"),
        "--source",
        str(tree),
        "--no-git",
        "--redact",
        "--no-banner",
    ]
    res = subprocess.run(cmd, cwd=REPO_ROOT, capture_output=True, text=True, timeout=60)
    assert res.returncode == 0, "Gitleaks detected secrets in Git candidates: " + res.stdout + " " + res.stderr


@pytest.mark.skipif(not shutil.which("gitleaks"), reason="gitleaks binary not installed")
def test_canary_leak_interception(tmp_path: Path) -> None:
    """Falsification test: verifies that an unmitigated fake token IS flagged by gitleaks."""
    canary_file = tmp_path / "leaked_key.py"
    fake_token = "sk-" + "proj-" + "abc1234567890abcdef" * 3
    canary_file.write_text(f'OPENAI_KEY = "{fake_token}"\n', encoding="utf-8")
    report = tmp_path / "report.json"
    cmd = [
        "gitleaks",
        "detect",
        "--source",
        str(tmp_path),
        "--no-git",
        "--redact",
        "--no-banner",
        "--report-format",
        "json",
        "--report-path",
        str(report),
    ]
    res = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
    assert res.returncode == 1, "Gitleaks should reject an active secret pattern"
    assert {entry["RuleID"] for entry in json.loads(report.read_text())} & {"openai-api-key", "generic-api-key"}


@pytest.mark.skipif(not shutil.which("gitleaks"), reason="gitleaks binary not installed")
def test_git_candidates_preserve_ignored_and_tracked_secret_boundary(tmp_path: Path) -> None:
    repository = tmp_path / "repository"
    repository.mkdir()
    subprocess.run(["git", "init", str(repository)], check=True, capture_output=True)
    (repository / ".gitignore").write_text("*.pem\n", encoding="utf-8")
    token = "sk-" + "proj-" + "abc1234567890abcdef" * 3
    ignored = repository / "keys" / "local.pem"
    ignored.parent.mkdir()
    ignored.write_text(f'OPENAI_KEY = "{token}"\n', encoding="utf-8")
    clean = tmp_path / "clean"
    clean.mkdir()
    copy_git_candidates(repository, clean)
    assert not (clean / "keys" / "local.pem").exists()
    subprocess.run(["git", "-C", str(repository), "add", "--force", "keys/local.pem"], check=True)
    (repository / "untracked.py").write_text(f'OPENAI_KEY = "{token}"\n', encoding="utf-8")
    candidates = tmp_path / "candidates"
    candidates.mkdir()
    copy_git_candidates(repository, candidates)
    report = tmp_path / "findings.json"
    result = subprocess.run(
        [
            "gitleaks",
            "detect",
            "--config",
            str(REPO_ROOT / ".gitleaks.toml"),
            "--source",
            str(candidates),
            "--no-git",
            "--redact",
            "--no-banner",
            "--report-format",
            "json",
            "--report-path",
            str(report),
        ],
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert result.returncode == 1
    detected = {Path(entry["File"]).relative_to(candidates).as_posix() for entry in json.loads(report.read_text())}
    assert {"keys/local.pem", "untracked.py"} <= detected


def test_devsecops_attestation_engine() -> None:
    """Verifies that C5 DevSecOps Zero-Trust verification passes 100%."""
    import sys

    sys.path.insert(0, str(REPO_ROOT / "scripts"))
    from c5_verifiers.devsecops_attest import audit_devsecops_invariants

    passed = audit_devsecops_invariants()
    assert passed is True, "C5 DevSecOps Zero-Trust attestation must pass"
