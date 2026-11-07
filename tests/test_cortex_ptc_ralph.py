# ============================================================================
# BABYLON-60 v4.0 Sovereign Hardened
# █ AUTOCOGNITION-Ω | STATE: C5-REAL | AESTHETIC: INDUSTRIAL_NOIR_2026
# ============================================================================
"""Unit suite for CORTEX PTC, Ralph Handoff, Pruner, Write-Scope Guard, and ASAR Alignment."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path
from typing import Any

import pytest

from babylon60.mcp.cortex_ptc_ralph import (
    DEFAULT_HEAD_CHARS,
    DEFAULT_TAIL_CHARS,
    DEFAULT_THRESHOLD_CHARS,
    PRUNE_MARKER,
    normalize_write_scope,
    prune_tool_result,
    render_mcp_tools_sdk_py,
    scopes_overlap,
    validate_ralph_handoff,
)

REPO_ROOT = Path(__file__).resolve().parent.parent


def test_prune_tool_result_preserves_within_threshold() -> None:
    exact = "A" * DEFAULT_THRESHOLD_CHARS
    assert prune_tool_result(exact) == exact


def test_prune_tool_result_slices_head_and_tail_deterministically() -> None:
    payload = ("H" * DEFAULT_HEAD_CHARS) + ("M" * 5000) + ("T" * DEFAULT_TAIL_CHARS)
    pruned = prune_tool_result(payload)
    assert pruned.startswith("H" * DEFAULT_HEAD_CHARS)
    assert pruned.endswith("T" * DEFAULT_TAIL_CHARS)
    assert PRUNE_MARKER in pruned
    assert len(pruned) == DEFAULT_HEAD_CHARS + len(PRUNE_MARKER) + DEFAULT_TAIL_CHARS


def test_prune_tool_result_rejects_invalid_bounds() -> None:
    with pytest.raises(ValueError, match="Invalid pruner bounds"):
        prune_tool_result("abc", threshold_chars=10, head_chars=6, tail_chars=5)
    with pytest.raises(ValueError, match="Invalid pruner bounds"):
        prune_tool_result("abc", threshold_chars=10, head_chars=-1, tail_chars=2)


def test_scopes_overlap_detects_nested_and_disjoint_paths() -> None:
    assert scopes_overlap("01_KISH_ENGINE/babylon60/mcp", "01_KISH_ENGINE/babylon60/mcp/cortex_memory_mcp.py")
    assert scopes_overlap("01_KISH_ENGINE/babylon60/mcp/", "01_KISH_ENGINE/babylon60/mcp")
    assert not scopes_overlap("01_KISH_ENGINE/babylon60/mcp", "01_KISH_ENGINE/babylon60/mcp_ext")
    assert not scopes_overlap("tests/test_a.py", "tests/test_b.py")
    assert scopes_overlap(".", "01_KISH_ENGINE/babylon60")
    assert normalize_write_scope("a//b/c/") == "a/b/c"


def test_validate_ralph_handoff_enforces_status_invariants() -> None:
    cont = validate_ralph_handoff(
        {
            "status": "continue",
            "summary": "Completed N1 schema contracts.",
            "evidence": ["tests/test_schema.py::test_ok PASS"],
            "nextSteps": ["Implement N2 CLI wiring"],
            "blocker": "",
        }
    )
    assert cont.status == "continue"
    assert cont.next_steps == ("Implement N2 CLI wiring",)

    comp = validate_ralph_handoff(
        {
            "status": "complete",
            "summary": "All DAG nodes verified.",
            "evidence": ["19/19 pytest PASS"],
            "nextSteps": [],
            "blocker": "",
        }
    )
    assert comp.status == "complete"
    assert comp.to_dict()["status"] == "complete"

    blk = validate_ralph_handoff(
        {
            "status": "blocked",
            "summary": "Missing hardware token.",
            "evidence": [],
            "nextSteps": [],
            "blocker": "YubiKey not inserted",
        }
    )
    assert blk.status == "blocked"


@pytest.mark.parametrize(
    "bad_report,match",
    [
        (
            {
                "status": "continue",
                "summary": "ok",
                "evidence": [],
                "nextSteps": [],
                "blocker": "",
            },
            "needs nextSteps",
        ),
        (
            {
                "status": "complete",
                "summary": "ok",
                "evidence": [],
                "nextSteps": [],
                "blocker": "",
            },
            "needs evidence",
        ),
        (
            {
                "status": "complete",
                "summary": "ok",
                "evidence": ["pass"],
                "nextSteps": ["leftover"],
                "blocker": "",
            },
            "no nextSteps",
        ),
        (
            {
                "status": "blocked",
                "summary": "ok",
                "evidence": [],
                "nextSteps": [],
                "blocker": "",
            },
            "concrete blocker",
        ),
        (
            {
                "status": "continue",
                "summary": "  untrimmed  ",
                "evidence": [],
                "nextSteps": ["step"],
                "blocker": "",
            },
            "summary must be non-empty and normalized",
        ),
        (
            {
                "status": "continue",
                "summary": "ok",
                "evidence": [],
                "nextSteps": ["step"],
                "blocker": "",
                "extraField": 1,
            },
            "keys mismatch",
        ),
    ],
)
def test_validate_ralph_handoff_rejects_violations(bad_report: dict[str, object], match: str) -> None:
    with pytest.raises(ValueError, match=match):
        validate_ralph_handoff(bad_report)


def test_validate_ralph_handoff_enforces_size_cap() -> None:
    with pytest.raises(ValueError, match="exceeds maxHandoffChars"):
        validate_ralph_handoff(
            {
                "status": "continue",
                "summary": "S" * 300,
                "evidence": [],
                "nextSteps": ["next"],
                "blocker": "",
            },
            max_handoff_chars=120,
        )


def test_emit_ptc_sdk_cli_and_renderer() -> None:
    proc = subprocess.run(
        [sys.executable, "-m", "babylon60.mcp.cortex_memory_mcp", "emit-ptc-sdk"],
        cwd=REPO_ROOT / "01_KISH_ENGINE",
        capture_output=True,
        text=True,
        check=True,
    )
    out = proc.stdout
    assert "class ToolsSDK(Protocol):" in out
    assert "async def memory_read(" in out
    assert "memory_append" not in out

    proc_all = subprocess.run(
        [sys.executable, "-m", "babylon60.mcp.cortex_memory_mcp", "emit-ptc-sdk", "--include-write"],
        cwd=REPO_ROOT / "01_KISH_ENGINE",
        capture_output=True,
        text=True,
        check=True,
    )
    assert "async def memory_append(" in proc_all.stdout
    assert "async def memory_forget(" in proc_all.stdout
    assert render_mcp_tools_sdk_py([]).endswith("    pass\n")


def test_asar_pickle_4byte_alignment_formula() -> None:
    from scripts.forensics.c5_dsh_inspector import compute_asar_base_offset

    # Verified values from DeepSeek Harness 0.2.2-rc.1 app.asar:
    # u2 = 5748756, json_size = 5748746 (5748746 % 4 == 2 -> +2 padding bytes)
    base = compute_asar_base_offset(5748756, 5748746)
    assert base == 5748764
    assert base - (16 + 5748746) == 2


def test_cortex_mcp_server_emit_ptc_sdk_and_pruner(tmp_path: Path) -> None:
    from babylon60.mcp.cortex_mcp_server import CortexMCPServer

    proc = subprocess.run(
        [sys.executable, "-m", "babylon60.mcp.cortex_mcp_server", "--emit-ptc-sdk"],
        cwd=REPO_ROOT / "01_KISH_ENGINE",
        capture_output=True,
        text=True,
        check=True,
    )
    assert "class ToolsSDK(Protocol):" in proc.stdout
    assert "async def bft_query_ledger(" in proc.stdout
    assert "async def skills_discover(" in proc.stdout

    proc_canon = subprocess.run(
        [sys.executable, "-m", "babylon60.mcp.cortex_mcp_server", "--emit-ptc-sdk", "--use-canonical-names"],
        cwd=REPO_ROOT / "01_KISH_ENGINE",
        capture_output=True,
        text=True,
        check=True,
    )
    assert "async def cortex_ledger_query(" in proc_canon.stdout

    server = CortexMCPServer(ledger_path=tmp_path / "ledger.db", causal_gate_path=tmp_path / "gate.db")
    assert "async def bft_query_ledger(" in server.emit_ptc_sdk()

    oversized_payload: dict[str, Any] = {
        "content": [{"type": "text", "text": ("A" * 5000) + ("B" * 5000) + ("C" * 1024)}],
        "isError": False,
    }
    pruned_res = server._prune_tool_response(oversized_payload, {})
    pruned_text = pruned_res["content"][0]["text"]
    assert PRUNE_MARKER in pruned_text
    assert pruned_text.startswith("A" * DEFAULT_HEAD_CHARS)
    assert pruned_text.endswith("C" * DEFAULT_TAIL_CHARS)

    # Verify opt-out via _meta["babylon60/prune"] = False
    unpruned_res = server._prune_tool_response(oversized_payload, {"babylon60/prune": False})
    assert unpruned_res["content"][0]["text"] == oversized_payload["content"][0]["text"]


def test_blackboard_dispatch_write_scope_collision_guard(tmp_path: Path) -> None:
    import inspect
    import json

    from babylon60.mcp.cortex_mcp_server import CortexMCPServer

    server = CortexMCPServer(ledger_path=tmp_path / "ledger.db", causal_gate_path=tmp_path / "gate.db")
    raw_bb = inspect.unwrap(CortexMCPServer._tool_blackboard_dispatch)
    bb_db = str(tmp_path / "bb_wal.db")

    # 1. Agent A publishes a PATCH_PROPOSAL on directory scope `01_KISH_ENGINE/babylon60/mcp`
    res1 = raw_bb(
        server,
        {
            "operation": "publish",
            "task_id": "task-dag-1",
            "logical_tick": 1,
            "topic": "PATCH_PROPOSAL",
            "author_agent_id": "agent-alpha",
            "target_path": "01_KISH_ENGINE/babylon60/mcp",
            "claim": "Refactor MCP transport",
            "db_path": bb_db,
        },
    )
    assert res1["isError"] is False
    assert json.loads(res1["content"][0]["text"])["admitted"] is True

    # 2. Agent B attempts to publish a PATCH_PROPOSAL on nested file `01_KISH_ENGINE/babylon60/mcp/cortex_mcp_server.py`
    res2 = raw_bb(
        server,
        {
            "operation": "publish",
            "task_id": "task-dag-1",
            "logical_tick": 2,
            "topic": "PATCH_PROPOSAL",
            "author_agent_id": "agent-beta",
            "target_path": "01_KISH_ENGINE/babylon60/mcp/cortex_mcp_server.py",
            "claim": "Concurrent edit on server",
            "db_path": bb_db,
        },
    )
    assert res2["isError"] is True
    body2 = json.loads(res2["content"][0]["text"])
    assert body2["admitted"] is False
    assert "WRITE_SCOPE_COLLISION" in body2["reason"]

    # 3. Agent B publishes on a disjoint path `01_KISH_ENGINE/babylon60/bft/cortex_persist_ledger.py` -> admitted
    res3 = raw_bb(
        server,
        {
            "operation": "publish",
            "task_id": "task-dag-1",
            "logical_tick": 3,
            "topic": "PATCH_PROPOSAL",
            "author_agent_id": "agent-beta",
            "target_path": "01_KISH_ENGINE/babylon60/bft/cortex_persist_ledger.py",
            "claim": "Disjoint edit on BFT ledger",
            "db_path": bb_db,
        },
    )
    assert res3["isError"] is False
    assert json.loads(res3["content"][0]["text"])["admitted"] is True


def test_blackboard_dispatch_ralph_handoff_gate(tmp_path: Path) -> None:
    import inspect
    import json

    from babylon60.mcp.cortex_mcp_server import CortexMCPServer

    server = CortexMCPServer(ledger_path=tmp_path / "ledger.db", causal_gate_path=tmp_path / "gate.db")
    raw_bb = inspect.unwrap(CortexMCPServer._tool_blackboard_dispatch)
    bb_db = str(tmp_path / "bb_handoff.db")

    valid_claim = json.dumps(
        {
            "status": "continue",
            "summary": "Round 1 verified schema invariants",
            "evidence": ["pytest 16/16 PASS"],
            "nextSteps": ["Wire round 2 handoff"],
            "blocker": "",
        }
    )
    ok_res = raw_bb(
        server,
        {
            "operation": "handoff",
            "task_id": "task-ralph-1",
            "logical_tick": 1,
            "author_agent_id": "ralph-worker-1",
            "claim": valid_claim,
            "db_path": bb_db,
        },
    )
    assert ok_res["isError"] is False
    ok_body = json.loads(ok_res["content"][0]["text"])
    assert ok_body["admitted"] is True
    assert ok_body["ralph_handoff"]["status"] == "continue"
    assert ok_body["tuple"]["claim"].startswith("[RALPH:CONTINUE] Round 1 verified schema invariants")

    # Invalid handoff (status=complete with non-empty nextSteps) must be rejected deterministically
    invalid_claim = json.dumps(
        {
            "status": "complete",
            "summary": "Premature completion",
            "evidence": ["partial"],
            "nextSteps": ["still pending work"],
            "blocker": "",
        }
    )
    bad_res = raw_bb(
        server,
        {
            "operation": "handoff",
            "task_id": "task-ralph-1",
            "logical_tick": 2,
            "author_agent_id": "ralph-worker-1",
            "claim": invalid_claim,
            "db_path": bb_db,
        },
    )
    assert bad_res["isError"] is True
    bad_body = json.loads(bad_res["content"][0]["text"])
    assert bad_body["admitted"] is False
    assert "RALPH_HANDOFF_INVALID" in bad_body["reason"]


def test_prune_tool_response_preserves_valid_json_and_handles_partial_bounds(tmp_path: Path) -> None:
    import json

    from babylon60.mcp.cortex_mcp_server import CortexMCPServer

    server = CortexMCPServer(ledger_path=tmp_path / "ledger.db", causal_gate_path=tmp_path / "gate.db")

    # 1. Oversized structured JSON payload must remain valid JSON after pruning
    large_json_doc = {
        "admitted": True,
        "status": "committed",
        "tuple_id": "abc123",
        "items": [f"entry-{i}-" + ("X" * 120) for i in range(100)],
    }
    raw_json_response = {
        "content": [{"type": "text", "text": json.dumps(large_json_doc)}],
        "isError": False,
    }
    pruned_json_res = server._prune_tool_response(raw_json_response, {})
    parsed_after_prune = json.loads(pruned_json_res["content"][0]["text"])
    assert parsed_after_prune["_pruned"] is True
    assert parsed_after_prune["admitted"] is True
    assert parsed_after_prune["status"] == "committed"
    assert PRUNE_MARKER in parsed_after_prune["pruned_preview"]

    # 2. Partial _meta["babylon60/prune"] with only threshold_chars < 5120 must not raise post-dispatch
    partial_meta = {"babylon60/prune": {"threshold_chars": 1200}}
    partial_res = server._prune_tool_response(raw_json_response, partial_meta)
    parsed_partial = json.loads(partial_res["content"][0]["text"])
    assert parsed_partial["_pruned"] is True

    # 3. Malformed _meta["babylon60/prune"] values must fall back safely without raising
    malformed_meta = {"babylon60/prune": {"threshold_chars": "not-an-int", "head_chars": True}}
    fallback_res = server._prune_tool_response(raw_json_response, malformed_meta)
    assert json.loads(fallback_res["content"][0]["text"])["_pruned"] is True


def test_scopes_overlap_and_blackboard_prevent_abs_handoff_and_toctou_bypasses(tmp_path: Path) -> None:
    from concurrent.futures import ThreadPoolExecutor
    import inspect
    import json
    import threading

    from babylon60.mcp.cortex_mcp_server import CortexMCPServer

    # 1. Relative vs. absolute workspace path & wildcard '.' vs. absolute path must overlap
    abs_target = str(REPO_ROOT / "01_KISH_ENGINE" / "babylon60" / "mcp" / "cortex_mcp_server.py")
    assert scopes_overlap("01_KISH_ENGINE/babylon60/mcp", abs_target)
    assert scopes_overlap(".", abs_target)
    assert scopes_overlap("../BABYLON-60/01_KISH_ENGINE/babylon60/mcp", abs_target)

    server = CortexMCPServer(ledger_path=tmp_path / "ledger.db", causal_gate_path=tmp_path / "gate.db")
    raw_bb = inspect.unwrap(CortexMCPServer._tool_blackboard_dispatch)
    bb_db = str(tmp_path / "bb_atomic.db")

    # 2. Concurrent publish race under BEGIN IMMEDIATE: exactly 1 admitted, 1 rejected with WRITE_SCOPE_COLLISION
    barrier = threading.Barrier(2)

    def _worker(agent_id: str, target: str, tick: int) -> dict[str, object]:
        barrier.wait(timeout=5.0)
        out = raw_bb(
            server,
            {
                "operation": "publish",
                "task_id": "task-race-1",
                "logical_tick": tick,
                "topic": "PATCH_PROPOSAL",
                "author_agent_id": agent_id,
                "target_path": target,
                "claim": f"Patch by {agent_id}",
                "db_path": bb_db,
            },
        )
        return json.loads(out["content"][0]["text"])

    with ThreadPoolExecutor(max_workers=2) as pool:
        f1 = pool.submit(_worker, "agent-1", "01_KISH_ENGINE/babylon60/mcp", 1)
        f2 = pool.submit(_worker, "agent-2", abs_target, 2)
        results = [f1.result(), f2.result()]

    admitted_count = sum(1 for r in results if r["admitted"] is True)
    collision_count = sum(1 for r in results if "WRITE_SCOPE_COLLISION" in str(r.get("reason", "")))
    assert admitted_count == 1
    assert collision_count == 1

    # 3. Handoff operation with topic=PATCH_PROPOSAL on colliding scope must also be blocked
    handoff_res = raw_bb(
        server,
        {
            "operation": "handoff",
            "task_id": "task-race-1",
            "logical_tick": 3,
            "topic": "PATCH_PROPOSAL",
            "author_agent_id": "agent-3",
            "target_path": "01_KISH_ENGINE/babylon60/mcp",
            "handoff_report": {
                "status": "continue",
                "summary": "Attempt handoff bypass on locked scope",
                "evidence": ["unit test"],
                "nextSteps": ["commit patch"],
                "blocker": "",
            },
            "db_path": bb_db,
        },
    )
    assert handoff_res["isError"] is True
    handoff_body = json.loads(handoff_res["content"][0]["text"])
    assert handoff_body["admitted"] is False
    assert "WRITE_SCOPE_COLLISION" in handoff_body["reason"]
