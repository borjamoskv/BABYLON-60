"""Software-only observer tests: real SQLite and signatures, never Touch ID."""

import argparse
import base64
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import pwd
import subprocess
import sys
import time

import pytest
from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec

from babylon60.bft.cortex_persist_ledger import CortexEvent, CortexPersistLedger
from babylon60.verification.verification_gate import InterventionChannel, RiskLevel, VerificationGate


MANUAL = Path(__file__).absolute().parent / "manual/hardware_mcp_cycle.py"
spec = importlib.util.spec_from_file_location("hardware_cycle_observers", MANUAL)
assert spec is not None and spec.loader is not None
cycle = importlib.util.module_from_spec(spec)
spec.loader.exec_module(cycle)


@pytest.fixture
def signed_fixture(tmp_path, monkeypatch):
    key = ec.generate_private_key(ec.SECP256R1())
    public = key.public_key().public_bytes(serialization.Encoding.X962, serialization.PublicFormat.UncompressedPoint)
    monkeypatch.setenv("BABYLON_ENCLAVE_PINNED_PUBKEY", public.hex())
    ledger = CortexPersistLedger(tmp_path / "ledger.db")
    gate = VerificationGate(str(tmp_path / "gate.db"))
    task = {"execution_id": "software-observer", "action": "mcp:bft_append_event", "is_mutative": True}
    now = time.time()
    proof = json.dumps({"version": 1, "task": task, "decision": "APPROVED", "nonce": "ab" * 32,
                        "issued_at": now - 1, "expires_at": now + 120}, indent=2)
    signature = key.sign(proof.encode(), ec.ECDSA(hashes.SHA256()))
    receipt = json.dumps({"status": "ATTESTED", "causal_hash": hashlib.sha256(proof.encode()).hexdigest(),
                          "public_key": base64.b64encode(public).decode(),
                          "secure_enclave_signature": base64.b64encode(signature).decode(),
                          "operator_user": pwd.getpwuid(os.getuid()).pw_name, "operator_name": "Software-only test operator",
                          "test_source": "SOFTWARE_ONLY"})
    gate.register_sign_off(task["execution_id"], task["action"], RiskLevel.CRITICAL, "APPROVED", InterventionChannel.HARD_SURGERY)
    ledger_id = gate._conn.execute("SELECT last_insert_rowid()").fetchone()[0]
    with gate._conn:
        gate._conn.execute("INSERT INTO signed_approvals VALUES (?,?,?)", (ledger_id, proof, receipt))
    task_file = tmp_path / "task.json"
    task_file.write_text(json.dumps(task))
    yield tmp_path, task, public, proof, receipt, gate, ledger
    gate._conn.close()


def test_observer_verifies_exact_stored_bytes_in_separate_process(signed_fixture):
    directory, task, _, proof, receipt, _, _ = signed_fixture
    result = subprocess.run([sys.executable, "-I", str(MANUAL), "--observe", str(directory), str(directory / "task.json")],
                            check=True, text=True, capture_output=True, timeout=15)
    observed = json.loads(result.stdout)
    assert observed["pid"] != os.getpid()
    cycle.check_observation(observed, task, executed=False)
    assert observed["approvals"][0]["proof_raw"] == proof
    assert observed["approvals"][0]["receipt_raw"] == receipt
    assert observed["approvals"][0]["causal_sha256"] == hashlib.sha256(proof.encode()).hexdigest()


@pytest.mark.parametrize("damage", ["task", "nonce", "receipt_hash", "key", "signature"])
def test_observer_rejects_signed_record_tampering(signed_fixture, damage):
    _, task, public, proof, receipt, _, _ = signed_fixture
    if damage in {"task", "nonce"}:
        data = json.loads(proof)
        data[damage] = {} if damage == "task" else "cd" * 32
        proof = json.dumps(data)
    else:
        data = json.loads(receipt)
        if damage == "receipt_hash":
            data["causal_hash"] = "0" * 64
        elif damage == "key":
            other = ec.generate_private_key(ec.SECP256R1()).public_key()
            data["public_key"] = base64.b64encode(other.public_bytes(serialization.Encoding.X962, serialization.PublicFormat.UncompressedPoint)).decode()
        else:
            data["secure_enclave_signature"] = base64.b64encode(b"invalid signature").decode()
        receipt = json.dumps(data)
    with pytest.raises((ValueError, InvalidSignature)):
        cycle.verify_signed_record(proof, receipt, task, public)


