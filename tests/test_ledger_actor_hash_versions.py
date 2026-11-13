"""Versioned actor hashes against real legacy SQLite/Fernet data; native IPC is disabled."""

import asyncio
from dataclasses import replace
from datetime import datetime, timezone
import hashlib
import json
import sqlite3
import sys
import uuid

import aiosqlite
from cryptography.fernet import Fernet
import pytest

from babylon60.bft import ledger_actor as module
from babylon60.bft.cortex_crypto_kernel import build_merkle_tree
from babylon60.bft.ledger_actor import BFTCausalInvariantError, BFTLedgerActor, LedgerEvent


@pytest.fixture(autouse=True)
def isolate_vault_and_ipc(monkeypatch):
    monkeypatch.delenv("CORTEX_VAULT_KEY", raising=False)
    monkeypatch.setitem(sys.modules, "strike_rs", None)


def event(index=1, **changes):
    return replace(LedgerEvent("fixture", str(index), "CREATED", {"index": index},
                               "fixture-taint", "fixture", "events", str(index)), **changes)


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False)


def create_legacy_db(path, encrypted=False, key=None):
    """Create the pre-versioning schema and SHA3 hashes without calling actor hash/schema APIs."""
    vault = Fernet(key) if encrypted else None
    with sqlite3.connect(path) as db:
        db.execute("PRAGMA journal_mode=WAL")
        db.execute("PRAGMA synchronous=FULL")
        db.execute("""CREATE TABLE ledger_entries (
            seq INTEGER PRIMARY KEY AUTOINCREMENT, event_id TEXT NOT NULL UNIQUE,
            stream TEXT NOT NULL CHECK(length(stream)>0), entity_id TEXT NOT NULL CHECK(length(entity_id)>0),
            event_type TEXT NOT NULL CHECK(length(event_type)>0), payload_json TEXT NOT NULL CHECK(length(payload_json)>=2),
            source_db TEXT NOT NULL CHECK(length(source_db)>0), source_table TEXT NOT NULL CHECK(length(source_table)>0),
            source_pk TEXT NOT NULL CHECK(length(source_pk)>0), cortex_taint TEXT NOT NULL CHECK(length(cortex_taint)>0),
            lamport_t INTEGER NOT NULL CHECK(lamport_t>0), prev_hash TEXT NOT NULL CHECK(length(prev_hash)=64),
            entry_hash TEXT NOT NULL UNIQUE CHECK(length(entry_hash)=64), created_at TEXT NOT NULL,
            agent_id TEXT NOT NULL DEFAULT '', UNIQUE(lamport_t,agent_id))""")
        previous = "0" * 64
        for index in (1, 2):
            ev = event(index)
            payload = canonical(ev.payload)
            identity = f"fixture\x1fevents\x1f{index}\x1f{payload}\x1ffixture-taint"
            event_id = str(uuid.uuid5(uuid.UUID("9897d6fd-d6a7-4fe9-86bc-f0c312886d5d"), identity))
            stored = "C5ENC:" + vault.encrypt(payload.encode()).decode() if vault else payload
            created_at = f"2020-01-0{index}T00:00:00Z"
            envelope = dict(event_id=event_id, stream=ev.stream, entity_id=ev.entity_id, event_type=ev.event_type,
                            payload_json=stored, source_db=ev.source_db, source_table=ev.source_table,
                            source_pk=ev.source_pk, cortex_taint=ev.cortex_taint, lamport_t=index,
                            prev_hash=previous, created_at=created_at)
            digest = hashlib.sha3_256(canonical(envelope).encode()).hexdigest()
            db.execute("INSERT INTO ledger_entries VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                       (index, event_id, ev.stream, ev.entity_id, ev.event_type, stored, ev.source_db,
                        ev.source_table, ev.source_pk, ev.cortex_taint, index, previous, digest, created_at, ""))
            previous = digest
        for operation in ("UPDATE", "DELETE"):
            db.execute(f"CREATE TRIGGER trg_ledger_immutable_{operation.lower()} BEFORE {operation} ON ledger_entries "
                       "BEGIN SELECT RAISE(ABORT, 'C5 BFT: immutable master ledger'); END")
    return rows(path)


