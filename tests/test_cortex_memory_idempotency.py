"""Idempotency intent/receipt contract through real MCP, SIGKILL and SQLite."""

from __future__ import annotations

import json
from pathlib import Path
import shutil

import blake3
import pytest

import babylon60.mcp.cortex_memory_core as core
from test_cortex_memory_mcp import BROKER_LIB, Client, cli, ledger_rows, ws as ws

pytestmark = pytest.mark.skipif(
    not BROKER_LIB.exists(), reason=f"native broker missing: {BROKER_LIB} (adapter is fail-closed)"
)


@pytest.fixture
def idempotency_ws(tmp_path: Path, ws: Path) -> Path:
    """Reuse only test authority files; each case gets an empty durable ledger."""
    for name in ("op.key.pub", "writer.json"):
        shutil.copy2(ws / name, tmp_path / name)
    return tmp_path


@pytest.mark.parametrize("conflict_first", [False, True], ids=["retry-first", "conflict-first"])
def test_request_id_binds_receipt_to_original_intent(idempotency_ws: Path, conflict_first: bool) -> None:
    ws = idempotency_ws
    args = {
        "request_id": "R1",
        "value": "idioma preferido: euskera",
        "entity": "user",
        "attribute": "preferred_language",
    }
    crashed = Client(ws, ws / "writer.json", crash="after_commit_before_ack")
    try:
        with pytest.raises(EOFError):
            crashed.call("memory_append", **args)
        crashed.proc.wait(timeout=10)
        assert crashed.proc.returncode == -9
    finally:
        crashed.close()

    writes_sql = (
        "SELECT seq, event_id, entry_hash, payload_json, event_type, agent_id, domain "
        "FROM cortex_ledger WHERE event_type IN ('memory.append','memory.supersede','memory.forget') "
        "ORDER BY seq"
    )
    original_rows = ledger_rows(ws, writes_sql)
    assert len(original_rows) == 1
    seq, memory_id, entry_hash, payload_json, event_type, actor, domain = original_rows[0]
    original = json.loads(payload_json)
    assert (event_type, actor, domain) == ("memory.append", "agent-a", core.project_domain("proj-p"))
    assert original["request_id"] == "R1"
    assert original["op"] == {
        "value": "idioma preferido: euskera",
        "entity": "user",
        "attribute": "preferred_language",
    }
    # Independently bind the receipt's row to the original operation and arguments.
    canonical = json.dumps(
        {"tool": "memory_append", "args": args}, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode("utf-8")
    assert original["projector"] == core.PROJECTOR_VERSION
    assert original["request_digest"] == blake3.blake3(canonical).hexdigest()

    client = Client(ws, ws / "writer.json")

    def retry(reordered: bool = False) -> None:
        retry_args = dict(reversed(list(args.items()))) if reordered else args
        if reordered:
            assert json.dumps(retry_args) != json.dumps(args)
        envelope = client.rpc("tools/call", {"name": "memory_append", "arguments": retry_args})["result"]
        result = envelope["structuredContent"]
        assert envelope["isError"] is False
        assert json.loads(envelope["content"][0]["text"]) == result
        assert {key: result[key] for key in ("status", "replayed", "memory_id", "seq", "entry_hash")} == {
            "status": "committed",
            "replayed": True,
            "memory_id": memory_id,
            "seq": seq,
            "entry_hash": entry_hash,
        }

    try:
        if not conflict_first:
            retry()
        for tool, changed_args in (
            ("memory_append", {**args, "value": "idioma preferido: castellano"}),
            ("memory_append", {**args, "attribute": "secondary_language"}),
            ("memory_supersede", {**args, "target": memory_id}),
        ):
            envelope = client.rpc("tools/call", {"name": tool, "arguments": changed_args})["result"]
            denied = envelope["structuredContent"]
            assert envelope["isError"] is True
            assert denied["status"] == "denied"
            assert denied["reason"] == "request_id already used with different content"
            # Neither MCP representation may pass off the old receipt as new success.
            assert set(denied) == {"status", "reason", "served_by"}
            assert json.loads(envelope["content"][0]["text"]) == denied
            assert ledger_rows(ws, writes_sql) == original_rows
        retry()
        retry(reordered=True)
        assert ledger_rows(ws, writes_sql) == original_rows
    finally:
        client.close()


@pytest.mark.parametrize("scope_change", ["actor", "project"])
def test_request_id_is_scoped_to_actor_and_project(idempotency_ws: Path, ws: Path, scope_change: str) -> None:
    isolated = idempotency_ws
    cli(
        "issue-binding",
        "--key",
        str(ws / "op.key"),
        "--actor",
        "agent-b" if scope_change == "actor" else "agent-a",
        "--project",
        "proj-q" if scope_change == "project" else "proj-p",
        "--caps",
        "read,append",
        "--out",
        str(isolated / "other-scope.json"),
    )
    receipts = []
    for binding, value in (
        ("writer.json", "idioma preferido: euskera"),
        ("other-scope.json", "idioma preferido: castellano"),
    ):
        client = Client(isolated, isolated / binding)
        try:
            result = client.call("memory_append", request_id="R1", value=value)
            assert result["error"] is False and result["status"] == "committed"
            assert result["replayed"] is False
            replayed = client.call("memory_append", request_id="R1", value=value)
            assert replayed == {**result, "replayed": True}
            receipts.append(result["memory_id"])
        finally:
            client.close()
    assert len(set(receipts)) == 2
    rows = ledger_rows(
        isolated,
        "SELECT event_id, agent_id, domain, json_extract(payload_json,'$.op.value') "
        "FROM cortex_ledger WHERE event_type='memory.append' ORDER BY seq",
    )
    assert rows == [
        (receipts[0], "agent-a", core.project_domain("proj-p"), "idioma preferido: euskera"),
        (
            receipts[1],
            "agent-b" if scope_change == "actor" else "agent-a",
            core.project_domain("proj-q" if scope_change == "project" else "proj-p"),
            "idioma preferido: castellano",
        ),
    ]
