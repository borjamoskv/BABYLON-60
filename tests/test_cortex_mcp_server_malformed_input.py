"""Malformed-input regressions for the CORTEX MCP servers.

Covers: stdio frame handling (parse error / invalid request / blank lines) and numeric
tool arguments in ``cortex_mcp_server``; anchored identifiers and real calendar dates in
``cortex_memory_mcp``. An input error must never execute anything.
"""

import inspect
import io
import json
from pathlib import Path
from typing import Any, cast

import pytest
from babylon60.mcp import cortex_memory_mcp as memory_mcp
from babylon60.mcp.cortex_mcp_server import CortexMCPServer


def _server(tmp_path: Path) -> CortexMCPServer:
    return CortexMCPServer(
        ledger_path=tmp_path / "ledger.db",
        mail_ledger_path=tmp_path / "mail.db",
        causal_gate_path=tmp_path / "causal.db",
    )


def _run_stdio(server: CortexMCPServer, monkeypatch: pytest.MonkeyPatch, raw: str) -> list[dict[str, Any]]:
    out = io.StringIO()
    monkeypatch.setattr("sys.stdin", io.StringIO(raw))
    monkeypatch.setattr("sys.stdout", out)
    server.run_stdio()
    return [json.loads(line) for line in out.getvalue().splitlines() if line.strip()]


def _ledger_rows(server: CortexMCPServer) -> int:
    with server.ledger._get_connection() as conn:
        return int(conn.execute("SELECT COUNT(*) FROM cortex_ledger").fetchone()[0])


def _call(server: CortexMCPServer, name: str, arguments: dict[str, object]) -> dict[str, Any]:
    response = server.process_request(
        {"jsonrpc": "2.0", "id": 1, "method": "tools/call", "params": {"name": name, "arguments": arguments}}
    )
    assert response is not None
    return cast(dict[str, Any], response["result"])


PING = '{"jsonrpc":"2.0","id":7,"method":"ping"}\n'


# --------------------------------------------------------------------------- stdio loop


