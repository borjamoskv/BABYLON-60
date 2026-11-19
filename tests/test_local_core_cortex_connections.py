"""Observe real SQLite ownership without relying on garbage collection."""

import sqlite3
from contextlib import closing

import pytest

from babylon60.bft.cortex_persist_ledger import CortexEvent, CortexPersistLedger


def event(index):
    return CortexEvent("LOCAL_TEST", {"index": index}, f"local-test:{index}")


@pytest.fixture
def ledger(tmp_path):
    instance = CortexPersistLedger(tmp_path / "ledger.db")
    instance.append_event(event(1))
    return instance


@pytest.fixture
def connections(monkeypatch):
    connect = sqlite3.connect
    opened = []

    def observe(*args, **kwargs):
        connection = connect(*args, **kwargs)
        opened.append(connection)
        return connection

    monkeypatch.setattr(sqlite3, "connect", observe)
    try:
        yield opened
    finally:
        for connection in opened:
            connection.close()


def assert_closed(connections):
    assert connections
    for connection in connections:
        with pytest.raises(sqlite3.ProgrammingError, match="closed"):
            connection.execute("SELECT 1")


@pytest.mark.parametrize(
    "method,args",
    [
        ("_init_db", ()),
        ("query_events", ()),
        ("append_event", (event(2),)),
        ("append_batch", ([event(2), event(3)],)),
        ("verify_integrity", ()),
        ("get_merkle_root", ()),
        ("get_event_proof", (1,)),
        ("get_mmr", ()),
        ("get_mmr_root", ()),
        ("get_mmr_event_proof", (1,)),
        ("get_state_attestation", ()),
    ],
)
def test_owned_connections_close_before_return(ledger, connections, method, args):
    getattr(ledger, method)(*args)
    assert_closed(connections)


@pytest.mark.parametrize("failure_index", [1, 2, 3])
def test_configuration_failure_closes_connection(ledger, connections, monkeypatch, failure_index):
    observe = sqlite3.connect

    def denied(*args, **kwargs):
        connection = observe(*args, **kwargs)
        seen = 0

        def authorize(action, *unused):
            nonlocal seen
            if action == sqlite3.SQLITE_PRAGMA:
                seen += 1
                if seen == failure_index:
                    return sqlite3.SQLITE_DENY
            return sqlite3.SQLITE_OK

        connection.set_authorizer(authorize)
        return connection

    monkeypatch.setattr(sqlite3, "connect", denied)
    with pytest.raises(sqlite3.DatabaseError, match="authorized"):
        ledger.query_events()
    assert_closed(connections)


def test_query_failure_closes_connection(ledger, connections, monkeypatch):
    observe = sqlite3.connect

    def denied(*args, **kwargs):
        connection = observe(*args, **kwargs)
        connection.set_authorizer(
            lambda action, *unused: sqlite3.SQLITE_DENY if action == sqlite3.SQLITE_SELECT else sqlite3.SQLITE_OK
        )
        return connection

    monkeypatch.setattr(sqlite3, "connect", denied)
    with pytest.raises(sqlite3.DatabaseError, match="authorized"):
        ledger.query_events()
    assert_closed(connections)


def test_failed_batch_closes_connection_and_preserves_committed_history(ledger, connections):
    with pytest.raises(ValueError, match="INV_BFT_03"):
        ledger.append_batch([event(2), CortexEvent("INVALID", {}, "")])
    assert_closed(connections)
    with closing(sqlite3.connect(ledger.db_path)) as observer:
        assert observer.execute("SELECT seq FROM cortex_ledger").fetchall() == [(1,)]


def test_external_connection_remains_owned_by_caller(ledger):
    connection = ledger._get_connection()
    try:
        connection.execute("BEGIN IMMEDIATE")
        ledger.append_event(event(2), connection=connection)
        assert connection.in_transaction
        assert connection.execute("SELECT COUNT(*) FROM cortex_ledger").fetchone()[0] == 2
        connection.rollback()
        assert connection.execute("SELECT COUNT(*) FROM cortex_ledger").fetchone()[0] == 1
    finally:
        connection.close()
