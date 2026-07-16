from __future__ import annotations
import os
import signal
import asyncio
import hashlib
import json
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional
from cryptography.fernet import Fernet
import aiosqlite
NAMESPACE_UUID = uuid.UUID('9897d6fd-d6a7-4fe9-86bc-f0c312886d5d')
ZERO_HASH = '0' * 64

def _canonical_json(data: Any) -> str:
    return json.dumps(data, sort_keys=True, separators=(',', ':'), ensure_ascii=False, allow_nan=False)

def _compute_entry_hash(event_id: str, stream: str, entity_id: str, event_type: str, payload_json: str, source_db: str, source_table: str, source_pk: str, cortex_taint: str, lamport_t: int, prev_hash: str, created_at: str) -> str:
    envelope = {'event_id': event_id, 'stream': stream, 'entity_id': entity_id, 'event_type': event_type, 'payload_json': payload_json, 'source_db': source_db, 'source_table': source_table, 'source_pk': source_pk, 'cortex_taint': cortex_taint, 'lamport_t': lamport_t, 'prev_hash': prev_hash, 'created_at': created_at}
    return hashlib.sha256(_canonical_json(envelope).encode('utf-8')).hexdigest()

@dataclass(frozen=True)
class LedgerEvent:
    stream: str
    entity_id: str
    event_type: str
    payload: Dict[str, Any]
    cortex_taint: str
    source_db: str
    source_table: str
    source_pk: str
    created_at: Optional[str] = None

def _compute_entry_hash_wrapper(event_id: str, stream: str, entity_id: str, event_type: str, payload_json: str, source_db: str, source_table: str, source_pk: str, cortex_taint: str, lamport_t: int, prev_hash: str, created_at: str) -> str:
    return _compute_entry_hash(event_id, stream, entity_id, event_type, payload_json, source_db, source_table, source_pk, cortex_taint, lamport_t, prev_hash, created_at)


