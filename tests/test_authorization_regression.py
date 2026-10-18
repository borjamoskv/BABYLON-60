"""Regression tests; software fixtures never attest physical hardware."""

import argparse
import base64
import hashlib
import io
import json
import subprocess
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import pytest

from babylon60.verification.verification_gate import VerificationGate, RiskLevel
from babylon60.cli.main_dispatcher import cmd_approve
from scripts import babylon_launcher as launcher
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec
from babylon60.verification import hardware_attestation as hardware


@pytest.fixture
def authority(monkeypatch):
    key = ec.generate_private_key(ec.SECP256R1())
    public = key.public_key().public_bytes(serialization.Encoding.X962, serialization.PublicFormat.UncompressedPoint)
    monkeypatch.setenv("BABYLON_ENCLAVE_PINNED_PUBKEY", public.hex())
    return key


def software_helper(key, cmd, **kwargs):
    payload = bytes.fromhex(cmd[cmd.index("--sign-hex") + 1])
    prehash = cmd[cmd.index("--causal-hash") + 1]
    assert prehash == hashlib.sha256(payload).hexdigest()
    public = key.public_key().public_bytes(serialization.Encoding.X962, serialization.PublicFormat.UncompressedPoint)
    data = {
        "status": "ATTESTED",
        "causal_hash": prehash,
        "public_key": base64.b64encode(public).decode(),
        "secure_enclave_signature": base64.b64encode(key.sign(payload, ec.ECDSA(hashes.SHA256()))).decode(),
    }
    return subprocess.CompletedProcess(cmd, 0, json.dumps(data, indent=2), "")


def test_unverified_ledger_row_never_authorizes():
    gate = VerificationGate()
    gate.register_sign_off("e1", "deploy", RiskLevel.CRITICAL, "APPROVED")
    assert not gate.is_allowed({"execution_id": "e1", "action": "deploy"})
    assert not gate.is_allowed({"execution_id": "e1", "action": "delete"})
    assert not gate.check_authorized_bifurcation()


def test_cli_cannot_bypass_hardware(tmp_path):
    task = {"execution_id": "e1", "action": "deploy", "command": "deploy staging"}
    task_file = tmp_path / "task.json"
    task_file.write_text(json.dumps(task))
    gate = VerificationGate()
    args = argparse.Namespace(
        execution_id="e1",
        action="deploy",
        decision="APPROVED",
        risk="CRITICAL",
        db=":memory:",
        task_file=str(task_file),
    )
    with (
        patch("babylon60.verification.verification_gate.VerificationGate", return_value=gate),
        patch.object(gate, "enforce_biometric_sign_off", return_value=False) as biometric,
    ):
        assert cmd_approve(args) != 0
        biometric.assert_called_once()
    assert not gate.is_allowed(task)


class MemorySocket:
    def __init__(self, raw):
        self.input = io.BytesIO(raw)
        self.output = bytearray()

    def makefile(self, *args, **kwargs):
        return self.input

    def sendall(self, data):
        self.output.extend(data)


def gateway_request(payload):
    import socket
    import socketserver
    from typing import cast

    body = json.dumps(payload).encode()
    raw = (
        f"POST /api/touchid/trigger HTTP/1.0\r\nHost: localhost\r\nContent-Length: {len(body)}\r\n\r\n"
    ).encode() + body
    sock = MemorySocket(raw)
    with patch.object(launcher.BabylonHTTPHandler, "log_message"):
        launcher.BabylonHTTPHandler(
            cast(socket.socket, sock),
            ("127.0.0.1", 12345),
            cast(socketserver.BaseServer, SimpleNamespace()),
        )
    header, data = bytes(sock.output).split(b"\r\n\r\n", 1)
    return int(header.split()[1]), json.loads(data)


@pytest.mark.parametrize(
    "stdout",
    [
        "",
        "NOT JSON",
        "{}",
        '{"success":false}',
        '{"status":"ATTESTED","causal_hash":"wrong","secure_enclave_signature":"bogus"}',
    ],
)
def test_gateway_exit_zero_is_not_attestation(stdout, authority):
    with (
        patch.object(launcher, "get_biometric_gate_path", return_value=Path("/test/helper")),
        patch.object(launcher.subprocess, "run", return_value=subprocess.CompletedProcess([], 0, stdout, "")),
    ):
        status, result = gateway_request({"mock": False})
    assert status == 400
    assert result["success"] is False
    assert result["verified_in_hardware"] is False


