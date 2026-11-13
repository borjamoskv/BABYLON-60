"""Reject protocol false positives without replacing any Docker/runtime boundary."""

import pytest

from scripts.c5_quality_gates.smoke_docker import (
    SmokeFailure,
    checked_response,
    validate_initialize,
    validate_tools,
)


@pytest.mark.parametrize("message", [
    {"id": 1, "result": {}},
    {"jsonrpc": "2.0", "id": True, "result": {}},
    {"jsonrpc": "2.0", "id": 2, "result": {}},
    {"jsonrpc": "2.0", "id": 1, "error": {"code": -32603}, "result": {}},
    {"jsonrpc": "2.0", "id": 1, "result": None},
    {"jsonrpc": "2.0", "method": "notifications/initialized"},
])
def test_mcp_response_rejects_errors_and_unrelated_messages(message: object) -> None:
    with pytest.raises(SmokeFailure):
        checked_response(message, 1)


def test_mcp_initialize_requires_protocol_identity_and_tools_capability() -> None:
    valid = {"protocolVersion": "2024-11-05", "capabilities": {"tools": {}},
             "serverInfo": {"name": "cortex-persist-bft", "version": "5.1.0"}}
    validate_initialize(valid)
    for field, replacement in (("protocolVersion", "unknown"), ("capabilities", {}),
                               ("serverInfo", {"name": "different-server", "version": "5.1.0"})):
        with pytest.raises(SmokeFailure):
            validate_initialize({**valid, field: replacement})


def test_tools_oracle_rejects_empty_duplicate_and_invalid_descriptors() -> None:
    descriptor = {"name": "bft_query_ledger", "inputSchema": {"type": "object"}}
    assert validate_tools({"tools": [descriptor]}) == ["bft_query_ledger"]
    for tools in ([], [descriptor, descriptor], [{"name": "bft_query_ledger"}],
                  [{"name": ["unhashable"]}], ["not-a-descriptor"]):
        with pytest.raises(SmokeFailure):
            validate_tools({"tools": tools})