def test_valid_receipt_cannot_authorize_a_different_prepared_task(signed_fixture):
    _, task, public, proof, receipt, _, _ = signed_fixture
    with pytest.raises(ValueError, match="differs from the task prepared"):
        cycle.verify_signed_record(proof, receipt, {**task, "execution_id": "substituted"}, public)


def test_signed_boolean_cannot_alias_integer_in_prepared_task(signed_fixture):
    _, task, public, proof, receipt, _, _ = signed_fixture
    assert task["is_mutative"] is True
    with pytest.raises(ValueError, match="differs from the task prepared"):
        cycle.verify_signed_record(proof, receipt, {**task, "is_mutative": 1}, public)


@pytest.mark.parametrize("field,value", [("operator_user", None), ("operator_user", "another-user"),
                                         ("operator_name", None), ("operator_name", "  ")])
def test_valid_signature_requires_operator_identity(signed_fixture, field, value):
    _, task, public, proof, receipt, _, _ = signed_fixture
    data = json.loads(receipt)
    if value is None:
        data.pop(field)
    else:
        data[field] = value
    with pytest.raises(ValueError, match="operator"):
        cycle.verify_signed_record(proof, json.dumps(data), task, public)


def test_independent_reopen_proves_exact_consumption_and_event(signed_fixture):
    directory, task, public, _, _, gate, ledger = signed_fixture
    gate.execute_once(task, lambda: ledger.append_event(CortexEvent(
        event_type=cycle.EVENT, payload={"execution_id": task["execution_id"]}, cortex_taint="software-only-test",
    )))
    observed = cycle.observe(directory / "ledger.db", directory / "gate.db", task, public)
    cycle.check_observation(observed, task, executed=True)
    result = subprocess.run([sys.executable, "-I", str(MANUAL), "--probe-consumed", str(directory), str(directory / "task.json")],
                            check=True, text=True, capture_output=True, timeout=15)
    report = json.loads(result.stdout)
    assert report["status"] == "CONSUMED_REJECTED"
    assert report["pid"] != os.getpid()
    assert not (directory / "UNEXPECTED-REPLAY").exists()
    after = cycle.observe(directory / "ledger.db", directory / "gate.db", task, public)
    assert after["events"] == observed["events"]
    assert after["consumed"] == [task["execution_id"]]


@pytest.mark.parametrize("field,value", [("consumed", ["another-task"]), ("events", []), ("approvals", [])])
def test_success_response_cannot_replace_physical_evidence(signed_fixture, field, value):
    directory, task, public, _, _, gate, ledger = signed_fixture
    gate.execute_once(task, lambda: ledger.append_event(CortexEvent(
        event_type=cycle.EVENT, payload={"execution_id": task["execution_id"]}, cortex_taint="software-only-test",
    )))
    observed = cycle.observe(directory / "ledger.db", directory / "gate.db", task, public)
    cycle.check_observation(observed, task, executed=True)
    observed[field] = value
    with pytest.raises(ValueError):
        cycle.check_observation(observed, task, executed=True)


def test_attempt_marker_is_exclusive_and_keeps_original_task(tmp_path):
    cycle.reserve_attempt(tmp_path, {"execution_id": "first"})
    original = (tmp_path / "attempt-started.json").read_bytes()
    with pytest.raises(FileExistsError):
        cycle.reserve_attempt(tmp_path, {"execution_id": "second"})
    assert (tmp_path / "attempt-started.json").read_bytes() == original


def test_missing_pin_fails_before_helper_or_attempt_and_cannot_reuse_directory(tmp_path, monkeypatch):
    monkeypatch.delenv("BABYLON_ENCLAVE_PINNED_PUBKEY", raising=False)
    monkeypatch.setattr(sys, "platform", "darwin")
    evidence = tmp_path / "attempt"
    args = argparse.Namespace(evidence_dir=evidence)
    with pytest.raises(ValueError, match="provisioned P-256"):
        cycle.run_once(args)
    report = json.loads((evidence / "result.json").read_text())
    assert report["status"] == "FAIL"
    assert report["attempt_started"] is False
    assert not (evidence / "attempt-started.json").exists()
    with pytest.raises(FileExistsError):
        cycle.run_once(args)


