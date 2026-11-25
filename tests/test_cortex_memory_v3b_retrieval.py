"""Deterministic test suite for V3b hybrid retrieval, VOID-VEC 1-bit, turn-window +-2 packing, and replay receipts."""

from __future__ import annotations

from collections.abc import Sequence
import sqlite3
from pathlib import Path
from typing import Any

import blake3
import numpy as np
import pytest

from babylon60.bft.cortex_crypto_kernel import _canonical_json
from babylon60.bft.cortex_persist_ledger import EventResult
import babylon60.mcp.cortex_memory_core as core
import babylon60.mcp.cortex_memory_mcp as mcp
import babylon60.mcp.cortex_retrieval_v3 as rv3
from tests.test_cortex_memory_mcp import BROKER_LIB, Client, cli


class _SemanticKeywordEmbedder:
    """Deterministic 16-dim (2-byte VOID-VEC) semantic embedder over orthogonal concept axes."""

    def embed(self, texts: Sequence[str]) -> np.ndarray:
        out: list[np.ndarray] = []
        for t in texts:
            low = t.lower()
            v = np.full(16, -0.2, dtype=np.float32)
            if any(k in low for k in ("beverage", "coffee", "espresso", "roast")):
                v[0:4] = 1.0
            if any(k in low for k in ("tea", "sencha", "kyoto", "uji")):
                v[4:8] = 1.0
            if any(k in low for k in ("workshop", "pottery", "glassblowing", "ceramics")):
                v[8:12] = 1.0
            if any(k in low for k in ("flight", "airline", "valentine", "february")):
                v[12:16] = 1.0
            out.append(v)
        return np.vstack(out)


def _append_ledger_item(
    ledger: core.CortexPersistLedger,
    *,
    req_id: str,
    value: str,
    entity: str | None = None,
    attribute: str | None = None,
    valid_from: str | None = None,
    project: str = "proj-v3b",
) -> EventResult:
    op: dict[str, Any] = {"value": value}
    if entity is not None:
        op["entity"] = entity
    if attribute is not None:
        op["attribute"] = attribute
    if valid_from is not None:
        op["valid_from"] = valid_from
    args = {"request_id": req_id, **op}
    req_digest = core.digest({"tool": "memory_append", "args": args})
    ev = core.CortexEvent(
        event_type="memory.append",
        payload={
            "request_id": req_id,
            "request_digest": req_digest,
            "op": op,
            "policy_version": 1,
            "projector": core.PROJECTOR_VERSION,
        },
        cortex_taint="binding:v3b_test",
        agent_id="agent-v3b",
        domain=core.project_domain(project),
    )
    return ledger.append_event(ev)


def test_fts_date_header_and_temporal_fts5_matching(tmp_path: Path) -> None:
    assert rv3.fts_date_header("2023-02-14T09:30:00Z") == "2023-02-14 February 2023 Feb"
    assert rv3.fts_date_header("2023-05-20T10:00:00Z") == "2023-05-20 May 2023"
    assert rv3.fts_date_header(None) == ""

    db = tmp_path / "temporal.db"
    ledger = core.CortexPersistLedger(db)
    _append_ledger_item(
        ledger,
        req_id="t-1",
        value="Booked a ticket on Delta to Atlanta.",
        entity="session:aug",
        attribute="user",
        valid_from="2023-08-10T10:00:00Z",
    )
    feb = _append_ledger_item(
        ledger,
        req_id="t-2",
        value="Booked a ticket on American Airlines to Miami.",
        entity="session:feb",
        attribute="user",
        valid_from="2023-02-14T09:00:00Z",
    )

    with sqlite3.connect(db) as conn:
        proj = core.head_projection(conn, "proj-v3b")

    # Literal search for "February" returns 0 items because "February" is only in valid_from.
    lit_view = core.query_view(proj, {"text": "February"})
    assert lit_view["items"] == []

    # V3b FTS5 mode matches "February 2023" via fts_date_header(valid_from) and ranks the Feb turn #1.
    fts_view = core.query_view(proj, {"text": "Which airline did I fly in February 2023?", "mode": "fts5", "limit": 1})
    fts_items = fts_view["items"]
    assert isinstance(fts_items, list)
    assert len(fts_items) == 1
    assert fts_items[0]["memory_id"] == feb["event_id"]


