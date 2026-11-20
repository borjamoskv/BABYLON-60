"""Production adapter over actual MCP pipes; live OpenAI is an explicit probe."""

from __future__ import annotations

from contextlib import asynccontextmanager
from copy import deepcopy
import inspect
import json
import os
from pathlib import Path
import sys
from typing import Any

import pytest
import httpx

from babylon60.mcp.cortex_openai_adapter import (
    CortexOpenAIAdapter,
    ProjectionError,
    cortex_stdio_session,
)


ROOT = Path(__file__).absolute().parents[1]
SERVER = ROOT / "tests/fixtures/cortex_openai_note_server.py"
VECTORS = json.loads((ROOT / "tests/fixtures/cortex_ptc_presence.json").read_text(encoding="utf-8"))
TOOL = {"name": VECTORS["tool"], "inputSchema": VECTORS["schema"]}


@pytest.mark.asyncio
@pytest.mark.parametrize("last_cursor", [None, "more"])
async def test_discovery_page_budget(monkeypatch, last_cursor):
    from unittest.mock import AsyncMock
    from mcp.types import ListToolsResult, Tool
    from babylon60.mcp import cortex_openai_adapter

    monkeypatch.setattr(cortex_openai_adapter, "MAX_DISCOVERY_PAGES", 2)
    session = AsyncMock()
    session.list_tools.side_effect = [
        ListToolsResult(tools=[Tool(**TOOL)], nextCursor="next"),
        ListToolsResult(tools=[], nextCursor=last_cursor),
    ]
    if last_cursor:
        with pytest.raises(ProjectionError, match="exceeded 2 pages"):
            await CortexOpenAIAdapter.discover(session, allowed_tools=[TOOL["name"]])
    else:
        await CortexOpenAIAdapter.discover(session, allowed_tools=[TOOL["name"]])
    assert session.list_tools.await_count == 2


@asynccontextmanager
async def note_session(observation: Path):
    async with cortex_stdio_session(
        sys.executable,
        [str(SERVER), "--observation", str(observation)],
        cwd=str(ROOT),
        env={"PYTHONPATH": str(ROOT / "01_KISH_ENGINE")},
    ) as session:
        yield session


def call(raw: str, **fields: Any) -> dict[str, Any]:
    return {"type": "function_call", "name": "update_note", "call_id": "test-call", "arguments": raw, **fields}


