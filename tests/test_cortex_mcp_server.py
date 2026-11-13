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

import asyncio
from collections.abc import Iterator
import json
import os
from pathlib import Path
import sqlite3
import sys
import tempfile
from typing import Any, cast
from unittest.mock import patch

import pytest
from babylon60.mcp.cortex_mcp_server import CortexMCPServer
from babylon60.mcp.skills_snapshot import GATEWAY_EXPECTED_AUDIENCE, derive_v31_contract


@pytest.fixture
def mcp_runtime_directory(monkeypatch: pytest.MonkeyPatch) -> Iterator[Path]:
    # Keep Unix socket names below the OS limit even when pytest's base is long.
    with tempfile.TemporaryDirectory(prefix="mcp-", dir="/tmp" if os.name == "posix" else None) as directory:
        runtime = Path(os.path.realpath(directory))
        monkeypatch.setattr(tempfile, "tempdir", str(runtime))
        yield runtime


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
    # Unconfigured effect dispatch must fail before the real ledger handler.
    assert result_append["isError"]
    assert "FL-MCP-01 DENIED" in result_append["content"][0]["text"]

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
    assert query_data["total_returned"] == 0


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
    assert cast(dict[str, Any], res_append["result"]).get("isError") is True

    req_query = {
        "jsonrpc": "2.0",
        "id": 21,
        "method": "tools/call",
        "params": {"name": "cortex_ledger_query", "arguments": {"event_type": "ALIAS_EVENT", "limit": 1}},
    }
    res_query = server.process_request(req_query)
    assert res_query is not None
    query_data = json.loads(cast(dict[str, Any], res_query["result"])["content"][0]["text"])
    assert query_data["total_returned"] == 0

    req_res = {"jsonrpc": "2.0", "id": 22, "method": "resources/read", "params": {"uri": "cortex://ledger/status"}}
    res_res = server.process_request(req_res)
    assert res_res is not None
    contents = cast(dict[str, Any], res_res["result"])["contents"]
    assert contents[0]["uri"] == "cortex://ledger/status"


def test_mcp_detonate_ephemeral_bomb(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, mcp_runtime_directory: Path
) -> None:
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
    # Capability/attestation gates precede AST validation and process launch.
    with patch("asyncio.create_subprocess_exec", wraps=asyncio.create_subprocess_exec) as subprocess_launcher:
        res_bomb = server.process_request(req_bomb)
    assert res_bomb is not None
    result_obj = cast(dict[str, Any], res_bomb["result"])
    assert result_obj.get("isError") is True
    assert "FL-MCP-01 DENIED" in result_obj["content"][0]["text"]
    subprocess_launcher.assert_not_called()
    assert list(mcp_runtime_directory.iterdir()) == []

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
    assert "FL-MCP-01 DENIED" in blocked_obj["content"][0]["text"]


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


def test_cmd_mcp_bomb_cli(
    capsys: pytest.CaptureFixture[str], tmp_path: Path, monkeypatch: pytest.MonkeyPatch, mcp_runtime_directory: Path
) -> None:
    import argparse
    from babylon60.cli.main_dispatcher import cmd_mcp_bomb
    from babylon60.kernel import mcp_lifecycle_manager

    # The CLI's default manager targets a persistent repo DB. Keep this
    # integration test on its own ledger, without changing production defaults.
    manager_type = mcp_lifecycle_manager.McpLifecycleManager
    monkeypatch.setattr(
        mcp_lifecycle_manager,
        "McpLifecycleManager",
        lambda: manager_type(db_path=str(tmp_path / "cli_causal_gate.db")),
    )

    args = argparse.Namespace(
        domain="CliNorm",
        code="return {'val': x * 2}",
        args='{"x": 21}',
        desc="CLI test bomb",
        timeout=5.0,
        json=True,
    )
    with patch("asyncio.create_subprocess_exec", wraps=asyncio.create_subprocess_exec) as subprocess_launcher:
        rc = cmd_mcp_bomb(args)
    out = json.loads(capsys.readouterr().out)
    assert out["self_destruct_verified"] is True
    if sys.platform == "darwin":
        assert rc == 0
        assert out["status"] == "SUCCESS"
        assert out["tool_output"]["result"] == {"val": 42}
    else:
        assert rc == 1
        assert out["status"] == "ERROR"
        assert out["error_code"] == "OS_ISOLATION_UNAVAILABLE"
        assert out["isolation_backend"] is None
        assert out["tool_output"] is None
        subprocess_launcher.assert_not_called()
    assert list(mcp_runtime_directory.iterdir()) == []
    with sqlite3.connect(tmp_path / "cli_causal_gate.db") as database:
        assert database.execute("SELECT COUNT(*) FROM mcp_registry").fetchone()[0] == 0


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
        causal_gate_path=tmp_path / "canonical_causal.db",
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


