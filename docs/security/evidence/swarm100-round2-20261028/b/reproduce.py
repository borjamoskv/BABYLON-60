import sys
import json
import hashlib
import uuid
import sqlite3
import traceback
from pathlib import Path

sys.path.insert(0, str(Path.cwd() / "01_KISH_ENGINE"))
from babylon60.verifier.cli import parse_crl_arg
from babylon60.verifier.standalone_verify import (
    verify_compliance_certificate,
    verify_offline_evidence,
    canonical_json,
    build_cortex_merkle_tree,
)
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.hazmat.primitives import serialization

BASE = Path(__file__).resolve().parent
cases = []


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def sources(*ps):
    return {p: sha(p) for p in ps}


def cert(root):
    c = {
        "certificate_id": "isolated-revoked-cert",
        "system_identifier": "isolated-system",
        "operator": "audit-fixture",
        "issued_at": "2026-01-01T00:00:00+00:00",
        "valid_until": "2099-01-01T00:00:00+00:00",
        "global_merkle_root": root,
        "articles_compliance": {},
    }
    k = Ed25519PrivateKey.generate()
    sig = k.sign(canonical_json(c).encode())
    pub = k.public_key().public_bytes(serialization.Encoding.Raw, serialization.PublicFormat.Raw)
    c["signature"] = {"public_key": pub.hex(), "signature": sig.hex(), "algorithm": "Ed25519"}
    return c


try:
    crl = BASE / "crl.json"
    crl.write_text(json.dumps(["isolated-revoked-cert"]))
    c = cert("0" * 64)
    goodlist = parse_crl_arg(str(crl))
    good = verify_compliance_certificate(c, crl=goodlist)
    crl.write_text("{malformed")
    badlist = parse_crl_arg(str(crl))
    bad = verify_compliance_certificate(c, crl=badlist)
    cases.append(
        {
            "case": "malformed_crl",
            "status": "confirmed" if not good["valid"] and bad["valid"] else "inconclusive",
            "sources": sources(
                "01_KISH_ENGINE/babylon60/verifier/cli.py", "01_KISH_ENGINE/babylon60/verifier/standalone_verify.py"
            ),
            "trigger": "Same signed unexpired temporary certificate; valid CRL replaced with invalid JSON at same path.",
            "observed": {
                "valid_crl_parsed": goodlist,
                "valid_crl_result": good,
                "malformed_crl_parsed": badlist,
                "malformed_crl_result": bad,
            },
            "scope": "Actual verifier functions on temporary data, real Ed25519 signature; no issuer identity or production runtime claim.",
            "guards": "Signature validates in both; membership rejects original ID, but malformed-file fallback supplies path string so ID membership guard misses.",
        }
    )
except Exception:
    cases.append({"case": "malformed_crl", "status": "inconclusive", "exception": traceback.format_exc()})
try:
    p = BASE / "ledger.json"
    event = {"payload": {"amount": 10}, "entry_hash": hashlib.sha256(b"fixture-original-entry").hexdigest()}
    root = build_cortex_merkle_tree([event["entry_hash"]])
    c = cert(root)
    p.write_text(json.dumps([event]))
    before = verify_offline_evidence(p, root)
    cert_before = verify_compliance_certificate(c, p)
    event["payload"]["amount"] = 999999
    p.write_text(json.dumps([event]))
    after = verify_offline_evidence(p, root)
    cert_after = verify_compliance_certificate(c, p)
    event["entry_hash"] = "f" * 64
    p.write_text(json.dumps([event]))
    negative = verify_offline_evidence(p, root)
    cases.append(
        {
            "case": "json_ledger_payload",
            "status": "confirmed"
            if before["verified"] and after["verified"] and cert_after["valid"] and not negative["verified"]
            else "inconclusive",
            "sources": sources("01_KISH_ENGINE/babylon60/verifier/standalone_verify.py"),
            "trigger": "Change event payload amount10 to999999 while retaining entry_hash and signed expected root.",
            "observed": {
                "original": before,
                "mutated_payload": after,
                "certificate_original": cert_before,
                "certificate_mutated_payload": cert_after,
                "negative_changed_hash": negative,
            },
            "scope": "Actual offline verifier and certificate consumer, temporary JSON fixture, real Ed25519 signature. Entry hash is a supplied fixture commitment, not proof of original event schema correctness.",
            "guards": "Root comparison rejects changed entry_hash but never recalculates event hash from payload; therefore event content mutation is invisible.",
        }
    )
