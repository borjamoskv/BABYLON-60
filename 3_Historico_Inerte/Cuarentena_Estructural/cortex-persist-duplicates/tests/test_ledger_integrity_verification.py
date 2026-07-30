# [C5-REAL] Exergy-Maximized
import os

import pytest

from babylon60.ledger.models import ActionResult, ActionTarget, LedgerEvent
from babylon60.ledger.queue import EnrichmentQueue
from babylon60.ledger.store import LedgerStore
from babylon60.ledger.verifier import LedgerVerifier
from babylon60.ledger.writer import LedgerWriter


@pytest.fixture
def test_db(tmp_path):
    db_path = tmp_path / "test_ledger_integrity.db"
    return str(db_path)


def test_ledger_integrity_chain(test_db):
    store = LedgerStore(test_db)
    queue = EnrichmentQueue(store)
    writer = LedgerWriter(store, queue)
    verifier = LedgerVerifier(store)

    # 1. Append valid events
    t = ActionTarget(app="Test")
    r = ActionResult(ok=True, latency_ms=10)

    for i in range(5):
        ev = LedgerEvent.new(
            tool="cli",
            actor="test-actor",
            action=f"action-{i}",
            target=t,
            result=r,
            metadata={"project": "test-proj"},
        )
        writer.append(ev)

    # 2. Verify chain is valid
    res = verifier.verify_chain()
    assert res["valid"]
    assert res["checked_events"] == 5
    # 3. Corrupt hash (Should be impossible due to append-only triggers)
    from babylon60.ledger.store import LedgerStoreError
    import pytest

    with pytest.raises(LedgerStoreError, match="ledger is append-only: UPDATE forbidden"):
        with store.tx() as conn:
            # Find the 3rd event by rowid
            cursor = conn.execute("SELECT event_id FROM ledger_events LIMIT 1 OFFSET 2")
            ev_id = cursor.fetchone()["event_id"]
            from babylon60.database.core import causal_write

            with causal_write(conn):
                conn.execute("DROP TRIGGER IF EXISTS prevent_update_ledger_events")
                conn.execute(
                    "UPDATE ledger_events SET hash = 'BADHASH' WHERE event_id = ?", (ev_id,)
                )


def test_ledger_chain_break(test_db):
    store = LedgerStore(test_db)
    queue = EnrichmentQueue(store)
    writer = LedgerWriter(store, queue)
    verifier = LedgerVerifier(store)

    # 2 events
    t = ActionTarget(app="Test")
    r = ActionResult(ok=True, latency_ms=10)
    for i in range(2):
        ev = LedgerEvent.new(tool="cli", actor="test", action=f"a{i}", target=t, result=r)
        writer.append(ev)

    # Break the chain by altering prev_hash of the second one (Should be impossible)
    from babylon60.ledger.store import LedgerStoreError
    import pytest

    with pytest.raises(LedgerStoreError, match="ledger is append-only: UPDATE forbidden"):
        with store.tx() as conn:
            cursor = conn.execute("SELECT event_id FROM ledger_events LIMIT 1 OFFSET 1")
            ev_id = cursor.fetchone()["event_id"]
            from babylon60.database.core import causal_write

            with causal_write(conn):
                conn.execute("DROP TRIGGER IF EXISTS prevent_update_ledger_events")
                conn.execute(
                    "UPDATE ledger_events SET prev_hash = 'WRONG_PREV' WHERE event_id = ?", (ev_id,)
                )
