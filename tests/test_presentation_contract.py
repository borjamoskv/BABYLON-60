"""Presentation guidance survives CLI and MCP boundaries without transport noise."""

from __future__ import annotations

import asyncio
from importlib.resources import files
import json
import os
from pathlib import Path
import subprocess
import sys
from typing import Literal, cast

import pytest


PRESENTATION_URI = "babylon://presentation/guide"
PRESENTATION_MIME_TYPE = "text/markdown"
REPO_ROOT = Path(__file__).absolute().parents[1]


def _guide() -> str:
    text = files("babylon60").joinpath("presentation.md").read_text(encoding="utf-8")
    assert text.strip(), "The packaged presentation guide must not be empty"
    return text


def _object(value: object) -> dict[str, object]:
    assert isinstance(value, dict)
    assert all(isinstance(key, str) for key in value)
    return cast(dict[str, object], value)


def _objects(value: object) -> list[dict[str, object]]:
    assert isinstance(value, list)
    return [_object(item) for item in value]


def _subprocess_env(tmp_path: Path) -> dict[str, str]:
    env = os.environ.copy()
    env["PYTHONPATH"] = os.pathsep.join((str(REPO_ROOT / "01_KISH_ENGINE"), str(REPO_ROOT)))
    env["BABYLON_HOME"] = str(tmp_path / "home")
    env["BABYLON_CAUSAL_GATE_DB"] = str(tmp_path / "causal_gate.db")
    env["BABYLON60_MCP_CANONICAL_NAMES"] = "0"
    return env


@pytest.mark.parametrize("json_output", [False, True])
def test_cli_presentation_is_complete_and_machine_readable(tmp_path: Path, json_output: bool) -> None:
    command = [sys.executable, "-m", "babylon60.cli.main_dispatcher", "presentation"]
    if json_output:
        command.append("--json")
    result = subprocess.run(
        command,
        capture_output=True,
        text=True,
        timeout=20,
        cwd=tmp_path,
        env=_subprocess_env(tmp_path),
        check=False,
    )
    assert result.returncode == 0, result.stderr
    assert result.stderr == ""
    expected = _guide()
    if json_output:
        # Parsing the entire stream rejects banners, ANSI decoration, and trailing prose.
        payload = _object(json.loads(result.stdout))
        assert payload == {"uri": PRESENTATION_URI, "mimeType": PRESENTATION_MIME_TYPE, "text": expected}
    else:
        assert result.stdout.rstrip("\n") == expected.rstrip("\n")
    assert not (tmp_path / "home").exists()
    assert not (tmp_path / "causal_gate.db").exists()


@pytest.mark.parametrize("canonical_names", [False, True])
def test_cortex_stdio_delivers_presentation_in_both_naming_modes(tmp_path: Path, canonical_names: bool) -> None:
    command = [
        sys.executable,
        "-m",
        "babylon60.mcp.cortex_mcp_server",
        "--ledger",
        str(tmp_path / "ledger.db"),
    ]
    if canonical_names:
        command.append("--use-canonical-names")
    requests = [
        {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}},
        {"jsonrpc": "2.0", "id": 2, "method": "resources/list", "params": {}},
        {"jsonrpc": "2.0", "id": 3, "method": "resources/read", "params": {"uri": PRESENTATION_URI}},
    ]
    result = subprocess.run(
        command,
        input="".join(json.dumps(request) + "\n" for request in requests),
        capture_output=True,
        text=True,
        timeout=20,
        cwd=tmp_path,
        env=_subprocess_env(tmp_path),
        check=False,
    )
    assert result.returncode == 0, result.stderr
    responses = [_object(json.loads(line)) for line in result.stdout.splitlines()]
    assert [response.get("id") for response in responses] == [1, 2, 3]
    assert all(response.get("jsonrpc") == "2.0" and "error" not in response for response in responses)
    initialized = _object(responses[0]["result"])
    assert isinstance(initialized.get("instructions"), str)
    expected = _guide()
    assert initialized["instructions"] == expected
    resources = _objects(_object(responses[1]["result"])["resources"])
    guides = [resource for resource in resources if resource.get("uri") == PRESENTATION_URI]
    assert len(guides) == 1
    assert guides[0]["mimeType"] == PRESENTATION_MIME_TYPE
    contents = _objects(_object(responses[2]["result"])["contents"])
    assert len(contents) == 1
    assert contents[0]["uri"] == PRESENTATION_URI
    assert contents[0]["mimeType"] == PRESENTATION_MIME_TYPE
    assert contents[0]["text"] == expected


@pytest.mark.parametrize("canonical_names", [False, True])
@pytest.mark.parametrize("connection_mode", ["legacy", "auto"])
def test_kernel_client_delivers_presentation_in_both_naming_modes(
    tmp_path: Path, canonical_names: bool, connection_mode: Literal["legacy", "auto"]
) -> None:
    pytest.importorskip("fastmcp")
    from fastmcp import Client

    from tools.babylon60_mcp import KernelHarness, create_server

    harness = KernelHarness(tmp_path)

    async def exercise_client() -> None:
        server = create_server(harness, use_canonical_names=canonical_names)
        async with Client(server, mode=connection_mode) as client:
            instructions = (
                (await client.initialize()).instructions if connection_mode == "legacy" else client.instructions
            )
            assert isinstance(instructions, str)
            expected = _guide()
            assert instructions == expected
            resources = await client.list_resources()
            guides = [resource for resource in resources if str(resource.uri) == PRESENTATION_URI]
            assert len(guides) == 1
            assert guides[0].model_dump(by_alias=True)["mimeType"] == PRESENTATION_MIME_TYPE
            contents = await client.read_resource(PRESENTATION_URI)
            assert len(contents) == 1
            assert str(contents[0].uri) == PRESENTATION_URI
            assert contents[0].model_dump(by_alias=True)["mimeType"] == PRESENTATION_MIME_TYPE
            assert getattr(contents[0], "text", None) == expected

    try:
        asyncio.run(exercise_client())
    finally:
        harness.close()