def test_role_aware_rrf_suppresses_assistant_filler_and_pins_consensus_assistant() -> None:
    emb = _SemanticKeywordEmbedder()
    # Case 1: verbose assistant essay vs short user preference -> user turn wins rank 0.
    corpus = [
        "Coffee espresso roast history encyclopedic essay " + ("filler " * 100),
        "I drink dark roast espresso every morning.",
        "Unrelated trail note.",
    ]
    roles = ["assistant", "user", "user"]
    res = rv3.role_aware_c2_rankings("What coffee beverage do I drink?", corpus, emb, roles=roles, include_void=True)
    assert res["hybrid"][0] == 1
    assert res["void_hybrid"][0] == 1

    # Case 2: single-session-assistant where the assistant turn itself is #1 lexical + top-2 semantic.
    ssa_corpus = [
        "Can you recommend a green tea?",
        "I recommend Uji sencha tea from Kyoto with steamed umami notes.",
        "I went for a walk.",
    ]
    ssa_roles = ["user", "assistant", "user"]
    ssa_res = rv3.role_aware_c2_rankings(
        "Which Uji sencha tea from Kyoto did you recommend?",
        ssa_corpus,
        emb,
        roles=ssa_roles,
        include_void=True,
    )
    assert ssa_res["fts5"][0] == 1
    assert ssa_res["hybrid"][0] == 1
    assert ssa_res["void_hybrid"][0] == 1


def test_turn_window_plus_minus_2_packing_overlap_merge_and_neighbor_cap(tmp_path: Path) -> None:
    db = tmp_path / "tw.db"
    ledger = core.CortexPersistLedger(db)
    # Session later (2023-05-20): user turn 0, huge assistant filler turn 1, user turn 2
    _append_ledger_item(
        ledger,
        req_id="s1-0",
        value="I joined a pottery workshop last week.",
        entity="session:later",
        attribute="user",
        valid_from="2023-05-20T10:00:00Z",
    )
    _append_ledger_item(
        ledger,
        req_id="s1-1",
        value="filler " * 500,
        entity="session:later",
        attribute="assistant",
        valid_from="2023-05-20T10:01:00Z",
    )
    _append_ledger_item(
        ledger,
        req_id="s1-2",
        value="The pottery glaze firing cost $45.",
        entity="session:later",
        attribute="user",
        valid_from="2023-05-20T10:02:00Z",
    )

    # Session earlier (2023-05-01): 6 turns so turn 0 and turn 5 with window=1 leave a [...] gap
    turns_earlier = [
        ("user", "I took a glassblowing workshop today."),
        ("assistant", "Sounds exciting!"),
        ("user", "Unrelated middle chat 1."),
        ("assistant", "Unrelated middle chat 2."),
        ("user", "Unrelated middle chat 3."),
        ("user", "I also spent $180 on glassblowing tools at the workshop."),
    ]
    for idx, (role, text) in enumerate(turns_earlier):
        _append_ledger_item(
            ledger,
            req_id=f"s0-{idx}",
            value=text,
            entity="session:earlier",
            attribute=role,
            valid_from="2023-05-01T09:00:00Z",
        )

    with sqlite3.connect(db) as conn:
        proj = core.head_projection(conn, "proj-v3b")

    view = core.query_view(
        proj,
        {
            "text": "What pottery and glassblowing workshops did I attend and what did tools cost?",
            "mode": "void_hybrid",
            "packing": "turn_window",
            "window": 1,
            "max_passages": 3,
            "context_budget": 4000,
            "center_budget": 600,
            "neighbor_budget": 80,
        },
        embedder=_SemanticKeywordEmbedder(),
    )
    packed = view["packed_context"]
    assert isinstance(packed, dict)
    ctx_text = str(packed["context_text"])
    assert packed["mode"] == "void_hybrid"
    assert packed["packing"] == "turn_window"
    assert packed["est_units"] <= 4000
    assert "pottery workshop" in ctx_text
    assert "glassblowing workshop" in ctx_text
    assert "$180 on glassblowing tools" in ctx_text
    assert "[...]" in ctx_text
    # Chronological across sessions: 2023-05-01 appears before 2023-05-20
    assert ctx_text.index("2023-05-01") < ctx_text.index("2023-05-20")
    # Huge assistant neighbor turn capped to neighbor_budget=80 rather than all 500 words
    assert ctx_text.count("filler") <= 90
    assert packed["context_blake3"] == blake3.blake3(ctx_text.encode("utf-8")).hexdigest()