def rows(path):
    with sqlite3.connect(path) as db:
        return db.execute("SELECT * FROM ledger_entries ORDER BY seq").fetchall()


async def append(actor, ev):
    return await asyncio.wait_for(actor.append(ev), timeout=5)


@pytest.mark.asyncio
@pytest.mark.parametrize("encrypted", [False, True])
async def test_real_legacy_rows_roots_and_sequence_survive_upgrade(tmp_path, monkeypatch, encrypted):
    path = tmp_path / "legacy.db"
    key = Fernet.generate_key()
    original = create_legacy_db(path, encrypted, key)
    actor = BFTLedgerActor(path)
    assert await actor.verify_chain()  # Historical ciphertext remains verifiable without its key.
    original_root = build_merkle_tree([row[12] for row in original])
    checkpoint = await actor.get_checkpoint()
    if encrypted:
        monkeypatch.setenv("CORTEX_VAULT_KEY", key.decode())
    await actor.start()
    try:
        retry = await append(actor, event(1))
        assert retry == {"seq": 1, "event_id": original[0][1], "entry_hash": original[0][12]}
        assert rows(path) == original
        assert await actor.get_merkle_root() == original_root
        assert await actor.get_checkpoint() == checkpoint
        inserted = await append(actor, event(3))
        assert inserted["seq"] == 3
        assert await actor.verify_chain()
    finally:
        await actor.stop()
    assert rows(path)[:2] == original
    with sqlite3.connect(path) as db:
        assert db.execute("SELECT seq FROM sqlite_sequence WHERE name='ledger_entries'").fetchone() == (3,)
        assert db.execute("SELECT hash_version,hash_algorithm,payload_hash FROM ledger_entry_hashes "
                          "ORDER BY rowid").fetchall()[:2] == [(1, "sha3-256", None)] * 2
        assert db.execute("SELECT singleton,schema_version,legacy_max_seq,legacy_tip_hash "
                          "FROM ledger_hash_policy").fetchone() == (1, 2, 2, original[-1][12])
    await actor.start()
    try:
        assert await append(actor, event(3)) == inserted
        assert await actor.verify_chain()
        assert (await actor.get_checkpoint()).entries == 3
    finally:
        await actor.stop()


@pytest.mark.asyncio
@pytest.mark.parametrize("encrypted", [False, True])
@pytest.mark.parametrize("explicit_date", [False, True])
async def test_replica_hashes_ignore_physical_dates_and_randomized_ciphertext(
    tmp_path, monkeypatch, encrypted, explicit_date,
):
    if encrypted:
        monkeypatch.setenv("CORTEX_VAULT_KEY", Fernet.generate_key().decode())
    results, persisted, roots = [], [], []
    for index, year in enumerate((2001, 2041)):
        class Clock:
            @staticmethod
            def now(tz):
                return datetime(year, 1, 1, tzinfo=timezone.utc)
        monkeypatch.setattr(module, "datetime", Clock)
        path = tmp_path / f"replica-{index}.db"
        actor = BFTLedgerActor(path)
        await actor.start()
        try:
            ev = event(created_at=f"{year}-02-01T00:00:00Z") if explicit_date else event()
            results.append(await append(actor, ev))
            assert await actor.verify_chain()
            roots.append((await actor.get_merkle_root(), await actor.get_mmr_root()))
        finally:
            await actor.stop()
        persisted.append(rows(path)[0])
    assert results[0] == results[1]
    assert roots[0] == roots[1]
    assert persisted[0][13] != persisted[1][13]
    if encrypted:
        assert persisted[0][5] != persisted[1][5]
        assert all(row[5].startswith("C5ENC:") for row in persisted)
        for key in (None, Fernet.generate_key().decode()):
            if key is None:
                monkeypatch.delenv("CORTEX_VAULT_KEY")
            else:
                monkeypatch.setenv("CORTEX_VAULT_KEY", key)
            with pytest.raises(BFTCausalInvariantError, match="INV_BFT_LEAN_04.*C5ENC"):
                await BFTLedgerActor(tmp_path / "replica-0.db").verify_chain()


