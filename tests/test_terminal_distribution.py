"""Distribution tests use isolated fixtures; no install or desktop mutation."""

import os
import hashlib
import json
import re
import shutil
import subprocess
import zipfile
from pathlib import Path
from urllib.parse import unquote, urlsplit

import pytest

from scripts.c5_quality_gates.governance_documents import GOVERNANCE_DOCUMENTS, validate_local_links

ROOT = Path(os.environ.get("BABYLON_TEST_SOURCE", str(Path(__file__).absolute().parents[1])))


def fixture_tree(tmp_path):
    root = tmp_path / "checkout with spaces"
    (root / "scripts").mkdir(parents=True)
    (root / "docs").mkdir(parents=True)
    for rel in [
        "install.sh",
        "install.ps1",
        "scripts/package_release.sh",
        "scripts/c5_quality_gates/prompt_exergy_oracle.py",
        "babylon.toml",
        "Cargo.toml",
        "Cargo.lock",
        "WHY_BABYLON_60.md",
        "pyproject.toml",
        "uv.lock",
        "README.md",
        "LICENSE",
        "docs/skills.json",
        "docs/skills-lock.json",
        "skills-lock.json",
        ".babylon60rules",
        "AGENTS.md",
        "docs/03_guides/agent_contracts.md",
        "docs/03_guides/guide_portable_signature.md",
        "docs/03_guides/guide_agent_workflow.md",
        "docs/01_spec/INVARIANTS_RED_TEAM_FALSIFICATION.md",
    ]:
        (root / rel).parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ROOT / rel, root / rel)
    runner = root / "scripts/c5_quality_gates/experience_pilot.py"
    runner.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(ROOT / "scripts/c5_quality_gates/experience_pilot.py", runner)
    # Package the real current Python sources, including newly added verification.
    for rel in ["01_KISH_ENGINE/babylon60", "02_EDIN_SWARMS/agents_archi", ".agents/skills"]:
        shutil.copytree(ROOT / rel, root / rel, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
    for rel in [
        "docs/03_guides/guide_codex_first_use.md",
        "docs/03_guides/guide_first_conversation_pilot.md",
        "docs/security/governance-comparison-2026-10-24.md",
        "verify.sh",
        "scripts/verify_release.sh",
    ]:
        source = ROOT / rel
        if source.is_file():
            destination = root / rel
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source, destination)
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
    assert Path(result.stdout.strip()) == bundles[0]
    unpack = tmp_path / "unpacked"
    with zipfile.ZipFile(bundles[0]) as bundle:
        names = bundle.namelist()
        for name in GOVERNANCE_DOCUMENTS:
            assert bundle.read(name) == (ROOT / name).read_bytes(), f"Stale governance in bundle: {name}"
        oracle = "scripts/c5_quality_gates/prompt_exergy_oracle.py"
        assert bundle.read(oracle) == (ROOT / oracle).read_bytes()
        assert "install.ps1" in names
        assert "01_KISH_ENGINE/babylon60/verification/hardware_attestation.py" in names
        assert "01_KISH_ENGINE/babylon60/guards/c5_biometric_gate.swift" in names
        for path in [
            "01_KISH_ENGINE/babylon60/session_profile.md",
            "01_KISH_ENGINE/babylon60/mcp_instructions.md",
            "01_KISH_ENGINE/babylon60/experience.py",
            "01_KISH_ENGINE/babylon60/onboarding.py",
            "docs/03_guides/guide_codex_first_use.md",
            "docs/03_guides/guide_first_conversation_pilot.md",
            "scripts/c5_quality_gates/experience_pilot.py",
            ".babylon60rules",
            "AGENTS.md",
            "docs/03_guides/agent_contracts.md",
            "docs/03_guides/guide_portable_signature.md",
            "docs/03_guides/guide_agent_workflow.md",
        ]:
            assert path in names
        assert "scripts/babylon_launcher.py" not in names
        assert not any(".app/" in name or name.startswith("ui/") for name in names)
        bundle.extractall(unpack)
    assert validate_local_links([unpack / name for name in GOVERNANCE_DOCUMENTS]) == []
    for name in [
        "docs/03_guides/guide_codex_first_use.md",
        "docs/03_guides/guide_first_conversation_pilot.md",
        "01_KISH_ENGINE/babylon60/presentation.md",
    ]:
        guide = unpack / name
        for target in re.findall(r"\]\(([^)]+)\)", guide.read_text(encoding="utf-8")):
            parsed = urlsplit(target)
            if parsed.scheme or parsed.netloc or not parsed.path:
                continue
            destination = (guide.parent / unquote(parsed.path)).resolve()
            assert destination.is_relative_to(unpack), f"{name}: link escapes bundle: {target}"
            assert destination.is_file(), f"{name}: missing linked file: {target}"
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

    pilot = tmp_path / "first-conversation-pilot"
    run = subprocess.run(
        [sys.executable, str(unpack / "scripts/c5_quality_gates/experience_pilot.py"), "prepare", str(pilot)],
        cwd=unpack,
        env=env,
        capture_output=True,
        text=True,
        timeout=10,
    )
    assert run.returncode == 0, run.stderr
    assert (pilot / "manifest.json").is_file()


def test_bundle_is_reproducible_and_never_embeds_historical_evidence(tmp_path):
    root = fixture_tree(tmp_path)
    generated = (
        "RELEASE_MANIFEST.json",
        "RELEASE_MANIFEST.json.sig",
        "evidence.json",
        "claims.lock",
        "sbom.cargo.cdx.json",
        "sbom.python.cdx.json",
    )
    for name in generated:
        (root / name).write_text('{"historical": true}')
    results = []
    for run in ("first", "second"):
        result = subprocess.run(
            ["bash", str(root / "scripts/package_release.sh"), str(tmp_path / run)],
            cwd=root,
            capture_output=True,
            text=True,
            timeout=30,
        )
        assert result.returncode == 0, result.stderr
        results.append(Path(result.stdout.strip()))
    assert results[0].read_bytes() == results[1].read_bytes()
    with zipfile.ZipFile(results[0]) as bundle:
        assert set(generated).isdisjoint(bundle.namelist())
        inventory = json.loads(bundle.read("SOURCE_MANIFEST.json"))
        assert inventory["authority"] == "unsigned_content_inventory"
        assert inventory["source_commit"] is None
        assert inventory["source_state"] == "unversioned"
        assert set(inventory["files_sha256"]) == set(bundle.namelist()) - {"SOURCE_MANIFEST.json"}
        for name, digest in inventory["files_sha256"].items():
            assert hashlib.sha256(bundle.read(name)).hexdigest() == digest


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
