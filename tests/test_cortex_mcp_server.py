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
    server = CortexMCPServer(
        ledger_path=tmp_path / "ledger.db",
        mail_ledger_path=tmp_path / "mail.db",
        causal_gate_path=tmp_path / "causal.db",
    )
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
    # AX-0 Invariant: Stochastic MCP client cannot be offered self-authorization tools
    assert "causal_register_sign_off" not in tool_names
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
    assert "bft://skills/catalog" in uris


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

    # 2. Attempt self sign-off via MCP -> MUST FAIL CLOSED (AX-0)
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
    assert res_sign_res.get("isError") is True
    assert "AX-0" in res_sign_res["content"][0]["text"]

    # 3. Legitimate operator sign-off occurs OUT-OF-BAND (not via stochastic MCP client)
    from babylon60.verification.verification_gate import RiskLevel

    server.verification_gate.register_sign_off(
        execution_id="EXEC-MCP-001",
        action_name="deploy_production",
        risk_level=RiskLevel.CRITICAL,
        decision="APPROVED",
    )

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


def test_mcp_canonical_tool_and_resource_aliases(tmp_path: Path) -> None:
    server = CortexMCPServer(
        ledger_path=tmp_path / "ledger.db",
        mail_ledger_path=tmp_path / "mail.db",
        causal_gate_path=tmp_path / "causal.db",
    )
    req_append = {
        "jsonrpc": "2.0",
        "id": 20,
        "method": "tools/call",
        "params": {
            "name": "cortex_event_append",
            "arguments": {"event_type": "ALIAS_EVENT", "payload": {"ok": True}, "cortex_taint": "alias_test"},
        },
    }
    res_append = server.process_request(req_append)
    assert res_append is not None
    assert not cast(dict[str, Any], res_append["result"]).get("isError")

    req_query = {
        "jsonrpc": "2.0",
        "id": 21,
        "method": "tools/call",
        "params": {"name": "cortex_ledger_query", "arguments": {"event_type": "ALIAS_EVENT", "limit": 1}},
    }
    res_query = server.process_request(req_query)
    assert res_query is not None
    query_data = json.loads(cast(dict[str, Any], res_query["result"])["content"][0]["text"])
    assert query_data["total_returned"] == 1

    req_res = {"jsonrpc": "2.0", "id": 22, "method": "resources/read", "params": {"uri": "cortex://ledger/status"}}
    res_res = server.process_request(req_res)
    assert res_res is not None
    contents = cast(dict[str, Any], res_res["result"])["contents"]
    assert contents[0]["uri"] == "cortex://ledger/status"


def test_mcp_detonate_ephemeral_bomb(tmp_path: Path) -> None:
    server = CortexMCPServer(
        ledger_path=tmp_path / "ledger.db",
        mail_ledger_path=tmp_path / "mail.db",
        causal_gate_path=tmp_path / "causal.db",
    )

    # 1. Valid ephemeral MCP bomb via canonical alias
    req_bomb = {
        "jsonrpc": "2.0",
        "id": 30,
        "method": "tools/call",
        "params": {
            "name": "cortex_mcp_bomb_detonate",
            "arguments": {
                "domain_name": "TokenEntropy",
                "implementation_body": "return {'shannon_proxy': len(set(text)) / max(len(text), 1)}",
                "call_arguments": {"text": "aaaaabbbbb"},
                "cortex_taint": "agent_ephemeral_synthesis",
            },
        },
    }
    res_bomb = server.process_request(req_bomb)
    assert res_bomb is not None
    result_obj = cast(dict[str, Any], res_bomb["result"])
    assert result_obj.get("isError") is False
    receipt = json.loads(result_obj["content"][0]["text"])
    assert receipt["status"] == "SUCCESS"
    assert receipt["self_destruct_verified"] is True
    assert receipt["tool_output"]["result"] == {"shannon_proxy": 0.2}
    assert "bft_attestation" in receipt

    # 2. Malicious AST escape attempt must be blocked fail-closed
    req_blocked = {
        "jsonrpc": "2.0",
        "id": 31,
        "method": "tools/call",
        "params": {
            "name": "detonate_ephemeral_mcp",
            "arguments": {
                "domain_name": "RogueShell",
                "implementation_body": "import os\nreturn os.system('whoami')",
                "call_arguments": {"cmd": "whoami"},
            },
        },
    }
    res_blocked = server.process_request(req_blocked)
    assert res_blocked is not None
    blocked_obj = cast(dict[str, Any], res_blocked["result"])
    assert blocked_obj.get("isError") is True
    assert "AX-0 AST GATE" in blocked_obj["content"][0]["text"]


