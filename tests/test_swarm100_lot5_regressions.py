"""Real async SQLite/Fernet in owned temporary roots; native IPC is blocked."""

import asyncio
from dataclasses import replace
import sys
import uuid

import aiosqlite
from cryptography.fernet import Fernet
import pytest

from babylon60.bft.ledger_actor import BFTLedgerActor, LedgerEvent


@pytest.fixture(autouse=True)
def isolated_crypto_and_ipc(monkeypatch):
    monkeypatch.delenv("CORTEX_VAULT_KEY", raising=False)
    monkeypatch.setitem(sys.modules, "strike_rs", None)


def event(index=1, **changes):
    base = LedgerEvent(
        stream="fixture",
        entity_id=str(index),
        event_type="CREATED",
        payload={"index": index},
        cortex_taint="fixture-taint",
        source_db="fixture",
        source_table="events",
        source_pk=str(index),
    )
    return replace(base, **changes)


async def cleanup(actor, *futures):
    # Failure-path fixture cleanup only; never supplies a successful test outcome.
    for future in futures:
        if future is not None and not future.done():
            future.cancel()
    if actor._task is not None and not actor._task.done():
        actor._task.cancel()
    if actor._task is not None:
        await asyncio.gather(actor._task, return_exceptions=True)
    for future in futures:
        if future is not None:
            await asyncio.gather(future, return_exceptions=True)
    while not actor._queue.empty():
        _, future = actor._queue.get_nowait()
        if not future.done():
            future.cancel()
        await asyncio.gather(future, return_exceptions=True)
        actor._queue.task_done()


async def bounded(future):
    return await asyncio.wait_for(asyncio.shield(future), timeout=3)


@pytest.mark.asyncio
async def test_c0428_stop_drains_event_queued_before_worker_loop(tmp_path, monkeypatch):
    actor = BFTLedgerActor(tmp_path / "shutdown.db")
    entered, release = asyncio.Event(), asyncio.Event()
    initialize = actor._init_db

    async def held_init(db):
        await initialize(db)
        entered.set()
        await release.wait()

    monkeypatch.setattr(actor, "_init_db", held_init)
    pending = stopping = None
    try:
        await actor.start()
        await bounded(entered.wait())
        pending = actor.append(event())
        stopping = asyncio.create_task(actor.stop())
        await bounded(actor._stop_event.wait())
        release.set()
        await bounded(stopping)
        assert (await bounded(pending))["seq"] == 1
        await bounded(actor._queue.join())
    finally:
        release.set()
        await cleanup(actor, pending, stopping)


@pytest.mark.asyncio
async def test_c0429_encrypted_retry_preserves_original_row(tmp_path, monkeypatch):
    monkeypatch.setenv("CORTEX_VAULT_KEY", Fernet.generate_key().decode())
    actor = BFTLedgerActor(tmp_path / "encrypted.db")
    first = second = None
    try:
        await actor.start()
        first = actor.append(event())
        original = await bounded(first)
        async with aiosqlite.connect(actor._db_path) as db:
            before = await (await db.execute("SELECT * FROM ledger_entries")).fetchall()
        second = actor.append(event())
        assert await bounded(second) == original
        async with aiosqlite.connect(actor._db_path) as db:
            after = await (await db.execute("SELECT * FROM ledger_entries")).fetchall()
        assert after == before
        assert await actor.verify_chain()
        await bounded(actor.stop())
    finally:
        await cleanup(actor, first, second)


@pytest.mark.asyncio
async def test_c0430_sql_rejection_rolls_back_once_and_worker_continues(tmp_path, monkeypatch):
    actor = BFTLedgerActor(tmp_path / "rollback.db")
    trace: list[str] = []
    initialize = actor._init_db

    async def traced_init(db):
        await initialize(db)
        await db.set_trace_callback(trace.append)

    monkeypatch.setattr(actor, "_init_db", traced_init)
    rejected = following = None
    try:
        await actor.start()
        rejected = actor.append(event(stream=""))  # Real SQLite CHECK failure inside BEGIN.
        with pytest.raises(aiosqlite.IntegrityError):
            await bounded(rejected)
        following = actor.append(event(2))
        assert (await bounded(following))["seq"] == 1
        assert sum(sql.strip().upper() == "ROLLBACK" for sql in trace) == 1
        assert await actor.verify_chain()
        await bounded(actor.stop())
    finally:
        await cleanup(actor, rejected, following)