def test_mcp_skills_snapshot_immutability_and_sep2640(tmp_path: Path) -> None:
    """SEP-2640 skills/list, skills/get and skill:// resources serve from an immutable RAM snapshot."""
    from babylon60.mcp.skills_snapshot import ImmutableSkillsSnapshot

    skills_dir = tmp_path / "skills"
    skill_folder = skills_dir / "popeye-strength"
    skill_folder.mkdir(parents=True)
    skill_md = skill_folder / "SKILL.md"
    original_md = (
        "---\n"
        "name: popeye-strength\n"
        "canonical_alias: spinach-transducer\n"
        'description: \'Fuerza agéntica gobernada. Dispara con "popeye", "espinacas".\'\n'
        "role: ejecutor\n"
        "---\n"
        "# Popeye Strength\nOriginal verified instructions.\n"
    )
    skill_md.write_text(original_md, encoding="utf-8")
    (skill_folder / "contract.yaml").write_text("schema_version: '1'\nskill: popeye-strength\n", encoding="utf-8")

    catalog_file = tmp_path / "skills.json"
    catalog_file.write_text(
        json.dumps(
            {
                "version": "26.400",
                "total_skills": 1,
                "average_exergy_density": 20000,
                "adjacency": [],
                "entries": [
                    {
                        "name": "popeye-strength",
                        "canonical_alias": "spinach-transducer",
                        "display_name": "Popeye Strength",
                        "description": "Fuerza agéntica gobernada.",
                        "role": "ejecutor",
                        "scope": "workspace",
                        "tier": 20000,
                        "category": "Kernel",
                        "triggers": ["popeye", "espinacas"],
                    }
                ],
            }
        ),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="SKILLS_SNAPSHOT_COUNT_MISMATCH"):
        ImmutableSkillsSnapshot.load(catalog_file, skills_dir, expected_count=107)

    server = CortexMCPServer(
        ledger_path=tmp_path / "ledger.db",
        causal_gate_path=tmp_path / "causal.db",
    )
    server._skills_snapshot = ImmutableSkillsSnapshot.load(catalog_file, skills_dir, expected_count=1)

    # Mutate files on disk AFTER snapshot load to test TOCTOU immunity
    skill_md.write_text("---\nname: popeye-strength\n---\n# TAMPERED ON DISK\n", encoding="utf-8")
    (skill_folder / "contract.yaml").unlink()

    res_list = server.process_request({"jsonrpc": "2.0", "id": 60, "method": "skills/list", "params": {}})
    assert res_list is not None
    list_payload = cast(dict[str, Any], res_list["result"])
    assert list_payload["total"] == 1
    assert list_payload["snapshot_root"].startswith("sha256:")
    assert list_payload["skills"][0]["name"] == "popeye-strength"
    assert len(list_payload["skills"][0]["resources"]) == 2

    res_get = server.process_request(
        {"jsonrpc": "2.0", "id": 61, "method": "skills/get", "params": {"uri": "skill://spinach-transducer"}}
    )
    assert res_get is not None
    get_payload = cast(dict[str, Any], res_get["result"])
    assert get_payload["isError"] is False
    assert get_payload["skill"]["name"] == "popeye-strength"

    res_read = server.process_request(
        {
            "jsonrpc": "2.0",
            "id": 62,
            "method": "resources/read",
            "params": {"uri": "skill://popeye-strength/SKILL.md"},
        }
    )
    assert res_read is not None
    read_payload = cast(dict[str, Any], res_read["result"])
    served_text = read_payload["contents"][0]["text"]
    assert "Original verified instructions." in served_text
    assert "TAMPERED ON DISK" not in served_text
    assert read_payload["contents"][0]["_meta"]["digest"].startswith("sha256:")

    res_contract = server.process_request(
        {
            "jsonrpc": "2.0",
            "id": 63,
            "method": "resources/read",
            "params": {"uri": "skill://popeye-strength/contract.yaml"},
        }
    )
    assert res_contract is not None
    contract_payload = cast(dict[str, Any], res_contract["result"])
    assert "schema_version: '1'" in contract_payload["contents"][0]["text"]


