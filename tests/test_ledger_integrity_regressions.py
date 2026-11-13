"""Regressions for silent ledger rewrites, aliasing, truncation and ephemeral Rekor keys."""

from __future__ import annotations

import sqlite3
import uuid
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from babylon60.bft.cortex_crypto_kernel import (
    ZERO_HASH_256,
    compute_cortex_hash,
    legacy_unit_separator_key,
    observation_commitment,
)
from babylon60.bft.cortex_persist_ledger import CortexEvent, CortexPersistLedger
from babylon60.bft.ledger_actor import (
    LEDGER_ENTRY_HASH_VERSION,
    NAMESPACE_UUID,
    ZERO_HASH,
    BFTCausalInvariantError,
    BFTLedgerActor,
    LedgerEvent,
    _compute_entry_hash,
)
from babylon60.crypto.rekor_client import RekorClient


def _event(name: str, **overrides: object) -> CortexEvent:
    fields = {
        "event_type": "T",
        "payload": {"k": name},
        "cortex_taint": "taint",
        "agent_id": "agent",
        "domain": "dom",
    }
    fields.update(overrides)
    return CortexEvent(**fields)  # type: ignore[arg-type]


def test_checkpoint_rejects_a_recomputed_chain_and_unpinned_verify_accepts_it(tmp_path: Path) -> None:
    path = tmp_path / "rewrite.db"
    ledger = CortexPersistLedger(path)
    ledger.append_event(_event("one"))
    ledger.append_event(_event("two"))
    pin = ledger.get_checkpoint()
    assert ledger.verify_integrity(expected_checkpoint=pin) is True

    with sqlite3.connect(path) as conn:
        conn.execute("DROP TRIGGER trg_cortex_no_update")
        rows = conn.execute(
            "SELECT seq, event_id, event_type, payload_json, cortex_taint, agent_id, domain, "
            "lamport_t, timestamp, hash_version FROM cortex_ledger ORDER BY seq"
        ).fetchall()
        prev = ZERO_HASH_256
        for seq, event_id, event_type, payload_json, taint, agent, domain, lamport, timestamp, version in rows:
            if seq == 1:
                payload_json = '{"forged":true}'
            digest = compute_cortex_hash(
                seq=seq,
                event_id=event_id,
                event_type=event_type,
                payload_json=payload_json,
                cortex_taint=taint,
                lamport_t=lamport,
                prev_hash=prev,
                timestamp=timestamp,
                agent_id=agent,
                domain=domain,
                hash_version=version,
            )
            conn.execute(
                "UPDATE cortex_ledger SET payload_json=?, prev_hash=?, entry_hash=?, observation_hash=? WHERE seq=?",
                (payload_json, prev, digest, observation_commitment(digest, timestamp, agent), seq),
            )
            prev = digest
    assert ledger.verify_integrity() is True
    assert ledger.verify_integrity(expected_checkpoint=pin) is False


def test_v3_binds_timestamp_and_v2_rows_still_verify(tmp_path: Path) -> None:
    path = tmp_path / "versions.db"
    timestamp = "2020-01-01T00:00:00+00:00"
    digest = compute_cortex_hash(
        1, "legacy-v2", "T", "{}", "taint", 1, ZERO_HASH_256, timestamp, agent_id="agent", domain="dom", hash_version=2
    )
    ledger = CortexPersistLedger(path)
    with sqlite3.connect(path) as conn:
        conn.execute(
            "INSERT INTO cortex_ledger (event_id, event_type, payload_json, cortex_taint, agent_id, domain, "
            "lamport_t, prev_hash, entry_hash, timestamp, hash_version) VALUES (?,?,?,?,?,?,?,?,?,?,?)",
            ("legacy-v2", "T", "{}", "taint", "agent", "dom", 1, ZERO_HASH_256, digest, timestamp, 2),
        )
    assert ledger.verify_integrity() is True
    with sqlite3.connect(path) as conn:
        conn.execute("DROP TRIGGER trg_cortex_no_update")
        conn.execute("UPDATE cortex_ledger SET timestamp='1999-01-01T00:00:00+00:00' WHERE hash_version=2")
    assert ledger.verify_integrity() is True

    ledger.append_event(_event("fresh"))
    with sqlite3.connect(path) as conn:
        version, entry_hash, agent_id, sealed = conn.execute(
            "SELECT hash_version, entry_hash, agent_id, observation_hash FROM cortex_ledger WHERE seq=2"
        ).fetchone()
        assert version == 3
        assert sealed == observation_commitment(entry_hash, conn.execute("SELECT timestamp FROM cortex_ledger WHERE seq=2").fetchone()[0], agent_id)
        conn.execute("UPDATE cortex_ledger SET timestamp='1970-01-01T00:00:00+00:00' WHERE seq=2")
    assert ledger.verify_integrity() is False


