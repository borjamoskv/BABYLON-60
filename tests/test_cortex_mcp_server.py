# ============================================================================
# BABYLON-60 v4.0 Sovereign Hardened
# █ AUTOCOGNITION-Ω | STATE: C5-REAL | AESTHETIC: INDUSTRIAL_NOIR_2026
# ============================================================================
# [Causal-Determinist] Exergy-Maximized
"""
Test Suite para el Servidor MCP Soberano BFT
=============================================
Authorship: Telmo Dinámico de Moskv (borjamoskv)
"""

import json
from pathlib import Path
from typing import Any, cast
from babylon60.mcp.cortex_mcp_server import CortexMCPServer


def test_mcp_initialize(tmp_path: Path) -> None:
    server = CortexMCPServer(ledger_path=tmp_path / "ledger.db", mail_ledger_path=tmp_path / "mail.db")
    request = {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}}
    response = server.process_request(request)
    assert response is not None
    assert response["jsonrpc"] == "2.0"
    assert response["id"] == 1
    result = cast(dict[str, Any], response["result"])
    assert "protocolVersion" in result
    assert result["serverInfo"]["name"] == "cortex-persist-bft"


def test_mcp_tools_list(tmp_path: Path) -> None:
    server = CortexMCPServer(
        ledger_path=tmp_path / "ledger.db",
        mail_ledger_path=tmp_path / "mail.db",
        causal_gate_path=tmp_path / "causal.db",
    )
    request = {"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}}
    response = server.process_request(request)
    assert response is not None
    result = cast(dict[str, Any], response["result"])
    tools = result["tools"]
    tool_names = [t["name"] for t in tools]
    assert "bft_append_event" in tool_names
    assert "bft_query_ledger" in tool_names
    assert "bft_verify_merkle_root" in tool_names
    assert "bft_send_sovereign_mail" in tool_names
    assert "causal_evaluate_task_risk" in tool_names
    assert "causal_register_sign_off" in tool_names
    assert "causal_verify_ledger" in tool_names


def test_mcp_resources_list(tmp_path: Path) -> None:
    server = CortexMCPServer(
        ledger_path=tmp_path / "ledger.db",
        mail_ledger_path=tmp_path / "mail.db",
        causal_gate_path=tmp_path / "causal.db",
    )
    request = {"jsonrpc": "2.0", "id": 3, "method": "resources/list", "params": {}}
    response = server.process_request(request)
    assert response is not None
    result = cast(dict[str, Any], response["result"])
    resources = result["resources"]
    uris = [r["uri"] for r in resources]
    assert "bft://ledger/status" in uris
    assert "bft://merkle/attestation" in uris
    assert "bft://causal/ledger" in uris


def test_mcp_tool_bft_append_and_query(tmp_path: Path) -> None:
    server = CortexMCPServer(
        ledger_path=tmp_path / "ledger.db",
        mail_ledger_path=tmp_path / "mail.db",
        causal_gate_path=tmp_path / "causal.db",
    )

    # Append
    req_append = {
        "jsonrpc": "2.0",
        "id": 4,
        "method": "tools/call",
        "params": {
            "name": "bft_append_event",
            "arguments": {"event_type": "TEST_EVENT", "payload": {"key": "value"}, "cortex_taint": "test_agent"},
        },
    }
    res_append = server.process_request(req_append)
    assert res_append is not None
    result_append = cast(dict[str, Any], res_append["result"])
    assert not result_append["isError"]
    content = result_append["content"][0]["text"]
    assert "🟢 Event appended to BFT Ledger" in content
    assert "Status:     C5_PERMANENT" in content

    # Query
    req_query = {
        "jsonrpc": "2.0",
        "id": 5,
        "method": "tools/call",
        "params": {"name": "bft_query_ledger", "arguments": {"event_type": "TEST_EVENT", "limit": 1}},
    }
    res_query = server.process_request(req_query)
    assert res_query is not None
    result_query = cast(dict[str, Any], res_query["result"])
    assert not result_query["isError"]
    query_text = result_query["content"][0]["text"]
    query_data = json.loads(query_text)
    assert query_data["total_returned"] == 1
    assert query_data["entries"][0]["event_type"] == "TEST_EVENT"


def test_mcp_causal_tools_and_resources(tmp_path: Path) -> None:
    server = CortexMCPServer(
        ledger_path=tmp_path / "ledger.db",
        mail_ledger_path=tmp_path / "mail.db",
        causal_gate_path=tmp_path / "causal.db",
    )

    # 1. Evaluate risk
    req_eval = {
        "jsonrpc": "2.0",
        "id": 10,
        "method": "tools/call",
        "params": {"name": "causal_evaluate_task_risk", "arguments": {"task_payload": {"action": "deploy_production"}}},
    }
    res_eval = server.process_request(req_eval)
    assert res_eval is not None
    res_eval_res = cast(dict[str, Any], res_eval["result"])
    assert "CRITICAL" in res_eval_res["content"][0]["text"]

    # 2. Register sign-off
    req_sign = {
        "jsonrpc": "2.0",
        "id": 11,
        "method": "tools/call",
        "params": {
            "name": "causal_register_sign_off",
            "arguments": {"execution_id": "EXEC-MCP-001", "action_name": "deploy_production", "decision": "APPROVED"},
        },
    }
    res_sign = server.process_request(req_sign)
    assert res_sign is not None
    res_sign_res = cast(dict[str, Any], res_sign["result"])
    assert "SHA256 Recpt" in res_sign_res["content"][0]["text"]

    # 3. Verify causal ledger tool
    req_verify = {
        "jsonrpc": "2.0",
        "id": 12,
        "method": "tools/call",
        "params": {"name": "causal_verify_ledger", "arguments": {}},
    }
    res_verify = server.process_request(req_verify)
    assert res_verify is not None
    res_verify_res = cast(dict[str, Any], res_verify["result"])
    assert "VERIFIED OK" in res_verify_res["content"][0]["text"]

    # 4. Read causal resource
    req_res = {"jsonrpc": "2.0", "id": 13, "method": "resources/read", "params": {"uri": "bft://causal/ledger"}}
    res_res = server.process_request(req_res)
    assert res_res is not None
    res_res_res = cast(dict[str, Any], res_res["result"])
    data = json.loads(res_res_res["contents"][0]["text"])
    assert data["causal_gate_status"] == "ACTIVE"
    assert data["scitt_integrity_verified"] is True


def test_mcp_resource_read(tmp_path: Path) -> None:
    server = CortexMCPServer(
        ledger_path=tmp_path / "ledger.db",
        mail_ledger_path=tmp_path / "mail.db",
        causal_gate_path=tmp_path / "causal.db",
    )
    request = {"jsonrpc": "2.0", "id": 6, "method": "resources/read", "params": {"uri": "bft://merkle/attestation"}}
    response = server.process_request(request)
    assert response is not None
    result = cast(dict[str, Any], response["result"])
    contents = result["contents"]
    assert len(contents) == 1
    assert contents[0]["uri"] == "bft://merkle/attestation"
    data = json.loads(contents[0]["text"])
    assert "merkle_root" in data
    assert "integrity_verified" in data
