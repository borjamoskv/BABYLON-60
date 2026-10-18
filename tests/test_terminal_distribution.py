"""Distribution tests use isolated fixtures; no install or desktop mutation."""

import os
import shutil
import subprocess
import zipfile
from pathlib import Path

import pytest

ROOT = Path(os.environ.get("BABYLON_TEST_SOURCE", str(Path(__file__).absolute().parents[1])))


def fixture_tree(tmp_path):
    root = tmp_path / "checkout with spaces"
    (root / "scripts").mkdir(parents=True)
    for rel in ["install.sh", "scripts/package_release.sh", "pyproject.toml", "uv.lock", "README.md", "LICENSE"]:
        shutil.copyfile(ROOT / rel, root / rel)
    # Package the real current Python sources, including newly added verification.
    for rel in ["01_KISH_ENGINE/babylon60", "02_EDIN_SWARMS/agents_archi"]:
        shutil.copytree(ROOT / rel, root / rel, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
    # Only prevents the legacy bundler from touching ~/Applications during red tests.
    (root / "Babylon60.app").mkdir()
    (root / "ui").mkdir()
    (root / "ui/index.html").write_text("legacy marker")
    return root


def test_installer_uses_checkout_from_any_directory(tmp_path):
    root = fixture_tree(tmp_path)
    result = subprocess.run(
        ["bash", str(root / "install.sh"), "--dry-run"], cwd=root, capture_output=True, text=True, timeout=10
    )
    assert result.returncode == 0, result.stderr
    assert "BABYLON_TERMINAL_VERIFIED" in result.stdout
    (root / "ui/index.html").unlink()
    result = subprocess.run(
        ["bash", str(root / "install.sh"), "--dry-run"], cwd=tmp_path, capture_output=True, text=True, timeout=10
    )
    assert result.returncode == 0, result.stderr
    assert str(root) in result.stdout


def test_terminal_bundle_contains_importable_cli_and_mcp(tmp_path):
    root = fixture_tree(tmp_path)
    result = subprocess.run(
        ["bash", str(root / "scripts/package_release.sh"), str(tmp_path / "output")],
        cwd=root,
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert result.returncode == 0, result.stderr
    bundles = list((tmp_path / "output").glob("*.zip"))
    assert len(bundles) == 1
    unpack = tmp_path / "unpacked"
    with zipfile.ZipFile(bundles[0]) as bundle:
        names = bundle.namelist()
        assert "01_KISH_ENGINE/babylon60/verification/hardware_attestation.py" in names
        assert "01_KISH_ENGINE/babylon60/guards/c5_biometric_gate.swift" in names
        assert "scripts/babylon_launcher.py" not in names
        assert not any(".app/" in name or name.startswith("ui/") for name in names)
        bundle.extractall(unpack)
    import sys

    env = os.environ.copy()
    env["PYTHONPATH"] = str(unpack / "01_KISH_ENGINE")
    for module in ["babylon60.cli.main_dispatcher", "babylon60.mcp.cortex_mcp_server"]:
        run = subprocess.run(
            [sys.executable, "-m", module, "--help"], cwd=unpack, env=env, capture_output=True, text=True, timeout=10
        )
        assert run.returncode == 0, run.stderr
    run = subprocess.run(
        ["bash", str(unpack / "install.sh"), "--dry-run"], cwd=tmp_path, capture_output=True, text=True, timeout=10
    )
    assert run.returncode == 0, run.stderr


@pytest.mark.skipif(
    os.environ.get("BABYLON_TEST_INSTALL_BUNDLE") != "1",
    reason="release integration: requires uv and cached locked dependencies",
)
def test_fresh_bundle_installs_declared_dependencies_and_runs_mcp(tmp_path):
    """A host Python with undeclared packages must not mask a broken release."""
    root = fixture_tree(tmp_path)
    output = tmp_path / "release"
    subprocess.run(
        ["bash", str(root / "scripts/package_release.sh"), str(output)],
        check=True,
        capture_output=True,
        text=True,
        timeout=30,
    )
    unpack = tmp_path / "fresh"
    with zipfile.ZipFile(next(output.glob("*.zip"))) as bundle:
        bundle.extractall(unpack)
    env = os.environ.copy()
    env.pop("PYTHONPATH", None)
    env["UV_OFFLINE"] = "1"
    env["BABYLON_CAUSAL_GATE_DB"] = str(tmp_path / "gate.db")
    install = subprocess.run(
        ["bash", str(unpack / "install.sh")], cwd=tmp_path, env=env, capture_output=True, text=True, timeout=60
    )
    assert install.returncode == 0, install.stderr
    assert "CLI installed:" in install.stdout
    import json

    initialize = json.dumps({"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}})
    server = subprocess.run(
        [str(unpack / ".venv/bin/babylon60-mcp"), "--ledger", str(tmp_path / "ledger.db")],
        input=initialize + "\n",
        cwd=tmp_path,
        env=env,
        capture_output=True,
        text=True,
        timeout=10,
    )
    assert server.returncode == 0, server.stderr
    responses = [json.loads(line) for line in server.stdout.splitlines()]
    assert responses[0]["id"] == 1 and "serverInfo" in responses[0]["result"]
