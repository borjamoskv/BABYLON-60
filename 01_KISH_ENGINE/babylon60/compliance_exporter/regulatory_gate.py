"""Native approval bridge and independent, read-only publication verifier."""

from __future__ import annotations

import hashlib
import os
import struct
import subprocess
import time
from pathlib import Path

import blake3
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives.asymmetric.utils import encode_dss_signature

from .regulatory import BLOCKING_IDS, CATALOGUE_DIGEST, JSONDocument, canonical, digest, verify_review


def invoke_native(request: JSONDocument, *, binary: str, policy_path: str, ledger_path: str) -> JSONDocument:
    """Only an explicit installed executable; never shell execution or fallback."""
    import json

    executable = Path(binary).absolute()
    if not executable.is_file() or not os.access(executable, os.X_OK):
        raise ValueError("Native gate unavailable; regulated operation rejected")
    result = subprocess.run(
        [str(executable), "--policy", str(Path(policy_path).absolute()), "--ledger", str(Path(ledger_path).absolute())],
        input=canonical(request),
        capture_output=True,
        timeout=55,
        check=False,
    )
    if result.returncode:
        raise ValueError(f"Native gate rejected operation: {result.stderr.decode(errors='replace')[:2000]}")
    response: JSONDocument = json.loads(result.stdout)
    if not isinstance(response, dict):
        raise ValueError("Invalid native response")
    return response


def authorization(
    action: str,
    result: JSONDocument,
    *,
    commit: str,
    artifact_sha256: str,
    destination: str,
    run_id: str,
    run_attempt: str,
    now: int | None = None,
) -> JSONDocument:
    now = int(time.time()) if now is None else now
    if action not in {"approve", "authorize-release"} or not result["gate_eligible"]:
        raise ValueError("Articles 9–14 require complete evidence and an authorized review")
    if not all(isinstance(v, str) and v.strip() for v in (commit, artifact_sha256, destination, run_id, run_attempt)):
        raise ValueError("Exact commit, artifact, destination and execution are required")
    import re

    if not re.fullmatch(r"[0-9a-f]{40}|[0-9a-f]{64}", commit) or not re.fullmatch(r"[0-9a-f]{64}", artifact_sha256):
        raise ValueError("Invalid commit or artifact digest")
    return {
        "schema": "babylon60.euai.authorization.v1",
        "action": action,
        "source_fact_hash": result["source_fact_hash"],
        "profile_digest": result["profile_digest"],
        "commit": commit,
        "artifact_sha256": artifact_sha256,
        "destination": destination,
        "run_id": run_id,
        "run_attempt": run_attempt,
        "expires_at": min(now + 3600, result["review_statement"]["expires_at"]),
        "native_validation_digest": result["native_validation_digest"],
    }


def verify_receipt(
    receipt: JSONDocument, policy: JSONDocument, expected: JSONDocument, *, now: int | None = None
) -> None:
    """Verify binding and P-256 signature using externally provisioned trust.

    The policy must attest independent validation of the native binary. This
    verifies a recorded authorization, not the legal adequacy of the evidence.
    """
    now = int(time.time()) if now is None else now
    if receipt.get("schema") != "babylon60.euai.receipt.v1" or receipt.get("simulated") is not False:
        raise ValueError("Historical, simulated or unknown receipt")
    if receipt.get("backend") != "apple_secure_enclave" or receipt.get("measurement_status") != "UNAVAILABLE":
        raise ValueError("Unsupported hardware receipt")
    validation = policy.get("native_validation", {})
    if validation.get("status") != "VERIFIED" or receipt.get("native_validation") != validation:
        raise ValueError("NO_VERIFICADO: independent native validation missing or changed")
    for name in ("binary_sha256", "evidence_sha256"):
        if len(bytes.fromhex(validation[name])) != 32:
            raise ValueError("Invalid native validation evidence")
    if validation.get("backend_digest") != digest(policy.get("hardware_backend")):
        raise ValueError("Native backend configuration changed")
    auth = receipt["authorization"]
    if auth.get("schema") != "babylon60.euai.authorization.v1" or set(auth) != {
        "schema",
        "action",
        "source_fact_hash",
        "profile_digest",
        "commit",
        "artifact_sha256",
        "destination",
        "run_id",
        "run_attempt",
        "expires_at",
        "native_validation_digest",
    }:
        raise ValueError("Invalid authorization schema")
    if auth["native_validation_digest"] != digest(validation):
        raise ValueError("Authorization uses a different native validation")
    required = {"action", "profile_digest", "commit", "artifact_sha256", "destination", "run_id", "run_attempt"}
    if set(expected) != required or any(auth.get(k) != v for k, v in expected.items()):
        raise ValueError("Authorization belongs to a different operation or release")
    if type(auth.get("expires_at")) is not int or auth["expires_at"] <= now:
        raise ValueError("Authorization expired")
    if digest(auth) in policy.get("revoked_authorizations", []):
        raise ValueError("Authorization revoked")
    statement = verify_review(receipt["source_record"], policy, now)
    if statement.get("catalogue_digest") != CATALOGUE_DIGEST or statement.get("blocking_ids") != BLOCKING_IDS:
        raise ValueError("Review uses a different catalogue")
    if statement.get("gate_eligible") is not True or statement.get("classification") != "high_risk":
        raise ValueError("Review is not eligible for regulated approval")
    if auth["profile_digest"] != statement["profile_digest"] or auth["source_fact_hash"] != digest(
        receipt["source_record"]
    ):
        raise ValueError("Review binding invalid")
    if auth["expires_at"] > statement["expires_at"]:
        raise ValueError("Authorization outlives its review")
    envelope = bytes.fromhex(receipt["envelope_hex"])
    if len(envelope) != 107:
        raise ValueError("Invalid envelope length")
    tick = struct.unpack(">Q", envelope[:8])[0]
    if not 0 < tick <= 2**63 - 1 or envelope[106] != 2 or envelope[104:106] != b"\x00\x00":
        raise ValueError("Human attestation required")
    if envelope[40:72].hex() != auth["source_fact_hash"] or envelope[72:104].hex() != digest(auth):
        raise ValueError("Envelope does not authorize this payload")
    key_bytes = bytes.fromhex(policy["hardware_public_key_hex"])
    if bytes.fromhex(receipt["public_key_hex"]) != key_bytes:
        raise ValueError("Untrusted hardware key")
    key = ec.EllipticCurvePublicKey.from_encoded_point(ec.SECP256R1(), key_bytes)
    sig = bytes.fromhex(receipt["signature_hex"])
    if len(sig) != 64:
        raise ValueError("Invalid P-256 signature")
    signed = blake3.blake3(envelope, derive_key_context="BABYLON-60::RING0::CAUSAL_ENVELOPE::V1").digest()
    key.verify(
        encode_dss_signature(int.from_bytes(sig[:32], "big"), int.from_bytes(sig[32:], "big")),
        signed,
        ec.ECDSA(hashes.SHA256()),
    )
    root = blake3.blake3(derive_key_context="BABYLON-60::L0::MERKLE_NODE::V1")
    root.update(envelope + sig + hashlib.sha256(key_bytes).digest() + bytes(32))
    if receipt["merkle_root"] != root.hexdigest():
        raise ValueError("Invalid committed Merkle root")