def test_stdio_non_json_line_returns_parse_error_and_server_survives(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    server = _server(tmp_path)
    before = _ledger_rows(server)
    frames = _run_stdio(server, monkeypatch, "{broken\n" + PING)
    assert [f["id"] for f in frames] == [None, 7]
    assert frames[0]["error"]["code"] == -32700
    assert "error" not in frames[1]
    assert _ledger_rows(server) == before


@pytest.mark.parametrize("frame", ["[1,2]", '"text"', "42", "null", "true", "[]"])
def test_stdio_non_object_json_returns_invalid_request_and_server_survives(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, frame: str
) -> None:
    server = _server(tmp_path)
    before = _ledger_rows(server)
    frames = _run_stdio(server, monkeypatch, frame + "\n" + PING)
    assert [f["id"] for f in frames] == [None, 7]
    assert frames[0]["error"]["code"] == -32600
    assert _ledger_rows(server) == before


def test_stdio_blank_lines_are_ignored_not_eof(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    frames = _run_stdio(_server(tmp_path), monkeypatch, "\n   \n\t\n" + PING + "\n" + PING)
    assert [f["id"] for f in frames] == [7, 7]
    assert all("error" not in f for f in frames)


def test_stdio_deeply_nested_json_is_parse_error_not_crash(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    frames = _run_stdio(_server(tmp_path), monkeypatch, "[" * 200_000 + "\n" + PING)
    assert frames[0]["error"]["code"] == -32700
    assert frames[1]["id"] == 7


def test_stdio_malformed_batch_with_effect_tool_executes_nothing(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    server = _server(tmp_path)
    before = _ledger_rows(server)
    call = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "tools/call",
        "params": {"name": "bft_append_event", "arguments": {"event_type": "x", "payload": {"a": 1}}},
    }
    raw = json.dumps([call]) + "\n" + json.dumps(call)[:-1] + "\n"
    frames = _run_stdio(server, monkeypatch, raw)
    assert [f["error"]["code"] for f in frames] == [-32600, -32700]
    assert _ledger_rows(server) == before


# --------------------------------------------------------------------------- numeric arguments


@pytest.mark.parametrize("limit", ["x", "5", -1, 0, True, False, 1.5, None, [1], 10**9])
def test_query_ledger_rejects_invalid_limit(tmp_path: Path, limit: object) -> None:
    server = _server(tmp_path)
    for i in range(3):
        server.ledger.append_event(_event(i))
    result = _call(server, "bft_query_ledger", {"limit": limit})
    assert result["isError"] is True
    text = result["content"][0]["text"]
    assert "limit" in text
    assert "entry_hash" not in text


def test_query_ledger_valid_limit_still_works(tmp_path: Path) -> None:
    server = _server(tmp_path)
    for i in range(3):
        server.ledger.append_event(_event(i))
    result = _call(server, "bft_query_ledger", {"limit": 2})
    assert result["isError"] is False
    assert json.loads(result["content"][0]["text"])["total_returned"] == 2
    default = _call(server, "bft_query_ledger", {})
    assert default["isError"] is False
    assert json.loads(default["content"][0]["text"])["total_returned"] == 3


@pytest.mark.parametrize("tick", ["x", True, -1, 1.5, None])
def test_blackboard_dispatch_rejects_invalid_logical_tick(tmp_path: Path, tick: object) -> None:
    server = _server(tmp_path)
    db_path = tmp_path / "bb" / "wal.db"
    raw_bb = inspect.unwrap(CortexMCPServer._tool_blackboard_dispatch)  # validation only; mediation untouched
    result = raw_bb(server, {"operation": "poll", "task_id": "t", "logical_tick": tick, "db_path": str(db_path)})
    assert result["isError"] is True
    assert "logical_tick" in cast(list[dict[str, str]], result["content"])[0]["text"]
    assert not db_path.parent.exists()


def _event(i: int) -> Any:
    from babylon60.bft.cortex_persist_ledger import CortexEvent

    return CortexEvent(
        event_type="probe",
        payload={"i": i},
        cortex_taint="test",
        agent_id="tester",
        domain="test",
    )


# --------------------------------------------------------------------------- cortex_memory_mcp


@pytest.mark.parametrize("request_id", ["abc\n", "\nabc", "abc\r", "a b", "", "a" * 129])
def test_memory_request_id_rejects_trailing_newline_and_garbage(request_id: str) -> None:
    assert memory_mcp.REQUEST_ID.match(request_id) is None


def test_memory_request_id_accepts_valid() -> None:
    assert memory_mcp.REQUEST_ID.match("req-1.a:b_C")
    assert memory_mcp.REQUEST_ID.match("a" * 128)


@pytest.mark.parametrize(
    "stamp",
    [
        "2026-01-01T00:00:00Z\n",
        "9999-99-99T99:99:99Z",
        "2026-02-30T00:00:00Z",
        "2025-02-29T00:00:00Z",
        "2026-13-01T00:00:00Z",
        "2026-01-01T24:00:00Z",
        "2026-01-01T00:60:00Z",
        "2026-01-01T00:00:60Z",
        "0000-01-01T00:00:00Z",
        "٢٠٢٦-01-01T00:00:00Z",
    ],
)
def test_memory_valid_from_rejects_impossible_or_unanchored_dates(stamp: str) -> None:
    with pytest.raises(ValueError, match="valid_from must be ISO-8601 UTC"):
        memory_mcp.Adapter._op_fields({"value": "v", "valid_from": stamp})


def test_memory_valid_dates_still_accepted() -> None:
    op = memory_mcp.Adapter._op_fields(
        {"value": "v", "valid_from": "2024-02-29T23:59:59Z", "valid_to": "9999-12-31T00:00:00Z"}
    )
    assert op["valid_from"] == "2024-02-29T23:59:59Z"
    assert op["valid_to"] == "9999-12-31T00:00:00Z"
