"""
Unit tests for BABYLON-60 Phase 3 Enterprise & MCP Components.
Verifies HMAC license key generation, offline validation, and MCP protocol tools initialization.
"""

import os
import subprocess
import sys
import tempfile
import pytest
from babylon60.guards.license_sovereign_validator import (
    generate_license_key,
    verify_license_key,
    LicenseStatus
)
from babylon60.mcp.cortex_mcp_server import CortexMCPServer, TOOLS, JSONRPC_VERSION


def test_enterprise_license_generation_and_verification():
    os.environ["BABYLON60_LICENSE_SALT"] = "test_sovereign_salt_999"
    
    # 1. Test community fallback (empty key)
    community_status = verify_license_key("")
    assert community_status.tier == "community"
    assert community_status.is_valid is False

    # 2. Test valid Enterprise key generation
    expires = 1956528000  # Year 2032
    key = generate_license_key(owner="TestCorp", tier="enterprise", expires_at=expires)
    
    # 3. Test verification of valid key
    valid_status: LicenseStatus = verify_license_key(key)
    assert valid_status.is_valid is True
    assert valid_status.owner == "TestCorp"
    assert valid_status.tier == "enterprise"
    assert valid_status.expires_at == expires

    # 4. Test tampering resistance
    tampered_key = key[:-4] + "0000"
    tampered_status = verify_license_key(tampered_key)
    assert tampered_status.is_valid is False
    assert tampered_status.tier == "invalid"


def test_mcp_server_tools_definition():
    tool_names = [t["name"] for t in TOOLS]
    assert "bft_append_event" in tool_names
    assert "bft_query_ledger" in tool_names
    assert "bft_verify_merkle_root" in tool_names
    assert "bft_send_sovereign_mail" in tool_names
    assert JSONRPC_VERSION == "2.0"


def test_mcp_server_initialization():
    with tempfile.TemporaryDirectory() as tmpdir:
        ledger_path = os.path.join(tmpdir, "mcp_ledger.db")
        mail_path = os.path.join(tmpdir, "mail_ledger.db")
        
        server = CortexMCPServer(
            ledger_path=ledger_path,
            mail_ledger_path=mail_path
        )
        assert server.ledger is not None
        assert server.mail_ledger is not None
