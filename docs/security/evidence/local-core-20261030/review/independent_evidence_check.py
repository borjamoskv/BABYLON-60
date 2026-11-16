"""Read-only independent observer; never imports Babylon or requests authentication.

A passing result validates the observed evidence, not Secure Enclave provenance.
That provenance additionally requires the reviewed native metadata preflight.
"""
from __future__ import annotations

import argparse
import base64
import hashlib
import json
import math
import sqlite3
import time
from pathlib import Path

from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False)


def load_key(raw):
    try:
        key = ec.EllipticCurvePublicKey.from_encoded_point(ec.SECP256R1(), raw)
    except ValueError:
        key = serialization.load_der_public_key(raw)
    if not isinstance(key, ec.EllipticCurvePublicKey) or not isinstance(key.curve, ec.SECP256R1):
        raise ValueError("Expected P-256 authority")
    return key


def validate(payload, evidence, expected_task, pinned_key, events, consumed):
    """Pure checks support synthetic falsification without product code or hardware."""
    proof = json.loads(payload)
    witness = json.loads(evidence)
    if proof.get("version") != 1 or proof.get("decision") != "APPROVED":
        raise ValueError("Missing approved proof")
    if canonical(proof.get("task")) != canonical(expected_task):
        raise ValueError("Proof does not bind the exact prepared task")
    issued, expires = proof.get("issued_at"), proof.get("expires_at")
    if any(type(v) not in (int, float) or not math.isfinite(v) for v in (issued, expires)):
        raise ValueError("Invalid proof times")
    if not 0 < expires - issued <= 300:
        raise ValueError("Invalid proof lifetime")
    nonce = proof.get("nonce")
    if not isinstance(nonce, str) or len(nonce) != 64 or any(c not in "0123456789abcdef" for c in nonce):
        raise ValueError("Invalid nonce")
    if witness.get("status") != "ATTESTED" or witness.get("success") is False:
        raise ValueError("Not attested")
    if witness.get("causal_hash") != hashlib.sha256(payload.encode("utf-8")).hexdigest():
        raise ValueError("Wrong causal hash")
    trusted = load_key(pinned_key)
    returned = load_key(base64.b64decode(witness["public_key"], validate=True))
    if trusted.public_numbers() != returned.public_numbers():
        raise ValueError("Wrong authority")
    trusted.verify(base64.b64decode(witness["secure_enclave_signature"], validate=True),
                   payload.encode("utf-8"), ec.ECDSA(hashes.SHA256()))
    if any(not isinstance(witness.get(k), str) or not witness[k] for k in ("operator_user", "operator_name")):
        raise ValueError("Missing operator identity")
    if len(events) != 1:
        raise ValueError("Effect count is not exactly one")
    event = events[0]
    arguments = expected_task["arguments"]
    if event["event_type"] != arguments["event_type"] or event["cortex_taint"] != arguments["cortex_taint"]:
        raise ValueError("Wrong effect identity")
    if canonical(json.loads(event["payload_json"])) != canonical(arguments["payload"]):
        raise ValueError("Wrong effect payload")
    if not event["event_id"] or not event["entry_hash"]:
        raise ValueError("Missing durable event identity")
    if consumed != [expected_task["execution_id"]]:
        raise ValueError("Durable consumption missing or inconsistent")
    return {"proof_sha256": hashlib.sha256(payload.encode()).hexdigest(),
            "event_id": event["event_id"], "entry_hash": event["entry_hash"],
            "proof_currently_valid": issued <= time.time() < expires,
            "hardware_provenance": "REQUIRES_SEPARATE_NATIVE_PREFLIGHT"}


def identity(path):
    s = path.stat()
    return {"device": s.st_dev, "inode": s.st_ino}


def read_db(path, queries):
    before = identity(path)
    conn = sqlite3.connect(path.absolute().as_uri() + "?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    try:
        conn.execute("BEGIN")
        if conn.execute("PRAGMA quick_check").fetchall()[0][0] != "ok":
            raise ValueError("Database integrity check failed")
        result = [[dict(row) for row in conn.execute(sql, params)] for sql, params in queries]
    finally:
        conn.close()
    if identity(path) != before:
        raise ValueError("Database identity changed while observing")
    return before, result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("ledger", "gate", "task", "public-key-file", "output"):
        parser.add_argument("--" + name, required=True, type=Path)
    args = parser.parse_args()
    task = json.loads(args.task.read_text())
    key = bytes.fromhex(args.public_key_file.read_text().strip())
    ledger_identity, ledger = read_db(args.ledger, [("SELECT event_id,event_type,payload_json,cortex_taint,entry_hash FROM cortex_ledger", ())])
    gate_identity, gate = read_db(args.gate, [
        ("SELECT a.decision,a.action_name,s.payload,s.evidence FROM audit_ledger a JOIN signed_approvals s ON s.ledger_id=a.id WHERE a.execution_id=? ORDER BY a.id", (task["execution_id"],)),
        ("SELECT execution_id FROM consumed_mcp_effects ORDER BY execution_id", ())])
    if len(gate[0]) != 1 or gate[0][0]["decision"] != "APPROVED" or gate[0][0]["action_name"] != task["action"]:
        raise ValueError("Expected exactly one matching signed approval")
    row = gate[0][0]
    checked = validate(row["payload"], row["evidence"], task, key, ledger[0], [r["execution_id"] for r in gate[1]])
    report = {"decision": "OBSERVED_EVIDENCE_VALID", "observed_at": time.time(), "ledger_identity": ledger_identity,
              "gate_identity": gate_identity, "event_count": len(ledger[0]), "signed_approval_count": len(gate[0]),
              "consumed_count": len(gate[1]), **checked}
    args.output.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, sort_keys=True))


if __name__ == "__main__":
    main()
