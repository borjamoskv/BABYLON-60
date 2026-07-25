from __future__ import annotations

import asyncio
import hashlib
import json
import time
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from babylon60.bft.lexicon import BFTLexicon
import aiosqlite

import babylon60.database.core
from babylon60.bft.payload_encryptor import PayloadEncryptor
from babylon60.core.crypto import _check_no_floats


class BFTCausalInvariantError(RuntimeError):
    pass


NAMESPACE_UUID = uuid.UUID("9897d6fd-d6a7-4fe9-86bc-f0c312886d5d")
ZERO_HASH = "0" * 64

INIT_TABLE_SQL = """
            CREATE TABLE IF NOT EXISTS ledger_entries (
                seq INTEGER PRIMARY KEY AUTOINCREMENT,
                event_id TEXT NOT NULL UNIQUE,
                stream TEXT NOT NULL CHECK (length(stream) > 0),
                entity_id TEXT NOT NULL CHECK (length(entity_id) > 0),
                event_type TEXT NOT NULL CHECK (length(event_type) > 0),
                payload_json TEXT NOT NULL CHECK (length(payload_json) >= 2),
                source_db TEXT NOT NULL CHECK (length(source_db) > 0),
                source_table TEXT NOT NULL CHECK (length(source_table) > 0),
                source_pk TEXT NOT NULL CHECK (length(source_pk) > 0),
                cortex_taint TEXT NOT NULL CHECK (length(cortex_taint) > 0),
                lamport_t INTEGER NOT NULL CHECK (lamport_t > 0),
                prev_hash TEXT NOT NULL CHECK (length(prev_hash) = 64 AND prev_hash GLOB '[0-9a-f]*'),
                entry_hash TEXT NOT NULL UNIQUE CHECK (length(entry_hash) = 64 AND entry_hash GLOB '[0-9a-f]*'),
                created_at INTEGER NOT NULL,
                agent_id TEXT NOT NULL DEFAULT '',
                UNIQUE(lamport_t, agent_id)
            );
"""
INIT_TRIG_UPDATE_SQL = """
            CREATE TRIGGER IF NOT EXISTS trg_ledger_immutable_update BEFORE UPDATE ON ledger_entries
            BEGIN SELECT RAISE(ABORT, 'C5 BFT: immutable master ledger'); END;
"""
INIT_TRIG_DELETE_SQL = """
            CREATE TRIGGER IF NOT EXISTS trg_ledger_immutable_delete BEFORE DELETE ON ledger_entries
            BEGIN SELECT RAISE(ABORT, 'C5 BFT: immutable master ledger'); END;
"""

INSERT_TX_SQL = """INSERT INTO ledger_entries (
                event_id, stream, entity_id, event_type, payload_json,
                source_db, source_table, source_pk, cortex_taint,
                lamport_t, prev_hash, entry_hash, created_at
            ) VALUES (
                ?, ?, ?, ?, ?, ?, ?, ?, ?,
                COALESCE((SELECT MAX(lamport_t) FROM ledger_entries), 0) + 1,
                COALESCE((SELECT entry_hash FROM ledger_entries ORDER BY seq DESC LIMIT 1), '0000000000000000000000000000000000000000000000000000000000000000'),
                c5_compute_hash(?, ?, ?, ?, ?, ?, ?, ?, ?, COALESCE((SELECT MAX(lamport_t) FROM ledger_entries), 0) + 1, COALESCE((SELECT entry_hash FROM ledger_entries ORDER BY seq DESC LIMIT 1), '0000000000000000000000000000000000000000000000000000000000000000'), ?),
                ?
            )
            ON CONFLICT(event_id) DO NOTHING
            RETURNING seq, entry_hash"""


def _canonical_json(data: Any) -> str:
    _check_no_floats(data)
    return json.dumps(data, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False)