def test_custom_embedder_semantic_order_witness_replays_and_detects_tamper(tmp_path: Path) -> None:
    db = tmp_path / "witness.db"
    ledger = core.CortexPersistLedger(db)
    _append_ledger_item(
        ledger,
        req_id="w-1",
        value="I went hiking on a rocky trail.",
        entity="session:1",
        attribute="user",
        valid_from="2023-03-01T10:00:00Z",
    )
    m2 = _append_ledger_item(
        ledger,
        req_id="w-2",
        value="I always prefer dark roast espresso every morning.",
        entity="session:2",
        attribute="user",
        valid_from="2023-03-02T10:00:00Z",
    )

    emb = _SemanticKeywordEmbedder()
    with sqlite3.connect(db) as conn:
        rows, snap, head_hash = core.load_rows(conn, "proj-v3b", None)
        proj = core.project(rows, snap, head_hash)

    raw_q = {
        "text": "What morning beverage does the user prefer?",
        "mode": "void_hybrid",
        "packing": "turn_window",
        "window": 2,
    }
    witness_q = core.attach_semantic_order(proj, raw_q, emb)
    assert witness_q["semantic_order"][0] == m2["event_id"]

    view = core.query_view(proj, witness_q)
    vdig = core.view_digest(view)
    sdig = core.state_digest(proj)

    view_items = view["items"]
    assert isinstance(view_items, list)
    rec = ledger.append_event(
        core.CortexEvent(
            event_type=core.RECEIPT_TYPE,
            payload={
                "query": witness_q,
                "snapshot_seq": snap,
                "snapshot_head_hash": head_hash,
                "snapshot_state_digest": sdig,
                "ordering": "v3b_void_hybrid_turn_window",
                "projector_version": core.PROJECTOR_VERSION,
                "policy_version": 1,
                "view_digest": vdig,
                "delivered_item_ids": [i["memory_id"] for i in view_items],
                "delivery": "recorded_before_send_unconfirmed",
                "instance_id": "inst-v3b",
                "n": 1,
            },
            cortex_taint="binding:v3b_test",
            agent_id="agent-v3b",
            domain=core.project_domain("proj-v3b"),
        )
    )

    # Offline core.replay verifies the receipt without needing the custom embedder instance.
    rep = core.replay(db)
    assert rep["chain_ok"] is True
    assert rep["receipts_checked"] == 1
    assert rep["receipt_mismatches"] == []

    # Invalid semantic_order (phantom memory_id) is flagged as a receipt mismatch during replay.
    bad_q = {**witness_q, "semantic_order": ["phantom_id", m2["event_id"]]}
    bad_rec = ledger.append_event(
        core.CortexEvent(
            event_type=core.RECEIPT_TYPE,
            payload={
                "query": bad_q,
                "snapshot_seq": snap,
                "snapshot_head_hash": head_hash,
                "snapshot_state_digest": sdig,
                "ordering": "v3b_void_hybrid_turn_window",
                "projector_version": core.PROJECTOR_VERSION,
                "policy_version": 1,
                "view_digest": vdig,
                "delivered_item_ids": [rec["event_id"]],
                "delivery": "recorded_before_send_unconfirmed",
                "instance_id": "inst-v3b",
                "n": 2,
            },
            cortex_taint="binding:v3b_test",
            agent_id="agent-v3b",
            domain=core.project_domain("proj-v3b"),
        )
    )
    rep_bad = core.replay(db)
    assert rep_bad["chain_ok"] is True
    assert rep_bad["receipt_mismatches"] == [bad_rec["event_id"]]


