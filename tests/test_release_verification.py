"""Behavioral and adversarial tamper tests for SBOM generation and Zero-Trust verify_release.sh."""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess

import pytest
from cryptography.hazmat.primitives.asymmetric import ed25519

from scripts.generate_sbom import build_cargo_cyclonedx, build_uv_cyclonedx, generate_sboms

REPO_ROOT = Path(__file__).absolute().parents[1]


def _compute_merkle_root(entry_hashes: list[str]) -> str:
    total_leaves = len(entry_hashes)
    layer = [bytes.fromhex(h) for h in entry_hashes]
    level = 0
    while len(layer) > 1:
        if len(layer) % 2 != 0:
            layer.append(layer[-1])
        next_layer = []
        for i in range(0, len(layer), 2):
            combined = layer[i] + layer[i + 1]
            domain_tag = b"\x00" if level == 0 else b"\x01"
            next_layer.append(hashlib.sha3_256(domain_tag + combined).digest())
        layer = next_layer
        level += 1
    root_with_cardinality = b"\x02" + layer[0] + total_leaves.to_bytes(8, "little")
    return hashlib.sha3_256(root_with_cardinality).hexdigest()


def _create_release_fixture(tmp_path: Path, *, signed: bool) -> tuple[Path, Path, str]:
    """Create synthetic candidate evidence, independent of the historical release."""
    root = tmp_path / "release_fixture"
    (root / "scripts").mkdir(parents=True)
    shutil.copyfile(REPO_ROOT / "scripts" / "verify_release.sh", root / "scripts" / "verify_release.sh")
    shutil.copyfile(REPO_ROOT / "CLAIMS.toml", root / "CLAIMS.toml")
    shutil.copyfile(REPO_ROOT / "Cargo.toml", root / "Cargo.toml")
    shutil.copyfile(REPO_ROOT / "Cargo.lock", root / "Cargo.lock")
    shutil.copyfile(REPO_ROOT / "uv.lock", root / "uv.lock")

    sbom_summary = generate_sboms(repo_root=root, output_dir=root)
    claims_digest = hashlib.sha256((root / "CLAIMS.toml").read_bytes()).hexdigest()

    subprocess.run(["git", "init", "-q"], cwd=root, check=True)
    subprocess.run(
        [
            "git",
            "add",
            "scripts/verify_release.sh",
            "CLAIMS.toml",
            "Cargo.toml",
            "Cargo.lock",
            "uv.lock",
        ],
        cwd=root,
        check=True,
    )
    from scripts.c5_quality_gates.verify_claims import source_tree_digest as compute_source_tree_digest

    real_tree_digest = compute_source_tree_digest(root)

    bundle_path = tmp_path / "babylon60-5.0.0-test.zip"
    bundle_bytes = b"PK\x03\x04BABYLON60_TEST_BUNDLE_PAYLOAD"
    bundle_path.write_bytes(bundle_bytes)
    bundle_sha256 = hashlib.sha256(bundle_bytes).hexdigest()

    cid = "inv_01_manifest_layout"
    comp = "00_ABZU_KERNEL"
    status = "verified"
    stmt = "SharedManifest is 64 bytes"
    canonical_leaf = f"{cid}:{comp}:{status}:True:{stmt}"
    leaf_hash = hashlib.sha3_256(canonical_leaf.encode("utf-8")).hexdigest()
    merkle_root = f"sha3-256:{_compute_merkle_root([leaf_hash])}"

    evidence = {
        "timestamp_iso": "2026-10-19T16:00:00Z",
        "source_commit": "0123456789abcdef0123456789abcdef01234567",
        "source_tree_digest": real_tree_digest,
        "claims_manifest_digest": claims_digest,
        "environment_digest": "11" * 32,
        "total_claims": 1,
        "verified_count": 1,
        "partial_count": 0,
        "experimental_count": 0,
        "failed_count": 0,
        "merkle_evidence_root": merkle_root,
        "evidence_entries": [
            {
                "id": cid,
                "component": comp,
                "statement": stmt,
                "status": status,
                "verified": True,
                "duration_s": 0.1,
                "leaf_hash": leaf_hash,
            }
        ],
    }
    (root / "evidence.json").write_text(json.dumps(evidence, indent=2) + "\n", encoding="utf-8")

    claims_lock = {
        "format": "babylon60.claims.lock.v1",
        "version": "5.0.0",
        "commit": evidence["source_commit"],
        "source_tree_digest": evidence["source_tree_digest"],
        "timestamp": evidence["timestamp_iso"],
        "claims_manifest_digest": claims_digest,
        "evidence_root": merkle_root,
        "claims_pinned": {
            cid: {
                "status": status,
                "component": comp,
                "hash": leaf_hash,
            }
        },
    }
    (root / "claims.lock").write_text(json.dumps(claims_lock, indent=2) + "\n", encoding="utf-8")

    priv_key = ed25519.Ed25519PrivateKey.from_private_bytes(os.urandom(32)) if signed else None
    pubkey_hex = priv_key.public_key().public_bytes_raw().hex() if priv_key is not None else ""

    manifest_body = {
        "release": "5.0.0",
        "state": "candidate",
        "commit": evidence["source_commit"],
        "source_tree_digest": evidence["source_tree_digest"],
        "axiom_root": "INV-OMEGA",
        "claims_manifest_digest": claims_digest,
        "compiled_at_iso": evidence["timestamp_iso"],
        "claims": {
            "verified": 1,
            "empirical_and_bounded": 0,
            "experimental": 0,
            "failed": 0,
            "total": 1,
        },
        "evidence_root": merkle_root,
        "artifacts_sha256": {"Cargo.toml": hashlib.sha256((root / "Cargo.toml").read_bytes()).hexdigest()},
        "sbom": {
            "format": sbom_summary["format"],
            "cargo_sbom_sha256": sbom_summary["cargo_sbom_sha256"],
            "cargo_components": sbom_summary["cargo_components"],
            "python_sbom_sha256": sbom_summary["python_sbom_sha256"],
            "python_components": sbom_summary["python_components"],
        },
        "release_bundle": {
            "name": bundle_path.name,
            "sha256": bundle_sha256,
            "size_bytes": len(bundle_bytes),
        },
        "signing_authority": {
            "algorithm": "Ed25519" if signed else None,
            "scope": "detached_release_attestation" if signed else "unsigned_local_evidence",
            "public_key": pubkey_hex or None,
        },
    }
    canonical_bytes = json.dumps(manifest_body, sort_keys=True).encode("utf-8")
    sig_hex = priv_key.sign(canonical_bytes).hex() if priv_key is not None else None

    manifest_full = dict(manifest_body)
    manifest_full["signature"] = sig_hex
    (root / "RELEASE_MANIFEST.json").write_text(json.dumps(manifest_full, indent=2) + "\n", encoding="utf-8")

    if signed:
        sig_doc = {
            "algorithm": "Ed25519",
            "public_key": pubkey_hex,
            "canonical_body_sha256": hashlib.sha256(canonical_bytes).hexdigest(),
            "signature": sig_hex,
        }
        (root / "RELEASE_MANIFEST.json.sig").write_text(json.dumps(sig_doc, indent=2) + "\n", encoding="utf-8")
    return root, bundle_path, pubkey_hex


