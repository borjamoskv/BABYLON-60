"""Regressions for the 2026-11-12 CORTEX persistence audit.

JSON memory (core/cortex_persist.py) runs against a temporary HOME; the SQLite
ledger (bft/cortex_persist_ledger.py) against temporary databases.
"""

from __future__ import annotations

import errno
import fcntl
import importlib.util
import json
import os
import sqlite3
import stat
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

from babylon60.bft.cortex_persist_ledger import (
    CortexEvent,
    CortexPersistFacade,
    CortexPersistLedger,
    IntegrityVerdict,
)

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "01_KISH_ENGINE/babylon60/core/cortex_persist.py"


@pytest.fixture
def memory(tmp_path, monkeypatch):
    home = tmp_path / "home"
    base = home / ".agent/memory"
    (base / "projects").mkdir(parents=True)
    (base / "snapshots").mkdir()
    (base / "projects/alpha.json").write_text(json.dumps({"meta": {}, "recent_changes": [], "decisions": []}))
    (base / "ghosts.json").write_text("{}")
    (base / "system.json").write_text(json.dumps({"meta": {}, "sessions_log": []}))
    monkeypatch.setenv("HOME", str(home))
    spec = importlib.util.spec_from_file_location("cortex_persist_hardening_fixture", SOURCE)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    monkeypatch.setitem(sys.modules, spec.name, module)
    spec.loader.exec_module(module)

    def delta(label):
        return module.SessionDelta("task " + label, "fixture.py", label, ["change " + label], ["decision " + label])

    def read(relative):
        return json.loads((base / relative).read_text())

    return SimpleNamespace(module=module, base=base, delta=delta, read=read)


def archive_lines(memory):
    path = memory.base / "snapshots" / memory.module.CortexOntologyLedger.RETENTION_ARCHIVE
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


# --- JSON memory: writers that do not take the lock -------------------------


@pytest.mark.parametrize("atomic", [False, True], ids=["in-place", "replace"])
def test_external_write_between_read_and_write_is_not_overwritten(memory, monkeypatch, atomic):
    cls = memory.module.CortexOntologyLedger
    target = memory.base / "projects/alpha.json"
    original = cls._read_json
    fired: list[str] = []

    def read(self, path):
        value = original(self, path)
        if path.endswith("alpha.json") and not fired:
            fired.append(path)
            data = json.loads(target.read_text())
            data["external_note"] = "another process"
            if atomic:
                staged = target.with_suffix(".external")
                staged.write_text(json.dumps(data))
                os.replace(staged, target)
            else:
                target.write_text(json.dumps(data))
        return value

    monkeypatch.setattr(cls, "_read_json", read)
    with pytest.raises(memory.module.ConsolidationError) as caught:
        cls("alpha").crystallize_session(memory.delta("A"))
    assert caught.value.replacement_state == "NOT_ATTEMPTED" and caught.value.completed_files == ()
    stored = memory.read("projects/alpha.json")
    assert stored["external_note"] == "another process" and "ghost" not in stored
    assert memory.read("ghosts.json") == {} and memory.read("system.json")["sessions_log"] == []


def test_session_without_interference_still_commits_all_files(memory):
    memory.module.CortexOntologyLedger("alpha").crystallize_session(memory.delta("A"))
    assert memory.read("projects/alpha.json")["ghost"]["last_conversation"] == "A"
    assert set(memory.read("ghosts.json")) == {"alpha"}
    assert memory.read("system.json")["sessions_log"][0]["conversation_id"] == "A"


def test_lock_wait_is_bounded(memory, monkeypatch):
    cls = memory.module.CortexOntologyLedger
    ledger = cls("alpha")
    monkeypatch.setattr(cls, "LOCK_TIMEOUT_SECONDS", 0.2)
    holder = os.open(memory.base / ".cortex-persist.lock", os.O_RDWR | os.O_CREAT, 0o600)
    try:
        fcntl.flock(holder, fcntl.LOCK_EX)
        with pytest.raises(memory.module.ConsolidationError) as caught:
            ledger.crystallize_session(memory.delta("A"))
        assert isinstance(caught.value.__cause__, TimeoutError)
        assert "ghost" not in memory.read("projects/alpha.json")
    finally:
        os.close(holder)
    ledger.crystallize_session(memory.delta("A"))
    assert memory.read("projects/alpha.json")["ghost"]["last_conversation"] == "A"


# --- JSON memory: project IDs that alias one file ---------------------------


def test_project_id_reaching_its_file_by_name_folding_is_rejected(memory):
    if not (memory.base / "projects/ALPHA.json").exists():
        pytest.skip("volume does not fold filename case")
    cls = memory.module.CortexOntologyLedger
    cls("alpha").crystallize_session(memory.delta("lower"))
    with pytest.raises(ValueError, match="case or normalization"):
        cls("ALPHA")
    assert set(memory.read("ghosts.json")) == {"alpha"}
    assert os.listdir(memory.base / "projects") == ["alpha.json"]


