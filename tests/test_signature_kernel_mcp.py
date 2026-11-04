"""Portable signatures cross the actual FastMCP boundary with declared capabilities."""

from __future__ import annotations

import asyncio
import os
from pathlib import Path
import runpy
import sys
from typing import Literal

import pytest

pytest.importorskip("fastmcp")
from fastmcp import Client
from fastmcp.client.transports import StdioTransport
from mcp.client.extension import ClientExtension

from tools.babylon60_mcp import CANONICAL_TOOL_ALIASES, KernelHarness, create_server


TOOL_NAME = "babylon_signature_render"
UI_URI = "ui://babylon60/signature"
UI_MIME = "text/html;profile=mcp-app"
SCHEMA_URI = "babylon://signature/schema"
REPO_ROOT = Path(__file__).absolute().parents[1]


class SignatureUiExtension(ClientExtension):
    identifier = "io.modelcontextprotocol/ui"

    def settings(self) -> dict[str, object]:
        return {"mimeTypes": [UI_MIME]}


def _payload() -> dict[str, object]:
    return {
        "observed_at": "2026-10-18T09:00:00+02:00",
        "fields": {"LLM": "Modelo de prueba", "TOPOLOGÍA ACTIVA": "MOSKV-1"},
        "sources": {"LLM": "metadatos de prueba", "TOPOLOGÍA ACTIVA": "contrato"},
    }


@pytest.mark.parametrize("canonical_names", [False, True])
@pytest.mark.parametrize("connection_mode", ["legacy", "auto"])
@pytest.mark.parametrize("ui_supported", [False, True])
def test_kernel_signature_negotiates_real_client_capabilities(
    tmp_path: Path,
    canonical_names: bool,
    connection_mode: Literal["legacy", "auto"],
    ui_supported: bool,
) -> None:
    harness = KernelHarness(tmp_path)

    async def exercise() -> None:
        extensions = [SignatureUiExtension()] if ui_supported else []
        server = create_server(harness, use_canonical_names=canonical_names)
        async with Client(server, mode=connection_mode, extensions=extensions) as client:
            tools = await client.list_tools()
            names = {tool.name for tool in tools}
            expected_kernel = set(CANONICAL_TOOL_ALIASES if canonical_names else CANONICAL_TOOL_ALIASES.values())
            assert expected_kernel <= names
            signature = next(tool for tool in tools if tool.name == TOOL_NAME)
            assert signature.meta is not None
            assert signature.meta["ui"] == {"resourceUri": UI_URI}
            assert signature.annotations is not None and signature.annotations.read_only_hint is True

            resources = await client.list_resources()
            assert {UI_URI, SCHEMA_URI} <= {str(resource.uri) for resource in resources}
            app = (await client.read_resource(UI_URI))[0]
            assert app.mime_type == UI_MIME
            assert getattr(app, "text", "").lower().startswith("<!doctype html>")
            assert app.meta is not None
            assert app.meta["ui"]["csp"] == {"connectDomains": [], "resourceDomains": []}
            schema = (await client.read_resource(SCHEMA_URI))[0]
            assert schema.mime_type == "application/json"

            result = await client.call_tool(TOOL_NAME, {"payload": _payload()})
            assert not result.is_error
            assert result.structured_content is not None
            assert result.structured_content["selected_format"] == ("ui" if ui_supported else "markdown")
            assert result.structured_content["signature"]["fields"]["LLM"] == "Modelo de prueba"
            assert len(result.content) == 1
            assert "Modelo de prueba" in getattr(result.content[0], "text", "")

            invalid = _payload()
            invalid["observed_at"] = "sin fecha"
            failure = await client.call_tool(TOOL_NAME, {"payload": invalid}, raise_on_error=False)
            assert failure.is_error
            assert failure.structured_content is None

    try:
        asyncio.run(exercise())
    finally:
        harness.close()


def test_kernel_launcher_preserves_existing_pythonpath(monkeypatch: pytest.MonkeyPatch) -> None:
    launcher = runpy.run_path(str(REPO_ROOT / "scripts/c5_cli/launch_kernel_mcp.py"))
    monkeypatch.setenv("PYTHONPATH", "/existing/entry")
    monkeypatch.setattr("sys.argv", ["launch_kernel_mcp.py"])

    class ExecIntercept(Exception):
        pass

    def intercept(_file: str, _argv: list[str]) -> None:
        raise ExecIntercept

    monkeypatch.setattr(os, "execv", intercept)
    with pytest.raises(ExecIntercept):
        launcher["main"]()
    assert os.environ["PYTHONPATH"].split(os.pathsep) == [str(REPO_ROOT / "01_KISH_ENGINE"), "/existing/entry"]


def test_kernel_launcher_serves_signature_from_unrelated_working_directory(tmp_path: Path) -> None:
    transport = StdioTransport(
        command=sys.executable,
        args=[str(REPO_ROOT / "scripts/c5_cli/launch_kernel_mcp.py"), "--root", str(tmp_path)],
        cwd=str(tmp_path),
        env={"PYTHONPATH": "/unrelated/source/path", "BABYLON_HOME": str(tmp_path / "home")},
    )

    async def exercise() -> None:
        async with Client(transport, mode="legacy", extensions=[SignatureUiExtension()]) as client:
            result = await client.call_tool(TOOL_NAME, {"payload": _payload()})
            assert not result.is_error
            assert result.structured_content is not None
            assert result.structured_content["selected_format"] == "ui"

    asyncio.run(exercise())
