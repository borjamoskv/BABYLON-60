"""C15: replay and migration retain a verifiable logical-clock hash chain."""

from datetime import datetime, tzinfo
from pathlib import Path
import sqlite3

import pytest

from babylon60.bft import cortex_persist_ledger as persistence
from babylon60.bft.cortex_crypto_kernel import ZERO_HASH_256, compute_cortex_hash
from babylon60.bft.cortex_persist_ledger import CortexEvent, CortexPersistLedger
from babylon60.verifier.standalone_verify import verify_offline_evidence


class EarlierClock(datetime):
    @classmethod
    def now(cls, tz: tzinfo | None = None) -> "EarlierClock":
        return cls(2020, 1, 1, tzinfo=tz)


class LaterClock(datetime):
    @classmethod
    def now(cls, tz: tzinfo | None = None) -> "LaterClock":
        return cls(2030, 1, 1, tzinfo=tz)


def _events() -> list[CortexEvent]:
    return [CortexEvent("TEST", {"index": i}, "audit") for i in range(5)]


def test_replay_matches_across_batch_boundaries_at_the_same_clock(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(persistence, "datetime", EarlierClock)
    first = CortexPersistLedger(tmp_path / "single.db")
    first_results = [first.append_event(event) for event in _events()]
    second = CortexPersistLedger(tmp_path / "batch.db")
    second_results = second.append_batch(_events())
    assert first_results == second_results
    assert first.get_merkle_root() == second.get_merkle_root()
    monkeypatch.setattr(persistence, "datetime", LaterClock)
    later = CortexPersistLedger(tmp_path / "later.db")
    later.append_batch(_events())
    assert later.get_merkle_root() == first.get_merkle_root()
    assert first.verify_integrity() and second.verify_integrity() and later.verify_integrity()


def test_reopen_continues_the_same_causal_chain(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    path = tmp_path / "reopen.db"
    monkeypatch.setattr(persistence, "datetime", EarlierClock)
    ledger = CortexPersistLedger(path)
    ledger.append_batch(_events()[:2])
    reopened = CortexPersistLedger(path)
    reopened.append_batch(_events()[2:])
    replay = CortexPersistLedger(tmp_path / "replay.db")
    replay.append_batch(_events())
    assert reopened.get_merkle_root() == replay.get_merkle_root()
    assert reopened.verify_integrity()
    assert reopened.get_state_attestation()["integrity_verified"]


def _create_legacy_ledger(path: Path) -> str:
    timestamp = "2020-01-01T00:00:00+00:00"
    digest = compute_cortex_hash(1, "legacy-id", "LEGACY", "{}", "audit", 1, ZERO_HASH_256, timestamp)
    assert digest == "397686bbb3c83c49ebbce7ea62809f3453361121647b7fd6595ea21e66426475"
    with sqlite3.connect(path) as conn:
        conn.execute("""CREATE TABLE cortex_ledger (
            seq INTEGER PRIMARY KEY AUTOINCREMENT, event_id TEXT NOT NULL UNIQUE,
            event_type TEXT NOT NULL, payload_json TEXT NOT NULL, cortex_taint TEXT NOT NULL,
            agent_id TEXT NOT NULL, domain TEXT NOT NULL, lamport_t INTEGER NOT NULL,
            prev_hash TEXT NOT NULL, entry_hash TEXT NOT NULL UNIQUE, timestamp TEXT NOT NULL
        )""")
        conn.execute(
            "INSERT INTO cortex_ledger VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                1,
                "legacy-id",
                "LEGACY",
                "{}",
                "audit",
                "ULTRATHINK-APEX",
                "babylon60.com",
                1,
                ZERO_HASH_256,
                digest,
                timestamp,
            ),
        )
    return digest


def test_legacy_hash_is_preserved_and_new_rows_are_versioned(tmp_path: Path) -> None:
    path = tmp_path / "legacy.db"
    original = _create_legacy_ledger(path)
    assert verify_offline_evidence(path)["verified"]
    ledger = CortexPersistLedger(path)
    assert ledger.verify_integrity()
    ledger.append_event(_events()[0])
    ledger.append_batch(_events()[1:])
    with sqlite3.connect(path) as conn:
        rows = conn.execute("SELECT entry_hash, hash_version FROM cortex_ledger ORDER BY seq").fetchall()
    assert rows[0] == (original, 1)
    assert [version for _, version in rows[1:]] == [3] * 5
    assert CortexPersistLedger(path).verify_integrity()
    assert ledger.get_state_attestation()["integrity_verified"]
    assert verify_offline_evidence(path, ledger.get_merkle_root())["verified"]


def test_unsupported_row_hash_version_is_rejected(tmp_path: Path) -> None:
    path = tmp_path / "unsupported.db"
    ledger = CortexPersistLedger(path)
    ledger.append_event(_events()[0])
    with sqlite3.connect(path) as conn:
        conn.execute("DROP TRIGGER trg_cortex_no_update")
        conn.execute("UPDATE cortex_ledger SET hash_version=999")
    assert not ledger.verify_integrity()
    assert not ledger.get_state_attestation()["integrity_verified"]


def test_v2_hash_binds_logical_tick_not_observation_time() -> None:
    def digest(tick: int, timestamp: str, version: int) -> str:
        return compute_cortex_hash(
            1,
            "event",
            "TEST",
            "{}",
            "audit",
            tick,
            ZERO_HASH_256,
            timestamp,
            hash_version=version,
        )

    assert digest(1, "earlier", 2) == digest(1, "later", 2)
    assert digest(1, "earlier", 2) != digest(2, "earlier", 2)
    assert digest(1, "earlier", 1) != digest(1, "later", 1)
    assert digest(1, "earlier", 3) == digest(1, "later", 3)
    assert digest(1, "earlier", 3) != digest(1, "earlier", 2)
    with pytest.raises(ValueError, match="Unsupported"):
        digest(1, "earlier", 999)


def test_v1_timestamp_tampering_remains_detectable(tmp_path: Path) -> None:
    path = tmp_path / "legacy-tamper.db"
    _create_legacy_ledger(path)
    ledger = CortexPersistLedger(path)
    with sqlite3.connect(path) as conn:
        conn.execute("DROP TRIGGER trg_cortex_no_update")
        conn.execute("UPDATE cortex_ledger SET timestamp='tampered'")
    assert not ledger.verify_integrity()


def test_bounded_replay_stress_after_warmup(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    warmup = CortexPersistLedger(tmp_path / "warmup.db")
    warmup.append_batch(_events())
    events = [CortexEvent("STRESS", {"index": i}, "audit") for i in range(129)]
    path = tmp_path / "restart-stress.db"
    expected = CortexPersistLedger(tmp_path / "reference.db")
    monkeypatch.setattr(persistence, "datetime", EarlierClock)
    expected.append_batch(events)
    for start in range(0, len(events), 17):
        restarted = CortexPersistLedger(path)
        restarted.append_batch(events[start : start + 17])
        assert restarted.verify_integrity()
    assert restarted.get_merkle_root() == expected.get_merkle_root()


def test_standalone_verifies_v2_ledger(tmp_path: Path) -> None:
    path = tmp_path / "standalone-v2.db"
    ledger = CortexPersistLedger(path)
    ledger.append_batch(_events())
    result = verify_offline_evidence(path, ledger.get_merkle_root())
    assert result["verified"], result["detail"]
    assert result["integrity_verified"]


@pytest.mark.parametrize(
    "mutation",
    [
        "UPDATE cortex_ledger SET payload_json='{}' WHERE seq=1",
        "UPDATE cortex_ledger SET lamport_t=99 WHERE seq=1",
        "UPDATE cortex_ledger SET hash_version=999 WHERE seq=1",
        "UPDATE cortex_ledger SET hash_version=1 WHERE seq=1",
    ],
)
def test_standalone_rejects_v2_tampering(tmp_path: Path, mutation: str) -> None:
    path = tmp_path / "standalone-tamper.db"
    ledger = CortexPersistLedger(path)
    ledger.append_batch(_events())
    with sqlite3.connect(path) as conn:
        conn.execute("DROP TRIGGER trg_cortex_no_update")
        conn.execute(mutation)
    result = verify_offline_evidence(path)
    assert not result["verified"]
    assert not result["integrity_verified"]
