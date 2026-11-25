"""The installed stdio service must negotiate a real MCP protocol version."""

import os
from pathlib import Path
import sys

import pytest
from babylon60 import __version__


@pytest.mark.asyncio
async def test_official_client_initializes_and_discovers_resources(tmp_path: Path) -> None:
    from mcp import ClientSession, StdioServerParameters
    from mcp.client.stdio import stdio_client
    from mcp.types import ReadResourceResult

    env = os.environ.copy()
    env["BABYLON_HOME"] = str(tmp_path)
    env["BABYLON_CAUSAL_GATE_DB"] = str(tmp_path / "gate.db")
    env["PYTHONIOENCODING"] = "cp1252"
    params = StdioServerParameters(
        command=sys.executable,
        args=["-m", "babylon60.mcp.cortex_mcp_server", "--ledger", str(tmp_path / "ledger.db")],
        env=env,
    )
    async with stdio_client(params) as (reader, writer):
        async with ClientSession(reader, writer, read_timeout_seconds=15) as session:
            initialized = await session.initialize()
            assert initialized.protocol_version == "2024-11-05"
            assert initialized.server_info.name == "cortex-persist-bft"
            assert initialized.server_info.version == __version__
            tools = await session.list_tools()
            assert "bft_query_ledger" in {tool.name for tool in tools.tools}
            resources = await session.list_resources()
            assert "babylon://presentation/guide" in {str(resource.uri) for resource in resources.resources}
            guide = await session.read_resource("babylon://presentation/guide")
            assert isinstance(guide, ReadResourceResult)
            assert guide.contents
            await session.send_ping()