def test_inspection_cannot_establish_its_own_pin(signed_fixture):
    _, _, public, _, _, _, _ = signed_fixture
    report = {"schema": "babylon60.public-key-inspection.v1", "status": "PUBLIC_KEY_INSPECTED",
              "origin": "CryptoKit.SecureEnclave.P256.Signing.PrivateKey(existing_dataRepresentation)",
              "public_key_sec1": public.hex(), "key_record_sha256": "a" * 64, "token_id": None}
    cycle.validate_inspection(report, public, "a" * 64)
    with pytest.raises(ValueError, match="record changed"):
        cycle.validate_inspection(report, public, "b" * 64)
    with pytest.raises(ValueError, match="provisioned pin"):
        cycle.validate_inspection(report, b"another pin", "a" * 64)


def test_partial_stdio_response_has_a_complete_message_deadline(tmp_path, monkeypatch):
    """An isolated broken transport process cannot strand the manual runner."""
    peer = cycle.Peer.__new__(cycle.Peer)
    peer.log = (tmp_path / "partial-stderr.log").open("wb")
    peer.process = subprocess.Popen(
        [sys.executable, "-I", "-c", "import sys,time;sys.stdin.readline();sys.stdout.write('{');sys.stdout.flush();time.sleep(2)"],
        stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=peer.log, text=True,
    )
    peer.counter, peer.buffer = 0, b""
    monkeypatch.setattr(cycle, "MCP_DEADLINE_SECONDS", 0.2)
    started = time.monotonic()
    try:
        with pytest.raises(ValueError, match="timeout"):
            peer.call("ping", {})
        assert time.monotonic() - started < 1.5
    finally:
        peer.close()


def test_manual_stdio_client_executes_once_and_restarts_with_software_authority(tmp_path, monkeypatch):
    """Real native broker and MCP transport; the signing authority is software only."""
    library = os.environ.get("BABYLON60_TEST_CAPABILITY_LIBRARY")
    if library is None:
        pytest.skip("requires the separately compiled native broker")
    key = ec.generate_private_key(ec.SECP256R1())
    public = key.public_key().public_bytes(serialization.Encoding.X962, serialization.PublicFormat.UncompressedPoint)
    monkeypatch.setenv("BABYLON_ENCLAVE_PINNED_PUBKEY", public.hex())
    env = dict(os.environ)
    peer = cycle.Peer(tmp_path, Path(library), env, "software-first")
    gate = None
    try:
        peer.initialize()
        params = {"name": "bft_append_event",
                  "arguments": {"event_type": cycle.EVENT, "payload": {"execution_id": "manual-client"}, "cortex_taint": "software-only"},
                  "_meta": {"babylon60/authorization": {"execution_id": "manual-client", "mode": "prepare"}}}
        prepared = peer.call("tools/call", params)
        assert prepared["isError"] is False
        task = prepared["approval_task"]
        now = time.time()
        proof = json.dumps({"version": 1, "task": task, "decision": "APPROVED", "nonce": "cd" * 32,
                            "issued_at": now - 1, "expires_at": now + 120})
        receipt = json.dumps({"status": "ATTESTED", "causal_hash": hashlib.sha256(proof.encode()).hexdigest(),
                              "public_key": base64.b64encode(public).decode(), "test_source": "SOFTWARE_ONLY",
                              "secure_enclave_signature": base64.b64encode(key.sign(proof.encode(), ec.ECDSA(hashes.SHA256()))).decode(),
                              "operator_user": pwd.getpwuid(os.getuid()).pw_name, "operator_name": "Software-only test operator"})
        gate = VerificationGate(str(tmp_path / "gate.db"))
        gate.register_sign_off(task["execution_id"], task["action"], RiskLevel.CRITICAL, "APPROVED", InterventionChannel.HARD_SURGERY)
        ledger_id = gate._conn.execute("SELECT last_insert_rowid()").fetchone()[0]
        with gate._conn:
            gate._conn.execute("INSERT INTO signed_approvals VALUES (?,?,?)", (ledger_id, proof, receipt))
        params["_meta"]["babylon60/authorization"]["mode"] = "execute"
        assert peer.call("tools/call", params)["isError"] is False
        first = cycle.observe(tmp_path / "ledger.db", tmp_path / "gate.db", task, public)
        cycle.check_observation(first, task, executed=True)
        peer.close()
        peer = cycle.Peer(tmp_path, Path(library), env, "software-restarted")
        peer.initialize()
        assert peer.call("tools/call", params)["isError"] is True
        reopened = cycle.observe(tmp_path / "ledger.db", tmp_path / "gate.db", task, public)
        cycle.check_observation(reopened, task, executed=True)
        assert reopened["events"] == first["events"]
    finally:
        peer.close()
        if gate is not None:
            gate._conn.close()