class BFTLedgerActor:

    def __init__(self, db_path: Path) -> None:
        self._db_path = db_path
        self._queue: asyncio.Queue[tuple[LedgerEvent, asyncio.Future[Dict[str, Any]]]] = asyncio.Queue()
        self._task: Optional[asyncio.Task[None]] = None

    async def start(self) -> None:
        self._task = asyncio.create_task(self._worker())

    async def stop(self) -> None:
        if self._task and not self._task.done():
            await asyncio.gather(self._queue.join(), return_exceptions=True)
            self._task.cancel()
            await asyncio.gather(self._task, return_exceptions=True)

    def append(self, event: LedgerEvent) -> asyncio.Future[Dict[str, Any]]:
        if self._task is None:
            raise RuntimeError('BFTLedgerActor: actor not started')
        if self._task.done():
            exc = self._task.exception()
            raise RuntimeError(f'Zombie Actor Prevention triggered: worker task terminated unexpectedly. Exception: {exc}') from exc
        loop = asyncio.get_running_loop()
        future: asyncio.Future[Dict[str, Any]] = loop.create_future()
        self._queue.put_nowait((event, future))
        return future

    async def verify_chain(self) -> bool:
        async with aiosqlite.connect(self._db_path) as db:
            await db.create_function('c5_compute_hash', 12, _compute_entry_hash_wrapper, deterministic=True)
            cursor = await db.execute('SELECT * FROM ledger_entries ORDER BY seq ASC')
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
                    return False
                if lamport_t <= last_lamport:
                    return False
                if row_prev_hash != prev_hash:
                    return False
                vault_key = os.environ.get('CORTEX_VAULT_KEY')
                if vault_key and payload_json.startswith('C5ENC:'):
                    fernet = Fernet(vault_key.encode('utf-8'))
                    payload_json = fernet.decrypt(payload_json[6:].encode('utf-8')).decode('utf-8')
                computed_hash = _compute_entry_hash(event_id=event_id, stream=stream, entity_id=entity_id, event_type=event_type, payload_json=payload_json, source_db=source_db, source_table=source_table, source_pk=source_pk, cortex_taint=cortex_taint, lamport_t=lamport_t, prev_hash=row_prev_hash, created_at=created_at)
                if entry_hash != computed_hash:
                    return False
                prev_hash = entry_hash
                last_lamport = lamport_t
                expected_seq += 1
            return True

    async def _worker(self) -> None:
        async with aiosqlite.connect(self._db_path, isolation_level=None, timeout=5.0) as db:
            await db.create_function('c5_compute_hash', 12, _compute_entry_hash_wrapper, deterministic=True)
            await db.execute('PRAGMA journal_mode=WAL')
            await db.execute('PRAGMA synchronous=FULL')
            await db.execute('PRAGMA foreign_keys=ON')
            await db.execute('PRAGMA busy_timeout=5000')
            await self._init_db(db)
            while True:
                await asyncio.sleep(0)
                get_res = await asyncio.gather(self._queue.get(), return_exceptions=True)
                if isinstance(get_res[0], asyncio.CancelledError):
                    break
                if isinstance(get_res[0], BaseException):
                    os.kill(os.getpid(), signal.SIGKILL)
                    raise RuntimeError('FAIL-FAST: General Exception intercepted on queue get.')
                event, future = get_res[0]
                process_res = await asyncio.gather(self._process(db, event, future), return_exceptions=True)
                if isinstance(process_res[0], ValueError):
                    if not future.done():
                        future.set_exception(process_res[0])
                elif isinstance(process_res[0], BaseException):
                    os.kill(os.getpid(), signal.SIGKILL)
                    raise RuntimeError(f'FAIL-FAST: General Exception intercepted on process: {process_res[0]}')
                self._queue.task_done()

    async def _init_db(self, db: aiosqlite.Connection) -> None:
        await db.execute("\n            CREATE TABLE IF NOT EXISTS ledger_entries (\n                seq INTEGER PRIMARY KEY AUTOINCREMENT,\n                event_id TEXT NOT NULL UNIQUE,\n                stream TEXT NOT NULL CHECK (length(stream) > 0),\n                entity_id TEXT NOT NULL CHECK (length(entity_id) > 0),\n                event_type TEXT NOT NULL CHECK (length(event_type) > 0),\n                payload_json TEXT NOT NULL CHECK (length(payload_json) >= 2),\n                source_db TEXT NOT NULL CHECK (length(source_db) > 0),\n                source_table TEXT NOT NULL CHECK (length(source_table) > 0),\n                source_pk TEXT NOT NULL CHECK (length(source_pk) > 0),\n                cortex_taint TEXT NOT NULL CHECK (length(cortex_taint) > 0),\n                lamport_t INTEGER NOT NULL UNIQUE CHECK (lamport_t > 0),\n                prev_hash TEXT NOT NULL CHECK (length(prev_hash) = 64 AND prev_hash GLOB '[0-9a-f]*'),\n                entry_hash TEXT NOT NULL UNIQUE CHECK (length(entry_hash) = 64 AND entry_hash GLOB '[0-9a-f]*'),\n                created_at TEXT NOT NULL\n            );\n        ")
        await db.execute("\n            CREATE TRIGGER IF NOT EXISTS trg_ledger_immutable_update BEFORE UPDATE ON ledger_entries\n            BEGIN SELECT RAISE(ABORT, 'C5 BFT: immutable master ledger'); END;\n        ")
        await db.execute("\n            CREATE TRIGGER IF NOT EXISTS trg_ledger_immutable_delete BEFORE DELETE ON ledger_entries\n            BEGIN SELECT RAISE(ABORT, 'C5 BFT: immutable master ledger'); END;\n        ")

    async def _execute_insert_tx(self, db: aiosqlite.Connection, event_id: str, event: LedgerEvent, stored_payload: str, created_at: str) -> tuple[int, str]:
        await db.execute('BEGIN IMMEDIATE')
        cursor = await db.execute('SELECT seq, entry_hash FROM ledger_entries WHERE event_id = ?', (event_id,))
        row = await cursor.fetchone()
        if row:
            await db.execute('COMMIT')
            return int(row[0]), str(row[1])
        cursor = await db.execute("INSERT INTO ledger_entries (\n                event_id, stream, entity_id, event_type, payload_json,\n                source_db, source_table, source_pk, cortex_taint,\n                lamport_t, prev_hash, entry_hash, created_at\n            ) VALUES (\n                ?, ?, ?, ?, ?, ?, ?, ?, ?,\n                COALESCE((SELECT MAX(lamport_t) FROM ledger_entries), 0) + 1,\n                COALESCE((SELECT entry_hash FROM ledger_entries ORDER BY seq DESC LIMIT 1), '0000000000000000000000000000000000000000000000000000000000000000'),\n                c5_compute_hash(?, ?, ?, ?, ?, ?, ?, ?, ?, COALESCE((SELECT MAX(lamport_t) FROM ledger_entries), 0) + 1, COALESCE((SELECT entry_hash FROM ledger_entries ORDER BY seq DESC LIMIT 1), '0000000000000000000000000000000000000000000000000000000000000000'), ?),\n                ?\n            )\n            ON CONFLICT(event_id) DO NOTHING\n            RETURNING seq, entry_hash", (event_id, event.stream, event.entity_id, event.event_type, stored_payload, event.source_db, event.source_table, event.source_pk, event.cortex_taint, event_id, event.stream, event.entity_id, event.event_type, stored_payload, event.source_db, event.source_table, event.source_pk, event.cortex_taint, created_at, created_at))
        db_row = await cursor.fetchone()
        if db_row is None:
            cursor = await db.execute('SELECT seq, entry_hash FROM ledger_entries WHERE event_id = ?', (event_id,))
            db_row = await cursor.fetchone()
            if db_row is None:
                raise RuntimeError('Insertion failed: event_id not persisted and not found')
        await db.execute('COMMIT')
        return int(db_row[0]), str(db_row[1])

    async def _process(self, db: aiosqlite.Connection, event: LedgerEvent, future: asyncio.Future[Dict[str, Any]]) -> None:
        if not event.cortex_taint or not isinstance(event.cortex_taint, str):
            raise ValueError('INV_BFT_03: cortex_taint must be a non-empty string representing the causal trace')
        payload_json = _canonical_json(event.payload)
        created_at = event.created_at or datetime.now(timezone.utc).isoformat(timespec='microseconds').replace('+00:00', 'Z')
        idempotent_key = f'{event.source_db}\x1f{event.source_table}\x1f{event.source_pk}\x1f{payload_json}\x1f{event.cortex_taint}'
        event_id = str(uuid.uuid5(NAMESPACE_UUID, idempotent_key))
        vault_key = os.environ.get('CORTEX_VAULT_KEY')
        if vault_key:
            fernet = Fernet(vault_key.encode('utf-8'))
            stored_payload = fernet.encrypt(payload_json.encode('utf-8')).decode('utf-8')
            stored_payload = f'C5ENC:{stored_payload}'
        else:
            stored_payload = payload_json
        tx_res = await asyncio.gather(self._execute_insert_tx(db, event_id, event, stored_payload, created_at), return_exceptions=True)
        if isinstance(tx_res[0], BaseException):
            exc = tx_res[0]
            rollback_res = await asyncio.gather(db.execute('ROLLBACK'), return_exceptions=True)
            if isinstance(rollback_res[0], BaseException):
                await asyncio.gather(db.close(), return_exceptions=True)
                future.set_exception(exc)
                raise RuntimeError('Cascading Rollback Defense triggered: connection aborted during rollback') from rollback_res[0]
            future.set_exception(exc)
        else:
            seq, entry_hash = tx_res[0]
            future.set_result({'seq': seq, 'event_id': event_id, 'entry_hash': entry_hash})