# [C5-REAL] Exergy-Maximized
"""
Test Suite para el Servidor MCP Soberano BFT
=============================================
Authorship: Telmo Dinámico de Moskv (borjamoskv)
"""

import json
from pathlib import Path
from babylon60.mcp.cortex_mcp_server import CortexMCPServer

def test_mcp_initialize(tmp_path: Path):
    server = CortexMCPServer(ledger_path=tmp_path / "ledger.db", mail_ledger_path=tmp_path / "mail.db")
    request = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "initialize",
        "params": {}
    }
    response = server.process_request(request)
    assert response is not None
    assert response["jsonrpc"] == "2.0"
    assert response["id"] == 1
    assert "protocolVersion" in response["result"]
    assert response["result"]["serverInfo"]["name"] == "cortex-persist-bft"

def test_mcp_tools_list(tmp_path: Path):
    server = CortexMCPServer(ledger_path=tmp_path / "ledger.db", mail_ledger_path=tmp_path / "mail.db")
    request = {
        "jsonrpc": "2.0",
        "id": 2,
        "method": "tools/list",
        "params": {}
    }
    response = server.process_request(request)
    assert response is not None
    tools = response["result"]["tools"]
    tool_names = [t["name"] for t in tools]
    assert "bft_append_event" in tool_names
    assert "bft_query_ledger" in tool_names
    assert "bft_verify_merkle_root" in tool_names
    assert "bft_send_sovereign_mail" in tool_names

def test_mcp_resources_list(tmp_path: Path):
    server = CortexMCPServer(ledger_path=tmp_path / "ledger.db", mail_ledger_path=tmp_path / "mail.db")
    request = {
        "jsonrpc": "2.0",
        "id": 3,
        "method": "resources/list",
        "params": {}
    }
    response = server.process_request(request)
    assert response is not None
    resources = response["result"]["resources"]
    uris = [r["uri"] for r in resources]
    assert "bft://ledger/status" in uris
    assert "bft://merkle/attestation" in uris

def test_mcp_tool_bft_append_and_query(tmp_path: Path):
    server = CortexMCPServer(ledger_path=tmp_path / "ledger.db", mail_ledger_path=tmp_path / "mail.db")
    
    # Append
    req_append = {
        "jsonrpc": "2.0",
        "id": 4,
        "method": "tools/call",
        "params": {
            "name": "bft_append_event",
            "arguments": {
                "event_type": "TEST_EVENT",
                "payload": {"key": "value"},
                "cortex_taint": "test_agent"
            }
        }
    }
    res_append = server.process_request(req_append)
    assert res_append is not None
    assert not res_append["result"]["isError"]
    content = res_append["result"]["content"][0]["text"]
    assert "🟢 Event appended to BFT Ledger" in content
    assert "Status:     C5_PERMANENT" in content
    
    # Query
    req_query = {
        "jsonrpc": "2.0",
        "id": 5,
        "method": "tools/call",
        "params": {
            "name": "bft_query_ledger",
            "arguments": {
                "event_type": "TEST_EVENT",
                "limit": 1
            }
        }
    }
    res_query = server.process_request(req_query)
    assert res_query is not None
    assert not res_query["result"]["isError"]
    query_text = res_query["result"]["content"][0]["text"]
    query_data = json.loads(query_text)
    assert query_data["total_returned"] == 1
    assert query_data["entries"][0]["event_type"] == "TEST_EVENT"

def test_mcp_resource_read(tmp_path: Path):
    server = CortexMCPServer(ledger_path=tmp_path / "ledger.db", mail_ledger_path=tmp_path / "mail.db")
    request = {
        "jsonrpc": "2.0",
        "id": 6,
        "method": "resources/read",
        "params": {
            "uri": "bft://merkle/attestation"
        }
    }
    response = server.process_request(request)
    assert response is not None
    contents = response["result"]["contents"]
    assert len(contents) == 1
    assert contents[0]["uri"] == "bft://merkle/attestation"
    data = json.loads(contents[0]["text"])
    assert "merkle_root" in data
    assert "integrity_verified" in data