def test_mcp_use_canonical_names_mode(tmp_path: Path) -> None:
    """When use_canonical_names=True, tools/list and resources/list expose cortex_* as primary names."""
    server = CortexMCPServer(
        ledger_path=tmp_path / "canonical_bft.db",
        mail_ledger_path=tmp_path / "canonical_mail.db",
        causal_gate_path=tmp_path / "canonical_gate.db",
        use_canonical_names=True,
    )
    res_tools = server.process_request({"jsonrpc": "2.0", "id": 40, "method": "tools/list", "params": {}})
    assert res_tools is not None
    tools = cast(dict[str, Any], res_tools["result"])["tools"]
    names = {t["name"] for t in tools}
    assert "cortex_event_append" in names
    assert "cortex_ledger_query" in names
    assert "cortex_merkle_verify" in names
    assert "cortex_mail_send" in names
    assert "cortex_mcp_bomb_detonate" in names
    assert "cortex_skill_route" in names
    assert "bft_append_event" not in names

    res_resources = server.process_request({"jsonrpc": "2.0", "id": 41, "method": "resources/list", "params": {}})
    assert res_resources is not None
    resources = cast(dict[str, Any], res_resources["result"])["resources"]
    uris = {r["uri"] for r in resources}
    assert uris == {
        "babylon://presentation/guide",
        "babylon://signature/schema",
        "cortex://ledger/status",
        "cortex://merkle/attestation",
        "cortex://causal/ledger",
        "cortex://skills/catalog",
    }


def test_cli_tools_and_skills_introspection(capsys: Any) -> None:
    """Verify babylon60 tools and babylon60 skills CLI subcommands."""
    import argparse

    from babylon60.cli.main_dispatcher import cmd_skills, cmd_tools

    rc_tools = cmd_tools(argparse.Namespace(server="all", json=True))
    assert rc_tools == 0
    tools_out = json.loads(capsys.readouterr().out)
    assert len(tools_out["tools"]) >= 14
    assert len(tools_out["resources"]) == 5
    assert "babylon://presentation/guide" in {resource["uri"] for resource in tools_out["resources"]}

    rc_status = cmd_skills(
        argparse.Namespace(skills_action="status", scope="workspace", role="all", query=None, json=True)
    )
    assert rc_status == 0
    status_out = json.loads(capsys.readouterr().out)
    ws_skills_dir = Path(__file__).resolve().parent.parent / ".agents" / "skills"
    expected_ws_skills = sum(1 for p in ws_skills_dir.iterdir() if p.is_dir() and (p / "SKILL.md").is_file())
    assert status_out["workspace_canonical_alias_coverage"] == f"{expected_ws_skills}/{expected_ws_skills}"

    rc_route = cmd_skills(
        argparse.Namespace(
            skills_action="route",
            scope="workspace",
            role="all",
            query="epistemic-simplifier",
            json=True,
        )
    )
    assert rc_route == 0
    route_out = json.loads(capsys.readouterr().out)
    assert route_out["name"] == "wait-what"
    assert route_out["canonical_alias"] == "epistemic-simplifier"


def test_cmd_mcp_bomb_cli(capsys: Any) -> None:
    import argparse
    from babylon60.cli.main_dispatcher import cmd_mcp_bomb

    args = argparse.Namespace(
        domain="CliNorm",
        code="return {'val': x * 2}",
        args='{"x": 21}',
        desc="CLI test bomb",
        timeout=5.0,
        json=True,
    )
    rc = cmd_mcp_bomb(args)
    assert rc == 0
    out = json.loads(capsys.readouterr().out)
    assert out["status"] == "SUCCESS"
    assert out["self_destruct_verified"] is True
    assert out["tool_output"]["result"] == {"val": 42}