except Exception:
    cases.append({"case": "json_ledger_payload", "status": "inconclusive", "exception": traceback.format_exc()})
try:
    from babylon60.memory.governance import MemoryGovernanceEngine

    db = BASE / "governance.sqlite"
    assert not db.exists(), "fresh fixture required"
    a = MemoryGovernanceEngine(db)
    b = MemoryGovernanceEngine(db)
    for e in (a, b):
        e.register_principal_key("tenant", "operator", b"isolated-fixture-key-32-bytes-long")
    parent = a.add_record(tenant_id="tenant", principal="operator", content="parent fixture")
    child_id = str(uuid.uuid4())
    original = a.ledger.append_event
    interceptions = []

    def controlled_append(event, *args, **kwargs):
        if event.event_type == "MEMORY_RECORD_COMMITTED" and event.payload.get("record_id") == child_id:
            interceptions.append(
                {
                    "point": "A ledger append entry after ACTIVE parent validation transaction committed",
                    "B_revocation": b.revoke_record(
                        record_id=parent.record_id, tenant_id="tenant", principal="operator"
                    ),
                }
            )
        return original(event, *args, **kwargs)

    a.ledger.append_event = controlled_append
    child = a.add_record(
        record_id=child_id,
        tenant_id="tenant",
        principal="operator",
        content="derived child fixture",
        parents=[parent.record_id],
    )
    with sqlite3.connect(db) as conn:
        rows = conn.execute("SELECT record_id,status FROM cortex_memory_records ORDER BY record_id").fetchall()
        blobs = conn.execute("SELECT record_id FROM cortex_memory_blobs").fetchall()
    try:
        a.add_record(
            tenant_id="tenant",
            principal="operator",
            content="negative after completed revocation",
            parents=[parent.record_id],
        )
        negative = {"accepted": True}
    except Exception as ex:
        negative = {"accepted": False, "type": type(ex).__name__, "message": str(ex)}
    statuses = dict(rows)
    cases.append(
        {
            "case": "governance_parent_revocation_interleaving",
            "status": "confirmed"
            if statuses[parent.record_id] == "REVOKED" and statuses[child_id] == "ACTIVE" and not negative["accepted"]
            else "inconclusive",
            "sources": sources(
                "01_KISH_ENGINE/babylon60/memory/governance.py", "01_KISH_ENGINE/babylon60/bft/cortex_persist_ledger.py"
            ),
            "trigger": "A validates parent; deterministic interception at A ledger append runs B full revoke on shared fresh SQLite database; A resumes actual ledger append and insertion.",
            "observed": {
                "interceptions": interceptions,
                "record_statuses": rows,
                "remaining_blob_ids": blobs,
                "child_return_status": child.status.value,
                "negative_add_after_revoke": negative,
            },
            "scope": "Actual governance and real ledger code on new temporary SQLite; synchronous deterministic scheduling interception, not a probabilistic multithread stress test. Hook only schedules B and delegates A unchanged; no validation or persistence code replaced.",
            "guards": "Both engines use registered same-tenant principal; FK checks row existence, not ACTIVE status. BEGIN IMMEDIATE ends before ledger append; resumed insert does not repeat status validation. Negative control rejects validation after revocation.",
        }
    )
except Exception:
    cases.append(
        {
            "case": "governance_parent_revocation_interleaving",
            "status": "inconclusive",
            "exception": traceback.format_exc(),
        }
    )
(BASE / "results.json").write_text(
    json.dumps(
        {
            "cases": cases,
            "source_script_sha256": sha(__file__),
            "tests_scope": "Three bounded isolated reproductions, no source edits, hardware or external network.",
        },
        indent=2,
    )
)
print(
    json.dumps([{"case": x["case"], "status": x["status"], "exception": x.get("exception")} for x in cases], indent=2)
)