@pytest.mark.asyncio
@pytest.mark.parametrize("mutation", [
    "unknown-version", "unknown-algorithm", "missing-marker", "downgrade", "legacy-as-v2",
    "payload-commitment", "legacy-boundary", "policy-version", "policy-tip", "event-metadata",
])
async def test_mixed_chain_rejects_changed_versions_policy_and_semantics(tmp_path, mutation):
    path = tmp_path / "tamper.db"
    create_legacy_db(path)
    actor = BFTLedgerActor(path)
    await actor.start()
    try:
        await append(actor, event(3))
        assert await actor.verify_chain()
    finally:
        await actor.stop()
    with sqlite3.connect(path) as db:
        for name in ("trg_ledger_entry_hashes_immutable_update", "trg_ledger_entry_hashes_immutable_delete",
                     "trg_ledger_hash_policy_immutable_update", "trg_ledger_immutable_update"):
            db.execute(f"DROP TRIGGER {name}")
        new_id = rows(path)[2][1]
        legacy_id = rows(path)[0][1]
        mutations = {
            "unknown-version": ("UPDATE ledger_entry_hashes SET hash_version=99 WHERE event_id=?", (new_id,)),
            "unknown-algorithm": ("UPDATE ledger_entry_hashes SET hash_algorithm='unknown' WHERE event_id=?", (new_id,)),
            "missing-marker": ("DELETE FROM ledger_entry_hashes WHERE event_id=?", (new_id,)),
            "downgrade": ("UPDATE ledger_entry_hashes SET hash_version=1,hash_algorithm='sha3-256',payload_hash=NULL "
                          "WHERE event_id=?", (new_id,)),
            "legacy-as-v2": ("UPDATE ledger_entry_hashes SET hash_version=2,hash_algorithm='blake3',payload_hash=? "
                             "WHERE event_id=?", ("0" * 64, legacy_id)),
            "payload-commitment": ("UPDATE ledger_entry_hashes SET payload_hash=? WHERE event_id=?", ("0" * 64, new_id)),
            "legacy-boundary": ("UPDATE ledger_hash_policy SET legacy_max_seq=0", ()),
            "policy-version": ("UPDATE ledger_hash_policy SET schema_version=99", ()),
            "policy-tip": ("UPDATE ledger_hash_policy SET legacy_tip_hash=?", ("0" * 64,)),
            "event-metadata": ("UPDATE ledger_entries SET source_table='changed' WHERE seq=3", ()),
        }
        sql, parameters = mutations[mutation]
        db.execute(sql, parameters)
    with pytest.raises(BFTCausalInvariantError):
        await BFTLedgerActor(path).verify_chain()


@pytest.mark.asyncio
@pytest.mark.parametrize("seq", [1, 3])
async def test_date_metadata_is_separate_only_for_new_entries(tmp_path, seq):
    path = tmp_path / "dates.db"
    create_legacy_db(path)
    actor = BFTLedgerActor(path)
    await actor.start()
    try:
        await append(actor, event(3))
        root = await actor.get_merkle_root()
    finally:
        await actor.stop()
    with sqlite3.connect(path) as db:
        db.execute("DROP TRIGGER trg_ledger_immutable_update")
        db.execute("UPDATE ledger_entries SET created_at='2099-01-01T00:00:00Z' WHERE seq=?", (seq,))
    if seq == 1:
        with pytest.raises(BFTCausalInvariantError, match="INV_BFT_LEAN_04"):
            await actor.verify_chain()
    else:
        assert await actor.verify_chain()
        assert await actor.get_merkle_root() == root


@pytest.mark.asyncio
async def test_hash_metadata_is_immutable_and_old_writer_is_rejected(tmp_path):
    path = tmp_path / "guard.db"
    create_legacy_db(path)
    actor = BFTLedgerActor(path)
    await actor.start()
    try:
        await append(actor, event(3))
    finally:
        await actor.stop()
    for table in ("ledger_entry_hashes", "ledger_hash_policy"):
        for sql in (f"DELETE FROM {table}", f"UPDATE {table} SET rowid=rowid"):
            with sqlite3.connect(path) as db, pytest.raises(sqlite3.IntegrityError, match="immutable"):
                db.execute(sql)
    legacy_row = list(rows(path)[0])
    legacy_row[0], legacy_row[1], legacy_row[10], legacy_row[12] = None, str(uuid.uuid4()), 4, "f" * 64
    with sqlite3.connect(path) as db, pytest.raises(sqlite3.IntegrityError):
        db.execute("INSERT INTO ledger_entries VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)", legacy_row)
    assert len(rows(path)) == 3
    assert await actor.verify_chain()