def test_mcp_skills_catalog_resource_read(tmp_path: Path) -> None:
    server = CortexMCPServer(
        ledger_path=tmp_path / "ledger.db",
        mail_ledger_path=tmp_path / "mail.db",
        causal_gate_path=tmp_path / "causal.db",
    )
    req = {
        "jsonrpc": "2.0",
        "id": 50,
        "method": "resources/read",
        "params": {"uri": "bft://skills/catalog"},
    }
    res = server.process_request(req)
    assert res is not None
    result = cast(dict[str, Any], res["result"])
    content = result["contents"][0]["text"]
    data = json.loads(content)
    canonical_catalog = json.loads(
        (Path(__file__).resolve().parent.parent / "docs" / "skills.json").read_text(encoding="utf-8")
    )
    expected_total_skills = int(canonical_catalog["total_skills"])
    assert expected_total_skills == len(canonical_catalog["entries"])
    assert data["total_skills"] == expected_total_skills
    assert len(data["skills"]) == expected_total_skills
    assert any(s["canonical_alias"] == "epistemic-simplifier" for s in data["skills"])


def test_mcp_bft_route_skill_tool(tmp_path: Path) -> None:
    server = CortexMCPServer(
        ledger_path=tmp_path / "ledger.db",
        mail_ledger_path=tmp_path / "mail.db",
        causal_gate_path=tmp_path / "causal.db",
    )
    # Legacy tool name call
    req = {
        "jsonrpc": "2.0",
        "id": 51,
        "method": "tools/call",
        "params": {
            "name": "bft_route_skill",
            "arguments": {"query": "epistemic-simplifier", "scope": "workspace"},
        },
    }
    res = server.process_request(req)
    assert res is not None
    result = cast(dict[str, Any], res["result"])
    assert not result["isError"]
    payload = json.loads(result["content"][0]["text"])
    assert payload["match"] is True
    assert payload["elected"]["canonical_alias"] == "epistemic-simplifier"
    assert payload["elected"]["name"] == "wait-what"

    # Canonical alias tool call on canonical server
    canonical_server = CortexMCPServer(
        ledger_path=tmp_path / "ledger2.db",
        use_canonical_names=True,
    )
    req_canonical = {
        "jsonrpc": "2.0",
        "id": 52,
        "method": "tools/call",
        "params": {
            "name": "cortex_skill_route",
            "arguments": {"query": "kernel-thermo-audit"},
        },
    }
    res_can = canonical_server.process_request(req_canonical)
    assert res_can is not None
    result_can = cast(dict[str, Any], res_can["result"])
    assert not result_can["isError"]
    payload_can = json.loads(result_can["content"][0]["text"])
    assert payload_can["match"] is True
    assert payload_can["elected"]["name"] == "thermo-audit"


def test_mcp_prompts_list_and_get(tmp_path: Path) -> None:
    server = CortexMCPServer(
        ledger_path=tmp_path / "ledger.db",
        mail_ledger_path=tmp_path / "mail.db",
        causal_gate_path=tmp_path / "causal.db",
    )
    req_list = {"jsonrpc": "2.0", "id": 53, "method": "prompts/list", "params": {}}
    res_list = server.process_request(req_list)
    assert res_list is not None
    result_list = cast(dict[str, Any], res_list["result"])
    prompts = result_list["prompts"]
    ws_skills_dir = Path(__file__).resolve().parent.parent / ".agents" / "skills"
    expected_ws_skills = sum(1 for p in ws_skills_dir.iterdir() if p.is_dir() and (p / "SKILL.md").is_file())
    assert len(prompts) == expected_ws_skills
    prompt_names = {p["name"] for p in prompts}
    assert "epistemic-simplifier" in prompt_names or "wait-what" in prompt_names

    req_get = {
        "jsonrpc": "2.0",
        "id": 54,
        "method": "prompts/get",
        "params": {"name": "wait-what", "arguments": {"task": "auditar silicio"}},
    }
    res_get = server.process_request(req_get)
    assert res_get is not None
    result_get = cast(dict[str, Any], res_get["result"])
    messages = result_get["messages"]
    assert len(messages) >= 1
    assert "auditar silicio" in messages[0]["content"]["text"]