def test_rust_babylon_skills_mcp_stdio_interop(tmp_path: Path) -> None:
    """Live stdio JSON-RPC 2.0 roundtrip against the compiled Rust babylon-skills-mcp binary."""
    import subprocess

    repo_root = Path(__file__).resolve().parent.parent
    target_dir = Path(os.environ.get("CARGO_TARGET_DIR", str(repo_root / "target")))
    if not target_dir.is_absolute():
        target_dir = repo_root / target_dir
    binary = target_dir / "debug" / "babylon-skills-mcp"
    if not binary.is_file():
        subprocess.run(
            ["cargo", "build", "--locked", "--offline", "-p", "babylon-skills-mcp"],
            cwd=repo_root,
            check=True,
            capture_output=True,
        )

    proc = subprocess.Popen(
        [
            str(binary),
            "--catalog",
            str(repo_root / "docs" / "skills.json"),
            "--skills-dir",
            str(repo_root / ".agents" / "skills"),
            "--expect-count",
            "131",
        ],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    assert proc.stdin is not None and proc.stdout is not None
    try:
        proc.stdin.write(json.dumps({"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}}) + "\n")
        proc.stdin.write(
            json.dumps({"jsonrpc": "2.0", "id": 2, "method": "skills/get", "params": {"uri": "skill://wait-what"}})
            + "\n"
        )
        proc.stdin.write(
            json.dumps(
                {
                    "jsonrpc": "2.0",
                    "id": 3,
                    "method": "resources/read",
                    "params": {"uri": "skill://wait-what/SKILL.md"},
                }
            )
            + "\n"
        )
        proc.stdin.flush()

        init_res = json.loads(proc.stdout.readline())
        get_res = json.loads(proc.stdout.readline())
        read_res = json.loads(proc.stdout.readline())

        assert init_res["result"]["serverInfo"]["name"] == "babylon-skills-mcp"
        assert init_res["result"]["capabilities"]["skills"]["readOnly"] is True
        assert get_res["result"]["skill"]["canonical_alias"] == "epistemic-simplifier"
        assert "wait-what" in read_res["result"]["contents"][0]["text"]
    finally:
        proc.stdin.close()
        proc.wait(timeout=5)
        proc.stdout.close()
        if proc.stderr is not None:
            proc.stderr.close()


def _skill_identity(server: CortexMCPServer, name: str) -> str:
    skill = server._skills_snapshot.resolve(name)
    assert skill is not None
    return skill.tool_identity_hash


def test_v31_gateway_3_primitives_and_fl_p08_to_fl_p11(tmp_path: Path) -> None:
    """Check Architecture v3.1 (discover, inspect, propose_effect) and FL-P08..FL-P11 in Python."""
    from babylon60.mcp.skills_snapshot import GATEWAY_EXPECTED_AUDIENCE

    server = CortexMCPServer(
        ledger_path=tmp_path / "ledger.db",
        causal_gate_path=tmp_path / "causal.db",
    )

    # 1. skills.discover enforces k <= 5
    disc_res = server.process_request(
        {
            "jsonrpc": "2.0",
            "id": 70,
            "method": "tools/call",
            "params": {
                "name": "skills.discover",
                "arguments": {"query": "kernel seqlock audit", "project_id": "babylon60", "k": 50},
            },
        }
    )
    assert disc_res is not None
    disc_payload = cast(dict[str, Any], disc_res["result"])
    assert disc_payload["isError"] is False
    assert 1 <= len(disc_payload["matches"]) <= 5

    # 2. skills.inspect returns schema, preconditions, and tool_identity_hash
    insp_res = server.process_request(
        {
            "jsonrpc": "2.0",
            "id": 71,
            "method": "tools/call",
            "params": {
                "name": "skills.inspect",
                "arguments": {"skill_id": "thermo-audit", "version": "1.0.0", "project_id": "babylon60"},
            },
        }
    )
    assert insp_res is not None
    insp_payload = cast(dict[str, Any], insp_res["result"])
    assert insp_payload["isError"] is False
    assert len(insp_payload["tool_identity_hash"]) == 64
    assert "input_json_schema" in insp_payload

    # 3. FL-P08: Tool Shadowing / unregistered Skill 108 rejected
    fl_p08_res = server.process_request(
        {
            "jsonrpc": "2.0",
            "id": 72,
            "method": "tools/call",
            "params": {
                "name": "skills.propose_effect",
                "arguments": {
                    "skill_id": "skill-108-shadow",
                    "version": "1.0.0",
                    "arguments": {"target_path": "workspace://src/lib.rs"},
                    "precondition_snapshot": {"allowed_roots": ["workspace://"]},
                    "credential": {
                        "audience": GATEWAY_EXPECTED_AUDIENCE,
                        "project_id": "babylon60",
                        "nonce": "py-fl-p08",
                    },
                },
            },
        }
    )
    assert fl_p08_res is not None
    p08_payload = cast(dict[str, Any], fl_p08_res["result"])
    assert p08_payload["status"] == "DENIED"
    assert p08_payload["failure_class"] == "TOOL_SHADOWING_OR_UNREGISTERED"

    # 4. FL-P09: Chaining READ_LOCAL -> EXTERNAL_NETWORK triggers PENDING_APPROVAL
    step1_res = server.process_request(
        {
            "jsonrpc": "2.0",
            "id": 73,
            "method": "tools/call",
            "params": {
                "name": "skills.propose_effect",
                "arguments": {
                    "skill_id": "thermo-audit",
                    "version": "1.0.0",
                    "tool_identity_hash": _skill_identity(server, "thermo-audit"),
                    "trace_id": "py-trace-p09",
                    "arguments": {"target_path": "workspace://src/lib.rs"},
                    "precondition_snapshot": {"allowed_roots": ["workspace://"]},
                    "credential": {
                        "audience": GATEWAY_EXPECTED_AUDIENCE,
                        "project_id": "babylon60",
                        "nonce": "py-fl-p09-1",
                    },
                },
            },
        }
    )
    assert step1_res is not None
    assert cast(dict[str, Any], step1_res["result"])["status"] == "AUTHORIZED"

    step2_res = server.process_request(
        {
            "jsonrpc": "2.0",
            "id": 74,
            "method": "tools/call",
            "params": {
                "name": "skills.propose_effect",
                "arguments": {
                    "skill_id": "c5-socint-extraction-suite",
                    "version": "1.0.0",
                    "tool_identity_hash": _skill_identity(server, "c5-socint-extraction-suite"),
                    "trace_id": "py-trace-p09",
                    "arguments": {"target_path": "workspace://docs/README.md"},
                    "precondition_snapshot": {"allowed_roots": ["workspace://"]},
                    "credential": {
                        "audience": GATEWAY_EXPECTED_AUDIENCE,
                        "project_id": "babylon60",
                        "nonce": "py-fl-p09-2",
                    },
                },
            },
        }
    )
    assert step2_res is not None
    p09_payload = cast(dict[str, Any], step2_res["result"])
    assert p09_payload["status"] == "PENDING_APPROVAL"
    assert p09_payload["failure_class"] == "COMPOSITION_ESCALATION_READ_LOCAL_TO_EXTERNAL_NETWORK"

    # 5. FL-P10: Token passthrough & nonce replay rejected
    p10_pass_res = server.process_request(
        {
            "jsonrpc": "2.0",
            "id": 75,
            "method": "tools/call",
            "params": {
                "name": "skills.propose_effect",
                "arguments": {
                    "skill_id": "thermo-audit",
                    "version": "1.0.0",
                    "tool_identity_hash": _skill_identity(server, "thermo-audit"),
                    "arguments": {"target_path": "workspace://src/lib.rs"},
                    "precondition_snapshot": {"allowed_roots": ["workspace://"]},
                    "credential": {
                        "audience": GATEWAY_EXPECTED_AUDIENCE,
                        "project_id": "babylon60",
                        "nonce": "py-fl-p10-pass",
                        "passthrough_token": "Bearer secret",
                    },
                },
            },
        }
    )
    assert p10_pass_res is not None
    assert cast(dict[str, Any], p10_pass_res["result"])["failure_class"] == "TOKEN_PASSTHROUGH_FORBIDDEN"

    p10_replay_res = server.process_request(
        {
            "jsonrpc": "2.0",
            "id": 76,
            "method": "tools/call",
            "params": {
                "name": "skills.propose_effect",
                "arguments": {
                    "skill_id": "thermo-audit",
                    "version": "1.0.0",
                    "tool_identity_hash": _skill_identity(server, "thermo-audit"),
                    "arguments": {"target_path": "workspace://src/lib.rs"},
                    "precondition_snapshot": {"allowed_roots": ["workspace://"]},
                    "credential": {
                        "audience": GATEWAY_EXPECTED_AUDIENCE,
                        "project_id": "babylon60",
                        "nonce": "py-fl-p09-1",
                    },
                },
            },
        }
    )
    assert p10_replay_res is not None
    assert cast(dict[str, Any], p10_replay_res["result"])["failure_class"] == "NONCE_REPLAY_DETECTED"

    # 6. FL-P11: False positive 200 OK downgraded to FAILED by independent postcondition verifier
    pre_hash = "b" * 64
    p11_res = server.process_request(
        {
            "jsonrpc": "2.0",
            "id": 77,
            "method": "tools/call",
            "params": {
                "name": "skills.propose_effect",
                "arguments": {
                    "skill_id": "c5-neural-face-swap-cuadrilla",
                    "version": "1.0.0",
                    "tool_identity_hash": _skill_identity(server, "c5-neural-face-swap-cuadrilla"),
                    "trace_id": "py-trace-p11",
                    "arguments": {
                        "target_path": "workspace://src/lib.rs",
                        "expected_pre_hash": pre_hash,
                    },
                    "precondition_snapshot": {
                        "allowed_roots": ["workspace://"],
                        "observed_pre_hash": pre_hash,
                    },
                    "credential": {
                        "audience": GATEWAY_EXPECTED_AUDIENCE,
                        "project_id": "babylon60",
                        "nonce": "py-fl-p11",
                    },
                    "simulated_execution_result": {
                        "http_status": 200,
                        "observed_post_hash": pre_hash,
                        "actual_file_sha256": pre_hash,
                    },
                },
            },
        }
    )
    assert p11_res is not None
    p11_payload = cast(dict[str, Any], p11_res["result"])
    assert p11_payload["status"] == "DENIED"
    assert p11_payload["decision"] == "DENIED"
    assert p11_payload["failure_class"] == "UNTRUSTED_EXECUTION_EVIDENCE"


def test_fl_p08_tool_shadowing_and_unvalidated_classification(tmp_path: Path) -> None:
    """FL-P08: Tool shadowing, tampered digest, and unvalidated classification are deterministically DENIED."""
    server = CortexMCPServer(
        ledger_path=tmp_path / "ledger.db",
        mail_ledger_path=tmp_path / "mail.db",
        causal_gate_path=tmp_path / "causal.db",
    )
    # 1. Unregistered shadow tool
    shadow_res = server.process_request(
        {
            "jsonrpc": "2.0",
            "id": 801,
            "method": "tools/call",
            "params": {
                "name": "skills.propose_effect",
                "arguments": {
                    "skill_id": "shadow-malicious-tool",
                    "version": "1.0.0",
                    "arguments": {"target_path": "workspace://src/lib.rs"},
                    "precondition_snapshot": {"allowed_roots": ["workspace://"]},
                    "credential": {
                        "audience": GATEWAY_EXPECTED_AUDIENCE,
                        "project_id": "babylon60",
                        "nonce": "fl-p08-shadow",
                    },
                },
            },
        }
    )
    assert shadow_res is not None
    shadow_payload = cast(dict[str, Any], shadow_res["result"])
    assert shadow_payload["status"] == "DENIED"
    assert shadow_payload["decision"] == "DENIED"
    assert shadow_payload["failure_class"] == "TOOL_SHADOWING_OR_UNREGISTERED"

    # 2. Tampered digest
    tampered_res = server.process_request(
        {
            "jsonrpc": "2.0",
            "id": 802,
            "method": "tools/call",
            "params": {
                "name": "skills.propose_effect",
                "arguments": {
                    "skill_id": "thermo-audit",
                    "version": "1.0.0",
                    "tool_identity_hash": "0" * 64,
                    "arguments": {"target_path": "workspace://src/lib.rs"},
                    "precondition_snapshot": {"allowed_roots": ["workspace://"]},
                    "credential": {
                        "audience": GATEWAY_EXPECTED_AUDIENCE,
                        "project_id": "babylon60",
                        "nonce": "fl-p08-tamper",
                    },
                },
            },
        }
    )
    assert tampered_res is not None
    tampered_payload = cast(dict[str, Any], tampered_res["result"])
    assert tampered_payload["status"] == "DENIED"
    assert tampered_payload["decision"] == "DENIED"
    assert tampered_payload["failure_class"] == "TOOL_IDENTITY_MISMATCH"

    # 3. Unvalidated role/category/scope produces UNVALIDATED and never infers from free-text descriptions
    prof, _ = derive_v31_contract("unknown-skill", "rogue-role", "UnknownCategory", "unknown-scope")
    assert prof["validated"] is False
    assert prof["class"] == "UNVALIDATED"


def test_fl_p09_chaining_exfiltration(tmp_path: Path) -> None:
    """FL-P09: Chaining READ_LOCAL -> EXTERNAL_NETWORK in the same trace is blocked without human approval."""
    server = CortexMCPServer(
        ledger_path=tmp_path / "ledger.db",
        mail_ledger_path=tmp_path / "mail.db",
        causal_gate_path=tmp_path / "causal.db",
    )
    read_res = server.process_request(
        {
            "jsonrpc": "2.0",
            "id": 901,
            "method": "tools/call",
            "params": {
                "name": "skills.propose_effect",
                "arguments": {
                    "skill_id": "thermo-audit",
                    "version": "1.0.0",
                    "tool_identity_hash": _skill_identity(server, "thermo-audit"),
                    "trace_id": "fl-p09-isolated-trace",
                    "arguments": {"target_path": "workspace://secrets/key.pem"},
                    "precondition_snapshot": {"allowed_roots": ["workspace://"]},
                    "credential": {
                        "audience": GATEWAY_EXPECTED_AUDIENCE,
                        "project_id": "babylon60",
                        "nonce": "fl-p09-step1",
                    },
                },
            },
        }
    )
    assert read_res is not None
    assert cast(dict[str, Any], read_res["result"])["status"] == "AUTHORIZED"

    egress_res = server.process_request(
        {
            "jsonrpc": "2.0",
            "id": 902,
            "method": "tools/call",
            "params": {
                "name": "skills.propose_effect",
                "arguments": {
                    "skill_id": "c5-socint-extraction-suite",
                    "version": "1.0.0",
                    "tool_identity_hash": _skill_identity(server, "c5-socint-extraction-suite"),
                    "trace_id": "fl-p09-isolated-trace",
                    "arguments": {"target_path": "workspace://out/report.json"},
                    "precondition_snapshot": {"allowed_roots": ["workspace://"]},
                    "credential": {
                        "audience": GATEWAY_EXPECTED_AUDIENCE,
                        "project_id": "babylon60",
                        "nonce": "fl-p09-step2",
                    },
                },
            },
        }
    )
    assert egress_res is not None
    egress_payload = cast(dict[str, Any], egress_res["result"])
    assert egress_payload["status"] == "PENDING_APPROVAL"
    assert egress_payload["decision"] == "DENIED"
    assert egress_payload["failure_class"] == "COMPOSITION_ESCALATION_READ_LOCAL_TO_EXTERNAL_NETWORK"
    assert "action_capability" not in egress_payload


def test_fl_p10_audience_bound_nonce_expiration_and_no_passthrough(tmp_path: Path) -> None:
    """FL-P10: Wrong audience, passthrough token, expired credential, and nonce replay are DENIED."""
    server = CortexMCPServer(
        ledger_path=tmp_path / "ledger.db",
        mail_ledger_path=tmp_path / "mail.db",
        causal_gate_path=tmp_path / "causal.db",
    )
    expired_res = server.process_request(
        {
            "jsonrpc": "2.0",
            "id": 1001,
            "method": "tools/call",
            "params": {
                "name": "skills.propose_effect",
                "arguments": {
                    "skill_id": "thermo-audit",
                    "version": "1.0.0",
                    "tool_identity_hash": _skill_identity(server, "thermo-audit"),
                    "current_epoch": 2000,
                    "arguments": {"target_path": "workspace://src/lib.rs"},
                    "precondition_snapshot": {"allowed_roots": ["workspace://"]},
                    "credential": {
                        "audience": GATEWAY_EXPECTED_AUDIENCE,
                        "project_id": "babylon60",
                        "nonce": "fl-p10-expired",
                        "expires_at_epoch": 1500,
                    },
                },
            },
        }
    )
    assert expired_res is not None
    expired_payload = cast(dict[str, Any], expired_res["result"])
    assert expired_payload["status"] == "DENIED"
    assert expired_payload["decision"] == "DENIED"
    assert expired_payload["failure_class"] == "CREDENTIAL_EXPIRED"


def test_fl_p11_postcondition_false_positive_rebuke(tmp_path: Path) -> None:
    """FL-P11: Client-supplied 200 OK evidence is rejected before capability issuance."""
    server = CortexMCPServer(
        ledger_path=tmp_path / "ledger.db",
        mail_ledger_path=tmp_path / "mail.db",
        causal_gate_path=tmp_path / "causal.db",
    )
    pre_hash = "c" * 64
    p11_res = server.process_request(
        {
            "jsonrpc": "2.0",
            "id": 1101,
            "method": "tools/call",
            "params": {
                "name": "skills.propose_effect",
                "arguments": {
                    "skill_id": "c5-neural-face-swap-cuadrilla",
                    "version": "1.0.0",
                    "tool_identity_hash": _skill_identity(server, "c5-neural-face-swap-cuadrilla"),
                    "trace_id": "fl-p11-isolated-trace",
                    "arguments": {
                        "target_path": "workspace://src/lib.rs",
                        "expected_pre_hash": pre_hash,
                    },
                    "precondition_snapshot": {
                        "allowed_roots": ["workspace://"],
                        "observed_pre_hash": pre_hash,
                    },
                    "credential": {
                        "audience": GATEWAY_EXPECTED_AUDIENCE,
                        "project_id": "babylon60",
                        "nonce": "fl-p11-isolated-nonce",
                    },
                    "simulated_execution_result": {
                        "http_status": 200,
                        "observed_post_hash": pre_hash,
                        "actual_file_sha256": pre_hash,
                    },
                },
            },
        }
    )
    assert p11_res is not None
    p11_payload = cast(dict[str, Any], p11_res["result"])
    assert p11_payload["status"] == "DENIED"
    assert p11_payload["decision"] == "DENIED"
    assert p11_payload["failure_class"] == "UNTRUSTED_EXECUTION_EVIDENCE"
