"""Presence conformance vectors; the projected client below is a TEST reference.

Exercises the production renderer and JSON-RPC framing with an in-memory synthetic
tool. It does not certify a deployed PTC client, OpenAI, stdio pipes or a ledger.
The vector layout borrows description/schema/tests/data from JSON Schema Test
Suite, adding independent argument and state oracles instead of a new validator.
"""

from __future__ import annotations

import asyncio
from copy import deepcopy
import inspect
from io import StringIO
import json
from pathlib import Path
from typing import Any

import pytest

from babylon60.mcp.cortex_mcp_server import CortexMCPServer
from babylon60.mcp.cortex_ptc_ralph import render_mcp_tools_sdk_py


VECTORS = json.loads((Path(__file__).parent / "fixtures" / "cortex_ptc_presence.json").read_text(encoding="utf-8"))
CASES = VECTORS["tests"]


class NoteServer(CortexMCPServer):
    """Synthetic test tool using CORTEX framing, with no production effects.

    Deliberately initializes only the request handler needed by this fixture:
    no production tool is registered and no ledger or authorization is opened.
    """

    def __init__(self, initial_state: dict[str, Any]) -> None:
        self.state = deepcopy(initial_state)
        self.received: list[dict[str, Any]] = []
        self._request_handlers = {"tools/call": self.update_note}

    def update_note(self, params: dict[str, object]) -> dict[str, object]:
        assert params["name"] == VECTORS["tool"]
        arguments = params["arguments"]
        assert isinstance(arguments, dict)
        self.received.append(deepcopy(arguments))
        if "nota" in arguments:
            self.state["nota"] = arguments["nota"]
        # Intentionally identical success replies, regardless of the effect.
        return {"content": [{"type": "text", "text": "ok"}], "isError": False}


def call_direct(server: NoteServer, arguments: dict[str, Any]) -> dict[str, Any]:
    """Cross a real JSON encoding/decoding boundary, using in-memory streams."""
    request = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "tools/call",
        "params": {"name": VECTORS["tool"], "arguments": arguments},
    }
    inbound = StringIO(json.dumps(request) + "\n")
    frame = server._read_message(inbound)
    assert frame is not None
    response = server.handle_frame(frame)
    assert response is not None
    outbound = StringIO()
    server._write_message(response, outbound)
    return json.loads(outbound.getvalue())


@pytest.fixture
def projected_signature() -> inspect.Signature:
    source = render_mcp_tools_sdk_py(
        [{"name": VECTORS["tool"], "description": VECTORS["description"], "inputSchema": VECTORS["schema"]}]
    )
    namespace: dict[str, Any] = {}
    # Only a fixed, repository-owned fixture is compiled; no model output.
    exec(compile(source, "<presence-sdk>", "exec"), namespace)  # noqa: S102
    method = getattr(namespace["ToolsSDK"], VECTORS["tool"])
    assert inspect.iscoroutinefunction(method)
    return inspect.signature(method)


class ProjectedReferenceClient:
    """Test-only consumer: bind the generated signature, forward supplied keys.

    CORTEX emits a Protocol, not this client. Keeping the reference explicit
    prevents these tests from masquerading as an actual PTC integration test.
    """

    def __init__(self, server: NoteServer, signature: inspect.Signature) -> None:
        self.server = server
        self.signature = signature

    async def update_note(self, **kwargs: Any) -> dict[str, Any]:
        bound = self.signature.bind(self, **kwargs)
        arguments = dict(bound.arguments)
        del arguments["self"]
        # Do not apply defaults: omitted and explicitly None must stay distinct.
        return call_direct(self.server, arguments)


@pytest.mark.parametrize("case", CASES, ids=lambda case: case["description"])
def test_direct_and_reference_projection_preserve_intent(
    case: dict[str, Any], projected_signature: inspect.Signature
) -> None:
    # Separate fresh state for each route, even when a prior vector cleared it.
    direct = NoteServer(case["initial_state"])
    projected = NoteServer(case["initial_state"])
    assert direct.state == projected.state == {"nota": "original"}

    direct_response = call_direct(direct, deepcopy(case["data"]))
    client = ProjectedReferenceClient(projected, projected_signature)
    projected_response = asyncio.run(client.update_note(**deepcopy(case["data"])))

    for server, response in ((direct, direct_response), (projected, projected_response)):
        assert "error" not in response
        assert response["result"]["isError"] is False
        assert server.received == [case["expected_arguments"]]
        assert server.state == case["expected_state"]
    assert direct.received == projected.received
    assert direct.state == projected.state


@pytest.mark.parametrize(
    "intent,mutation",
    [("preserve", "materialize_none"), ("clear", "drop_none"), ("empty", "drop_falsy")],
)
def test_oracles_detect_loss_despite_identical_ok_responses(intent: str, mutation: str) -> None:
    """Negative controls, not findings about any production serializer."""
    case = next(case for case in CASES if case["description"] == intent)
    arguments = deepcopy(case["data"])
    if mutation == "materialize_none":
        arguments.setdefault("nota", None)
    elif mutation == "drop_none":
        arguments = {key: value for key, value in arguments.items() if value is not None}
    else:
        arguments = {key: value for key, value in arguments.items() if value}

    direct = NoteServer(case["initial_state"])
    lossy = NoteServer(case["initial_state"])
    assert call_direct(direct, case["data"]) == call_direct(lossy, arguments)
    assert direct.received == [case["expected_arguments"]]
    assert direct.state == case["expected_state"]
    assert lossy.received != [case["expected_arguments"]]
    assert lossy.state != case["expected_state"]