def _create_signed_release_fixture(tmp_path: Path) -> tuple[Path, Path, str]:
    return _create_release_fixture(tmp_path, signed=True)


def test_cyclonedx_sbom_generation_is_deterministic(tmp_path: Path) -> None:
    out1 = tmp_path / "run1"
    out2 = tmp_path / "run2"
    s1 = generate_sboms(repo_root=REPO_ROOT, output_dir=out1)
    s2 = generate_sboms(repo_root=REPO_ROOT, output_dir=out2)

    assert s1["cargo_sbom_sha256"] == s2["cargo_sbom_sha256"]
    assert s1["python_sbom_sha256"] == s2["python_sbom_sha256"]
    assert s1["cargo_components"] > 20
    assert s1["python_components"] > 10

    cargo_cdx = json.loads((out1 / "sbom.cargo.cdx.json").read_text(encoding="utf-8"))
    assert cargo_cdx["bomFormat"] == "CycloneDX"
    assert cargo_cdx["specVersion"] == "1.5"


def test_sbom_application_versions_follow_root_lockfiles(tmp_path: Path) -> None:
    (tmp_path / "Cargo.lock").write_text(
        'version = 4\n[[package]]\nname = "babylon60_root"\nversion = "7.2.3"\n'
        '[[package]]\nname = "babylon60_root"\nversion = "5.0.0"\nsource = "registry+https://example.invalid"\n'
    )
    (tmp_path / "uv.lock").write_text(
        'version = 1\n[[package]]\nname = "babylon60"\nversion = "8.4.2"\nsource = { editable = "." }\n'
        '[[package]]\nname = "babylon60"\nversion = "5.0.0"\nsource = { registry = "https://example.invalid" }\n'
    )
    generate_sboms(repo_root=tmp_path, output_dir=tmp_path)
    for ecosystem, name, version in [("cargo", "babylon60_root", "7.2.3"), ("python", "babylon60", "8.4.2")]:
        bom = json.loads((tmp_path / f"sbom.{ecosystem}.cdx.json").read_text())
        application = bom["metadata"]["component"]
        assert application["name"] == name
        assert application["version"] == version
        scheme = "cargo" if ecosystem == "cargo" else "pypi"
        assert application["bom-ref"] == f"pkg:{scheme}/{name}@{version}"
        assert any(c["bom-ref"] == application["bom-ref"] for c in bom["components"])