async def hold_init(actor, monkeypatch):
    entered, release = asyncio.Event(), asyncio.Event()
    initialize = actor._init_db

    async def paused(db):
        await initialize(db)
        entered.set()
        await release.wait()

    monkeypatch.setattr(actor, "_init_db", paused)
    return entered, release


@pytest.mark.asyncio
@pytest.mark.parametrize("encrypted", [False, True])
async def test_stop_closes_admission_and_coalesces_callers(tmp_path, monkeypatch, encrypted):
    if encrypted:
        monkeypatch.setenv("CORTEX_VAULT_KEY", Fernet.generate_key().decode())
    actor = BFTLedgerActor(tmp_path / "closing.db")
    entered, release = await hold_init(actor, monkeypatch)
    pending = first = second = None
    try:
        await actor.start()
        await bounded(entered.wait())
        pending = actor.append(event())
        first = asyncio.create_task(actor.stop())
        await bounded(actor._stop_event.wait())
        with pytest.raises(RuntimeError, match="stopping"):
            actor.append(event(2))
        second = asyncio.create_task(actor.stop())
        release.set()
        await bounded(asyncio.gather(first, second))
        assert (await bounded(pending))["seq"] == 1
        await bounded(actor._queue.join())
        assert actor._task is not None and actor._task.done()
    finally:
        release.set()
        await cleanup(actor, pending, first, second)


@pytest.mark.asyncio
async def test_cancelling_stop_waiter_does_not_cancel_writer(tmp_path, monkeypatch):
    actor = BFTLedgerActor(tmp_path / "stop-waiter.db")
    entered, release = await hold_init(actor, monkeypatch)
    pending = stopping = None
    try:
        await actor.start()
        await bounded(entered.wait())
        pending = actor.append(event())
        stopping = asyncio.create_task(actor.stop())
        await bounded(actor._stop_event.wait())
        stopping.cancel()
        await asyncio.gather(stopping, return_exceptions=True)
        assert actor._task is not None and not actor._task.done()
        release.set()
        await bounded(actor.stop())
        assert (await bounded(pending))["seq"] == 1
        assert await actor.verify_chain()
    finally:
        release.set()
        await cleanup(actor, pending, stopping)


@pytest.mark.asyncio
@pytest.mark.parametrize("when", ["before-worker-start", "during-init", "during-processing"])
async def test_worker_failure_makes_all_accepted_futures_terminal(tmp_path, monkeypatch, when):
    actor = BFTLedgerActor(tmp_path / "worker-fatal.db")
    release = asyncio.Event()
    if when == "during-init":

        async def failed_init(db):
            await release.wait()
            raise aiosqlite.OperationalError("fixture init failure")

        monkeypatch.setattr(actor, "_init_db", failed_init)
    elif when == "during-processing":

        async def failed_tx(*args, **kwargs):
            raise RuntimeError("fixture fatal transaction")

        monkeypatch.setattr(actor, "_execute_insert_tx", failed_tx)
    pending = []
    try:
        await actor.start()
        pending = [actor.append(event(i)) for i in range(4)]
        if when == "before-worker-start":
            assert actor._task is not None
            actor._task.cancel()
        release.set()
        results = await bounded(asyncio.gather(*pending, return_exceptions=True))
        assert all(isinstance(result, RuntimeError) for result in results)
        await bounded(actor.stop())
        await bounded(actor._queue.join())
        with pytest.raises(RuntimeError, match="Zombie Actor Prevention"):
            actor.append(event(99))
    finally:
        release.set()
        await cleanup(actor, *pending)


@pytest.mark.asyncio
async def test_double_start_is_rejected_without_replacing_live_worker(tmp_path):
    actor = BFTLedgerActor(tmp_path / "single-worker.db")
    pending = None
    try:
        results = await asyncio.gather(actor.start(), actor.start(), return_exceptions=True)
        assert sum(isinstance(result, RuntimeError) for result in results) == 1
        worker = actor._task
        pending = actor.append(event())
        assert (await bounded(pending))["seq"] == 1
        assert actor._task is worker
        await bounded(actor.stop())
    finally:
        await cleanup(actor, pending)


