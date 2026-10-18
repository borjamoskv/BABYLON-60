"""Signature delivery through the real Cortex stdio boundary."""

from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import sys

import pytest


ROOT = Path(__file__).absolute().parents[1]


@pytest.mark.parametrize("canonical", [False, True])
@pytest.mark.parametrize("ui_supported", [False, True])
def test_signature_stdio_negotiation(tmp_path: Path, canonical: bool, ui_supported: bool) -> None:
    env = os.environ.copy()
    env["PYTHONPATH"] = os.pathsep.join((str(ROOT / "01_KISH_ENGINE"), str(ROOT)))
    env["BABYLON_HOME"] = str(tmp_path / "home")
    env["BABYLON_CAUSAL_GATE_DB"] = str(tmp_path / "gate.db")
    env["BABYLON60_MCP_CANONICAL_NAMES"] = "1" if canonical else "0"
    capabilities = (
        {"extensions": {"io.modelcontextprotocol/ui": {"mimeTypes": ["text/html;profile=mcp-app"]}}}
        if ui_supported
        else {}
    )
    payload = {
        "observed_at": "2026-10-18T10:00:00+02:00",
        "fields": {"LLM": "Test fixture model"},
        "sources": {"LLM": "Synthetic test fixture only"},
    }
    operations = [
        ("initialize", {"capabilities": capabilities, "clientInfo": {"name": "unknown-client", "version": "1"}}),
        ("tools/list", {}),
        ("resources/list", {}),
        ("tools/call", {"name": "babylon_signature_render", "arguments": {"payload": payload}}),
        ("resources/read", {"uri": "ui://babylon60/signature"}),
        ("resources/read", {"uri": "babylon://signature/schema"}),
        ("tools/call", {"name": "babylon_signature_render", "arguments": {"payload": {}}}),
    ]
    requests = [
        {"jsonrpc": "2.0", "id": index, "method": method, "params": params}
        for index, (method, params) in enumerate(operations, start=1)
    ]
    result = subprocess.run(
        [sys.executable, "-m", "babylon60.mcp.cortex_mcp_server", "--ledger", str(tmp_path / "ledger.db")],
        input="".join(json.dumps(request) + "\n" for request in requests),
        text=True,
        capture_output=True,
        cwd=tmp_path,
        env=env,
        timeout=30,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    responses = [json.loads(line) for line in result.stdout.splitlines()]
    assert [response["id"] for response in responses] == list(range(1, 8))
    assert all("error" not in response for response in responses), responses
    tools = responses[1]["result"]["tools"]
    signature_tools = [tool for tool in tools if tool["name"] == "babylon_signature_render"]
    assert len(signature_tools) == 1
    descriptor = signature_tools[0]
    assert ("_meta" in descriptor) is ui_supported
    if ui_supported:
        assert descriptor["_meta"]["ui"]["resourceUri"] == "ui://babylon60/signature"
    resources = responses[2]["result"]["resources"]
    assert any(resource["uri"] == "babylon://signature/schema" for resource in resources)
    assert any(resource["uri"] == "ui://babylon60/signature" for resource in resources) is ui_supported
    rendered = responses[3]["result"]
    assert not rendered.get("isError", False)
    assert rendered["structuredContent"]["selected_format"] == ("ui" if ui_supported else "markdown")
    assert rendered["structuredContent"]["signature"]["fields"]["LLM"] == "Test fixture model"
    assert "Test fixture model" in rendered["content"][0]["text"]
    app = responses[4]["result"]["contents"][0]
    assert app["mimeType"] == "text/html;profile=mcp-app"
    assert app["text"].lstrip().lower().startswith("<!doctype html>")
    assert app["_meta"]["ui"]["csp"]["connectDomains"] == []
    schema = json.loads(responses[5]["result"]["contents"][0]["text"])
    assert "observed_at" in schema["required"]
    rejected = responses[6]["result"]
    assert rejected["isError"] is True
    assert "structuredContent" not in rejected
