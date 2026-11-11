"""Chained confinement journal: integrity, append-only storage and determinism."""

from __future__ import annotations

import math
from pathlib import Path
import sqlite3
import threading

import pytest

from babylon60.confine.journal import GENESIS, ConfineJournal, JournalError, canonical, digest


def _raw(path: Path) -> sqlite3.Connection:
    conn = sqlite3.connect(str(path), isolation_level=None)
    conn.execute("DROP TRIGGER IF EXISTS confine_events_no_update")
    conn.execute("DROP TRIGGER IF EXISTS confine_events_no_delete")
    return conn


def test_chain_verifies_and_head_matches(tmp_path: Path) -> None:
    with ConfineJournal(tmp_path / "j.db") as journal:
        first = journal.append("session_start", {"policy": "a" * 64})
        second = journal.append("session_end", {"exit_code": 0})
        assert first.prev == GENESIS and second.prev == first.digest
        assert (first.logical_tick, second.logical_tick) == (1, 2)
        assert journal.head() == (second.seq, second.digest)
        result = journal.verify()
        assert result.ok and result.events == 2 and result.head == second.digest


def test_full_sync_and_wal_are_enforced(tmp_path: Path) -> None:
    with ConfineJournal(tmp_path / "j.db") as journal:
        assert journal._conn.execute("PRAGMA synchronous").fetchone()[0] == 2
        assert journal._conn.execute("PRAGMA journal_mode").fetchone()[0] == "wal"


def test_rows_cannot_be_updated_or_deleted(tmp_path: Path) -> None:
    with ConfineJournal(tmp_path / "j.db") as journal:
        journal.append("session_start", {})
        with pytest.raises(sqlite3.DatabaseError, match="append-only"):
            journal._conn.execute("UPDATE confine_events SET body='{}'")
        with pytest.raises(sqlite3.DatabaseError, match="append-only"):
            journal._conn.execute("DELETE FROM confine_events")


def test_tampered_body_is_located(tmp_path: Path) -> None:
    path = tmp_path / "j.db"
    with ConfineJournal(path) as journal:
        for code in range(3):
            journal.append("vector", {"code": code})
    conn = _raw(path)
    conn.execute("UPDATE confine_events SET body=? WHERE seq=2", ('{"code":99}',))
    conn.close()
    with ConfineJournal(path) as journal:
        result = journal.verify()
    assert not result.ok and result.first_invalid_seq == 2
    assert result.reason == "digest does not match body"


def test_deleted_event_breaks_the_link(tmp_path: Path) -> None:
    path = tmp_path / "j.db"
    with ConfineJournal(path) as journal:
        for code in range(3):
            journal.append("vector", {"code": code})
    conn = _raw(path)
    conn.execute("DELETE FROM confine_events WHERE seq=2")
    conn.close()
    with ConfineJournal(path) as journal:
        result = journal.verify()
    assert not result.ok and result.first_invalid_seq == 3


def test_wall_clock_metadata_is_outside_the_digest(tmp_path: Path) -> None:
    path = tmp_path / "j.db"
    with ConfineJournal(path) as journal:
        entry = journal.append("session_start", {"k": 1})
    expected = digest({"kind": "session_start", "logical_tick": 1, "prev": GENESIS, "body": {"k": 1}})
    assert entry.digest == expected
    conn = _raw(path)
    conn.execute("UPDATE confine_events SET recorded_at='1970-01-01T00:00:00+00:00'")
    conn.close()
    with ConfineJournal(path) as journal:
        assert journal.verify().ok


@pytest.mark.parametrize("value", [{"x": math.nan}, {"x": math.inf}, {1: "a"}, {"x": object()}])
def test_canonical_rejects_ambiguous_values(value: object) -> None:
    with pytest.raises(JournalError):
        canonical(value)


def test_canonical_respects_size_limit() -> None:
    with pytest.raises(JournalError):
        canonical({"x": "a" * 100}, limit=50)


def test_concurrent_appends_stay_contiguous(tmp_path: Path) -> None:
    path = tmp_path / "j.db"
    ConfineJournal(path).close()
    errors: list[BaseException] = []

    def writer(name: str) -> None:
        try:
            with ConfineJournal(path) as journal:
                for index in range(25):
                    journal.append("vector", {"writer": name, "index": index})
        except BaseException as exc:  # noqa: BLE001 - surfaced through the assertion below
            errors.append(exc)

    threads = [threading.Thread(target=writer, args=(str(n),)) for n in range(4)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()
    assert not errors
    with ConfineJournal(path) as journal:
        result = journal.verify()
        ticks = [entry.logical_tick for entry in journal.entries()]
    assert result.ok and result.events == 100
    assert ticks == list(range(1, 101))


def test_entries_limit_returns_the_tail(tmp_path: Path) -> None:
    with ConfineJournal(tmp_path / "j.db") as journal:
        for index in range(5):
            journal.append("vector", {"index": index})
        assert [e.body["index"] for e in journal.entries(limit=2)] == [3, 4]
        assert journal.entries(limit=0) == []


def test_append_many_writes_one_contiguous_chained_batch(tmp_path: Path) -> None:
    with ConfineJournal(tmp_path / "j.db") as journal:
        journal.append("session_start", {})
        batch = journal.append_many([("vector", {"index": index}) for index in range(5)])
        assert [entry.logical_tick for entry in batch] == [2, 3, 4, 5, 6]
        assert all(later.prev == earlier.digest for earlier, later in zip(batch, batch[1:]))
        assert journal.append_many([]) == []
        assert journal.verify().ok and journal.head()[1] == batch[-1].digest


def test_failed_batch_leaves_no_partial_events(tmp_path: Path) -> None:
    with ConfineJournal(tmp_path / "j.db") as journal:
        journal.append("session_start", {})
        with pytest.raises(JournalError):
            journal.append_many([("vector", {"ok": 1}), ("vector", {"bad": math.nan})])
        assert journal.verify().events == 1
