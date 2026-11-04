"""Isolated ledger retrieval regression and durability checks."""

import sqlite3
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import cast

import pytest

from babylon60.bft.cortex_persist_ledger import CortexEvent, CortexPersistLedger


def _seq(row: dict[str, object]) -> int:
    seq = row["seq"]
    assert isinstance(seq, int)
    return seq


def _event(number: int, **payload: object) -> CortexEvent:
    return CortexEvent(
        event_type="LESSON" if number % 2 else "ATTEMPT",
        payload={"number": number, "skill_id": "verify", "context": "code", "status": "validated", **payload},
        cortex_taint=f"isolated-test:{number}",
        agent_id="query-tests",
    )


def test_filters_precede_limit_and_paginate_across_interleaved_scopes(tmp_path: Path) -> None:
    ledger = CortexPersistLedger(tmp_path / "pages.db")
    events = []
    for number in range(151):
        payload = {}
        if number % 3 == 0:
            payload["skill_id"] = "other"
        if number % 5 == 0:
            payload["context"] = "deployment"
        if number % 7 == 0:
            payload["status"] = "candidate"
        events.append(_event(number, **payload))
    written = ledger.append_batch(events)
    expected = [
        result["seq"]
        for event, result in reversed(list(zip(events, written)))
        if event.event_type == "LESSON"
        and event.payload["skill_id"] == "verify"
        and event.payload["context"] == "code"
        and event.payload["status"] == "validated"
    ]
    found: list[int] = []
    before_seq = None
    while True:
        page = ledger.query_events(
            event_type="LESSON",
            skill_id="verify",
            context="code",
            status="validated",
            limit=7,
            before_seq=before_seq,
        )
        if not page:
            break
        assert len(page) == min(7, len(expected) - len(found))
        found.extend(_seq(row) for row in page)
        before_seq = _seq(page[-1])
    assert len(expected) > 14
    assert found == expected
    assert len(found) == len(set(found))


def test_individual_filters_are_exact_and_preserve_event_evidence(tmp_path: Path) -> None:
    ledger = CortexPersistLedger(tmp_path / "scope.db")
    expected = ledger.append_event(_event(1))
    ledger.append_batch(
        [
            _event(2, skill_id="verify-extra"),
            _event(3, context="code-extra"),
            _event(4, status="validated-extra"),
            _event(5, skill_id=None, context=1, status=True),
        ]
    )
    rows = ledger.query_events(event_type="LESSON", skill_id="verify", context="code", status="validated")
    assert len(rows) == 1
    row = rows[0]
    assert row["seq"] == expected["seq"]
    assert row["event_id"] == expected["event_id"]
    assert row["entry_hash"] == expected["entry_hash"]
    assert row["lamport_t"] == expected["lamport_t"]
    assert row["event_type"] == "LESSON"
    assert row["payload"] == _event(1).payload
    assert row["cortex_taint"] == "isolated-test:1"
    assert row["agent_id"] == "query-tests"
    assert row["timestamp"]
    assert [r["seq"] for r in ledger.query_events(skill_id="verify-extra")] == [2]
    assert [r["seq"] for r in ledger.query_events(context="code-extra")] == [3]
    assert [r["seq"] for r in ledger.query_events(status="validated-extra")] == [4]
    assert ledger.query_events(context="1") == []
    assert ledger.query_events(status="true") == []


def test_injection_values_are_bound_and_empty_strings_are_exact(tmp_path: Path) -> None:
    ledger = CortexPersistLedger(tmp_path / "bound.db")
    injection = "' OR 1=1; DROP TABLE cortex_ledger; --"
    written = ledger.append_event(
        CortexEvent(
            event_type=injection,
            payload={"skill_id": injection, "context": "", "status": injection},
            cortex_taint="isolated-test:injection",
        )
    )
    ledger.append_event(_event(1))
    assert [
        row["seq"]
        for row in ledger.query_events(
            event_type=injection,
            skill_id=injection,
            context="",
            status=injection,
        )
    ] == [written["seq"]]
    assert ledger.query_events(skill_id="absent' OR 1=1 --") == []
    assert len(ledger.query_events()) == 2
    assert ledger.verify_integrity()


@pytest.mark.parametrize("field", ["event_type", "skill_id", "context", "status"])
@pytest.mark.parametrize("value", [True, 1, 1.2, [], {}])
def test_filter_types_are_validated(tmp_path: Path, field: str, value: object) -> None:
    ledger = CortexPersistLedger(tmp_path / "invalid-filter.db")
    with pytest.raises(TypeError, match=field):
        # Casts deliberately exercise runtime boundaries with invalid input.
        invalid = cast(str, value)
        if field == "event_type":
            ledger.query_events(event_type=invalid)
        elif field == "skill_id":
            ledger.query_events(skill_id=invalid)
        elif field == "context":
            ledger.query_events(context=invalid)
        else:
            ledger.query_events(status=invalid)