@pytest.mark.parametrize("ecosystem", ["cargo", "python"])
@pytest.mark.parametrize("root_count", [0, 2])
def test_sbom_rejects_missing_or_ambiguous_root(tmp_path: Path, ecosystem: str, root_count: int) -> None:
    name = "babylon60_root" if ecosystem == "cargo" else "babylon60"
    source = "" if ecosystem == "cargo" else 'source = { editable = "." }\n'
    contents = "version = 1\n" + "".join(
        f'[[package]]\nname = "{name}"\nversion = "{index}.0.0"\n{source}' for index in range(root_count)
    )
    lock = tmp_path / "fixture.lock"
    lock.write_text(contents)
    build = build_cargo_cyclonedx if ecosystem == "cargo" else build_uv_cyclonedx
    with pytest.raises(ValueError, match="root application"):
        build(lock)


def test_verify_release_passes_valid_signed_bundle_and_rejects_tampering(tmp_path: Path) -> None:
    root, bundle_path, pubkey_hex = _create_signed_release_fixture(tmp_path)
    verifier = str(root / "scripts" / "verify_release.sh")

    # 1. Valid signed bundle passes
    res = subprocess.run(
        [
            "bash",
            verifier,
            "--repo-root",
            str(root),
            "--bundle",
            str(bundle_path),
            "--pubkey",
            pubkey_hex,
            "--require-signature",
        ],
        capture_output=True,
        text=True,
        timeout=15,
    )
    assert res.returncode == 0, res.stderr
    assert "[VERIFIED]" in res.stdout

    # 2. Wrong expected pubkey fails closed
    wrong_key = "00" * 32
    res_wrong_key = subprocess.run(
        [
            "bash",
            verifier,
            "--repo-root",
            str(root),
            "--bundle",
            str(bundle_path),
            "--pubkey",
            wrong_key,
            "--require-signature",
        ],
        capture_output=True,
        text=True,
        timeout=15,
    )
    assert res_wrong_key.returncode != 0
    assert "public key mismatch" in res_wrong_key.stderr

    # 3. Tampered bundle bytes fail closed
    bundle_path.write_bytes(b"TAMPERED_ZIP_BYTES")
    res_tampered_bundle = subprocess.run(
        ["bash", verifier, "--repo-root", str(root), "--bundle", str(bundle_path)],
        capture_output=True,
        text=True,
        timeout=15,
    )
    assert res_tampered_bundle.returncode != 0
    assert "Release bundle SHA-256 mismatch" in res_tampered_bundle.stderr

    # 4. Tampered evidence statement fails Merkle leaf check
    root2, bundle2, pub2 = _create_signed_release_fixture(tmp_path / "case2")
    ev_data = json.loads((root2 / "evidence.json").read_text(encoding="utf-8"))
    ev_data["evidence_entries"][0]["statement"] = "FORGED STATEMENT"
    (root2 / "evidence.json").write_text(json.dumps(ev_data, indent=2) + "\n", encoding="utf-8")
    res_tampered_ev = subprocess.run(
        ["bash", str(root2 / "scripts" / "verify_release.sh"), "--repo-root", str(root2), "--bundle", str(bundle2)],
        capture_output=True,
        text=True,
        timeout=15,
    )
    assert res_tampered_ev.returncode != 0
    assert "Tampered leaf_hash detected" in res_tampered_ev.stderr