def test_restart_on_new_event_loop_keeps_encrypted_idempotency(tmp_path, monkeypatch):
    monkeypatch.setenv("CORTEX_VAULT_KEY", Fernet.generate_key().decode())
    actor = BFTLedgerActor(tmp_path / "different-loops.db")

    async def cycle():
        pending = None
        try:
            await actor.start()
            pending = actor.append(event())
            result = await bounded(pending)
            await bounded(actor.stop())
            return result
        finally:
            await cleanup(actor, pending)

    results = [asyncio.run(cycle()) for _ in range(3)]
    assert results == [results[0]] * 3
    assert asyncio.run(actor.verify_chain())


@pytest.mark.asyncio
@pytest.mark.parametrize("created_at", [None, "", "2026-10-28T00:00:00Z"])
async def test_retry_uses_canonical_plaintext_and_original_timestamp(tmp_path, monkeypatch, created_at):
    key = Fernet.generate_key()
    monkeypatch.setenv("CORTEX_VAULT_KEY", key.decode())
    actor = BFTLedgerActor(tmp_path / "canonical-retry.db")
    pending = []
    try:
        await actor.start()
        pending.append(actor.append(event(payload={"b": 2, "a": 1}, created_at=created_at)))
        first = await bounded(pending[-1])
        pending.append(actor.append(event(payload={"a": 1, "b": 2}, created_at=created_at)))
        assert await bounded(pending[-1]) == first
        async with aiosqlite.connect(actor._db_path) as db:
            rows = list(await (await db.execute("SELECT payload_json FROM ledger_entries")).fetchall())
        assert len(rows) == 1
        assert Fernet(key).decrypt(rows[0][0][6:].encode()) == b'{"a":1,"b":2}'
        await bounded(actor.stop())
    finally:
        await cleanup(actor, *pending)


@pytest.mark.asyncio
@pytest.mark.parametrize("mode", ["missing", "wrong"])
async def test_unavailable_original_key_rejects_retry_but_not_next_event(tmp_path, monkeypatch, mode):
    monkeypatch.setenv("CORTEX_VAULT_KEY", Fernet.generate_key().decode())
    actor = BFTLedgerActor(tmp_path / "key-unavailable.db")
    pending = []
    try:
        await actor.start()
        pending.append(actor.append(event()))
        first = await bounded(pending[-1])
        async with aiosqlite.connect(actor._db_path) as db:
            before = await (await db.execute("SELECT * FROM ledger_entries")).fetchall()
        if mode == "missing":
            monkeypatch.delenv("CORTEX_VAULT_KEY")
        else:
            monkeypatch.setenv("CORTEX_VAULT_KEY", Fernet.generate_key().decode())
        pending.append(actor.append(event()))
        with pytest.raises(ValueError, match="C5ENC"):
            await bounded(pending[-1])
        pending.append(actor.append(event(2)))
        assert (await bounded(pending[-1]))["seq"] == 2
        async with aiosqlite.connect(actor._db_path) as db:
            after = await (await db.execute("SELECT * FROM ledger_entries WHERE seq=1")).fetchall()
        assert after == before and first["seq"] == 1
        assert await actor.verify_chain()
        await bounded(actor.stop())
    finally:
        await cleanup(actor, *pending)


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "field,value",
    [("stream", "other"), ("entity_id", "other"), ("event_type", "OTHER"), ("created_at", "2000-01-01T00:00:00Z")],
)
async def test_same_event_id_with_different_persisted_metadata_is_rejected(tmp_path, field, value):
    actor = BFTLedgerActor(tmp_path / "metadata-collision.db")
    pending = []
    try:
        await actor.start()
        pending.append(actor.append(event()))
        await bounded(pending[-1])
        pending.append(actor.append(event(**{field: value})))
        with pytest.raises(ValueError, match="Collision"):
            await bounded(pending[-1])
        pending.append(actor.append(event(2)))
        assert (await bounded(pending[-1]))["seq"] == 2
        assert await actor.verify_chain()
        await bounded(actor.stop())
    finally:
        await cleanup(actor, *pending)


