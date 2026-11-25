"""Verify the local biometric helper protocol against an operator-provisioned key.

A valid signature proves possession of the pinned key. Hardware provenance depends
on its trusted provisioning; a self-reported public key never establishes trust.
"""

from __future__ import annotations

import base64
import hashlib
import json
import os
import subprocess as subprocess
from pathlib import Path

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec


def _public_key(raw: bytes) -> ec.EllipticCurvePublicKey:
    key: object
    try:
        key = ec.EllipticCurvePublicKey.from_encoded_point(ec.SECP256R1(), raw)
    except ValueError:
        key = serialization.load_der_public_key(raw)
    if not isinstance(key, ec.EllipticCurvePublicKey) or not isinstance(key.curve, ec.SECP256R1):
        raise ValueError("Expected a P-256 public key")
    return key


def configured_public_key() -> bytes:
    value = os.environ.get("BABYLON_ENCLAVE_PINNED_PUBKEY", "")
    for decode in (bytes.fromhex, lambda text: base64.b64decode(text, validate=True)):
        try:
            return _public_key(decode(value)).public_bytes(
                serialization.Encoding.X962, serialization.PublicFormat.UncompressedPoint
            )
        except (ValueError, TypeError):
            continue
    raise ValueError("BABYLON_ENCLAVE_PINNED_PUBKEY must contain a provisioned P-256 key")


def verify_attestation(payload: bytes, evidence: str, trusted_key: bytes) -> dict[str, object]:
    """Reject incomplete, contradictory, substituted or incorrectly signed responses."""
    result = json.loads(evidence)
    if not isinstance(result, dict) or result.get("status") != "ATTESTED" or result.get("success") is False:
        raise ValueError("Biometric helper did not attest the request")
    # SHA-256 is restricted to the NIST P-256 signing pre-hash/context.
    if result.get("causal_hash") != hashlib.sha256(payload).hexdigest():
        raise ValueError("Attestation is for a different request")
    public_key = result.get("public_key")
    signature = result.get("secure_enclave_signature")
    if not isinstance(public_key, str) or not isinstance(signature, str):
        raise ValueError("Attestation has no public key or signature")
    returned = _public_key(base64.b64decode(public_key, validate=True))
    trusted = _public_key(trusted_key)
    if returned.public_numbers() != trusted.public_numbers():
        raise ValueError("Attestation key is not the provisioned authority")
    try:
        trusted.verify(base64.b64decode(signature, validate=True), payload, ec.ECDSA(hashes.SHA256()))
    except InvalidSignature as exc:
        raise ValueError("Invalid attestation signature") from exc
    return result


def request_attestation(payload: bytes, gate: Path, action: str, scope: str, trusted_key: bytes) -> str:
    """One bounded attempt; callers must deny authorization on every failure."""
    cmd = ["swift", str(gate)] if gate.suffix == ".swift" else [str(gate)]
    cmd += [
        "--causal-hash",
        hashlib.sha256(payload).hexdigest(),
        "--sign-hex",
        payload.hex(),
        "--action",
        action,
        "--scope",
        scope,
        "--agent",
        "BABYLON-60",
        "--no-sound",
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, check=True, timeout=25)
    verify_attestation(payload, result.stdout, trusted_key)
    return result.stdout