def test_verified_cli_exact_task_persistence_and_revocation(authority, tmp_path):
    task: dict[str, object] = {
        "execution_id": "e1",
        "action": "deploy",
        "command": "deploy staging",
        "parameters": {"target": "staging", "count": 1},
    }
    task_file = tmp_path / "task.json"
    task_file.write_text(json.dumps(task))
    db = str(tmp_path / "gate.db")
    args = argparse.Namespace(
        execution_id="e1", action="deploy", decision="APPROVED", risk="LOW", db=db, task_file=str(task_file)
    )
    with patch.object(hardware.subprocess, "run", side_effect=lambda cmd, **kw: software_helper(authority, cmd, **kw)):
        assert cmd_approve(args) == 0
    gate = VerificationGate(db)
    assert gate.is_allowed(task)
    assert gate.check_authorized_bifurcation(task_payload=task)
    for alteration in (
        {"action": "delete"},
        {"command": "deploy production"},
        {"execution_id": "e2"},
        {"parameters": {"target": "prod", "count": 1}},
    ):
        assert not gate.is_allowed(task | alteration)
    assert not gate.check_authorized_bifurcation()
    args.decision = "REJECTED"
    assert cmd_approve(args) == 0
    assert not gate.is_allowed(task)
    gate._conn.close()


def test_expiry_tampering_wrong_key_and_restart(authority, tmp_path, monkeypatch):
    task = {"execution_id": "e", "action": "deploy", "command": "deploy a"}
    db = str(tmp_path / "gate.db")
    gate = VerificationGate(db)
    with (
        patch.object(hardware.subprocess, "run", side_effect=lambda cmd, **kw: software_helper(authority, cmd, **kw)),
        patch("babylon60.verification.verification_gate.time.time", return_value=1000),
    ):
        assert gate.enforce_biometric_sign_off("e", "deploy", "test", task_payload=task)
    gate._conn.close()
    gate = VerificationGate(db)
    with patch("babylon60.verification.verification_gate.time.time", return_value=1299):
        assert gate.is_allowed(task)
    for now in [999, 1300, 1301]:
        with patch("babylon60.verification.verification_gate.time.time", return_value=now):
            assert not gate.is_allowed(task)
    proof = gate._conn.execute("SELECT payload FROM signed_approvals").fetchone()[0]
    gate._conn.execute("UPDATE signed_approvals SET payload=?", (proof.replace("deploy a", "deploy b"),))
    gate._conn.commit()
    with patch("babylon60.verification.verification_gate.time.time", return_value=1001):
        assert not gate.is_allowed(task | {"command": "deploy b"})
    gate._conn.close()
    monkeypatch.delenv("BABYLON_ENCLAVE_PINNED_PUBKEY")
    gate = VerificationGate(db)
    assert not gate.is_allowed(task)
    with patch.object(hardware.subprocess, "run") as helper:
        assert not gate.enforce_biometric_sign_off("e", "deploy", "test", task_payload=task)
        helper.assert_not_called()
    gate._conn.close()


def test_gateway_valid_multiline_signature_and_fresh_challenges(authority):
    challenges = []

    def helper(cmd, **kwargs):
        challenges.append(cmd[cmd.index("--sign-hex") + 1])
        return software_helper(authority, cmd, **kwargs)

    with (
        patch.object(launcher, "get_biometric_gate_path", return_value=Path("/test/helper.swift")),
        patch.object(hardware.subprocess, "run", side_effect=helper),
    ):
        for _ in range(2):
            status, result = gateway_request({"mock": False})
            assert status == 200 and result["success"]
            assert result["status"] == "ATTESTED"
    assert challenges[0] != challenges[1]


@pytest.mark.parametrize(
    "fault", ["wrong_key", "wrong_hash", "bad_signature", "contradiction", "rejected", "nonzero", "timeout"]
)
def test_signed_gateway_failures(authority, fault):
    def helper(cmd, **kwargs):
        if fault == "nonzero":
            raise subprocess.CalledProcessError(1, cmd)
        if fault == "timeout":
            raise subprocess.TimeoutExpired(cmd, 25)
        signer = ec.generate_private_key(ec.SECP256R1()) if fault == "wrong_key" else authority
        result = software_helper(signer, cmd, **kwargs)
        data = json.loads(result.stdout)
        if fault == "wrong_hash":
            data["causal_hash"] = "0" * 64
        if fault == "bad_signature":
            data["secure_enclave_signature"] = base64.b64encode(b"invalid").decode()
        if fault == "contradiction":
            data["success"] = False
        if fault == "rejected":
            data["status"] = "REJECTED"
        result.stdout = json.dumps(data)
        return result

    with (
        patch.object(launcher, "get_biometric_gate_path", return_value=Path("/test/helper")),
        patch.object(hardware.subprocess, "run", side_effect=helper) as run,
    ):
        status, result = gateway_request({"mock": False})
    assert status == 400 and not result["verified_in_hardware"]
    run.assert_called_once()


def test_signature_stress_after_warmup(authority):
    task = {"execution_id": "stress", "action": "deploy"}
    gate = VerificationGate()
    with patch.object(hardware.subprocess, "run", side_effect=lambda cmd, **kw: software_helper(authority, cmd, **kw)):
        assert gate.enforce_biometric_sign_off("stress", "deploy", "test", task_payload=task)
    for _ in range(32):
        assert gate.is_allowed(task)
    for _ in range(256):
        assert gate.is_allowed(task)
        assert not gate.is_allowed(task | {"command": "unapproved"})
    gate._conn.close()