@pytest.mark.asyncio
async def test_two_actors_migrate_and_retry_legacy_chain_without_duplicates(tmp_path):
    path = tmp_path / "concurrent.db"
    original = create_legacy_db(path)
    actors = [BFTLedgerActor(path), BFTLedgerActor(path)]
    await asyncio.gather(*(actor.start() for actor in actors))
    try:
        results = await asyncio.gather(*(append(actor, event(index)) for index in (1, 3, 4) for actor in actors))
        assert results[0] == results[1]
        assert results[2] == results[3]
        assert results[4] == results[5]
        assert rows(path)[:2] == original
        assert [(row[0], row[10]) for row in rows(path)] == [(i, i) for i in range(1, 5)]
        assert await actors[0].verify_chain()
    finally:
        await asyncio.gather(*(actor.stop() for actor in actors))


@pytest.mark.asyncio
async def test_migration_failure_rolls_back_tables_and_preserves_legacy_history(tmp_path, monkeypatch):
    path = tmp_path / "atomic.db"
    original = create_legacy_db(path)
    async with aiosqlite.connect(path, isolation_level=None) as db:
        execute = db.execute

        async def fail_policy_ddl(sql, *args, **kwargs):
            if "CREATE TABLE" in sql.upper() and "ledger_hash_policy" in sql:
                raise aiosqlite.OperationalError("injected migration failure")
            return await execute(sql, *args, **kwargs)

        monkeypatch.setattr(db, "execute", fail_policy_ddl)
        with pytest.raises(aiosqlite.OperationalError, match="injected migration failure"):
            await BFTLedgerActor(path)._init_db(db)
        assert not db.in_transaction
    assert rows(path) == original
    with sqlite3.connect(path) as db:
        names = {row[0] for row in db.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        assert "ledger_entry_hashes" not in names
        assert "ledger_hash_policy" not in names
    assert await BFTLedgerActor(path).verify_chain()


@pytest.mark.asyncio
async def test_wrong_vault_key_rejects_new_encrypted_event_without_advancing_state(tmp_path, monkeypatch):
    path = tmp_path / "key-continuity.db"
    original_key = Fernet.generate_key().decode()
    monkeypatch.setenv("CORTEX_VAULT_KEY", original_key)
    actor = BFTLedgerActor(path)

    def snapshot():
        with sqlite3.connect(path) as db:
            return tuple(db.execute(f"SELECT * FROM {table} ORDER BY rowid").fetchall() for table in (
                "ledger_entries", "ledger_entry_hashes", "ledger_hash_policy", "sqlite_sequence",
            ))

    await actor.start()
    try:
        assert (await append(actor, event(1)))["seq"] == 1
        before = snapshot()
        monkeypatch.setenv("CORTEX_VAULT_KEY", Fernet.generate_key().decode())
        with pytest.raises(ValueError, match="C5ENC"):
            await append(actor, event(2))
        assert snapshot() == before
        monkeypatch.setenv("CORTEX_VAULT_KEY", original_key)
        assert (await append(actor, event(2)))["seq"] == 2
        assert await actor.verify_chain()
    finally:
        await actor.stop()


@pytest.mark.asyncio
async def test_plaintext_event_can_follow_encrypted_history_without_loaded_key(tmp_path, monkeypatch):
    path = tmp_path / "key-unloaded.db"
    original_key = Fernet.generate_key().decode()
    monkeypatch.setenv("CORTEX_VAULT_KEY", original_key)
    actor = BFTLedgerActor(path)
    await actor.start()
    try:
        assert (await append(actor, event(1)))["seq"] == 1
        monkeypatch.delenv("CORTEX_VAULT_KEY")
        assert (await append(actor, event(2)))["seq"] == 2
        assert rows(path)[0][5].startswith("C5ENC:")
        assert rows(path)[1][5] == canonical(event(2).payload)
        monkeypatch.setenv("CORTEX_VAULT_KEY", original_key)
        assert await actor.verify_chain()
    finally:
        await actor.stop()