def test_alias_introduced_after_construction_is_rejected_at_use(memory):
    if not (memory.base / "projects/ALPHA.json").exists():
        pytest.skip("volume does not fold filename case")
    ledger = memory.module.CortexOntologyLedger("alpha")
    os.rename(memory.base / "projects/alpha.json", memory.base / "projects/Alpha.json")
    with pytest.raises(memory.module.ConsolidationError):
        ledger.crystallize_session(memory.delta("A"))
    assert memory.read("ghosts.json") == {} and "ghost" not in memory.read("projects/Alpha.json")


def test_project_without_a_file_yet_still_constructs(memory):
    memory.module.CortexOntologyLedger("not-created-yet")


# --- JSON memory: bounded lists ---------------------------------------------


def test_entries_leaving_bounded_lists_are_archived(memory):
    ledger = memory.module.CortexOntologyLedger("alpha")
    for index in range(32):
        ledger.crystallize_session(memory.delta(str(index)))
    kept_changes = {row["desc"] for row in memory.read("projects/alpha.json")["recent_changes"]}
    kept_sessions = {row["conversation_id"] for row in memory.read("system.json")["sessions_log"]}
    lines = archive_lines(memory)
    assert {line["project"] for line in lines} == {"alpha"}
    archived_changes = {line["entry"]["desc"] for line in lines if line["source"] == "recent_changes"}
    archived_sessions = {line["entry"]["conversation_id"] for line in lines if line["source"] == "sessions_log"}
    assert len(kept_changes) == 10 and len(kept_sessions) == 30
    assert kept_changes | archived_changes == {f"change {index}" for index in range(32)}
    assert kept_sessions | archived_sessions == {str(index) for index in range(32)}
    assert not kept_changes & archived_changes and not kept_sessions & archived_sessions


def test_archive_failure_leaves_the_list_untruncated(memory):
    project = memory.base / "projects/alpha.json"
    history = [{"ts": "t", "desc": f"old {index}"} for index in range(10)]
    project.write_text(json.dumps({"meta": {}, "recent_changes": history, "decisions": []}))
    archive = memory.base / "snapshots" / memory.module.CortexOntologyLedger.RETENTION_ARCHIVE
    archive.symlink_to(memory.base / "elsewhere.jsonl")  # Refused: the archive is opened without following links.
    with pytest.raises(memory.module.ConsolidationError) as caught:
        memory.module.CortexOntologyLedger("alpha").crystallize_session(memory.delta("new"))
    assert caught.value.completed_files == ()
    assert memory.read("projects/alpha.json")["recent_changes"] == history
    assert not (memory.base / "elsewhere.jsonl").exists()


def test_torn_archive_tail_does_not_absorb_the_next_record(memory):
    project = memory.base / "projects/alpha.json"
    history = [{"ts": "t", "desc": f"old {index}"} for index in range(10)]
    project.write_text(json.dumps({"meta": {}, "recent_changes": history, "decisions": []}))
    archive = memory.base / "snapshots" / memory.module.CortexOntologyLedger.RETENTION_ARCHIVE
    archive.write_text('{"archived_at": "torn')
    memory.module.CortexOntologyLedger("alpha").crystallize_session(memory.delta("new"))
    lines = archive.read_text().splitlines()
    assert lines[0] == '{"archived_at": "torn'
    assert json.loads(lines[1])["entry"] == {"ts": "t", "desc": "old 9"}


# --- JSON memory: durability request ----------------------------------------


@pytest.mark.skipif(not hasattr(fcntl, "F_FULLFSYNC"), reason="F_FULLFSYNC is Darwin-only")
def test_write_requests_a_full_flush_of_file_and_directory(memory, monkeypatch):
    real = fcntl.fcntl
    flushed = []

    def recording(descriptor, command, *args):
        if command == getattr(fcntl, "F_FULLFSYNC", None):
            flushed.append(stat.S_ISDIR(os.fstat(descriptor).st_mode))
        return real(descriptor, command, *args)

    monkeypatch.setattr(fcntl, "fcntl", recording)
    ledger = memory.module.CortexOntologyLedger("alpha")
    ledger._write_json(str(memory.base / "projects/alpha.json"), {"value": 1})
    assert flushed == [False, True]


@pytest.mark.skipif(not hasattr(fcntl, "F_FULLFSYNC"), reason="F_FULLFSYNC is Darwin-only")
@pytest.mark.parametrize(("code", "fails"), [(errno.ENOTSUP, False), (errno.EIO, True)])
def test_full_flush_error_is_ignored_only_when_unsupported(memory, monkeypatch, code, fails):
    real = fcntl.fcntl

    def failing(descriptor, command, *args):
        if command == getattr(fcntl, "F_FULLFSYNC", None):
            raise OSError(code, os.strerror(code))
        return real(descriptor, command, *args)

    monkeypatch.setattr(fcntl, "fcntl", failing)
    ledger = memory.module.CortexOntologyLedger("alpha")
    path = str(memory.base / "projects/alpha.json")
    if fails:
        with pytest.raises(memory.module.PersistenceWriteError) as caught:
            ledger._write_json(path, {"value": 1})
        assert caught.value.replacement_state == "NOT_ATTEMPTED"
    else:
        ledger._write_json(path, {"value": 1})
        assert memory.read("projects/alpha.json") == {"value": 1}