@pytest.mark.asyncio
async def test_forced_uuid_collision_keeps_existing_payload_and_writer_live(tmp_path, monkeypatch):
    from babylon60.bft import ledger_actor as module

    actor = BFTLedgerActor(tmp_path / "forced-collision.db")
    pending = []
    try:
        await actor.start()
        pending.append(actor.append(event()))
        first = await bounded(pending[-1])
        assert vars(module)["uuid"] is uuid
        uuid5 = uuid.uuid5
        monkeypatch.setattr(uuid, "uuid5", lambda *args: uuid.UUID(first["event_id"]))
        pending.append(actor.append(event(payload={"index": 999})))
        with pytest.raises(ValueError, match="Collision"):
            await bounded(pending[-1])
        monkeypatch.setattr(uuid, "uuid5", uuid5)
        pending.append(actor.append(event(2)))
        assert (await bounded(pending[-1]))["seq"] == 2
        assert await actor.verify_chain()
        await bounded(actor.stop())
    finally:
        await cleanup(actor, *pending)


@pytest.mark.asyncio
async def test_cancelled_reply_does_not_kill_worker_or_duplicate_commit(tmp_path, monkeypatch):
    actor = BFTLedgerActor(tmp_path / "cancelled-reply.db")
    entered, release = await hold_init(actor, monkeypatch)
    first = second = None
    try:
        await actor.start()
        await bounded(entered.wait())
        first = actor.append(event())
        first.cancel()
        second = actor.append(event(2))
        release.set()
        assert (await bounded(second))["seq"] == 2
        assert first.cancelled()
        assert await actor.verify_chain()
        await bounded(actor.stop())
    finally:
        release.set()
        await cleanup(actor, first, second)


@pytest.mark.asyncio
async def test_rollback_failure_is_fatal_and_fails_queue(tmp_path, monkeypatch):
    actor = BFTLedgerActor(tmp_path / "rollback-failed.db")
    initialize = actor._init_db
    attempts = []

    async def initialized(db):
        await initialize(db)

        async def broken_rollback():
            attempts.append("rollback")
            raise aiosqlite.OperationalError("fixture rollback failed")

        monkeypatch.setattr(db, "rollback", broken_rollback)

    monkeypatch.setattr(actor, "_init_db", initialized)
    pending = []
    try:
        await actor.start()
        pending = [actor.append(event(stream="")), actor.append(event(2)), actor.append(event(3))]
        results = await bounded(asyncio.gather(*pending, return_exceptions=True))
        assert all(isinstance(result, RuntimeError) for result in results)
        assert attempts == ["rollback"]
        await bounded(actor.stop())
        await bounded(actor._queue.join())
        async with aiosqlite.connect(actor._db_path) as db:
            row = await (await db.execute("SELECT COUNT(*) FROM ledger_entries")).fetchone()
            assert row is not None and row[0] == 0
    finally:
        await cleanup(actor, *pending)


@pytest.mark.asyncio
async def test_failed_commit_rolls_back_and_following_request_commits(tmp_path, monkeypatch):
    actor = BFTLedgerActor(tmp_path / "commit-failed.db")
    initialize = actor._init_db
    trace: list[str] = []

    async def initialized(db):
        await initialize(db)
        await db.set_trace_callback(trace.append)
        original = db.commit
        first = True

        async def commit_once_failed():
            nonlocal first
            if first:
                first = False
                raise aiosqlite.OperationalError("fixture commit rejected before SQLite commit")
            await original()

        monkeypatch.setattr(db, "commit", commit_once_failed)

    monkeypatch.setattr(actor, "_init_db", initialized)
    pending = []
    try:
        await actor.start()
        pending.append(actor.append(event()))
        with pytest.raises(aiosqlite.OperationalError):
            await bounded(pending[-1])
        pending.append(actor.append(event(2)))
        assert (await bounded(pending[-1]))["seq"] == 1
        assert sum(sql.strip().upper() == "ROLLBACK" for sql in trace) == 1
        assert await actor.verify_chain()
        await bounded(actor.stop())
    finally:
        await cleanup(actor, *pending)