def test_v3b_schema_validation_and_zero_reserved_arg_collision() -> None:
    props = mcp.TOOL_SPECS["memory_read"][1]["properties"]
    assert isinstance(props, dict)
    for arg_name in props:
        assert not mcp.RESERVED_ARGS.search(arg_name), f"{arg_name} collides with RESERVED_ARGS"

    # Default literal query stays exact 4-key dict for backward compatibility.
    assert core.normalize_query({"text": "abc", "limit": 5}) == {
        "text": "abc",
        "entity": None,
        "limit": 5,
        "view": "current",
    }

    bad_cases: list[dict[str, Any]] = [
        {"mode": "unknown_mode"},
        {"packing": "session"},
        {"window": -1},
        {"window": 9},
        {"window": True},
        {"max_passages": 0},
        {"max_passages": 51},
        {"context_budget": 32},
        {"center_budget": 10},
        {"neighbor_budget": 8},
    ]
    for bad_args in bad_cases:
        with pytest.raises(ValueError):
            mcp.validate_args("memory_read", bad_args)
        with pytest.raises(ValueError):
            core.normalize_query(bad_args)


@pytest.mark.skipif(not BROKER_LIB.exists(), reason=f"native broker missing: {BROKER_LIB}")
def test_mcp_stdio_v3b_modes_turn_window_and_replay_receipts(tmp_path: Path) -> None:
    cli("keygen", "--out", str(tmp_path / "op.key"))
    cli(
        "issue-binding",
        "--key",
        str(tmp_path / "op.key"),
        "--actor",
        "agent-v3b",
        "--project",
        "proj-v3b-stdio",
        "--caps",
        "read,append,supersede,forget",
        "--out",
        str(tmp_path / "writer.json"),
    )

    c = Client(tmp_path, tmp_path / "writer.json")
    try:
        c.call(
            "memory_append",
            request_id="m-1",
            value="I signed up for a pottery workshop in Bilbao.",
            entity="session:1",
            attribute="user",
            valid_from="2026-02-10T10:00:00Z",
        )
        c.call(
            "memory_append",
            request_id="m-2",
            value="Great! Remember to bring an apron and clay tools.",
            entity="session:1",
            attribute="assistant",
            valid_from="2026-02-10T10:01:00Z",
        )
        c.call(
            "memory_append",
            request_id="m-3",
            value="I also booked a glassblowing workshop in May.",
            entity="session:2",
            attribute="user",
            valid_from="2026-05-15T14:00:00Z",
        )

        for mode in ("fts5", "hybrid", "void_hybrid"):
            res = c.call(
                "memory_read",
                text="Which workshops did I book in February and May 2026?",
                mode=mode,
                packing="turn_window",
                window=2,
                max_passages=10,
                context_budget=4000,
                center_budget=800,
                neighbor_budget=180,
            )
            assert not res["error"]
            assert len(res["items"]) == 3
            packed = res["packed_context"]
            assert packed["mode"] == mode
            assert packed["packing"] == "turn_window"
            assert packed["passage_count"] == 2
            assert "pottery workshop" in packed["context_text"]
            assert "glassblowing workshop" in packed["context_text"]
            assert "apron and clay tools" in packed["context_text"]
            expected_vdig = blake3.blake3(
                _canonical_json(
                    {
                        "items": res["items"],
                        "conflicts": res["conflicts"],
                        "packed_context": res["packed_context"],
                    }
                ).encode("utf-8")
            ).hexdigest()
            assert res["receipt"]["view_digest"] == expected_vdig
    finally:
        c.close()

    rep = core.replay(tmp_path / "ledger.db")
    assert rep["chain_ok"] is True
    assert rep["receipts_checked"] == 3
    assert rep["receipt_mismatches"] == []