def _compute_entry_hash(
    event_id: str,
    stream: str,
    entity_id: str,
    event_type: str,
    payload_json: str,
    source_db: str,
    source_table: str,
    source_pk: str,
    cortex_taint: str,
    lamport_t: int,
    prev_hash: str,
    created_at: int,
) -> str:
    envelope = {
        "event_id": event_id,
        "stream": stream,
        "entity_id": entity_id,
        "event_type": event_type,
        "payload_json": payload_json,
        "source_db": source_db,
        "source_table": source_table,
        "source_pk": source_pk,
        "cortex_taint": cortex_taint,
        "lamport_t": lamport_t,
        "prev_hash": prev_hash,
        "created_at": created_at,
    }
    return hashlib.sha3_256(_canonical_json(envelope).encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class LedgerEvent:
    stream: str
    entity_id: str
    event_type: str
    payload: dict[str, Any]
    cortex_taint: str
    source_db: str
    source_table: str
    source_pk: str
    created_at: int | None = None


def _compute_entry_hash_wrapper(
    event_id: str,
    stream: str,
    entity_id: str,
    event_type: str,
    payload_json: str,
    source_db: str,
    source_table: str,
    source_pk: str,
    cortex_taint: str,
    lamport_t: int,
    prev_hash: str,
    created_at: int,
) -> str:
    return _compute_entry_hash(
        event_id,
        stream,
        entity_id,
        event_type,
        payload_json,
        source_db,
        source_table,
        source_pk,
        cortex_taint,
        lamport_t,
        prev_hash,
        created_at,
    )


class BFTLedgerActor:
    def __init__(self, db_path: Path, lexicon: BFTLexicon | None = None, queue_maxsize: int = 10000) -> None:
        self._db_path = db_path
        self._queue: asyncio.Queue[tuple[LedgerEvent, asyncio.Future[dict[str, Any]]]] = asyncio.Queue(
            maxsize=queue_maxsize
        )
        self._task: asyncio.Task[None] | None = None
        self._encryptor = PayloadEncryptor()
        self._events_processed = 0
        self._start_time = 0.0
        if lexicon is None:
            from babylon60.bft.lexicon import BFTLexicon

            self.lexicon = BFTLexicon()
        else:
            self.lexicon = lexicon

    async def start(self) -> None:
        self._task = asyncio.create_task(self._worker())

    async def stop(self) -> None:
        if self._task and (not self._task.done()):
            await asyncio.gather(self._queue.join(), return_exceptions=True)
            self._task.cancel()
            await asyncio.gather(self._task, return_exceptions=True)

    def append(self, event: LedgerEvent) -> asyncio.Future[dict[str, Any]]:
        if self._task is None:
            raise RuntimeError("BFTLedgerActor: actor not started")
        if self._task.done():
            exc = self._task.exception()
            raise RuntimeError(
                f"Zombie Actor Prevention triggered: worker task terminated unexpectedly. Exception: {exc}"
            ) from exc
        loop = asyncio.get_running_loop()
        future: asyncio.Future[dict[str, Any]] = loop.create_future()
        self._queue.put_nowait((event, future))
        return future

    async def verify_chain(self) -> bool:
        db = await babylon60.database.core.connect(self._db_path)
        try:
            await db.create_function("c5_compute_hash", 12, _compute_entry_hash_wrapper, deterministic=True)
            cursor = await db.execute("SELECT * FROM ledger_entries ORDER BY seq ASC")
            rows = await cursor.fetchall()
            prev_hash = ZERO_HASH
            expected_seq = 1
            last_lamport = 0
            for row in rows:
                seq = row[0]
                event_id = row[1]
                stream = row[2]
                entity_id = row[3]
                event_type = row[4]
                payload_json = row[5]
                source_db = row[6]
                source_table = row[7]
                source_pk = row[8]
                cortex_taint = row[9]
                lamport_t = row[10]
                row_prev_hash = row[11]
                entry_hash = row[12]
                created_at = row[13]
                if seq != expected_seq:
                    raise BFTCausalInvariantError(
                        f"INV_BFT_LEAN_03 (seq_monotone): Sequence gap at expected seq {expected_seq}"
                    )
                if lamport_t <= last_lamport:
                    raise BFTCausalInvariantError(
                        f"INV_BFT_LEAN_01 (causal_strict): lamport_t {lamport_t} is not strictly greater than {last_lamport}"
                    )
                if row_prev_hash != prev_hash:
                    raise BFTCausalInvariantError(
                        f"INV_BFT_LEAN_02 (causal_antisymm): Hash chain cycle or break detected at seq {seq}"
                    )
                computed_hash = _compute_entry_hash(
                    event_id=event_id,
                    stream=stream,
                    entity_id=entity_id,
                    event_type=event_type,
                    payload_json=payload_json,
                    source_db=source_db,
                    source_table=source_table,
                    source_pk=source_pk,
                    cortex_taint=cortex_taint,
                    lamport_t=lamport_t,
                    prev_hash=row_prev_hash,
                    created_at=created_at,
                )
                if entry_hash != computed_hash:
                    raise BFTCausalInvariantError(f"INV_BFT_LEAN_04 (merkle_proof): Hash mismatch at seq {seq}")
                prev_hash = entry_hash
                last_lamport = lamport_t
                expected_seq += 1
            return True
        finally:
            await db.close()

    async def _worker(self) -> None:
        self._start_time = time.time()
        db = await babylon60.database.core.connect(self._db_path)
        try:
            await db.create_function("c5_compute_hash", 12, _compute_entry_hash_wrapper, deterministic=True)
            await self._init_db(db)
            while True:
                try:
                    event, future = await self._queue.get()
                except asyncio.CancelledError:
                    break
                try:
                    await self._process(db, event, future)
                    self._events_processed += 1
                except ValueError as ve:
                    if not future.done():
                        future.set_exception(ve)
                except BaseException as exc:
                    if not future.done():
                        future.set_exception(exc)
                    self._queue.task_done()
                    raise RuntimeError(f"FAIL-FAST: {exc}") from exc
                self._queue.task_done()
        finally:
            await db.close()

    def get_throughput(self) -> float:
        elapsed = time.time() - self._start_time
        if elapsed > 0:
            return self._events_processed / elapsed
        return 0.0

    async def _init_db(self, db: aiosqlite.Connection) -> None:
        await db.execute(INIT_TABLE_SQL)
        await db.execute(INIT_TRIG_UPDATE_SQL)
        await db.execute(INIT_TRIG_DELETE_SQL)

    async def _execute_insert_tx(
        self,
        db: aiosqlite.Connection,
        event_id: str,
        event: LedgerEvent,
        semantic_hash: str,
        stored_payload: str,
        created_at: int,
    ) -> tuple[int, str]:
        await db.execute("BEGIN IMMEDIATE")
        cursor = await db.execute("SELECT seq, entry_hash FROM ledger_entries WHERE event_id = ?", (event_id,))
        row = await cursor.fetchone()
        if row:
            await db.execute("COMMIT")
            return (int(row[0]), str(row[1]))
        cursor = await db.execute(
            INSERT_TX_SQL,
            (
                event_id,
                event.stream,
                event.entity_id,
                semantic_hash,
                stored_payload,
                event.source_db,
                event.source_table,
                event.source_pk,
                event.cortex_taint,
                event_id,
                event.stream,
                event.entity_id,
                semantic_hash,
                stored_payload,
                event.source_db,
                event.source_table,
                event.source_pk,
                event.cortex_taint,
                created_at,
                created_at,
            ),
        )
        db_row = await cursor.fetchone()
        if db_row is None:
            cursor = await db.execute("SELECT seq, entry_hash FROM ledger_entries WHERE event_id = ?", (event_id,))
            db_row = await cursor.fetchone()
            if db_row is None:
                raise RuntimeError("Insertion failed: event_id not persisted and not found")
        await db.execute("COMMIT")
        return (int(db_row[0]), str(db_row[1]))

    async def _process(
        self, db: aiosqlite.Connection, event: LedgerEvent, future: asyncio.Future[dict[str, Any]]
    ) -> None:
        if not event.cortex_taint or not isinstance(event.cortex_taint, str):
            raise ValueError("INV_BFT_03: cortex_taint must be a non-empty string representing the causal trace")
        payload_json = _canonical_json(event.payload)
        created_at = event.created_at or int(time.time() * 1000)
        idempotent_key = (
            f"{event.source_db}\x1f{event.source_table}\x1f{event.source_pk}\x1f{payload_json}\x1f{event.cortex_taint}"
        )
        event_id = str(uuid.uuid5(NAMESPACE_UUID, idempotent_key))
        stored_payload = self._encryptor.encrypt(payload_json)
        from babylon60.bft.lexicon import LEXICON_NAMESPACE

        if len(event.event_type) != 36:
            semantic_hash = str(uuid.uuid5(LEXICON_NAMESPACE, f"TYPE::{event.event_type}"))
        else:
            semantic_hash = event.event_type
        if not self.lexicon.resolve_hash(semantic_hash):
            raise BFTCausalInvariantError(
                f"INV_BFT_LEAN_05 (semantic_strict): event_type '{event.event_type}' (Hash: {semantic_hash}) is not registered in Lexicon DAG."
            )
        tx_res = await asyncio.gather(
            self._execute_insert_tx(db, event_id, event, semantic_hash, stored_payload, created_at),
            return_exceptions=True,
        )
        if isinstance(tx_res[0], BaseException):
            exc = tx_res[0]
            rollback_res = await asyncio.gather(db.execute("ROLLBACK"), return_exceptions=True)
            if isinstance(rollback_res[0], BaseException):
                await asyncio.gather(db.close(), return_exceptions=True)
                future.set_exception(exc)
                raise RuntimeError(
                    "Cascading Rollback Defense triggered: connection aborted during rollback"
                ) from rollback_res[0]
            future.set_exception(exc)
        else:
            seq, entry_hash = tx_res[0]
            future.set_result({"seq": seq, "event_id": event_id, "entry_hash": entry_hash})
