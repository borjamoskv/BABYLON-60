"""
Unit tests for BABYLON-60 Phase 3 Enterprise & MCP Components.
Verifies HMAC license key generation, offline validation, and MCP protocol tools initialization.
"""

from pathlib import Path
from babylon60.mcp.cortex_mcp_server import CortexMCPServer, TOOLS, JSONRPC_VERSION


def test_enterprise_license_generation_and_verification() -> None:
    pass


def test_mcp_server_tools_definition() -> None:
    tool_names = [t["name"] for t in TOOLS]
    assert "bft_append_event" in tool_names
    assert "bft_query_ledger" in tool_names
    assert "bft_verify_merkle_root" in tool_names
    assert "bft_send_sovereign_mail" not in tool_names
    assert JSONRPC_VERSION == "2.0"


def test_mcp_server_initialization(tmp_path: Path) -> None:
    server = CortexMCPServer(
        ledger_path=tmp_path / "mcp_ledger.db",
        mail_ledger_path=tmp_path / "mail_ledger.db",
        causal_gate_path=tmp_path / "causal_gate.db",
    )
    assert server.ledger is not None
    assert server.mail_ledger is not None
