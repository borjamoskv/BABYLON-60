from __future__ import annotations

import sqlite3

import pytest

from apex_trials.ledger import GENESIS_PREV_HASH, AmendmentLedger, BabylonBFTLedgerAdapter


def _payload(score: int) -> dict[str, object]:
    return {"nct_id": "NCT00000001", "score": score, "features": {"a": 1, "b": [1, 2, 3]}}


def test_genesis_and_chain_linkage(tmp_path) -> None:
    db = tmp_path / "l.db"
    with AmendmentLedger(db) as led:
        e0 = led.append(_payload(10), "agent:t0")
        e1 = led.append(_payload(20), "agent:t1")
        assert e0.prev_hash == GENESIS_PREV_HASH
        assert e0.lamport_t == 1 and e1.lamport_t == 2
        assert e1.prev_hash == e0.entry_hash
        v = led.verify_chain()
        assert v.valid and v.entries == 2 and (v.broken_at is None)


def test_determinism_same_inputs_same_hash(tmp_path) -> None:
    with AmendmentLedger(tmp_path / "a.db") as a, AmendmentLedger(tmp_path / "b.db") as b:
        ha = a.append(_payload(42), "agent:x").entry_hash
        hb = b.append(_payload(42), "agent:x").entry_hash
        assert ha == hb


def test_key_order_independence(tmp_path) -> None:
    with AmendmentLedger(tmp_path / "a.db") as a, AmendmentLedger(tmp_path / "b.db") as b:
        p1 = {"score": 5, "nct_id": "X", "z": 1}
        p2 = {"z": 1, "nct_id": "X", "score": 5}
        assert a.append(p1, "agent:x").entry_hash == b.append(p2, "agent:x").entry_hash


def test_idempotency(tmp_path) -> None:
    with AmendmentLedger(tmp_path / "l.db") as led:
        first = led.append(_payload(7), "agent:same")
        again = led.append(_payload(7), "agent:same")
        assert first.id == again.id
        assert led.count() == 1


def test_causal_taint_mandatory(tmp_path) -> None:
    with AmendmentLedger(tmp_path / "l.db") as led:
        with pytest.raises(ValueError):
            led.append(_payload(1), "")
        with pytest.raises(ValueError):
            led.append(_payload(1), "no-colon-here")


def test_tamper_detection(tmp_path) -> None:
    db = tmp_path / "l.db"
    with AmendmentLedger(db) as led:
        led.append(_payload(10), "agent:t0")
        led.append(_payload(20), "agent:t1")
        assert led.verify_chain().valid
    conn = sqlite3.connect(db)
    conn.execute("DROP TRIGGER IF EXISTS trg_ledger_immutable_update;")
    conn.execute("UPDATE ledger_entries SET payload_json = ? WHERE seq = 1;", ('{"score":9999}',))
    conn.commit()
    conn.close()
    with AmendmentLedger(db) as led:
        v = led.verify_chain()
        assert not v.valid and v.broken_at == 1 and ("Hash mismatch" in (v.reason or ""))


def test_babylon_bft_ledger_adapter() -> None:

    class MockActor:
        def __init__(self):
            self.events = []

        def append(self, event):
            self.events.append(event)
            return "mock-future"

    mock = MockActor()
    adapter = BabylonBFTLedgerAdapter(mock)
    res = adapter.append({"nct_id": "NCT99999999", "score": 42}, "apex:test")
    assert res == "mock-future"
    assert len(mock.events) == 1
    assert mock.events[0].stream == "apex_trials"
    assert mock.events[0].entity_id == "NCT99999999"
    assert mock.events[0].cortex_taint == "apex:test"