# --- SQLite ledger ----------------------------------------------------------


def event(index):
    return CortexEvent("HARDENING", {"index": index}, "taint:hardening")


def advance_counter(database):
    with sqlite3.connect(database) as conn:
        conn.execute("UPDATE sqlite_sequence SET seq = 10 WHERE name = 'cortex_ledger'")


def stored_seqs(database):
    with sqlite3.connect(database) as conn:
        return [row[0] for row in conn.execute("SELECT seq FROM cortex_ledger ORDER BY seq")]


def test_single_append_stores_the_hashed_seq_when_counter_is_ahead(tmp_path):
    database = tmp_path / "ledger.db"
    ledger = CortexPersistLedger(database)
    ledger.append_event(event(1))
    advance_counter(database)
    assert ledger.append_event(event(2))["seq"] == 11
    assert stored_seqs(database) == [1, 11] and ledger.verify_integrity() is False


def test_batch_append_stores_the_hashed_seqs_when_counter_is_ahead(tmp_path):
    database = tmp_path / "ledger.db"
    ledger = CortexPersistLedger(database)
    ledger.append_event(event(1))
    advance_counter(database)
    results = ledger.append_batch([event(2), event(1), event(3), event(2)])
    assert [(row["seq"], row["status"]) for row in results] == [
        (11, "C5_PERMANENT"),
        (1, "DUPLICATE_IGNORED"),
        (12, "C5_PERMANENT"),
        (11, "DUPLICATE_IGNORED"),
    ]
    assert stored_seqs(database) == [1, 11, 12] and ledger.verify_integrity() is False


def test_connections_request_full_fsync(tmp_path):
    conn = CortexPersistLedger(tmp_path / "ledger.db")._get_connection()
    try:
        assert conn.execute("PRAGMA synchronous").fetchone()[0] == 2
        assert conn.execute("PRAGMA fullfsync").fetchone()[0] == 1
        assert conn.execute("PRAGMA checkpoint_fullfsync").fetchone()[0] == 1
    finally:
        conn.close()


def test_governance_connections_request_full_fsync(tmp_path):
    from babylon60.memory.governance import MemoryGovernanceEngine

    conn = MemoryGovernanceEngine(tmp_path / "memory.db")._get_connection()
    try:
        assert conn.execute("PRAGMA synchronous").fetchone()[0] == 2
        assert conn.execute("PRAGMA fullfsync").fetchone()[0] == 1
        assert conn.execute("PRAGMA checkpoint_fullfsync").fetchone()[0] == 1
    finally:
        conn.close()


async def test_ledger_actor_writer_requests_full_fsync(tmp_path, monkeypatch):
    """The pragmas are per connection, so they are read on the writer's own connection."""
    import aiosqlite

    from babylon60.bft import ledger_actor

    real_connect = aiosqlite.connect
    opened = []

    def recording_connect(*args, **kwargs):
        connection = real_connect(*args, **kwargs)
        opened.append(connection)
        return connection

    monkeypatch.setattr(aiosqlite, "connect", recording_connect)
    actor = ledger_actor.BFTLedgerActor(tmp_path / "ledger.db")
    await actor.start()
    try:
        await actor.append(
            ledger_actor.LedgerEvent(
                stream="hardening",
                entity_id="writer",
                event_type="HARDENING",
                payload={"index": 1},
                cortex_taint="taint:hardening",
                source_db="fixture",
                source_table="fixture",
                source_pk="1",
            )
        )
        writer = opened[0]
        values = {}
        for name in ("synchronous", "fullfsync", "checkpoint_fullfsync"):
            cursor = await writer.execute(f"PRAGMA {name}")
            row = await cursor.fetchone()
            assert row is not None
            values[name] = row[0]
        assert values == {"synchronous": 2, "fullfsync": 1, "checkpoint_fullfsync": 1}
    finally:
        await actor.stop()


def test_integrity_verdict_truth_follows_validity():
    failed = IntegrityVerdict(False, "CADENA_CORRUPTA")
    valid, detail = failed
    assert not failed and (valid, detail) == (False, "CADENA_CORRUPTA")
    assert IntegrityVerdict(True, "CADENA_INTEGRA")


def test_facade_verdict_and_separate_table(tmp_path):
    database = tmp_path / "facade.db"
    facade = CortexPersistFacade(database)
    facade.append_event(event(1))
    verdict = facade.verify_integrity()
    assert isinstance(verdict, IntegrityVerdict) and verdict and verdict.detail == "CADENA_INTEGRA"
    # Documented boundary: the facade's events live in the actor's table.
    assert CortexPersistLedger(database).query_events() == []
