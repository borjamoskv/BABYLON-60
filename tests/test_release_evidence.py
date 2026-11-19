"""Release evidence must describe this source and never invent signing authority."""

import hashlib
import json
from pathlib import Path
import shutil
import zipfile

import pytest

from scripts.c5_quality_gates import compile_claims_manifest as compiler


@pytest.fixture
def evidence_root(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    for lockfile in ("Cargo.lock", "uv.lock"):
        shutil.copyfile(compiler.REPO_ROOT / lockfile, tmp_path / lockfile)
    monkeypatch.setattr(compiler, "REPO_ROOT", tmp_path)
    monkeypatch.setattr(compiler, "get_git_commit", lambda: "a" * 40)
    monkeypatch.setattr(compiler, "source_tree_digest", lambda root: "d" * 64)
    monkeypatch.delenv("BABYLON_RELEASE_SIGNING_KEY", raising=False)
    manifest = '[claim.safety]\nstatement = "denies replay"\nstatus = "verified_local"\n'
    (tmp_path / "CLAIMS.toml").write_text(manifest)
    (tmp_path / "babylon.toml").write_text('[release]\nversion = "5.0.0"\nstate = "candidate"\n')
    report_dir = tmp_path / "scripts/c5_quality_gates"
    report_dir.mkdir(parents=True)
    report = {
        "source_commit": "a" * 40,
        "source_tree_digest": "d" * 64,
        "claims_manifest_digest": hashlib.sha256(manifest.encode()).hexdigest(),
        "environment_digest": "b" * 64,
        "failed_claims": [],
        "verified": 0,
        "partial": 1,
        "experimental": 0,
        "claims": [
            {
                "id": "safety",
                "statement": "denies replay",
                "status": "verified_local",
                "verified": False,
                "suite_passed": True,
            }
        ],
    }
    (report_dir / "claims_sitrep.json").write_text(json.dumps(report))
    return tmp_path


def test_old_commit_cannot_be_relabelled_as_current(evidence_root: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(compiler, "get_git_commit", lambda: "c" * 40)
    with pytest.raises(ValueError, match="source commit"):
        compiler.compile_claims_evidence()


def test_added_claim_requires_new_evidence(evidence_root: Path) -> None:
    with (evidence_root / "CLAIMS.toml").open("a") as stream:
        stream.write('\n[claim.new_contract]\nstatement = "new"\n')
    with pytest.raises(ValueError, match="CLAIMS.toml"):
        compiler.compile_claims_evidence()


@pytest.mark.parametrize("corruption", ["missing", "duplicate", "failure"])
def test_incomplete_or_failed_evidence_is_rejected(evidence_root: Path, corruption: str) -> None:
    path = evidence_root / "scripts/c5_quality_gates/claims_sitrep.json"
    report = json.loads(path.read_text())
    if corruption == "missing":
        report["claims"] = []
    elif corruption == "duplicate":
        report["claims"] *= 2
    else:
        report["claims"][0]["suite_passed"] = False
        report["claims"][0]["verified"] = False
    path.write_text(json.dumps(report))
    with pytest.raises(ValueError):
        compiler.compile_claims_evidence()


def test_no_key_emits_explicitly_unsigned_evidence(evidence_root: Path) -> None:
    evidence = compiler.compile_claims_evidence()
    _, _, manifest_path = compiler.emit_claims_artifacts(evidence)
    manifest = json.loads(manifest_path.read_text())
    assert manifest["signature"] is None
    assert manifest["signing_authority"]["public_key"] is None
    assert manifest["signing_authority"]["scope"] == "unsigned_local_evidence"
    assert manifest["commit"] == evidence["source_commit"]
    assert manifest["sbom"]["cargo_components"] > 0
    assert manifest["sbom"]["python_components"] > 0


def test_invalid_configured_key_fails_before_artifact_writes(
    evidence_root: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("BABYLON_RELEASE_SIGNING_KEY", str(evidence_root / "absent-key"))
    with pytest.raises(FileNotFoundError):
        compiler.emit_claims_artifacts(compiler.compile_claims_evidence())
    assert not (evidence_root / "evidence.json").exists()


def test_source_changes_after_verification_are_rejected(evidence_root: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(compiler, "source_tree_digest", lambda root: "e" * 64)
    with pytest.raises(ValueError, match="source changed"):
        compiler.compile_claims_evidence()


def test_partial_claims_set_suite_passed_without_inflating_verified_flag(evidence_root: Path) -> None:
    evidence = compiler.compile_claims_evidence()
    entry = evidence["evidence_entries"][0]
    assert entry["status"] == "verified_local"
    assert entry["suite_passed"] is True
    assert entry["verified"] is False
    assert sum(1 for e in evidence["evidence_entries"] if e["verified"]) == evidence["verified_count"]


def test_v5_manifest_keeps_verifier_fields_and_chains_prior_release(evidence_root: Path) -> None:
    prior_bytes = json.dumps({"manifest_schema": "babylon60.release.v5", "version": "4.9.0", "prior_commit": "f" * 40})
    (evidence_root / "RELEASE_MANIFEST.json").write_text(prior_bytes)
    (evidence_root / "Cargo.toml").write_text('[workspace.package]\nversion = "5.0.0"\n')
    evidence = compiler.compile_claims_evidence()
    _, _, manifest_path = compiler.emit_claims_artifacts(evidence)
    manifest = json.loads(manifest_path.read_text())
    assert manifest["manifest_schema"] == compiler.MANIFEST_SCHEMA
    assert manifest["release"] == manifest["version"] == "5.0.0"
    for field in ("commit", "claims_manifest_digest", "claims", "evidence_root", "sbom", "signing_authority"):
        assert field in manifest
    assert manifest["claims_manifest_digest"] == evidence["claims_manifest_digest"]
    assert manifest["prior_release"] == {
        "version": "4.9.0",
        "commit": "f" * 40,
        "manifest_schema": "babylon60.release.v5",
        "manifest_sha256": hashlib.sha256(prior_bytes.encode()).hexdigest(),
    }
    assert manifest["version_sync"]["cargo_workspace"] == "5.0.0"
    assert manifest["artifacts_sha256"]["CLAIMS.toml"] == evidence["claims_manifest_digest"]


def test_v5_manifest_rejects_version_drift_before_writes(evidence_root: Path) -> None:
    (evidence_root / "Cargo.toml").write_text('[workspace.package]\nversion = "9.9.9"\n')
    with pytest.raises(ValueError, match="Version drift"):
        compiler.emit_claims_artifacts(compiler.compile_claims_evidence())
    assert not (evidence_root / "evidence.json").exists()


def test_emit_claims_artifacts_records_bundle_zip_inventory_and_rejects_symlinks(
    evidence_root: Path, tmp_path: Path
) -> None:
    bundle_zip = tmp_path / "bundle.zip"
    readme_bytes = b"# Babylon60 Bundle\n"
    with zipfile.ZipFile(bundle_zip, "w") as zf:
        zf.writestr("README.md", readme_bytes)
        zf.writestr("RELEASE_MANIFEST.json", b'{"stale": true}\n')

    manifest_path = compiler.emit_claims_artifacts(compiler.compile_claims_evidence(), bundle_path=bundle_zip)[2]
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    expected_digest = hashlib.sha256(b"README.md\x00" + len(readme_bytes).to_bytes(8, "big") + readme_bytes).hexdigest()
    assert manifest["release_bundle"] == {
        "name": "bundle.zip",
        "sha256": hashlib.sha256(bundle_zip.read_bytes()).hexdigest(),
        "size_bytes": len(bundle_zip.read_bytes()),
        "tree_digest": expected_digest,
        "source_files": ["README.md", "RELEASE_MANIFEST.json"],
    }

    bad_zip = tmp_path / "symlink_bundle.zip"
    with zipfile.ZipFile(bad_zip, "w") as zf:
        info = zipfile.ZipInfo("bad_link")
        info.external_attr = 0o120777 << 16
        zf.writestr(info, "/etc/passwd")
    with pytest.raises(ValueError, match="Symlink entry forbidden"):
        compiler.emit_claims_artifacts(compiler.compile_claims_evidence(), bundle_path=bad_zip)


def test_emit_claims_artifacts_reads_packager_list_files_when_present(evidence_root: Path) -> None:
    packager = evidence_root / "scripts" / "package_release.sh"
    packager.write_text("#!/bin/sh\necho CLAIMS.toml\necho RELEASE_MANIFEST.json\n", encoding="utf-8")
    manifest_path = compiler.emit_claims_artifacts(compiler.compile_claims_evidence())[2]
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    claims_bytes = (evidence_root / "CLAIMS.toml").read_bytes()
    expected_digest = hashlib.sha256(
        b"CLAIMS.toml\x00" + len(claims_bytes).to_bytes(8, "big") + claims_bytes
    ).hexdigest()
    assert manifest["release_bundle"] == {
        "name": "Babylon60-v5.0.0-terminal-mcp.zip",
        "tree_digest": expected_digest,
        "source_files": ["CLAIMS.toml", "RELEASE_MANIFEST.json"],
    }


def _configure_invariant_fixture(evidence_root: Path, *, state: str = "candidate") -> None:
    claims_text = (
        '[claim.safety]\nstatement = "denies replay"\nstatus = "verified_local"\n\n'
        "[invariants.mcp_lifecycle_confinement]\n"
        'claim_id = "CLAIM-MCP-006"\n'
        'status = "NO_VERIFICADO"\n'
        'summary = "Objetivo acotado sin recibo"\n'
        "required_for_release = true\n"
        'evidence_level = "L3_ISOLATION"\n'
        'component = "00_ABZU_KERNEL"\n'
    )
    (evidence_root / "CLAIMS.toml").write_text(claims_text, encoding="utf-8")
    (evidence_root / "babylon.toml").write_text(
        f'[release]\nversion = "5.0.0"\nstate = "{state}"\n\n'
        "[release.gate_attestations.mcp_confinement]\n"
        'claim_id = "CLAIM-MCP-006"\n'
        'status = "NO_VERIFICADO"\n'
        "token_replay_window_seconds = 300\n",
        encoding="utf-8",
    )
    sitrep_path = evidence_root / "scripts/c5_quality_gates/claims_sitrep.json"
    report = json.loads(sitrep_path.read_text(encoding="utf-8"))
    report["claims_manifest_digest"] = hashlib.sha256(claims_text.encode("utf-8")).hexdigest()
    report["invariant_alignment_errors"] = []
    report["invariants"] = [
        {
            "key": "mcp_lifecycle_confinement",
            "claim_id": "CLAIM-MCP-006",
            "status": "NO_VERIFICADO",
            "evidence_level": "L3_ISOLATION",
            "component": "00_ABZU_KERNEL",
            "required_for_release": True,
            "summary": "Objetivo acotado sin recibo",
            "gate_aligned": True,
        }
    ]
    sitrep_path.write_text(json.dumps(report), encoding="utf-8")


def test_compile_rejects_invariant_alignment_errors_in_sitrep(evidence_root: Path) -> None:
    sitrep_path = evidence_root / "scripts/c5_quality_gates/claims_sitrep.json"
    report = json.loads(sitrep_path.read_text(encoding="utf-8"))
    report["invariant_alignment_errors"] = [
        "babylon.toml gate_attestations.mcp_confinement.effect_tx_quarantine='ACTIVE' sobre-reivindica"
    ]
    sitrep_path.write_text(json.dumps(report), encoding="utf-8")

    with pytest.raises(ValueError, match="invariant alignment errors"):
        compiler.compile_claims_evidence()


def test_compile_rejects_missing_or_unaligned_invariants_in_sitrep(evidence_root: Path) -> None:
    _configure_invariant_fixture(evidence_root, state="candidate")
    sitrep_path = evidence_root / "scripts/c5_quality_gates/claims_sitrep.json"

    # 1. Missing invariants array when CLAIMS.toml declares [invariants.*]
    report = json.loads(sitrep_path.read_text(encoding="utf-8"))
    del report["invariants"]
    sitrep_path.write_text(json.dumps(report), encoding="utf-8")
    with pytest.raises(ValueError, match="Invariant evidence is missing"):
        compiler.compile_claims_evidence()

    # 2. Unaligned invariant record (gate_aligned=False)
    report["invariants"] = [{"key": "mcp_lifecycle_confinement", "gate_aligned": False}]
    sitrep_path.write_text(json.dumps(report), encoding="utf-8")
    with pytest.raises(ValueError, match="unaligned \\[invariants\\.\\*\\]"):
        compiler.compile_claims_evidence()


def test_compile_and_emit_reject_stable_state_when_required_invariant_unverified(evidence_root: Path) -> None:
    _configure_invariant_fixture(evidence_root, state="candidate")
    evidence = compiler.compile_claims_evidence()
    _, _, manifest_path = compiler.emit_claims_artifacts(evidence)
    assert json.loads(manifest_path.read_text(encoding="utf-8"))["state"] == "candidate"

    # Flipping babylon.toml to stable-terminal-mcp must fail closed in both compile and emit
    _configure_invariant_fixture(evidence_root, state="stable-terminal-mcp")
    with pytest.raises(ValueError, match="release\\.state='stable-terminal-mcp'"):
        compiler.compile_claims_evidence()
    with pytest.raises(ValueError, match="release\\.state='stable-terminal-mcp'"):
        compiler.emit_claims_artifacts(evidence)


def test_source_bundle_rejects_path_swap_during_open(evidence_root: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """A matching payload behind a substituted symlink is not verified source."""
    import os

    source = evidence_root / "CLAIMS.toml"
    payload = source.read_bytes()
    outside = evidence_root / "outside.txt"
    outside.write_bytes(payload)
    bundle_path = evidence_root / "candidate.zip"
    inventory = {
        "format": "babylon60.source-bundle.v1",
        "version": "5.0.0",
        "source_commit": "a" * 40,
        "files_sha256": {"CLAIMS.toml": hashlib.sha256(payload).hexdigest()},
    }
    with zipfile.ZipFile(bundle_path, "w") as bundle:
        bundle.writestr("CLAIMS.toml", payload)
        bundle.writestr("SOURCE_MANIFEST.json", json.dumps(inventory))
    real_open, real_is_file = os.open, Path.is_file
    swapped = False

    def replace_source():
        nonlocal swapped
        if not swapped:
            source.unlink()
            source.symlink_to(outside)
            swapped = True

    def open_after_swap(path, *args, **kwargs):
        if Path(path) == source:
            replace_source()
        return real_open(path, *args, **kwargs)

    def checked_then_swapped(path):
        result = real_is_file(path)
        if path == source:
            replace_source()
        return result

    monkeypatch.setattr(os, "open", open_after_swap)
    monkeypatch.setattr(Path, "is_file", checked_then_swapped)
    with pytest.raises(ValueError, match="release source|verified source"):
        compiler.inspect_source_bundle(bundle_path, version="5.0.0", commit="a" * 40)
    assert swapped
