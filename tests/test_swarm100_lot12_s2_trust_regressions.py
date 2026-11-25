"""Software-only, temporary regression fixtures for SW100 C0271/C0276/C0432."""

import base64
import importlib.util
import json
import os
from pathlib import Path
import socket
import sqlite3
import subprocess
import sys
from typing import Any

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
import pytest

from babylon60.attestation.conformal_tree import AeonVerifier
from babylon60.attestation.conformal_tree import compute_claim_leaf_hash
from babylon60.attestation.merkle_anchor import MerkleCausalAnchor


@pytest.fixture(autouse=True)
def confined(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.delenv("BABYLON_AEON_TRUSTED_PUBLIC_KEY_B64", raising=False)
    monkeypatch.delenv("BABYLON_LICENSE_ED25519_SEED", raising=False)
    monkeypatch.setattr(
        MerkleCausalAnchor,
        "get_hardware_identity",
        lambda self: {"uuid": "FIXTURE-UUID", "os": "Fixture", "machine": "CPU", "enclave_type": "SYNTHETIC"},
    )

    def forbidden(*args: object, **kwargs: object) -> None:
        raise AssertionError("Network forbidden in software fixture")

    monkeypatch.setattr(socket, "create_connection", forbidden)
    monkeypatch.setattr(socket, "getaddrinfo", forbidden)


def _public_b64(key: Ed25519PrivateKey) -> str:
    return base64.b64encode(
        key.public_key().public_bytes(serialization.Encoding.Raw, serialization.PublicFormat.Raw)
    ).decode()


def _legacy_manifest(key: Ed25519PrivateKey) -> dict[str, Any]:
    root = "12" * 32
    return {
        "aeon_id": "AEON-FIXTURE",
        "status": "FROZEN_C5_REAL",
        "merkle_root": root,
        "total_claims_sealed": 1,
        "sovereign_identity": {
            "l0_public_key_b64": _public_b64(key),
            "ed25519_signature_b64": base64.b64encode(key.sign(bytes.fromhex(root))).decode(),
        },
        "hardware_attestation": {"hardware_uuid": "FIXTURE-UUID"},
    }


def _write(tmp_path: Path, manifest: dict[str, Any]) -> Path:
    path = tmp_path / "manifest.json"
    path.write_text(json.dumps(manifest))
    return path


def test_c0271_self_signed_manifest_is_not_an_authority(tmp_path: Path) -> None:
    path = _write(tmp_path, _legacy_manifest(Ed25519PrivateKey.generate()))
    assert AeonVerifier.verify_manifest(path)["overall_valid"] is False


def test_c0276_software_hash_never_claims_hardware_sealing() -> None:
    quote = MerkleCausalAnchor().generate_hardware_pcr_quote("12" * 32)
    assert not quote["hardware_enclave"].startswith("TPM_2_0_HARDWARE_SEALED")
    assert quote.get("attestation_status") == "SOFTWARE_ONLY_UNATTESTED"
    assert not quote["tpm_quote_signature"]


def _license_module():
    path = Path(__file__).resolve().parents[1] / "tools/tamkarum_license_provisioner.py"
    spec = importlib.util.spec_from_file_location("lot12_fixture_license", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.mark.parametrize("seed", [None, "", "ab", "gg" * 32, "00" * 32])
def test_c0432_missing_or_invalid_authority_is_rejected(monkeypatch: pytest.MonkeyPatch, seed: str | None) -> None:
    if seed is not None:
        monkeypatch.setenv("BABYLON_LICENSE_ED25519_SEED", seed)
    with pytest.raises(ValueError, match="authority"):
        _license_module().generate_license_certificate("Synthetic Client", "FIXTURE", "pilot")


def _sign_manifest(key: Ed25519PrivateKey, data: dict[str, Any]) -> dict[str, Any]:
    data["schema"] = "babylon60.aeon-manifest.v2"
    identity = data["sovereign_identity"]
    identity["signed_payload"] = "manifest-canonical-json-v2"
    identity.pop("ed25519_signature_b64", None)
    encoded = json.dumps(data, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode()
    identity["ed25519_signature_b64"] = base64.b64encode(key.sign(encoded)).decode()
    return data


def _valid_manifest() -> tuple[Ed25519PrivateKey, dict[str, Any]]:
    key = Ed25519PrivateKey.generate()
    data = _legacy_manifest(key)
    data["hardware_attestation"]["attestation_status"] = "SOFTWARE_ONLY_UNATTESTED"
    return key, _sign_manifest(key, data)


def test_c0271_full_manifest_authenticated_with_external_anchor(tmp_path: Path) -> None:
    key, data = _valid_manifest()
    report = AeonVerifier.verify_manifest(_write(tmp_path, data), expected_public_key_b64=_public_b64(key))
    assert report["overall_valid"] is True
    assert report["identity_trusted"] is True
    assert report["ed25519_signature_valid"] is True
    assert report["tree_integrity_valid"] is None
    assert report["verification_scope"] == "AUTHENTICATED_MANIFEST_ONLY"
    assert report["hardware_attestation_verified"] is False


def test_c0271_environment_anchor_for_existing_cli_consumers(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    key, data = _valid_manifest()
    monkeypatch.setenv("BABYLON_AEON_TRUSTED_PUBLIC_KEY_B64", _public_b64(key))
    path = _write(tmp_path, data)
    assert AeonVerifier.verify_manifest(path)["overall_valid"] is True
    assert AeonVerifier.verify_manifest(path, expected_public_key_b64="")["overall_valid"] is False


@pytest.mark.parametrize(
    "anchor", ["", "invalid", " ", base64.b64encode(b"x" * 31).decode(), base64.b64encode(b"x" * 33).decode()]
)
def test_c0271_invalid_external_anchor_rejected(tmp_path: Path, anchor: str) -> None:
    _, data = _valid_manifest()
    assert (
        AeonVerifier.verify_manifest(_write(tmp_path, data), expected_public_key_b64=anchor)["overall_valid"] is False
    )


def test_c0271_foreign_key_cannot_authorize_manifest(tmp_path: Path) -> None:
    _, data = _valid_manifest()
    foreign = Ed25519PrivateKey.generate()
    assert (
        AeonVerifier.verify_manifest(_write(tmp_path, data), expected_public_key_b64=_public_b64(foreign))[
            "overall_valid"
        ]
        is False
    )


def test_c0271_legacy_root_only_signature_rejected_even_with_pin(tmp_path: Path) -> None:
    key = Ed25519PrivateKey.generate()
    report = AeonVerifier.verify_manifest(
        _write(tmp_path, _legacy_manifest(key)), expected_public_key_b64=_public_b64(key)
    )
    assert report["overall_valid"] is False


@pytest.mark.parametrize(
    "field,value",
    [
        ("aeon_id", "OTHER-AEON"),
        ("status", "FORGED"),
        ("merkle_root", "34" * 32),
        ("total_claims_sealed", 17),
        ("hardware_attestation", {"hardware_uuid": "FOREIGN"}),
        ("extra", {"nested": ["unsigned", 1]}),
        ("schema", "unrecognized"),
    ],
)
def test_c0271_every_manifest_field_is_covered(tmp_path: Path, field: str, value: object) -> None:
    key, data = _valid_manifest()
    data[field] = value
    report = AeonVerifier.verify_manifest(_write(tmp_path, data), expected_public_key_b64=_public_b64(key))
    assert report["overall_valid"] is False
    assert report["ed25519_signature_valid"] is False


def test_c0271_cannot_promote_host_uuid_to_hardware_attestation(tmp_path: Path) -> None:
    key, data = _valid_manifest()
    report = AeonVerifier.verify_manifest(
        _write(tmp_path, data), expected_public_key_b64=_public_b64(key), require_hardware=True
    )
    assert report["is_origin_host"] is True
    assert report["ed25519_signature_valid"] is True
    assert report["hardware_attestation_verified"] is False
    assert report["overall_valid"] is False


def test_c0271_duplicate_manifest_keys_are_rejected(tmp_path: Path) -> None:
    path = tmp_path / "duplicate.json"
    path.write_text('{"merkle_root":"a","merkle_root":"b"}')
    with pytest.raises(ValueError, match="Duplicate"):
        AeonVerifier.verify_manifest(path)


@pytest.mark.parametrize("mutate_db", [False, True])
def test_c0271_optional_ledger_crosscheck(tmp_path: Path, mutate_db: bool) -> None:
    key, data = _valid_manifest()
    db = tmp_path / "claims.sqlite"
    with sqlite3.connect(db) as connection:
        connection.execute(
            "CREATE TABLE bounty_claims (claim_id, advisory_id, domain, risk_score, payload_hash, timestamp_utc, hardware_anchor, attestation_merkle_root)"
        )
        connection.execute(
            "INSERT INTO bounty_claims VALUES (?,?,?,?,?,?,?,?)",
            ("claim", "advisory", "domain", 1, "payload", "fixture", "software", "anchor"),
        )
    data["merkle_root"] = compute_claim_leaf_hash("claim", "advisory", "domain", "payload", "anchor")
    _sign_manifest(key, data)
    if mutate_db:
        with sqlite3.connect(db) as connection:
            connection.execute("UPDATE bounty_claims SET payload_hash='altered'")
    report = AeonVerifier.verify_manifest(_write(tmp_path, data), db_path=db, expected_public_key_b64=_public_b64(key))
    assert report["overall_valid"] is not mutate_db
    assert report["tree_integrity_valid"] is not mutate_db
    assert report["verification_scope"] == ("REJECTED" if mutate_db else "AUTHENTICATED_MANIFEST_AND_LEDGER")


def test_c0276_hardware_requirement_fails_before_identifier_access(monkeypatch: pytest.MonkeyPatch) -> None:
    def unexpected(self):
        raise AssertionError("Must fail before metadata access")

    monkeypatch.setattr(MerkleCausalAnchor, "get_hardware_identity", unexpected)
    with pytest.raises(RuntimeError, match="Hardware attestation is unavailable"):
        MerkleCausalAnchor().generate_hardware_pcr_quote("12" * 32, require_hardware=True)


def test_c0276_software_measurement_never_loads_signing_seed(monkeypatch: pytest.MonkeyPatch) -> None:
    class NoSigningSeed(dict[str, str]):
        def get(self, key, default=None):
            if key == "BABYLON60_SIGNING_SEED":
                raise AssertionError("Must not read a signing seed for unauthenticated metadata")
            return super().get(key, default)

    monkeypatch.setattr(os, "environ", NoSigningSeed(os.environ))
    quote = MerkleCausalAnchor().generate_hardware_pcr_quote("12" * 32)
    assert len(quote["pcr_value"]) == 64
    assert quote["measurement_algorithm"] == "SHA-256_SOFTWARE"
    assert quote["hardware_attestation_verified"] is False


def test_c0432_explicit_software_authority_signature_is_verifiable(monkeypatch: pytest.MonkeyPatch) -> None:
    key = Ed25519PrivateKey.generate()
    seed = key.private_bytes(serialization.Encoding.Raw, serialization.PrivateFormat.Raw, serialization.NoEncryption())
    monkeypatch.setenv("BABYLON_LICENSE_ED25519_SEED", seed.hex())
    cert, digest = _license_module().generate_license_certificate("Synthetic Client", "FIXTURE", "pilot")
    seal = cert.pop("cryptographic_seal")
    encoded = json.dumps(cert, sort_keys=True, ensure_ascii=False).encode()
    key.public_key().verify(bytes.fromhex(seal["signature_hex"]), encoded)
    assert seal["digest"] == digest
    assert seal["status"] == "SIGNED_WITH_CONFIGURED_AUTHORITY"
    assert (
        seal["public_key_hex"]
        == key.public_key().public_bytes(serialization.Encoding.Raw, serialization.PublicFormat.Raw).hex()
    )


def test_c0432_cli_rejects_before_creating_output(tmp_path: Path) -> None:
    module = Path(__file__).resolve().parents[1] / "tools/tamkarum_license_provisioner.py"
    target = tmp_path / "not-created"
    result = subprocess.run(
        [sys.executable, str(module), "--client", "Synthetic", "--vat", "FIXTURE", "--out-dir", str(target)],
        capture_output=True,
        text=True,
        timeout=10,
    )
    assert result.returncode != 0
    assert "License authority" in result.stderr
    assert not target.exists()


def test_c0432_cli_emits_verifiable_software_signed_license(tmp_path: Path) -> None:
    module = Path(__file__).resolve().parents[1] / "tools/tamkarum_license_provisioner.py"
    key = Ed25519PrivateKey.generate()
    seed = key.private_bytes(serialization.Encoding.Raw, serialization.PrivateFormat.Raw, serialization.NoEncryption())
    environment = dict(os.environ, BABYLON_LICENSE_ED25519_SEED=seed.hex())
    target = tmp_path / "licenses"
    result = subprocess.run(
        [sys.executable, str(module), "--client", "Synthetic", "--vat", "FIXTURE", "--out-dir", str(target)],
        env=environment,
        capture_output=True,
        text=True,
        timeout=10,
    )
    assert result.returncode == 0
    licenses = list(target.glob("*_license.json"))
    assert len(licenses) == len(list(target.glob("*_invoice.txt"))) == 1
    payload = json.loads(licenses[0].read_text())
    seal = payload.pop("cryptographic_seal")
    assert seal["status"] == "SIGNED_WITH_CONFIGURED_AUTHORITY"
    key.public_key().verify(
        bytes.fromhex(seal["signature_hex"]), json.dumps(payload, sort_keys=True, ensure_ascii=False).encode()
    )


@pytest.mark.parametrize("root", [" " * 64, "00 " * 21 + "0", "gg" * 32])
def test_c0271_signed_but_malformed_root_rejected(tmp_path: Path, root: str) -> None:
    key, data = _valid_manifest()
    data["merkle_root"] = root
    _sign_manifest(key, data)
    assert (
        AeonVerifier.verify_manifest(_write(tmp_path, data), expected_public_key_b64=_public_b64(key))["overall_valid"]
        is False
    )


def test_c0271_warmup_and_repeated_valid_tampered_rounds(tmp_path: Path) -> None:
    for _ in range(3 + 20):
        key, data = _valid_manifest()
        path = _write(tmp_path, data)
        pin = _public_b64(key)
        assert AeonVerifier.verify_manifest(path, expected_public_key_b64=pin)["overall_valid"] is True
        data["total_claims_sealed"] += 1
        path = _write(tmp_path, data)
        assert AeonVerifier.verify_manifest(path, expected_public_key_b64=pin)["overall_valid"] is False
