"""Software authority fixtures verify shared state, never hardware attestation."""

from __future__ import annotations

import argparse
import base64
import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec

from babylon60 import state_paths
from babylon60.cli import main_dispatcher as cli
from babylon60.mcp.cortex_mcp_server import CortexMCPServer
from babylon60.onboarding import _transport
from babylon60.verification import verification_gate
from babylon60.verification.verification_gate import VerificationGate


@pytest.fixture(autouse=True)
def isolated_state(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("BABYLON_HOME", str(tmp_path / "state"))
    monkeypatch.delenv("BABYLON_CAUSAL_GATE_DB", raising=False)
    monkeypatch.setattr(state_paths, "legacy_causal_gate_path", lambda: tmp_path / "legacy" / "gate.db")


def test_default_home_and_override_precedence(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    assert state_paths.causal_gate_path() == tmp_path / "state" / "causal_gate.db"
    monkeypatch.delenv("BABYLON_HOME")
    monkeypatch.setattr(Path, "home", lambda: tmp_path / "user")
    assert state_paths.causal_gate_path() == tmp_path / "user" / ".babylon60" / "causal_gate.db"
    monkeypatch.setenv("BABYLON_CAUSAL_GATE_DB", str(tmp_path / "chosen.db"))
    assert state_paths.causal_gate_path() == tmp_path / "chosen.db"
    assert state_paths.causal_gate_path(tmp_path / "argument.db") == tmp_path / "argument.db"
    assert state_paths.causal_gate_path(":memory:") == Path(":memory:")


@pytest.mark.parametrize("suffix", ["", "-wal", "-shm"])
def test_legacy_state_requires_explicit_selection_even_with_new_gate(
    tmp_path: Path, suffix: str
) -> None:
    canonical = tmp_path / "state" / "causal_gate.db"
    canonical.parent.mkdir()
    canonical.write_bytes(b"new-state-must-not-change")
    legacy = state_paths.legacy_causal_gate_path()
    legacy.parent.mkdir()
    legacy_file = Path(f"{legacy}{suffix}")
    legacy_file.write_bytes(b"legacy-must-not-change")
    with pytest.raises(ValueError, match="BABYLON_CAUSAL_GATE_DB"):
        state_paths.causal_gate_path()
    assert state_paths.causal_gate_path(legacy) == legacy
    assert state_paths.causal_gate_path(canonical) == canonical
    assert canonical.read_bytes() == b"new-state-must-not-change"
    assert legacy_file.read_bytes() == b"legacy-must-not-change"


def test_transport_preserves_explicit_gate(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    chosen = tmp_path / "authority" / "chosen.db"
    monkeypatch.setenv("BABYLON_CAUSAL_GATE_DB", str(chosen))
    environment = _transport(state_paths.state_home())["env"]
    assert isinstance(environment, dict)
    assert environment["BABYLON_CAUSAL_GATE_DB"] == str(chosen)


@pytest.mark.parametrize("variable", ["BABYLON_HOME", "BABYLON_CAUSAL_GATE_DB"])
@pytest.mark.parametrize("module", ["babylon60.cli.main_dispatcher", "babylon60.mcp.cortex_mcp_server"])
def test_help_does_not_validate_unrelated_state_environment(variable: str, module: str) -> None:
    environment = dict(os.environ, **{variable: ""})
    result = subprocess.run(
        [sys.executable, "-m", module, "--help"], env=environment, capture_output=True, text=True, timeout=10
    )
    assert result.returncode == 0, result.stderr
    assert "usage:" in result.stdout
    assert "Traceback" not in result.stderr


def test_explicit_cli_db_precedes_invalid_db_environment(tmp_path: Path) -> None:
    path = tmp_path / "explicit.db"
    gate = VerificationGate(str(path))
    gate._conn.close()
    environment = dict(os.environ, BABYLON_CAUSAL_GATE_DB="")
    result = subprocess.run(
        [sys.executable, "-m", "babylon60.cli.main_dispatcher", "status", "--db", str(path)],
        env=environment, capture_output=True, text=True, timeout=10,
    )
    assert result.returncode == 1
    assert str(path) in result.stdout
    assert "no recorded authorization evidence" in result.stdout
    assert "Traceback" not in result.stderr


def test_explicit_mcp_paths_precede_invalid_environment(tmp_path: Path) -> None:
    code = (
        "import sys; from babylon60.mcp.cortex_mcp_server import CortexMCPServer; "
        "server=CortexMCPServer(ledger_path=sys.argv[1],causal_gate_path=sys.argv[2]); "
        "print(server.verification_gate.db_path); server.verification_gate._conn.close()"
    )
    path = tmp_path / "explicit.db"
    result = subprocess.run(
        [sys.executable, "-c", code, str(tmp_path / "memory.db"), str(path)],
        env=dict(os.environ, BABYLON_HOME="", BABYLON_CAUSAL_GATE_DB=""),
        capture_output=True, text=True, timeout=10,
    )
    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == str(path)


def test_status_fresh_does_not_create_or_certify_a_ledger(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    assert cli.cmd_status(argparse.Namespace(db=None)) == 1
    output = capsys.readouterr()
    assert "NO_VERIFICADO" in output.out
    assert "Chain Verified" not in output.out
    assert output.err == ""
    assert not (tmp_path / "state").exists()


def test_status_empty_gate_is_not_authorization_evidence(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    path = state_paths.causal_gate_path()
    path.parent.mkdir()
    gate = VerificationGate(str(path))
    gate._conn.close()
    assert cli.cmd_status(argparse.Namespace(db=None)) == 1
    output = capsys.readouterr()
    assert "no recorded authorization evidence" in output.out
    assert "Chain Verified" not in output.out


def test_cli_default_approval_and_revocation_reach_same_mcp_gate(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    key = ec.generate_private_key(ec.SECP256R1())
    public = key.public_key().public_bytes(serialization.Encoding.X962, serialization.PublicFormat.UncompressedPoint)
    monkeypatch.setenv("BABYLON_ENCLAVE_PINNED_PUBKEY", public.hex())

    def attest(payload: bytes, gate: Path, action: str, scope: str, trusted_key: bytes) -> str:
        assert trusted_key == public
        return json.dumps({
            "status": "ATTESTED",
            "causal_hash": hashlib.sha256(payload).hexdigest(),
            "public_key": base64.b64encode(public).decode(),
            "secure_enclave_signature": base64.b64encode(key.sign(payload, ec.ECDSA(hashes.SHA256()))).decode(),
        })

    monkeypatch.setattr(verification_gate, "request_attestation", attest)
    task = {"execution_id": "shared-gate", "action": "deploy", "parameters": {"target": "fixture"}}
    task_file = tmp_path / "task.json"
    task_file.write_text(json.dumps(task))
    args = argparse.Namespace(
        db=None, execution_id=task["execution_id"], action=task["action"], decision="APPROVED", task_file=task_file
    )
    server = CortexMCPServer(ledger_path=tmp_path / "memory.db")
    try:
        assert Path(server.verification_gate.db_path) == state_paths.causal_gate_path()
        assert not server.verification_gate.is_allowed(task)
        assert cli.cmd_approve(args) == 0
        assert server.verification_gate.is_allowed(task)
        assert not server.verification_gate.is_allowed(task | {"parameters": {"target": "changed"}})
        args.decision = "REJECTED"
        assert cli.cmd_approve(args) == 0
        assert not server.verification_gate.is_allowed(task)
        assert server.verification_gate.verify_ledger_integrity()
    finally:
        server.verification_gate._conn.close()


def test_cli_explicit_db_can_revoke_when_legacy_and_default_coexist(tmp_path: Path) -> None:
    legacy = state_paths.legacy_causal_gate_path()
    legacy.parent.mkdir()
    gate = VerificationGate(str(legacy))
    gate._conn.close()
    canonical = tmp_path / "state" / "causal_gate.db"
    canonical.parent.mkdir()
    canonical.write_bytes(b"untouched-canonical")
    args = argparse.Namespace(db=str(legacy), execution_id="revoke", action="deploy", decision="REJECTED")
    assert cli.cmd_approve(args) == 0
    check = VerificationGate(str(legacy))
    try:
        assert check._conn.execute("SELECT decision FROM audit_ledger").fetchall() == [("REJECTED",)]
        assert check.verify_ledger_integrity()
        assert canonical.read_bytes() == b"untouched-canonical"
    finally:
        check._conn.close()
