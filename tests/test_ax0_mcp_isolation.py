# -*- coding: utf-8 -*-
"""
Axiom-0 (AX-0) Epistemic Invariant Test:
'A stochastic component MUST NOT authorize an irreversible effect it proposes.'
Proposer(action) != Authorizer(action).

The MCP client is the AI / LLM agent (stochastic proposer).
It MUST NOT have access to self-sign or register approvals for protected/CRITICAL tasks.
"""

import json
import subprocess
import sys
from pathlib import Path
from typing import Any, cast

from babylon60.mcp.cortex_mcp_server import CortexMCPServer


def test_ax0_mcp_tools_list_omits_sign_off(tmp_path: Path) -> None:
    """Verifies that causal_register_sign_off is NOT exposed in MCP tools list."""
    server = CortexMCPServer(
        ledger_path=tmp_path / "ledger.db",
        mail_ledger_path=tmp_path / "mail.db",
        causal_gate_path=tmp_path / "causal.db",
    )
    request = {"jsonrpc": "2.0", "id": 1, "method": "tools/list", "params": {}}
    response = server.process_request(request)
    assert response is not None
    result = cast(dict[str, Any], response["result"])
    tool_names = [t["name"] for t in result.get("tools", [])]

    assert "causal_register_sign_off" not in tool_names, (
        "AX-0 VIOLATION: causal_register_sign_off must not be exposed to stochastic MCP clients"
    )


def test_ax0_mcp_rejects_self_sign_off_call(tmp_path: Path) -> None:
    """Verifies that calling causal_register_sign_off via MCP fails closed."""
    causal_db = tmp_path / "causal.db"
    server = CortexMCPServer(
        ledger_path=tmp_path / "ledger.db",
        mail_ledger_path=tmp_path / "mail.db",
        causal_gate_path=causal_db,
    )

    # 1. Propose critical task
    task = {"action": "deploy_production", "execution_id": "EXEC-ROGUE-001", "is_mutative": True}
    req_eval = {
        "jsonrpc": "2.0",
        "id": 2,
        "method": "tools/call",
        "params": {"name": "causal_evaluate_task_risk", "arguments": {"task_payload": task}},
    }
    res_eval = server.process_request(req_eval)
    assert res_eval is not None
    res_eval_res = cast(dict[str, Any], res_eval["result"])
    assert "CRITICAL" in res_eval_res["content"][0]["text"]

    # 2. Rogue agent attempts self-approval
    req_self_sign = {
        "jsonrpc": "2.0",
        "id": 3,
        "method": "tools/call",
        "params": {
            "name": "causal_register_sign_off",
            "arguments": {
                "execution_id": "EXEC-ROGUE-001",
                "action_name": "drop_production_database",
                "risk_level": "CRITICAL",
                "decision": "APPROVED",
            },
        },
    }
    res_self_sign = server.process_request(req_self_sign)
    assert res_self_sign is not None
    res_sign_res = cast(dict[str, Any], res_self_sign["result"])

    # Must be marked error and blocked under AX-0
    assert res_sign_res.get("isError") is True
    assert "AX-0" in res_sign_res["content"][0]["text"]

    # 3. Gate must still forbid execution of the critical task
    assert server.verification_gate.is_allowed(task) is False, (
        "AX-0 VIOLATION: Task was unauthorizedly marked allowed after blocked self-sign attempt"
    )


def test_ax0_mcp_subprocess_stdio_quarantine(tmp_path: Path) -> None:
    """End-to-end verification over subprocess stdio JSON-RPC stream."""
    msgs = [
        json.dumps(
            {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "initialize",
                "params": {"protocolVersion": "2025-06-18", "capabilities": {}, "clientInfo": {"name": "ax0-agent"}},
            }
        ),
        json.dumps({"jsonrpc": "2.0", "method": "notifications/initialized"}),
        json.dumps({"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}}),
        json.dumps(
            {
                "jsonrpc": "2.0",
                "id": 3,
                "method": "tools/call",
                "params": {
                    "name": "causal_register_sign_off",
                    "arguments": {
                        "execution_id": "EXEC-SUBPROCESS-001",
                        "action_name": "rm -rf /",
                        "risk_level": "CRITICAL",
                        "decision": "APPROVED",
                    },
                },
            }
        ),
    ]

    import os

    env = os.environ.copy()
    env["PYTHONPATH"] = f"01_KISH_ENGINE:{tmp_path.parent}"
    env["BABYLON_CAUSAL_GATE_DB"] = str(tmp_path / "causal.db")

    p = subprocess.run(
        [sys.executable, "-m", "babylon60.mcp.cortex_mcp_server", "--ledger", str(tmp_path / "ledger.db")],
        input="\n".join(msgs) + "\n",
        capture_output=True,
        text=True,
        timeout=10,
        env=env,
    )

    replies: dict[int, dict[str, Any]] = {}
    for line in p.stdout.splitlines():
        try:
            m = json.loads(line)
            if "id" in m and isinstance(m["id"], int):
                replies[m["id"]] = m
        except json.JSONDecodeError:
            continue

    assert 2 in replies, "Failed to get tools/list reply from MCP server"
    tools = [t["name"] for t in replies[2].get("result", {}).get("tools", [])]
    assert "causal_register_sign_off" not in tools, "AX-0 VIOLATION: Tool exposed over stdio"

    assert 3 in replies, "Failed to get tools/call reply from MCP server"
    r3 = replies[3].get("result", {})
    assert r3.get("isError") is True, "AX-0 VIOLATION: Self sign-off call was not flagged as error"
    assert "AX-0" in r3.get("content", [{}])[0].get("text", "")
