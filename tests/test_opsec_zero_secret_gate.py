"""
Unit & Integration Tests for BABYLON-60 Zero-Secret Gate & DevSecOps Attestation.
Verifies pre-commit hook installation, .gitleaks.toml configuration integrity,
active working tree cleanliness, canary leak interception, and Zero-Trust scaffold.
"""

import os
import shutil
import subprocess
import tomllib
from pathlib import Path
import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent


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
    assert hook_path.exists(), ".git/hooks/pre-commit must be installed"
    assert os.access(str(hook_path), os.X_OK), "pre-commit hook must be executable"
    content = hook_path.read_text(encoding="utf-8")
    assert "gitleaks protect --staged" in content, "pre-commit hook must enforce gitleaks protect"


@pytest.mark.skipif(not shutil.which("gitleaks"), reason="gitleaks binary not installed")
def test_active_working_tree_zero_secrets() -> None:
    """Verifies that the entire working tree passes Gitleaks with zero leaks."""
    cmd = ["gitleaks", "detect", "--config=.gitleaks.toml", "--no-git", "--verbose"]
    res = subprocess.run(cmd, cwd=str(REPO_ROOT), capture_output=True, text=True)
    assert res.returncode == 0, "Gitleaks detected secrets in working tree: " + res.stdout + " " + res.stderr


@pytest.mark.skipif(not shutil.which("gitleaks"), reason="gitleaks binary not installed")
def test_canary_leak_interception(tmp_path: Path) -> None:
    """Falsification test: verifies that an unmitigated fake token IS flagged by gitleaks."""
    canary_file = tmp_path / "leaked_key.py"
    fake_token = "sk-" + "proj-" + "abc1234567890abcdef" * 3
    canary_file.write_text(f'OPENAI_KEY = "{fake_token}"\n', encoding="utf-8")
    cmd = ["gitleaks", "detect", "--source", str(tmp_path), "--no-git", "--verbose"]
    res = subprocess.run(cmd, capture_output=True, text=True)
    assert res.returncode != 0, "Gitleaks should fail when an active secret pattern is detected"
    assert "openai-api-key" in res.stdout or "generic-api-key" in res.stdout


def test_devsecops_attestation_engine() -> None:
    """Verifies that C5 DevSecOps Zero-Trust verification passes 100%."""
    import sys

    sys.path.insert(0, str(REPO_ROOT / "scripts"))
    from c5_verifiers.devsecops_attest import audit_devsecops_invariants

    passed = audit_devsecops_invariants()
    assert passed is True, "C5 DevSecOps Zero-Trust attestation must pass"
