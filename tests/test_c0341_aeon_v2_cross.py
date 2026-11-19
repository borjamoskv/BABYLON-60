"""C0341: Python signs an Aeon v2 manifest with its canonical JSON; the Rust verifier must
accept it with the right external anchor and reject foreign anchors and altered fields."""

from __future__ import annotations

import base64
import json
import subprocess
from pathlib import Path

import pytest
from cryptography.hazmat.primitives.asymmetric import ed25519
from cryptography.hazmat.primitives.serialization import Encoding, PublicFormat

from babylon60.attestation.conformal_tree import canonical_aeon_manifest_bytes

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="module")
def rust_bin() -> Path:
    subprocess.run(
        ["cargo", "build", "--locked", "-p", "babylon-attest", "--target-dir", str(ROOT / "target")],
        cwd=ROOT,
        check=True,
        capture_output=True,
    )
    binary = ROOT / "target" / "debug" / "babylon-attest"
    assert binary.is_file()
    return binary


def _b64(data: bytes) -> str:
    return base64.b64encode(data).decode("ascii")


def _public_b64(key: ed25519.Ed25519PrivateKey) -> str:
    return _b64(key.public_key().public_bytes(Encoding.Raw, PublicFormat.Raw))


def _signed_manifest(key: ed25519.Ed25519PrivateKey) -> dict:
    manifest = {
        "schema": "babylon60.aeon-manifest.v2",
        "$schema": "https://babylon60.org/schemas/l1_aeon_seal_v4.json",
        "aeon_id": "AEON-CROSS",
        "status": "FROZEN_C5_REAL",
        "timestamp_utc": "2026-11-18T00:00:00Z",
        "total_claims_sealed": 3,
        "claims_distribution": {"DOMAIN_EVM": 2, "dominio_ñ€": 1},
        "merkle_root": "ab" * 32,
        "op_return_hex": "ab" * 32,
        "payload_size_bytes": 32,
        "hardware_attestation": {"hardware_uuid": "fixture"},
        "thermodynamics": {
            "landauer_bound_300k_joules": 1.2345e-19,
            "tiny": 1e-05,
            "huge": 1e16,
            "round": 100.0,
            "ratio": "3:1 -> 32B root",
        },
        "governance_invariants": ["INV_C5_AEON", "HARDWARE_UNVERIFIED (software evidence only)"],
        "sovereign_identity": {
            "l0_public_key_b64": _public_b64(key),
            "ed25519_signature_b64": "",
            "signed_payload": "manifest-canonical-json-v2",
        },
    }
    manifest["sovereign_identity"]["ed25519_signature_b64"] = _b64(key.sign(canonical_aeon_manifest_bytes(manifest)))
    return manifest


def _verify(rust_bin: Path, tmp_path: Path, manifest: dict, anchor: str) -> subprocess.CompletedProcess[str]:
    path = tmp_path / "aeon.json"
    path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")
    return subprocess.run(
        [str(rust_bin), "verify-aeon", "--manifest", str(path), "--trusted-key", anchor],
        capture_output=True,
        text=True,
        timeout=30,
    )


def test_python_signed_v2_manifest_verifies_in_rust(rust_bin, tmp_path):
    key = ed25519.Ed25519PrivateKey.from_private_bytes(bytes(range(32)))
    result = _verify(rust_bin, tmp_path, _signed_manifest(key), _public_b64(key))
    assert result.returncode == 0, result.stdout + result.stderr


def test_foreign_anchor_is_rejected(rust_bin, tmp_path):
    key = ed25519.Ed25519PrivateKey.from_private_bytes(bytes(range(32)))
    other = ed25519.Ed25519PrivateKey.from_private_bytes(bytes(range(1, 33)))
    assert _verify(rust_bin, tmp_path, _signed_manifest(key), _public_b64(other)).returncode != 0


@pytest.mark.parametrize(
    ("field", "value"),
    [("total_claims_sealed", 4), ("aeon_id", "AEON-OTHER"), ("claims_distribution", {"DOMAIN_EVM": 3})],
)
def test_altered_field_is_rejected(rust_bin, tmp_path, field, value):
    key = ed25519.Ed25519PrivateKey.from_private_bytes(bytes(range(32)))
    manifest = _signed_manifest(key)
    manifest[field] = value
    assert _verify(rust_bin, tmp_path, manifest, _public_b64(key)).returncode != 0