def test_root_verify_sh_and_wheel_scope_hygiene(tmp_path: Path) -> None:
    import tomllib

    root_verifier = REPO_ROOT / "verify.sh"
    assert root_verifier.is_file(), "Root ./verify.sh must exist"
    assert os.access(root_verifier, os.X_OK), "Root ./verify.sh must be executable"
    root, bundle_path, _ = _create_release_fixture(tmp_path, signed=False)

    res = subprocess.run(
        ["bash", str(root_verifier), "--repo-root", str(root), "--bundle", str(bundle_path)],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        timeout=15,
    )
    assert res.returncode == 0, res.stderr
    assert "[VERIFIED]" in res.stdout

    pyproj = tomllib.loads((REPO_ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    scripts = pyproj.get("project", {}).get("scripts", {})
    assert "babylon60-onco" not in scripts, "Unannounced oncology CLI must not be exposed in wheel scripts"

    excludes = (
        pyproj.get("tool", {}).get("hatch", {}).get("build", {}).get("targets", {}).get("wheel", {}).get("exclude", [])
    )
    for required_exclude in (
        "01_KISH_ENGINE/babylon60/oncology_primitives.py",
        "01_KISH_ENGINE/babylon60/genomics",
        "01_KISH_ENGINE/babylon60/cli/onco_transducer.py",
        "01_KISH_ENGINE/babylon60/services/voice_cloner.py",
    ):
        assert required_exclude in excludes, f"Missing wheel exclusion: {required_exclude}"

    nemesis_v1 = json.loads((REPO_ROOT / "reports" / "nemesis_verified_report.json").read_text(encoding="utf-8"))
    assert "attestation" not in nemesis_v1, "16-byte hash prefix must not be labeled as an attestation signature"

    license_text = (REPO_ROOT / "LICENSE").read_text(encoding="utf-8")
    assert "SOURCE AUDITABILITY & COMMERCIAL BOUNDARY" in license_text


def test_verify_sh_expected_manifest_sha256_pin(tmp_path: Path) -> None:
    root_verifier = REPO_ROOT / "verify.sh"
    root, bundle_path, _ = _create_release_fixture(tmp_path, signed=False)
    manifest_sha = hashlib.sha256((root / "RELEASE_MANIFEST.json").read_bytes()).hexdigest()
    command = ["bash", str(root_verifier), "--repo-root", str(root), "--bundle", str(bundle_path)]

    res_ok = subprocess.run(
        [*command, "--expected-manifest-sha256", manifest_sha],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        timeout=15,
    )
    assert res_ok.returncode == 0, res_ok.stderr

    res_bad = subprocess.run(
        [*command, "--expected-manifest-sha256", "0" * 64],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        timeout=15,
    )
    assert res_bad.returncode != 0
    assert "RELEASE_MANIFEST.json SHA-256 mismatch against --expected-manifest-sha256" in res_bad.stderr


def test_unsigned_candidate_cannot_satisfy_required_signature(tmp_path: Path) -> None:
    root, bundle_path, _ = _create_release_fixture(tmp_path, signed=False)
    manifest = json.loads((root / "RELEASE_MANIFEST.json").read_text(encoding="utf-8"))
    assert manifest["signature"] is None
    assert manifest["signing_authority"]["scope"] == "unsigned_local_evidence"
    assert not (root / "RELEASE_MANIFEST.json.sig").exists()
    result = subprocess.run(
        [
            "bash",
            str(REPO_ROOT / "verify.sh"),
            "--repo-root",
            str(root),
            "--bundle",
            str(bundle_path),
            "--require-signature",
        ],
        capture_output=True,
        text=True,
        timeout=15,
    )
    assert result.returncode != 0
    assert "Signature required (--require-signature)" in result.stderr


def test_external_audit_invariants_parity() -> None:
    # 1. Verified(tx) 7-conjunct parity between spec_nemesis.md and nemesis_evidence_report.json
    expected_def = (
        "Verified(tx) := authority_valid ∧ capability_epoch_valid ∧ locator_match "
        "∧ pre_state_hash_match ∧ effect_allowed ∧ quarantine_isolated ∧ ledger_precondition_valid"
    )
    spec_text = (REPO_ROOT / "docs" / "01_spec" / "spec_nemesis.md").read_text(encoding="utf-8").replace(r"\_", "_")
    nemesis_ev = json.loads((REPO_ROOT / "reports" / "nemesis_evidence_report.json").read_text(encoding="utf-8"))
    assert nemesis_ev["formal_invariants"]["NEM_I2_VERIFIED_COMMIT"]["definition"] == expected_def
    ev_body = {k: v for k, v in nemesis_ev.items() if k != "manifest_hash"}
    expected_ev_hash = "sha256:" + hashlib.sha256(json.dumps(ev_body, sort_keys=True).encode("utf-8")).hexdigest()
    assert nemesis_ev["manifest_hash"] == expected_ev_hash
    for conjunct in (
        "authority_valid",
        "capability_epoch_valid",
        "locator_match",
        "pre_state_hash_match",
        "effect_allowed",
        "quarantine_isolated",
        "ledger_precondition_valid",
    ):
        assert conjunct in spec_text

    # 2. License parity across root LICENSE, contracts/, docs/, and ADR-005
    for rel_doc in (
        "LICENSE",
        "contracts/ENTERPRISE_LICENSE.md",
        "docs/COMMERCIAL_LICENSE.md",
        "docs/adr/ADR-005-sovereign-dual-license.md",
    ):
        doc_text = (REPO_ROOT / rel_doc).read_text(encoding="utf-8")
        assert "sovereign dual-license" in doc_text.lower(), f"Missing Sovereign Dual-License in {rel_doc}"
        assert "Sovereign Exclusion License v1.0" not in doc_text, f"Stale license name in {rel_doc}"


def test_verify_release_rejects_governance_artifact_tampering(tmp_path: Path) -> None:
    from scripts.c5_quality_gates.verify_claims import is_excluded_from_public_tree

    assert is_excluded_from_public_tree("docs/security/evidence/swarm100/manifest.json")
    assert is_excluded_from_public_tree("tools/skill_library/catalog.json")
    assert not is_excluded_from_public_tree("01_KISH_ENGINE/babylon60/cli/main.py")

    root, bundle_path, _ = _create_release_fixture(tmp_path, signed=False)
    (root / "README.md").write_text("# Original README\n", encoding="utf-8")
    manifest = json.loads((root / "RELEASE_MANIFEST.json").read_text(encoding="utf-8"))
    manifest["artifacts_sha256"] = {
        "README.md": hashlib.sha256(b"# Original README\n").hexdigest(),
    }
    (root / "RELEASE_MANIFEST.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")

    # Tamper with README.md after manifest compilation
    (root / "README.md").write_text("# Tampered README\n", encoding="utf-8")
    res = subprocess.run(
        ["bash", str(root / "scripts" / "verify_release.sh"), "--repo-root", str(root), "--bundle", str(bundle_path)],
        capture_output=True,
        text=True,
        timeout=15,
    )
    assert res.returncode != 0
    assert "Governance artifact SHA-256 mismatch for README.md" in res.stderr


def test_verify_release_five_controlled_regression_cases(tmp_path: Path) -> None:
    """Verify the 5 controlled assurance cases and PASS/FAIL/NOT_CHECKED semantics."""
    verifier = str(REPO_ROOT / "scripts" / "verify_release.sh")

    # Case 1: Tracked source in Git with matching source_tree_digest -> [VERIFIED], exit 0
    root1, bundle1, _ = _create_release_fixture(tmp_path / "case1", signed=False)
    manifest1_sha = hashlib.sha256((root1 / "RELEASE_MANIFEST.json").read_bytes()).hexdigest()
    res1 = subprocess.run(
        [
            "bash",
            verifier,
            "--repo-root",
            str(root1),
            "--bundle",
            str(bundle1),
            "--expected-manifest-sha256",
            manifest1_sha,
        ],
        capture_output=True,
        text=True,
        timeout=15,
    )
    assert res1.returncode == 0, res1.stderr
    assert "[CHECK] source_tree_digest: PASS [required]" in res1.stdout
    assert "[CHECK] provenance_alignment: PASS [required]" in res1.stdout
    assert "[CHECK] release_bundle: PASS [required]" in res1.stdout
    assert "[VERIFIED]" in res1.stdout

    # Case 2: Modify tracked source while preserving .git -> Reject, exit 1
    root2, bundle2, _ = _create_release_fixture(tmp_path / "case2", signed=False)
    (root2 / "src_mod.py").write_text("x = 1\n", encoding="utf-8")
    subprocess.run(["git", "add", "src_mod.py"], cwd=root2, check=True)
    from scripts.c5_quality_gates.verify_claims import source_tree_digest as compute_source_tree_digest

    digest2 = compute_source_tree_digest(root2)
    for fname in ("RELEASE_MANIFEST.json", "evidence.json", "claims.lock"):
        doc = json.loads((root2 / fname).read_text(encoding="utf-8"))
        doc["source_tree_digest"] = digest2
        (root2 / fname).write_text(json.dumps(doc, indent=2) + "\n", encoding="utf-8")
    manifest2_sha = hashlib.sha256((root2 / "RELEASE_MANIFEST.json").read_bytes()).hexdigest()
    (root2 / "src_mod.py").write_text("x = 2  # tampered\n", encoding="utf-8")

    res2 = subprocess.run(
        [
            "bash",
            verifier,
            "--repo-root",
            str(root2),
            "--bundle",
            str(bundle2),
            "--expected-manifest-sha256",
            manifest2_sha,
        ],
        capture_output=True,
        text=True,
        timeout=15,
    )
    assert res2.returncode == 1
    assert "[VERIFIED]" not in res2.stdout
    assert "[CHECK] source_tree_digest: FAIL [required]" in res2.stderr
    assert "Public source_tree_digest mismatch" in res2.stderr

    # Case 3: Same modified source with .git removed -> Reject (mandatory check NOT_CHECKED), exit 1
    shutil.rmtree(root2 / ".git")
    res3 = subprocess.run(
        [
            "bash",
            verifier,
            "--repo-root",
            str(root2),
            "--bundle",
            str(bundle2),
            "--expected-manifest-sha256",
            manifest2_sha,
        ],
        capture_output=True,
        text=True,
        timeout=15,
    )
    assert res3.returncode == 1
    assert "[VERIFIED]" not in res3.stdout
    assert "[CHECK] source_tree_digest: NOT_CHECKED [required]" in res3.stderr
    assert "Mandatory check source_tree_digest is NOT_CHECKED" in res3.stderr

    # Case 4: evidence.json with commit and source_tree_digest differing from RELEASE_MANIFEST.json -> Reject, exit 1
    root4, bundle4, _ = _create_release_fixture(tmp_path / "case4", signed=False)
    manifest4_sha = hashlib.sha256((root4 / "RELEASE_MANIFEST.json").read_bytes()).hexdigest()
    ev4 = json.loads((root4 / "evidence.json").read_text(encoding="utf-8"))
    ev4["source_commit"] = "deadbeef" * 5
    ev4["source_tree_digest"] = "aa" * 32
    (root4 / "evidence.json").write_text(json.dumps(ev4, indent=2) + "\n", encoding="utf-8")

    res4 = subprocess.run(
        [
            "bash",
            verifier,
            "--repo-root",
            str(root4),
            "--bundle",
            str(bundle4),
            "--expected-manifest-sha256",
            manifest4_sha,
        ],
        capture_output=True,
        text=True,
        timeout=15,
    )
    assert res4.returncode == 1
    assert "[VERIFIED]" not in res4.stdout
    assert "[CHECK] provenance_alignment: FAIL [required]" in res4.stderr
    assert "Provenance commit mismatch" in res4.stderr

    # Case 5: --bundle pointing to arbitrary file when manifest has release_bundle: null -> Reject, exit 1
    root5, _, _ = _create_release_fixture(tmp_path / "case5", signed=False)
    manifest5 = json.loads((root5 / "RELEASE_MANIFEST.json").read_text(encoding="utf-8"))
    manifest5["release_bundle"] = None
    (root5 / "RELEASE_MANIFEST.json").write_text(json.dumps(manifest5, indent=2) + "\n", encoding="utf-8")
    manifest5_sha = hashlib.sha256((root5 / "RELEASE_MANIFEST.json").read_bytes()).hexdigest()
    arbitrary_bundle = tmp_path / "arbitrary_untrusted_payload.zip"
    arbitrary_bundle.write_bytes(b"UNTRUSTED_ARBITRARY_ZIP")

    res5 = subprocess.run(
        [
            "bash",
            verifier,
            "--repo-root",
            str(root5),
            "--bundle",
            str(arbitrary_bundle),
            "--expected-manifest-sha256",
            manifest5_sha,
        ],
        capture_output=True,
        text=True,
        timeout=15,
    )
    assert res5.returncode == 1
    assert "[VERIFIED]" not in res5.stdout
    assert "[CHECK] release_bundle: NOT_CHECKED [required]" in res5.stderr
    assert "Mandatory check release_bundle is NOT_CHECKED" in res5.stderr

    # Case 6 (Git-less distribution with authenticated source_files inventory):
    # Passes when intact, rejects when source file is modified without .git
    root6, bundle6, _ = _create_release_fixture(tmp_path / "case6", signed=False)
    tracked_files = [
        p.decode("utf-8") for p in subprocess.check_output(["git", "ls-files", "-z"], cwd=root6).split(b"\0") if p
    ]
    shutil.rmtree(root6 / ".git")
    manifest6 = json.loads((root6 / "RELEASE_MANIFEST.json").read_text(encoding="utf-8"))
    manifest6["source_files"] = tracked_files
    (root6 / "RELEASE_MANIFEST.json").write_text(json.dumps(manifest6, indent=2) + "\n", encoding="utf-8")
    manifest6_sha = hashlib.sha256((root6 / "RELEASE_MANIFEST.json").read_bytes()).hexdigest()

    res6_ok = subprocess.run(
        [
            "bash",
            verifier,
            "--repo-root",
            str(root6),
            "--bundle",
            str(bundle6),
            "--expected-manifest-sha256",
            manifest6_sha,
        ],
        capture_output=True,
        text=True,
        timeout=15,
    )
    assert res6_ok.returncode == 0, res6_ok.stderr
    assert "[CHECK] source_tree_digest: PASS [required]" in res6_ok.stdout
    assert "[VERIFIED]" in res6_ok.stdout

    (root6 / "Cargo.lock").write_text("# tampered in git-less distribution\n", encoding="utf-8")
    res6_tampered = subprocess.run(
        [
            "bash",
            verifier,
            "--repo-root",
            str(root6),
            "--bundle",
            str(bundle6),
            "--expected-manifest-sha256",
            manifest6_sha,
        ],
        capture_output=True,
        text=True,
        timeout=15,
    )
    assert res6_tampered.returncode == 1
    assert "[VERIFIED]" not in res6_tampered.stdout
    assert "[CHECK] source_tree_digest: FAIL [required]" in res6_tampered.stderr
    assert "Public source_tree_digest mismatch" in res6_tampered.stderr


def test_packaged_release_zip_standalone_verification_without_git(tmp_path: Path) -> None:
    """Execute package_release.sh, extract the ZIP without .git, and verify intact vs tampered source."""
    import zipfile

    dist_dir = tmp_path / "dist"
    pkg_res = subprocess.run(
        ["bash", str(REPO_ROOT / "scripts" / "package_release.sh"), str(dist_dir)],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert pkg_res.returncode == 0, pkg_res.stderr
    zip_path = dist_dir / "Babylon60-v5.1.0-terminal-mcp.zip"
    assert zip_path.is_file()

    extract_dir = tmp_path / "extracted_no_git"
    with zipfile.ZipFile(zip_path) as zf:
        zf.extractall(extract_dir)
    assert not (extract_dir / ".git").exists()

    # Intact standalone extraction passes verify.sh
    res_ok = subprocess.run(
        ["bash", "verify.sh"],
        cwd=extract_dir,
        capture_output=True,
        text=True,
        timeout=15,
    )
    assert res_ok.returncode == 0, res_ok.stderr
    assert "[CHECK] governance_artifacts: PASS [required] (files=10)" in res_ok.stdout
    assert "[CHECK] source_tree_digest: PASS [required]" in res_ok.stdout
    assert "[VERIFIED]" in res_ok.stdout

    # Modifying a non-governance source file in the git-less directory fails closed
    install_sh = extract_dir / "install.sh"
    install_sh.write_text(install_sh.read_text(encoding="utf-8") + "\n# tampered\n", encoding="utf-8")
    res_tampered = subprocess.run(
        ["bash", "verify.sh"],
        cwd=extract_dir,
        capture_output=True,
        text=True,
        timeout=15,
    )
    assert res_tampered.returncode == 1
    assert "[VERIFIED]" not in res_tampered.stdout
    assert "[CHECK] source_tree_digest: FAIL [required]" in res_tampered.stderr
    assert "Public source_tree_digest mismatch" in res_tampered.stderr