def test_resealed_timestamp_does_not_keep_the_checkpoint(tmp_path: Path) -> None:
    path = tmp_path / "reseal.db"
    ledger = CortexPersistLedger(path)
    ledger.append_event(_event("one"))
    pin = ledger.get_checkpoint()
    with sqlite3.connect(path) as conn:
        conn.execute("DROP TRIGGER trg_cortex_no_update")
        entry_hash, agent_id = conn.execute("SELECT entry_hash, agent_id FROM cortex_ledger").fetchone()
        new_stamp = "1999-01-01T00:00:00+00:00"
        conn.execute(
            "UPDATE cortex_ledger SET timestamp=?, observation_hash=?",
            (new_stamp, observation_commitment(entry_hash, new_stamp, agent_id)),
        )
    assert ledger.verify_integrity() is True
    assert ledger.verify_integrity(expected_checkpoint=pin) is False


def test_unit_separator_no_longer_collapses_distinct_events(tmp_path: Path) -> None:
    ledger = CortexPersistLedger(tmp_path / "alias.db")
    first = ledger.append_event(_event("same", cortex_taint="a\x1fb", agent_id="c"))
    second = ledger.append_event(_event("same", cortex_taint="a", agent_id="b\x1fc"))
    assert first["status"] == "C5_PERMANENT"
    assert second["status"] == "C5_PERMANENT"
    assert first["event_id"] != second["event_id"]
    with sqlite3.connect(tmp_path / "alias.db") as conn:
        assert conn.execute("SELECT COUNT(*) FROM cortex_ledger").fetchone()[0] == 2
    replay = ledger.append_event(_event("same", cortex_taint="a\x1fb", agent_id="c"))
    assert replay["status"] == "DUPLICATE_IGNORED"
    assert replay["event_id"] == first["event_id"]


