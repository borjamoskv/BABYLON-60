"""The base MCP server works without mail; explicit opt-in records locally."""

from __future__ import annotations

import gc
import json
import os
from pathlib import Path
import subprocess
import sys
from collections.abc import Iterator

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


def test_opt_in_records_existing_mail_schema_without_changing_base(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("USER", "test operator/unsafe")
    mail_path = tmp_path / "mail.db"
    server = CortexMCPServer(
        ledger_path=tmp_path / "ledger.db", mail_ledger_path=mail_path, causal_gate_path=tmp_path / "causal.db"
    )
    base = CortexMCPServer(ledger_path=tmp_path / "base.db", causal_gate_path=tmp_path / "base-causal.db")
    try:
        assert _tool_names(server) == _tool_names(base) | {"bft_send_sovereign_mail"}
        response = server.process_request(
            {
                "id": 2,
                "method": "tools/call",
                "params": {
                    "name": "bft_send_sovereign_mail",
                    "arguments": {"to": "recipient@example.invalid", "subject": "Local test", "body": "Record only"},
                },
            }
        )
        assert response is not None
        result = response["result"]
        assert isinstance(result, dict)
        assert result["isError"] is False
        assert "local ledger only" in result["content"][0]["text"]
        assert server.mail_ledger is not None
        assert server.mail_ledger.verify_integrity()
        assert server.ledger.get_state_attestation()["total_entries"] == 0
        with server.mail_ledger._get_connection() as connection:
            row = connection.execute("SELECT event_type, payload_json, cortex_taint FROM cortex_ledger").fetchone()
        assert row[0] == "BABYLON_MAIL_SENT"  # Compatibility event; no network delivery.
        payload = json.loads(row[1])
        assert payload["from"] == "testoperatorunsafe@babylon60.com"
        assert payload["to"] == "recipient@example.invalid"
        assert payload["subject"] == "Local test"
        assert payload["body"] == "Record only"
        assert row[2] == "testoperatorunsafe:mcp_server:send_mail"
    finally:
        server.verification_gate._conn.close()
        base.verification_gate._conn.close()


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
