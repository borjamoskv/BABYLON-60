"""The base MCP server works without mail; explicit opt-in records locally."""

from __future__ import annotations

import gc
import json
import os
from pathlib import Path
import subprocess
import sys
from collections.abc import Iterator, Mapping

import pytest

from babylon60.mcp import cortex_mcp_server
from babylon60.mcp.cortex_mcp_server import CortexMCPServer


def _subprocess_env(tmp_path: Path) -> dict[str, str]:
    env = os.environ.copy()
    env["BABYLON_HOME"] = str(tmp_path / "fresh-home")
    package_root = str(Path(cortex_mcp_server.__file__).resolve().parents[2])
    env["PYTHONPATH"] = os.pathsep.join([package_root, *sys.path])
    return env


@pytest.fixture(autouse=True)
def remove_sqlite_triplets(tmp_path: Path) -> Iterator[None]:
    yield
    gc.collect()
    for pattern in ("*.db", "*.db-wal", "*.db-shm"):
        for path in tmp_path.rglob(pattern):
            path.unlink(missing_ok=True)


def _tool_names(server: CortexMCPServer) -> set[str]:
    response = server.process_request({"id": 1, "method": "tools/list"})
    assert response is not None
    result = response["result"]
    assert isinstance(result, dict)
    return {tool["name"] for tool in result["tools"]}


def test_base_server_has_no_mail_side_effects(tmp_path: Path) -> None:
    server = CortexMCPServer(ledger_path=tmp_path / "ledger.db", causal_gate_path=tmp_path / "causal.db")
    try:
        assert server.mail_ledger is None
        assert "bft_send_sovereign_mail" not in _tool_names(server)
        response = server.process_request(
            {"id": 2, "method": "tools/call", "params": {"name": "bft_send_sovereign_mail", "arguments": {}}}
        )
        assert response is not None
        result = response["result"]
        assert isinstance(result, dict)
        assert result["isError"] is True
        assert server.ledger.get_state_attestation()["total_entries"] == 0
        assert {path.name for path in tmp_path.glob("*.db")} == {"ledger.db", "causal.db"}
    finally:
        server.verification_gate._conn.close()


MAIL_ARGUMENTS: dict[str, object] = {"to": "recipient@example.invalid", "subject": "Local test", "body": "Record only"}


def _mail_call(authorization: Mapping[str, object] | None = None) -> dict[str, object]:
    params: dict[str, object] = {"name": "bft_send_sovereign_mail", "arguments": dict(MAIL_ARGUMENTS)}
    if authorization is not None:
        params["_meta"] = {"babylon60/authorization": authorization}
    return {"id": 2, "method": "tools/call", "params": params}


def _call_result(server: CortexMCPServer, request: dict[str, object]) -> dict[str, object]:
    response = server.process_request(request)
    assert response is not None
    result = response["result"]
    assert isinstance(result, dict)
    return result


def _content_text(result: Mapping[str, object]) -> str:
    content = result["content"]
    assert isinstance(content, list)
    first = content[0]
    assert isinstance(first, dict)
    text = first["text"]
    assert isinstance(text, str)
    return text


def _mail_rows(server: CortexMCPServer) -> list[tuple[str, str, str]]:
    assert server.mail_ledger is not None
    rows: list[tuple[str, str, str]] = []
    with server.mail_ledger._get_connection() as connection:
        for event_type, payload_json, taint in connection.execute(
            "SELECT event_type, payload_json, cortex_taint FROM cortex_ledger"
        ).fetchall():
            assert isinstance(event_type, str)
            assert isinstance(payload_json, str)
            assert isinstance(taint, str)
            rows.append((event_type, payload_json, taint))
    return rows