def test_batch_uuid_collision_compares_identity(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    ledger = CortexPersistLedger(tmp_path / "batch-collision.db")
    monkeypatch.setattr(
        "babylon60.bft.cortex_persist_ledger.uuid.uuid5",
        lambda *_args, **_kwargs: "same-batch-id",
    )
    with pytest.raises(ValueError, match="INV_BFT_04"):
        ledger.append_batch([_event("one"), _event("two")])
    with sqlite3.connect(tmp_path / "batch-collision.db") as conn:
        assert conn.execute("SELECT COUNT(*) FROM cortex_ledger").fetchone()[0] == 0


def test_duplicate_event_id_with_different_content_is_rejected(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    ledger = CortexPersistLedger(tmp_path / "collision.db")
    stored = ledger.append_event(_event("one"))
    monkeypatch.setattr(
        "babylon60.bft.cortex_persist_ledger.uuid.uuid5",
        lambda *_args, **_kwargs: stored["event_id"],
    )
    with pytest.raises(ValueError, match="INV_BFT_04"):
        ledger.append_event(_event("two"))


def test_append_after_tail_delete_keeps_seq_inside_the_digest(tmp_path: Path) -> None:
    path = tmp_path / "gap.db"
    ledger = CortexPersistLedger(path)
    ledger.append_event(_event("one"))
    ledger.append_event(_event("two"))
    with sqlite3.connect(path) as conn:
        conn.execute("DROP TRIGGER trg_cortex_no_delete")
        conn.execute("DELETE FROM cortex_ledger WHERE seq=2")
    fresh = ledger.append_event(_event("three"))
    with sqlite3.connect(path) as conn:
        stored_seq, stored_hash, version, payload, event_id, event_type, taint, agent, domain, lamport, prev, timestamp = conn.execute(
            "SELECT seq, entry_hash, hash_version, payload_json, event_id, event_type, cortex_taint, agent_id, domain, lamport_t, prev_hash, timestamp FROM cortex_ledger ORDER BY seq DESC LIMIT 1"
        ).fetchone()
    assert stored_seq == fresh["seq"] == 3
    assert stored_hash == compute_cortex_hash(
        seq=stored_seq,
        event_id=event_id,
        event_type=event_type,
        payload_json=payload,
        cortex_taint=taint,
        lamport_t=lamport,
        prev_hash=prev,
        timestamp=timestamp,
        agent_id=agent,
        domain=domain,
        hash_version=version,
    )
    assert ledger.verify_integrity() is False


def test_tail_truncation_is_detected_via_sqlite_sequence(tmp_path: Path) -> None:
    path = tmp_path / "truncate.db"
    ledger = CortexPersistLedger(path)
    ledger.append_event(_event("one"))
    ledger.append_event(_event("two"))
    with sqlite3.connect(path) as conn:
        conn.execute("DROP TRIGGER trg_cortex_no_delete")
        conn.execute("DELETE FROM cortex_ledger WHERE seq=2")
        high_water = conn.execute("SELECT seq FROM sqlite_sequence WHERE name='cortex_ledger'").fetchone()[0]
    assert high_water == 2
    assert ledger.verify_integrity() is False
    assert ledger.get_state_attestation()["integrity_verified"] is False


def test_head_read_follows_highest_seq_when_lamport_ties(tmp_path: Path) -> None:
    path = tmp_path / "head.db"
    ledger = CortexPersistLedger(path)
    earlier = "a" * 64
    latest = "b" * 64
    with sqlite3.connect(path) as conn:
        conn.executemany(
            "INSERT INTO cortex_ledger (seq, event_id, event_type, payload_json, cortex_taint, agent_id, domain, "
            "lamport_t, prev_hash, entry_hash, timestamp, hash_version) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
            [
                (1, "e1", "T", "{}", "t", "a", "d", 9, ZERO_HASH_256, earlier, "ts", 3),
                (2, "e2", "T", "{}", "t", "a", "d", 9, earlier, latest, "ts", 3),
            ],
        )
    ledger.append_event(_event("next"))
    with sqlite3.connect(path) as conn:
        prev_hash, lamport = conn.execute(
            "SELECT prev_hash, lamport_t FROM cortex_ledger ORDER BY seq DESC LIMIT 1"
        ).fetchone()
    assert prev_hash == latest
    assert lamport == 10


def test_rekor_refuses_missing_or_invalid_seed(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    ledger = CortexPersistLedger(tmp_path / "rekor.db")
    ledger.append_event(_event("anchor"))
    client = MagicMock(spec=RekorClient)
    client.anchor_payload.return_value = {"uuid": "abc", "logIndex": 1}
    monkeypatch.delenv("BABYLON60_SIGNING_SEED", raising=False)
    with pytest.raises(ValueError, match="ephemeral"):
        ledger.anchor_to_rekor(rekor_client=client)
    monkeypatch.setenv("BABYLON60_SIGNING_SEED", "zz")
    with pytest.raises(ValueError, match="hex-encoded"):
        ledger.anchor_to_rekor(rekor_client=client)
    monkeypatch.setenv("BABYLON60_SIGNING_SEED", "00" * 31)
    with pytest.raises(ValueError, match="32 bytes"):
        ledger.anchor_to_rekor(rekor_client=client)
    assert client.anchor_payload.called is False

    monkeypatch.setenv("BABYLON60_SIGNING_SEED", "11" * 32)
    result = ledger.anchor_to_rekor(rekor_client=client)
    assert result is not None
    from nacl.signing import SigningKey

    expected = SigningKey(bytes.fromhex("11" * 32)).verify_key.encode()
    import base64

    published = base64.b64decode(client.anchor_payload.call_args.args[2])
    assert published == expected


@pytest.mark.asyncio
async def test_actor_persists_agent_id_and_checkpoint_rejects_replacement(tmp_path: Path) -> None:
    path = tmp_path / "actor.db"
    actor = BFTLedgerActor(path)
    await actor.start()
    await actor.append(
        LedgerEvent("s", "entity", "T", {"n": 1}, "taint", "db", "table", "pk", agent_id="honest")
    )
    pin = await actor.get_checkpoint()
    await actor.stop()
    with sqlite3.connect(path) as conn:
        stored = conn.execute("SELECT agent_id, hash_version, created_at FROM ledger_entries").fetchone()
    assert stored[0] == "honest"
    assert stored[1] == LEDGER_ENTRY_HASH_VERSION

    with sqlite3.connect(path) as conn:
        conn.execute("DROP TRIGGER trg_ledger_immutable_update")
        conn.execute("UPDATE ledger_entries SET agent_id='forged'")
    with pytest.raises(BFTCausalInvariantError, match="INV_BFT_LEAN_04"):
        await BFTLedgerActor(path).verify_chain()

    with sqlite3.connect(path) as conn:
        conn.execute("UPDATE ledger_entries SET agent_id='honest'")
    assert await BFTLedgerActor(path).verify_chain(expected_checkpoint=pin) is True

    replacement = tmp_path / "other.db"
    other = BFTLedgerActor(replacement)
    await other.start()
    await other.append(LedgerEvent("s", "entity", "T", {"n": 2}, "taint", "db", "table", "pk2", agent_id="honest"))
    await other.stop()
    with sqlite3.connect(replacement) as source, sqlite3.connect(path) as dest:
        source.backup(dest)
    assert await BFTLedgerActor(path).verify_chain() is True
    with pytest.raises(BFTCausalInvariantError, match="checkpoint"):
        await BFTLedgerActor(path).verify_chain(expected_checkpoint=pin)


@pytest.mark.asyncio
async def test_actor_timestamp_rewrite_fails_and_legacy_v1_row_still_verifies(tmp_path: Path) -> None:
    path = tmp_path / "legacy-actor.db"
    actor = BFTLedgerActor(path)
    await actor.start()
    await actor.stop()
    created = "2020-01-01T00:00:00Z"
    digest = _compute_entry_hash(
        "legacy",
        "s",
        "e",
        "T",
        "{}",
        "db",
        "table",
        "pk",
        "taint",
        1,
        ZERO_HASH,
        created,
        agent_id="ignored-by-v1",
        hash_version=1,
    )
    with sqlite3.connect(path) as conn:
        conn.execute(
            "INSERT INTO ledger_entries (event_id, stream, entity_id, event_type, payload_json, source_db, "
            "source_table, source_pk, cortex_taint, lamport_t, prev_hash, entry_hash, created_at, agent_id, "
            "hash_version) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            ("legacy", "s", "e", "T", "{}", "db", "table", "pk", "taint", 1, ZERO_HASH, digest, created, "", 1),
        )
    assert await BFTLedgerActor(path).verify_chain() is True

    fresh = BFTLedgerActor(path)
    await fresh.start()
    await fresh.append(LedgerEvent("s", "e2", "T", {"n": 2}, "taint-2", "db", "table", "pk2", agent_id="kept"))
    await fresh.stop()
    with sqlite3.connect(path) as conn:
        conn.execute("DROP TRIGGER trg_ledger_immutable_update")
        conn.execute("UPDATE ledger_entries SET created_at='1999-01-01T00:00:00Z' WHERE hash_version=2")
    with pytest.raises(BFTCausalInvariantError, match="INV_BFT_LEAN_04"):
        await BFTLedgerActor(path).verify_chain()


@pytest.mark.asyncio
async def test_historical_retry_returns_the_persisted_event_id(tmp_path: Path) -> None:
    path = tmp_path / "legacy-id.db"
    actor = BFTLedgerActor(path)
    await actor.start()
    await actor.stop()
    payload = '{"n":1}'
    legacy_id = str(uuid.uuid5(NAMESPACE_UUID, legacy_unit_separator_key("db", "table", "pk", payload, "taint")))
    created = "2020-01-01T00:00:00Z"
    digest = _compute_entry_hash(
        legacy_id, "s", "entity", "T", payload, "db", "table", "pk", "taint", 1, ZERO_HASH, created, hash_version=1
    )
    with sqlite3.connect(path) as conn:
        conn.execute(
            "INSERT INTO ledger_entries (event_id, stream, entity_id, event_type, payload_json, source_db, "
            "source_table, source_pk, cortex_taint, lamport_t, prev_hash, entry_hash, created_at, agent_id, "
            "hash_version) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (legacy_id, "s", "entity", "T", payload, "db", "table", "pk", "taint", 1, ZERO_HASH, digest, created, "", 1),
        )
    retry = BFTLedgerActor(path)
    await retry.start()
    receipt = await retry.append(
        LedgerEvent("s", "entity", "T", {"n": 1}, "taint", "db", "table", "pk", agent_id="later")
    )
    await retry.stop()
    assert receipt["event_id"] == legacy_id
    assert receipt["entry_hash"] == digest
    with sqlite3.connect(path) as conn:
        assert conn.execute("SELECT COUNT(*) FROM ledger_entries").fetchone()[0] == 1


@pytest.mark.asyncio
async def test_fractional_hash_version_is_rejected(tmp_path: Path) -> None:
    path = tmp_path / "fraction.db"
    actor = BFTLedgerActor(path)
    await actor.start()
    await actor.append(LedgerEvent("s", "e", "T", {"n": 1}, "taint", "db", "table", "pk", agent_id="a"))
    await actor.stop()
    with sqlite3.connect(path) as conn:
        conn.execute("DROP TRIGGER trg_ledger_immutable_update")
        conn.execute("UPDATE ledger_entries SET hash_version=2.5")
    with pytest.raises(ValueError, match="Unsupported ledger entry hash version"):
        await BFTLedgerActor(path).verify_chain()