@pytest.mark.asyncio
async def test_worker_cancel_during_commit_waits_for_sql_and_settles_all_futures(tmp_path, monkeypatch):
    actor = BFTLedgerActor(tmp_path / "cancel-commit.db")
    initialize = actor._init_db
    entered, release = asyncio.Event(), asyncio.Event()
    live = {}

    async def initialized(db):
        await initialize(db)
        live["db"] = db
        original = db.commit

        async def paused_commit():
            entered.set()
            await release.wait()
            await original()

        monkeypatch.setattr(db, "commit", paused_commit)

    monkeypatch.setattr(actor, "_init_db", initialized)
    pending = []
    try:
        await actor.start()
        pending = [actor.append(event()), actor.append(event(2))]
        await bounded(entered.wait())
        assert live["db"].in_transaction
        assert not pending[0].done()
        async with aiosqlite.connect(actor._db_path) as observer:
            row = await (await observer.execute("SELECT COUNT(*) FROM ledger_entries")).fetchone()
            assert row is not None and row[0] == 0
        assert actor._task is not None
        actor._task.cancel()
        await bounded(actor._stop_event.wait())
        with pytest.raises(RuntimeError, match="stopping"):
            actor.append(event(3))
        release.set()
        assert (await bounded(pending[0]))["seq"] == 1
        with pytest.raises(RuntimeError):
            await bounded(pending[1])
        await bounded(actor.stop())
        assert actor._task is not None and actor._task.cancelled()
        assert await actor.verify_chain()
    finally:
        release.set()
        await cleanup(actor, *pending)


@pytest.mark.asyncio
async def test_queue_full_does_not_prevent_graceful_drain(tmp_path, monkeypatch):
    actor = BFTLedgerActor(tmp_path / "bounded-queue.db")
    entered, release = await hold_init(actor, monkeypatch)
    pending = []
    try:
        await actor.start()
        await bounded(entered.wait())
        assert actor._queue.maxsize == 4096
        monkeypatch.setattr(actor._queue, "_maxsize", 2)  # Small owned fixture queue, same lifecycle.
        pending = [actor.append(event(1)), actor.append(event(2))]
        with pytest.raises(asyncio.QueueFull):
            actor.append(event(3))
        stopping = asyncio.create_task(actor.stop())
        await bounded(actor._stop_event.wait())
        release.set()
        await bounded(stopping)
        assert [result["seq"] for result in await bounded(asyncio.gather(*pending))] == [1, 2]
        await bounded(actor._queue.join())
    finally:
        release.set()
        await cleanup(actor, *pending)


@pytest.mark.asyncio
async def test_worker_connection_retains_wal_full_and_schema(tmp_path, monkeypatch):
    actor = BFTLedgerActor(tmp_path / "worker-pragmas.db")
    initialize = actor._init_db
    observed = {}

    async def inspected(db):
        await initialize(db)
        observed["journal_mode"] = (await (await db.execute("PRAGMA journal_mode")).fetchone())[0]
        observed["synchronous"] = (await (await db.execute("PRAGMA synchronous")).fetchone())[0]
        observed["columns"] = [r[1] for r in await (await db.execute("PRAGMA table_info(ledger_entries)")).fetchall()]

    monkeypatch.setattr(actor, "_init_db", inspected)
    pending = None
    try:
        await actor.start()
        pending = actor.append(event())
        await bounded(pending)
        await bounded(actor.stop())
        assert observed["journal_mode"] == "wal"
        assert observed["synchronous"] == 2
        assert observed["columns"] == [
            "seq",
            "event_id",
            "stream",
            "entity_id",
            "event_type",
            "payload_json",
            "source_db",
            "source_table",
            "source_pk",
            "cortex_taint",
            "lamport_t",
            "prev_hash",
            "entry_hash",
            "created_at",
            "agent_id",
        ]
    finally:
        await cleanup(actor, pending)


@pytest.mark.asyncio
@pytest.mark.parametrize("encrypted", [False, True])
async def test_warmup_and_concurrent_retries_preserve_chain(tmp_path, monkeypatch, encrypted):
    if encrypted:
        monkeypatch.setenv("CORTEX_VAULT_KEY", Fernet.generate_key().decode())
    actor = BFTLedgerActor(tmp_path / "concurrent.db")
    pending = []
    try:
        await actor.start()
        pending.append(actor.append(event(0)))
        await bounded(pending[-1])
        pending.extend(actor.append(event(i)) for _ in range(4) for i in range(1, 33))
        results = await asyncio.wait_for(asyncio.gather(*pending), timeout=10)
        assert len({result["event_id"] for result in results}) == 33
        assert len({result["seq"] for result in results}) == 33
        await bounded(actor.stop())
        async with aiosqlite.connect(actor._db_path) as db:
            rows = list(await (await db.execute("SELECT seq,lamport_t FROM ledger_entries ORDER BY seq")).fetchall())
        assert rows == [(i, i) for i in range(1, 34)]
        assert await actor.verify_chain()
    finally:
        await cleanup(actor, *pending)