def test_opt_in_exposes_mediated_mail_tool_and_unapproved_call_records_nothing(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Since FL-MCP-01 (1fb053dc) mail is a mediated LedgerAppend effect: fail-closed without approval."""
    monkeypatch.setenv("USER", "test operator/unsafe")
    mail_path = tmp_path / "mail.db"
    server = CortexMCPServer(
        ledger_path=tmp_path / "ledger.db", mail_ledger_path=mail_path, causal_gate_path=tmp_path / "causal.db"
    )
    base = CortexMCPServer(ledger_path=tmp_path / "base.db", causal_gate_path=tmp_path / "base-causal.db")
    try:
        assert _tool_names(server) == _tool_names(base) | {"bft_send_sovereign_mail"}
        listed = server.process_request({"id": 1, "method": "tools/list"})
        assert listed is not None
        listed_result = listed["result"]
        assert isinstance(listed_result, dict)
        (mail_tool,) = [tool for tool in listed_result["tools"] if tool["name"] == "bft_send_sovereign_mail"]
        assert mail_tool["_meta"]["babylon60/authorization"]["required"] is True
        assert server.mail_ledger is not None
        assert mail_path.exists()
        # Missing authorization and an unsigned execute are both denied before any effect.
        for authorization in (None, {"execution_id": "unsigned-mail"}):
            result = _call_result(server, _mail_call(authorization))
            assert result["isError"] is True
            assert _content_text(result).startswith("FL-MCP-01 DENIED:")
        assert _mail_rows(server) == []
        assert server.mail_ledger.verify_integrity()
        assert server.ledger.get_state_attestation()["total_entries"] == 0
        assert base.ledger.get_state_attestation()["total_entries"] == 0
    finally:
        server.verification_gate._conn.close()
        base.verification_gate._conn.close()


def _sign_task(server: CortexMCPServer, task: dict[str, object], key: object) -> None:
    """Persist an isolated software P-256 approval; never presented as a hardware/biometric result."""
    import base64
    import hashlib
    import secrets
    import time

    from cryptography.hazmat.primitives import hashes, serialization
    from cryptography.hazmat.primitives.asymmetric import ec

    from babylon60.verification.verification_gate import RiskLevel

    assert isinstance(key, ec.EllipticCurvePrivateKey)
    now = time.time()
    proof = json.dumps(
        {
            "version": 1,
            "task": task,
            "decision": "APPROVED",
            "nonce": secrets.token_hex(32),
            "issued_at": now - 1,
            "expires_at": now + 120,
        },
        sort_keys=True,
        separators=(",", ":"),
    )
    payload = proof.encode()
    public = key.public_key().public_bytes(serialization.Encoding.X962, serialization.PublicFormat.UncompressedPoint)
    evidence = json.dumps(
        {
            "status": "ATTESTED",
            "causal_hash": hashlib.sha256(payload).hexdigest(),
            "public_key": base64.b64encode(public).decode(),
            "secure_enclave_signature": base64.b64encode(key.sign(payload, ec.ECDSA(hashes.SHA256()))).decode(),
        }
    )
    gate = server.verification_gate
    gate.register_sign_off(str(task["execution_id"]), str(task["action"]), RiskLevel.CRITICAL, "APPROVED")
    ledger_id = gate._conn.execute("SELECT last_insert_rowid()").fetchone()[0]
    with gate._conn:
        gate._conn.execute("INSERT INTO signed_approvals VALUES (?, ?, ?)", (ledger_id, proof, evidence))


def test_signed_opt_in_records_existing_mail_schema_without_changing_base(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    library_value = os.environ.get("BABYLON60_TEST_CAPABILITY_LIBRARY")
    if library_value is None:
        pytest.skip("build kernel with --features python and set BABYLON60_TEST_CAPABILITY_LIBRARY")
    library = Path(library_value).absolute()
    assert library.is_file(), library
    from cryptography.hazmat.primitives import serialization
    from cryptography.hazmat.primitives.asymmetric import ec

    key = ec.generate_private_key(ec.SECP256R1())
    public = key.public_key().public_bytes(serialization.Encoding.X962, serialization.PublicFormat.UncompressedPoint)
    monkeypatch.setenv("BABYLON_ENCLAVE_PINNED_PUBKEY", public.hex())
    monkeypatch.setenv("USER", "test operator/unsafe")
    server = CortexMCPServer(
        ledger_path=tmp_path / "ledger.db",
        mail_ledger_path=tmp_path / "mail.db",
        causal_gate_path=tmp_path / "causal.db",
        capability_library=library,
    )
    try:
        prepared = _call_result(server, _mail_call({"execution_id": "signed-mail", "mode": "prepare"}))
        assert prepared["isError"] is False, prepared
        assert _mail_rows(server) == []  # Prepare is observation only.
        task = prepared["approval_task"]
        assert isinstance(task, dict)
        _sign_task(server, task, key)
        result = _call_result(server, _mail_call({"execution_id": "signed-mail"}))
        assert result["isError"] is False, result
        assert "local ledger only" in _content_text(result)
        assert _call_result(server, _mail_call({"execution_id": "signed-mail"}))["isError"] is True  # No replay.
        assert server.mail_ledger is not None
        assert server.mail_ledger.verify_integrity()
        assert server.ledger.get_state_attestation()["total_entries"] == 0
        rows = _mail_rows(server)
        assert len(rows) == 1
        event_type, payload_json, taint = rows[0]
        assert event_type == "BABYLON_MAIL_SENT"  # Compatibility event; no network delivery.
        payload = json.loads(payload_json)
        assert payload["from"] == "testoperatorunsafe@babylon60.com"
        assert payload["to"] == "recipient@example.invalid"
        assert payload["subject"] == "Local test"
        assert payload["body"] == "Record only"
        assert taint == "testoperatorunsafe:mcp_server:send_mail"
    finally:
        server.verification_gate._conn.close()


def test_base_import_and_start_do_not_load_optional_mail_dependencies(tmp_path: Path) -> None:
    code = """
import importlib.abc
from pathlib import Path
import sys

class DenyOptionalImports(importlib.abc.MetaPathFinder):
    def find_spec(self, fullname, path, target=None):
        if fullname in {"babylon60.mcp.mail_integration", "fastapi", "uvicorn"}:
            raise ImportError("Optional dependency must not be imported: " + fullname)
        return None

sys.meta_path.insert(0, DenyOptionalImports())
from babylon60.mcp.cortex_mcp_server import CortexMCPServer
root = Path(sys.argv[1])
server = CortexMCPServer(ledger_path=root / "ledger.db", causal_gate_path=root / "causal.db")
assert server.mail_ledger is None
assert server.process_request({"id": 1, "method": "initialize"})["result"]["serverInfo"]["name"] == "cortex-persist-bft"
assert "babylon60.mcp.mail_integration" not in sys.modules
server.verification_gate._conn.close()
"""
    subprocess.run(
        [sys.executable, "-c", code, str(tmp_path)],
        check=True,
        capture_output=True,
        text=True,
        timeout=20,
        env=_subprocess_env(tmp_path),
    )


@pytest.mark.parametrize("enable_mail", [False, True])
def test_stdio_mail_is_explicit_opt_in(tmp_path: Path, enable_mail: bool) -> None:
    command = [sys.executable, "-m", "babylon60.mcp.cortex_mcp_server", "--ledger", str(tmp_path / "ledger.db")]
    mail_path = tmp_path / "mail.db"
    if enable_mail:
        command.extend(["--mail-ledger", str(mail_path)])
    response = subprocess.run(
        command,
        input=json.dumps({"id": 1, "method": "tools/list"}) + "\n",
        capture_output=True,
        text=True,
        timeout=20,
        check=True,
        env=_subprocess_env(tmp_path),
    )
    tool_names = {tool["name"] for tool in json.loads(response.stdout)["result"]["tools"]}
    assert ("bft_send_sovereign_mail" in tool_names) is enable_mail
    assert mail_path.exists() is enable_mail
    assert (tmp_path / "fresh-home" / "causal_gate.db").exists()
    assert not (tmp_path / "fresh-home" / "data" / "mail_ledger.db").exists()
