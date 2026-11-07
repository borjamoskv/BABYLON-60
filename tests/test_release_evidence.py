"""Release evidence must describe this source and never invent signing authority."""

import hashlib
import json
from pathlib import Path
import shutil

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
