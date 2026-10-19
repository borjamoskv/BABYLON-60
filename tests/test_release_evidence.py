"""Release evidence must describe this source and never invent signing authority."""

import hashlib
import json
from pathlib import Path

import pytest

from scripts.c5_quality_gates import compile_claims_manifest as compiler


@pytest.fixture
def evidence_root(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
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
        "claims": [{"id": "safety", "statement": "denies replay", "status": "verified_local", "verified": True}],
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