@pytest.mark.parametrize("value", [True, False, 1.2, "10", None])
def test_limit_rejects_non_integer_values(tmp_path: Path, value: object) -> None:
    ledger = CortexPersistLedger(tmp_path / "invalid-limit.db")
    with pytest.raises(TypeError, match="limit"):
        ledger.query_events(limit=cast(int, value))


@pytest.mark.parametrize("value", [0, -1, 1001, 2**64])
def test_limit_bounds_are_validated(tmp_path: Path, value: int) -> None:
    ledger = CortexPersistLedger(tmp_path / "limit-bounds.db")
    with pytest.raises(ValueError, match="limit"):
        ledger.query_events(limit=value)


@pytest.mark.parametrize("value", [True, False, 1.2, "10", [], {}])
def test_cursor_rejects_non_integer_values(tmp_path: Path, value: object) -> None:
    ledger = CortexPersistLedger(tmp_path / "invalid-cursor.db")
    with pytest.raises(TypeError, match="before_seq"):
        ledger.query_events(before_seq=cast(int, value))


@pytest.mark.parametrize("value", [0, -1, 2**63])
def test_cursor_bounds_are_validated(tmp_path: Path, value: int) -> None:
    ledger = CortexPersistLedger(tmp_path / "cursor-bounds.db")
    with pytest.raises(ValueError, match="before_seq"):
        ledger.query_events(before_seq=value)


def test_reopening_preserves_history_hashes_and_append_only_durability(tmp_path: Path) -> None:
    path = tmp_path / "reopen.db"
    first_session = CortexPersistLedger(path)
    first_session.append_batch([_event(number) for number in range(12)])
    evidence = first_session.query_events(limit=1000)
    root = first_session.get_merkle_root()
    del first_session
    second_session = CortexPersistLedger(path)
    assert second_session.query_events(limit=1000) == evidence
    assert second_session.get_merkle_root() == root
    assert second_session.verify_integrity()
    second_session.append_event(_event(100))
    assert second_session.query_events(before_seq=13, limit=1000) == evidence
    with second_session._get_connection() as connection:
        assert connection.execute("PRAGMA journal_mode").fetchone()[0] == "wal"
        assert connection.execute("PRAGMA synchronous").fetchone()[0] == 2
        for mutation in ("DELETE FROM cortex_ledger", "UPDATE cortex_ledger SET agent_id = 'changed'"):
            with pytest.raises(sqlite3.IntegrityError, match="CortexPersistLedger"):
                connection.execute(mutation)
    assert second_session.verify_integrity()


def test_warmup_and_repeated_paged_retrieval_with_appends(tmp_path: Path) -> None:
    """Modest isolated functional stress; no physical performance guarantee."""
    path = tmp_path / "stress.db"
    ledger = CortexPersistLedger(path)
    ledger.append_batch([_event(number, context="warmup") for number in range(20)])
    for _ in range(5):
        assert len(ledger.query_events(context="warmup", limit=20)) == 20
    for batch in range(5):
        ledger.append_batch(
            [
                _event(20 + batch * 200 + number, context="target" if number % 4 == 0 else "noise")
                for number in range(200)
            ]
        )
        ledger = CortexPersistLedger(path)
        rows = []
        before_seq = None
        while True:
            page = ledger.query_events(context="target", limit=31, before_seq=before_seq)
            if not page:
                break
            rows.extend(page)
            before_seq = _seq(page[-1])
        assert len(rows) == (batch + 1) * 50
        for row in rows:
            payload = row["payload"]
            assert isinstance(payload, dict)
            assert payload["context"] == "target"
        assert [_seq(row) for row in rows] == sorted({_seq(row) for row in rows}, reverse=True)
    assert ledger.verify_integrity()


def test_transition_precondition_rolls_back_and_serializes_concurrent_writers(tmp_path: Path) -> None:
    ledger = CortexPersistLedger(tmp_path / "transitions.db")
    # Warm the actual SQLite path before concurrent functional stress.
    ledger.append_event(_event(0, context="warmup"))
    ledger.query_events(context="warmup")
    before = ledger.get_merkle_root()

    def reject() -> None:
        raise ValueError("rejected transition")

    with pytest.raises(ValueError, match="rejected transition"):
        ledger.append_event(_event(100), precondition=reject)
    assert ledger.get_merkle_root() == before

    def append_once(number: int) -> bool:
        def unique_transition() -> None:
            if ledger.query_events(context="single-transition"):
                raise ValueError("already present")

        try:
            ledger.append_event(_event(number, context="single-transition"), precondition=unique_transition)
        except ValueError as error:
            assert str(error) == "already present"
            return False
        return True

    with ThreadPoolExecutor(max_workers=8) as pool:
        committed = list(pool.map(append_once, range(1, 33)))
    assert sum(committed) == 1
    assert len(ledger.query_events(context="single-transition")) == 1
    assert ledger.verify_integrity()