def observe(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


@pytest.mark.parametrize("vector", VECTORS["tests"], ids=lambda vector: vector["description"])
async def test_real_stdio_direct_and_projected_routes(vector: dict[str, Any], tmp_path: Path) -> None:
    direct_path, projected_path = tmp_path / "direct.json", tmp_path / "projected.json"
    async with note_session(direct_path) as direct:
        assert observe(direct_path)["state"] == vector["initial_state"]
        direct_result = await direct.call_tool("update_note", vector["data"])
    async with note_session(projected_path) as session:
        assert observe(projected_path)["state"] == vector["initial_state"]
        adapter = await CortexOpenAIAdapter.discover(session, allowed_tools=["update_note"])
        assert inspect.signature(adapter.tools.update_note).parameters["nota"].default is None
        result = await adapter.execute_function_call(call(json.dumps(vector["data"])))
    assert json.loads(result["output"])["isError"] is False
    assert direct_result.model_dump(by_alias=True)["isError"] is False
    for path in (direct_path, projected_path):
        observed = observe(path)
        assert observed["pid"] != os.getpid()
        assert observed["has_openai_key"] is False
        assert observed["received"] == [vector["expected_arguments"]]
        assert observed["state"] == vector["expected_state"]
    assert observe(direct_path)["pid"] != observe(projected_path)["pid"]


async def test_invalid_calls_never_reach_the_server(tmp_path: Path) -> None:
    path = tmp_path / "observation.json"
    invalid = [
        call("null"),
        call("[]"),
        call('{"nota": null, "nota": "changed"}'),
        call('{"nota": NaN}'),
        call('{"nota": Infinity}'),
        call('{"unknown": "value"}'),
        call("{}", name="not_allowed"),
        call("{}", status="in_progress"),
        call("{}", type="message"),
        call("{}", call_id=""),
        call("{malformed"),
        call("{}", arguments={}),
    ]
    async with note_session(path) as session:
        adapter = await CortexOpenAIAdapter.discover(session, allowed_tools=["update_note"])
        for value in invalid:
            with pytest.raises((ProjectionError, json.JSONDecodeError)):
                await adapter.execute_function_call(value)
            assert observe(path)["received"] == []
            assert observe(path)["state"] == {"nota": "original"}


async def test_schema_validation_remains_on_real_server(tmp_path: Path) -> None:
    path = tmp_path / "observation.json"
    async with note_session(path) as session:
        adapter = await CortexOpenAIAdapter.discover(session, allowed_tools=["update_note"])
        result = await adapter.execute_function_call(call('{"nota": 42}'))
    assert json.loads(result["output"])["isError"] is True
    assert observe(path)["received"] == []
    assert observe(path)["state"] == {"nota": "original"}


async def test_trusted_metadata_is_forwarded_but_model_metadata_is_not(tmp_path: Path) -> None:
    path = tmp_path / "observation.json"
    trusted = {"babylon60/authorization": {"mode": "prepare"}}
    async with note_session(path) as session:
        adapter = await CortexOpenAIAdapter.discover(session, allowed_tools=["update_note"], metadata=trusted)
        # A model-supplied top-level _meta is never a source of authority.
        value = call("{}", _meta={"babylon60/authorization": {"mode": "execute"}})
        value["caller"] = {"type": "program", "caller_id": "synthetic-program"}
        output = await adapter.execute_function_call(value)
    assert observe(path)["metadata"] == [trusted]
    assert output["caller"] == value["caller"]


async def test_discovery_rejects_missing_allowlisted_tools(tmp_path: Path) -> None:
    async with note_session(tmp_path / "observation.json") as session:
        with pytest.raises(ProjectionError, match="missing"):
            await CortexOpenAIAdapter.discover(session, allowed_tools=["not_allowed"])


@pytest.mark.parametrize("schema_type", ["string", ["string", "null"]])
def test_original_schema_is_preserved_without_strict_normalization(schema_type: Any) -> None:
    descriptor = deepcopy(TOOL)
    descriptor["inputSchema"]["properties"]["nota"]["type"] = schema_type
    adapter = CortexOpenAIAdapter(object(), [descriptor])
    emitted = adapter.openai_tools[0]
    assert emitted["parameters"] == descriptor["inputSchema"]
    assert emitted["strict"] is False
    emitted["parameters"]["required"].append("nota")
    assert adapter.openai_tools[0]["parameters"]["required"] == []


@pytest.mark.parametrize("properties", [{"a-b": {}, "a_b": {}}, {"self": {}}])
def test_property_alias_collisions_are_rejected(properties: dict[str, Any]) -> None:
    descriptor = deepcopy(TOOL)
    descriptor["inputSchema"]["properties"] = properties
    with pytest.raises(ProjectionError, match="collide"):
        CortexOpenAIAdapter(object(), [descriptor])


def test_open_schemas_and_duplicate_tool_aliases_are_rejected() -> None:
    descriptor = deepcopy(TOOL)
    descriptor["inputSchema"].pop("additionalProperties")
    with pytest.raises(ProjectionError, match="additionalProperties"):
        CortexOpenAIAdapter(object(), [descriptor])
    with pytest.raises(ProjectionError, match="Duplicate"):
        CortexOpenAIAdapter(object(), [TOOL, TOOL])


async def test_missing_required_parameter_fails_before_mcp() -> None:
    descriptor = deepcopy(TOOL)
    descriptor["inputSchema"]["required"] = ["nota"]
    adapter = CortexOpenAIAdapter(object(), [descriptor])
    with pytest.raises(TypeError, match="nota"):
        await adapter.tools.update_note()


async def test_probe_records_auth_failure_without_secrets_or_tool_effects(tmp_path: Path, monkeypatch) -> None:
    from scripts.cortex_memory.probe_openai_presence import run_probe

    marker = "synthetic-credential-do-not-record"
    monkeypatch.setenv("OPENAI_API_KEY", marker)
    requests = 0

    async def rejected_request(self, **kwargs):
        nonlocal requests
        requests += 1
        request = httpx.Request("POST", "https://api.openai.com/v1/responses", headers={"Authorization": marker})
        response = httpx.Response(
            401,
            request=request,
            json={"error": {"type": "invalid_request_error", "code": "invalid_api_key", "message": marker}},
        )
        raise httpx.HTTPStatusError(marker, request=request, response=response)

    monkeypatch.setattr(CortexOpenAIAdapter, "request_function_call", rejected_request)
    output = tmp_path / "failure.json"
    assert await run_probe("synthetic-model", output) is False
    serialized = output.read_text(encoding="utf-8")
    report = json.loads(serialized)
    assert marker not in serialized
    assert requests == 1
    assert report["errors"] == [
        {
            "type": "HTTPStatusError",
            "status_code": 401,
            "api_error_type": "invalid_request_error",
            "api_error_code": "invalid_api_key",
        }
    ]
    assert report["cases"][0]["openai"]["received"] == []
    assert report["cases"][0]["openai"]["state"] == {"nota": "original"}
    assert report["cases"][0]["openai"]["response_ok"] is False
