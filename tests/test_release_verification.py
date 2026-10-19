"""Behavioral and adversarial tamper tests for SBOM generation and Zero-Trust verify_release.sh."""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess

from cryptography.hazmat.primitives.asymmetric import ed25519

from scripts.generate_sbom import generate_sboms

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


def _create_signed_release_fixture(tmp_path: Path) -> tuple[Path, Path, str]:
    root = tmp_path / "release_fixture"
    (root / "scripts").mkdir(parents=True)
    shutil.copyfile(REPO_ROOT / "scripts" / "verify_release.sh", root / "scripts" / "verify_release.sh")
    shutil.copyfile(REPO_ROOT / "CLAIMS.toml", root / "CLAIMS.toml")
    shutil.copyfile(REPO_ROOT / "Cargo.lock", root / "Cargo.lock")
    shutil.copyfile(REPO_ROOT / "uv.lock", root / "uv.lock")

    sbom_summary = generate_sboms(repo_root=root, output_dir=root)
    claims_digest = hashlib.sha256((root / "CLAIMS.toml").read_bytes()).hexdigest()

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
        "source_tree_digest": "fedcba9876543210fedcba9876543210fedcba9876543210fedcba9876543210",
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

    priv_key = ed25519.Ed25519PrivateKey.from_private_bytes(os.urandom(32))
    pubkey_hex = priv_key.public_key().public_bytes_raw().hex()

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
            "algorithm": "Ed25519",
            "scope": "detached_release_attestation",
            "public_key": pubkey_hex,
        },
    }
    canonical_bytes = json.dumps(manifest_body, sort_keys=True).encode("utf-8")
    sig_hex = priv_key.sign(canonical_bytes).hex()

    manifest_full = dict(manifest_body)
    manifest_full["signature"] = sig_hex
    (root / "RELEASE_MANIFEST.json").write_text(json.dumps(manifest_full, indent=2) + "\n", encoding="utf-8")

    sig_doc = {
        "algorithm": "Ed25519",
        "public_key": pubkey_hex,
        "canonical_body_sha256": hashlib.sha256(canonical_bytes).hexdigest(),
        "signature": sig_hex,
    }
    (root / "RELEASE_MANIFEST.json.sig").write_text(json.dumps(sig_doc, indent=2) + "\n", encoding="utf-8")
    return root, bundle_path, pubkey_hex


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
