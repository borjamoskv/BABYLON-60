"""Isolated authorization checks: software keys never attest hardware."""

import importlib.util
import base64
import hashlib
import json
import sys
from pathlib import Path

import pytest
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec

from babylon60.verification.verification_gate import VerificationGate


@pytest.mark.parametrize(
    "payload",
    [
        {},
        {"action": "transfer_transaction"},
        {"action": "read_and_transfer"},
        {"action": "read_records", "command": "python arbitrary.py"},
    ],
)
def test_unclassified_requests_are_denied(payload):
    gate = VerificationGate()
    try:
        assert not gate.is_allowed(payload)
    finally:
        gate._conn.close()


def load_demo():
    path = Path(__file__).parents[1] / "scripts/c5_demos/c5_darknode_core.py"
    spec = importlib.util.spec_from_file_location("a02_darknode_demo", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_demo_rejects_invalid_json():
    demo = load_demo()
    with pytest.raises(ValueError):
        demo.BiometricTouchIDGate._parse_attestation_output("not-json", "00")


def signed_evidence(payload):
    key = ec.generate_private_key(ec.SECP256R1())
    public = key.public_key().public_bytes(serialization.Encoding.X962, serialization.PublicFormat.UncompressedPoint)
    evidence = json.dumps(
        {
            "status": "ATTESTED",
            "causal_hash": hashlib.sha256(payload).hexdigest(),
            "public_key": base64.b64encode(public).decode(),
            "secure_enclave_signature": base64.b64encode(key.sign(payload, ec.ECDSA(hashes.SHA256()))).decode(),
        }
    )
    return public, evidence


def test_demo_validates_signature_payload_and_pinned_key():
    demo = load_demo()
    payload = b'{"mutates_external_state":true}'
    public, evidence = signed_evidence(payload)
    assert demo.BiometricTouchIDGate._parse_attestation_output(evidence, payload, public)["status"] == "ATTESTED"
    other_public, _ = signed_evidence(payload)
    for response, actual, pinned in [
        ("not-json", payload, public),
        ('{"status":"ATTESTED"}', payload, public),
        (evidence, payload + b" ", public),
        (evidence, payload, other_public),
    ]:
        with pytest.raises(ValueError):
            demo.BiometricTouchIDGate._parse_attestation_output(response, actual, pinned)


def test_demo_helper_receives_real_payload_and_rejects_bad_evidence(monkeypatch):
    demo = load_demo()
    payload = b'{"effect":"test-only"}'
    public, evidence = signed_evidence(payload)
    monkeypatch.setattr(demo, "configured_public_key", lambda: public)
    calls = []

    def isolated_request(actual, gate, reason, scope, trusted):
        calls.append((actual, trusted))
        return evidence

    monkeypatch.setattr(demo, "request_attestation", isolated_request)
    assert demo.BiometricTouchIDGate.attest_causal_mutation("isolated test", payload)[0]
    assert calls == [(payload, public)]
    monkeypatch.setattr(demo, "request_attestation", lambda *args: "invalid")
    assert demo.BiometricTouchIDGate.attest_causal_mutation("isolated test", payload) == (False, {})


def test_unknown_operation_stays_denied_after_warmup():
    gate = VerificationGate()
    try:
        for _ in range(16):
            assert gate.is_allowed({"action": "read_records"})
        for index in range(256):
            assert not gate.is_allowed({"action": f"read_records_and_transfer_{index}"})
    finally:
        gate._conn.close()
