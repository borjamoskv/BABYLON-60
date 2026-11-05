# ============================================================================
# BABYLON-60 v4.0 Sovereign Hardened
# █ AUTOCOGNITION-Ω | STATE: C5-REAL | AESTHETIC: INDUSTRIAL_NOIR_2026
# ============================================================================
from __future__ import annotations
import os
import asyncio
import uuid
from dataclasses import dataclass
import base64
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Mapping, Optional, TypedDict
from cryptography.fernet import Fernet, InvalidToken
import aiosqlite
from blake3 import blake3
from babylon60.bft.integrity import LedgerCheckpoint


class BFTCausalInvariantError(RuntimeError):
    """FAIL-FAST Exception for violations of Babylon.lean BFT invariants."""


from babylon60.bft.cortex_crypto_kernel import (  # noqa: E402
    _canonical_json,
    compute_envelope_hash,
    build_merkle_tree,
    MerkleMountainRange,
    ZERO_HASH_256,
)

NAMESPACE_UUID = uuid.UUID("9897d6fd-d6a7-4fe9-86bc-f0c312886d5d")
ZERO_HASH = "0" * 64
ACTOR_HASH_VERSION = 2


class LedgerEntryResult(TypedDict):
    seq: int
    event_id: str
    entry_hash: str


class StateAttestation(TypedDict):
    total_entries: int
    max_lamport: int
    max_seq: int
    merkle_root: str
    mmr_root: str
    integrity_verified: bool
    attested_at: str
    rekor_anchor: Optional[Dict[str, object]]


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
    created_at: str,
) -> str:
    """Exact historical SHA3-256 format, including stored bytes and UTC metadata."""
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
    return compute_envelope_hash(envelope)


def _compute_payload_hash(payload_json: str) -> str:
    return blake3(b"B60-BFT-PAYLOAD-v2\x00" + payload_json.encode("utf-8")).hexdigest()


def _compute_entry_hash_v2(
    event_id: str, stream: str, entity_id: str, event_type: str, payload_hash: str,
    source_db: str, source_table: str, source_pk: str, cortex_taint: str,
    logical_tick: int, prev_hash: str,
) -> str:
    """BLAKE3 commitment to semantic content and logical order; UTC is metadata."""
    if type(logical_tick) is not int or logical_tick <= 0:
        raise ValueError("BFT logical_tick must be a positive integer")
    envelope = {
        "hash_version": ACTOR_HASH_VERSION, "hash_algorithm": "blake3",
        "event_id": event_id, "stream": stream, "entity_id": entity_id,
        "event_type": event_type, "payload_hash": payload_hash,
        "source_db": source_db, "source_table": source_table, "source_pk": source_pk,
        "cortex_taint": cortex_taint, "logical_tick": logical_tick, "prev_hash": prev_hash,
    }
    return blake3(b"B60-BFT-ENTRY-v2\x00" + _canonical_json(envelope).encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class LedgerEvent:
    stream: str
    entity_id: str
    event_type: str
    payload: Mapping[str, object] | Dict[str, object]
    cortex_taint: str
    source_db: str
    source_table: str
    source_pk: str
    created_at: Optional[str] = None
    agent_id: str = ""


def cortex_event_to_ledger_event(event: Any) -> LedgerEvent:
    """Mapea un CortexEvent al contrato de evento estructurado de LedgerEvent (BFTLedgerActor)."""
    return LedgerEvent(
        stream="cortex",
        entity_id=getattr(event, "agent_id", "ULTRATHINK-APEX") or "ULTRATHINK-APEX",
        event_type=getattr(event, "event_type", "UNKNOWN"),
        payload=getattr(event, "payload", {}),
        cortex_taint=getattr(event, "cortex_taint", "C5_TAINT"),
        source_db=getattr(event, "domain", "babylon60.com") or "babylon60.com",
        source_table="cortex_ledger",
        source_pk=getattr(event, "agent_id", "ULTRATHINK-APEX") or "ULTRATHINK-APEX",
        agent_id=getattr(event, "agent_id", ""),
    )


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
    created_at: str,
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
    def __init__(self, db_path: Path) -> None:
        self._db_path = db_path
        self._queue: asyncio.Queue[tuple[LedgerEvent, asyncio.Future[LedgerEntryResult]]] = asyncio.Queue(maxsize=4096)
        self._task: Optional[asyncio.Task[None]] = None
        self._stop_event = asyncio.Event()
        self._wake_event = asyncio.Event()
        self._state = "stopped"

    @staticmethod
    def _fail_pending(queue: asyncio.Queue[tuple[LedgerEvent, asyncio.Future[LedgerEntryResult]]]) -> None:
        while not queue.empty():
            _, future = queue.get_nowait()
            if not future.done():
                future.set_exception(RuntimeError("BFTLedgerActor worker stopped before processing accepted request"))
            queue.task_done()

    def _worker_done(
        self, task: asyncio.Task[None],
        queue: asyncio.Queue[tuple[LedgerEvent, asyncio.Future[LedgerEntryResult]]],
    ) -> None:
        # Also handles cancellation before the worker executes its first line.
        failed = task.cancelled() or task.exception() is not None
        self._fail_pending(queue)
        if self._task is task:
            self._state = "failed" if failed else "stopped"

    async def start(self) -> None:
        if self._task is not None:
            if not self._task.done():
                raise RuntimeError("BFTLedgerActor: actor already running or stopping")
            self._worker_done(self._task, self._queue)
        # The facade may reuse the actor via separate asyncio.run() calls.
        self._queue = asyncio.Queue(maxsize=4096)
        self._stop_event = asyncio.Event()
        self._wake_event = asyncio.Event()
        self._state = "running"
        queue = self._queue
        self._task = asyncio.create_task(self._worker())
        self._task.add_done_callback(lambda task: self._worker_done(task, queue))

    async def stop(self) -> None:
        task, queue = self._task, self._queue
        if task is None:
            return
        self._state = "stopping"  # Close admission before the first await.
        self._stop_event.set()
        self._wake_event.set()
        if not task.done():
            # A cancelled stop caller cannot cancel an in-flight SQLite operation.
            await asyncio.shield(asyncio.gather(task, return_exceptions=True))
        self._worker_done(task, queue)

    def append(self, event: LedgerEvent) -> asyncio.Future[LedgerEntryResult]:
        if self._task is None:
            raise RuntimeError("BFTLedgerActor: actor not started")
        if self._task.done():
            self._worker_done(self._task, self._queue)
            exc = None if self._task.cancelled() else self._task.exception()
            raise RuntimeError(
                f"Zombie Actor Prevention triggered: worker task terminated unexpectedly. Exception: {exc}"
            ) from exc
        if self._state != "running":
            raise RuntimeError("BFTLedgerActor: actor is stopping; admission is closed")
        loop = asyncio.get_running_loop()
        future: asyncio.Future[LedgerEntryResult] = loop.create_future()
        try:
            self._queue.put_nowait((event, future))
        except asyncio.QueueFull:
            future.cancel()
            raise
        self._wake_event.set()
        return future

    async def _verified_checkpoint(self) -> LedgerCheckpoint:
        async with aiosqlite.connect(self._db_path) as db:
            await db.execute("BEGIN")
            policy = await self._hash_policy(db)
            if policy is None:
                cursor = await db.execute("SELECT * FROM ledger_entries ORDER BY seq ASC")
            else:
                cursor = await db.execute(
                    "SELECT e.*, h.hash_version, h.hash_algorithm, h.payload_hash FROM ledger_entries e "
                    "LEFT JOIN ledger_entry_hashes h USING(event_id) ORDER BY e.seq ASC"
                )
            rows = list(await cursor.fetchall())
            if policy is not None:
                cursor = await db.execute("SELECT COUNT(*) FROM ledger_entry_hashes")
                metadata_count = await cursor.fetchone()
                if metadata_count is None or metadata_count[0] != len(rows):
                    raise BFTCausalInvariantError("INV_BFT_LEAN_05: Hash metadata truncation or orphan detected")
            prev_hash = ZERO_HASH
            expected_seq = 1
            last_lamport = 0
            legacy_tip = ZERO_HASH
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
                version, algorithm, payload_hash = (1, "sha3-256", None) if policy is None else row[15:18]
                if version == 1 and algorithm == "sha3-256" and payload_hash is None:
                    if policy is not None and seq > policy[0]:
                        raise BFTCausalInvariantError(f"INV_BFT_LEAN_04: Legacy hash downgrade at seq {seq}")
                    # Legacy binds stored ciphertext bytes, so it remains verifiable without a vault key.
                    computed_hash = _compute_entry_hash(
                        event_id, stream, entity_id, event_type, payload_json, source_db, source_table,
                        source_pk, cortex_taint, lamport_t, row_prev_hash, created_at,
                    )
                    legacy_tip = entry_hash
                elif version == ACTOR_HASH_VERSION and algorithm == "blake3":
                    if policy is None or seq <= policy[0]:
                        raise BFTCausalInvariantError(f"INV_BFT_LEAN_04: Altered legacy hash version at seq {seq}")
                    # V2 excludes randomized ciphertext. Authenticate its link to the semantic commitment
                    # by decrypting; unlike legacy, encrypted V2 verification requires the original key.
                    try:
                        vault_key = os.environ.get("CORTEX_VAULT_KEY")
                        vault = Fernet(vault_key.encode("utf-8")) if vault_key else None
                        canonical_payload = self._plaintext(payload_json, vault)
                    except ValueError as exc:
                        raise BFTCausalInvariantError(f"INV_BFT_LEAN_04: Payload authentication at seq {seq}: {exc}") from exc
                    if payload_hash != _compute_payload_hash(canonical_payload):
                        raise BFTCausalInvariantError(f"INV_BFT_LEAN_04: Payload commitment mismatch at seq {seq}")
                    computed_hash = _compute_entry_hash_v2(
                        event_id, stream, entity_id, event_type, payload_hash, source_db, source_table,
                        source_pk, cortex_taint, lamport_t, row_prev_hash,
                    )
                else:
                    raise BFTCausalInvariantError(f"INV_BFT_LEAN_04: Unsupported or missing hash version at seq {seq}")
                if entry_hash != computed_hash:
                    raise BFTCausalInvariantError(f"INV_BFT_LEAN_04 (merkle_proof): Hash mismatch at seq {seq}")
                prev_hash = entry_hash
                last_lamport = lamport_t
                expected_seq += 1
            if policy is not None and (policy[0] > len(rows) or legacy_tip != policy[1]):
                raise BFTCausalInvariantError("INV_BFT_LEAN_04: Legacy migration checkpoint mismatch")
            cursor = await db.execute("SELECT seq FROM sqlite_sequence WHERE name='ledger_entries'")
            high_water = await cursor.fetchone()
            if (high_water[0] if high_water else 0) != expected_seq - 1:
                raise BFTCausalInvariantError("INV_BFT_LEAN_05: Ledger truncation detected")
            return LedgerCheckpoint(expected_seq - 1, prev_hash)

    async def verify_chain(self, *, expected_checkpoint: LedgerCheckpoint | None = None) -> bool:
        """Verify a snapshot; encrypted V2 requires its vault key. A trusted checkpoint detects rollback."""
        checkpoint = await self._verified_checkpoint()
        if expected_checkpoint is not None and checkpoint != expected_checkpoint:
            raise BFTCausalInvariantError("INV_BFT_LEAN_05: Trusted checkpoint mismatch")
        return True

    async def get_checkpoint(self) -> LedgerCheckpoint:
        return await self._verified_checkpoint()

    async def get_merkle_root(self) -> str:
        """Computa la raíz de Merkle canónica sobre todos los entry_hash de ledger_entries."""
        async with aiosqlite.connect(self._db_path) as db:
            cursor = await db.execute("SELECT entry_hash FROM ledger_entries ORDER BY seq ASC")
            rows = await cursor.fetchall()
            leaves = [r[0] for r in rows]
            if not leaves:
                return ZERO_HASH_256
            return build_merkle_tree(leaves)

    async def get_mmr_root(self) -> str:
        """Computa la raíz del acumulador MMR O(log N) sobre todos los entry_hash."""
        async with aiosqlite.connect(self._db_path) as db:
            cursor = await db.execute("SELECT entry_hash FROM ledger_entries ORDER BY seq ASC")
            rows = await cursor.fetchall()
            mmr = MerkleMountainRange()
            for r in rows:
                mmr.append(r[0])
            return mmr.get_root()

    async def get_state_attestation(self) -> StateAttestation:
        """
        Retorna un manifiesto de atestación criptográfica del estado actual del ledger BFT.
        Unifica la semántica de atestación con CortexPersistLedger para verificación de evidencia.
        """
        async with aiosqlite.connect(self._db_path) as db:
            cursor = await db.execute(
                "SELECT COUNT(*), COALESCE(MAX(lamport_t), 0), COALESCE(MAX(seq), 0) FROM ledger_entries"
            )
            row = await cursor.fetchone()
            total_entries = row[0] if row else 0
            max_lamport = row[1] if row else 0
            max_seq = row[2] if row else 0

            cursor = await db.execute("SELECT entry_hash FROM ledger_entries ORDER BY seq ASC")
            rows = await cursor.fetchall()
            leaves = [r[0] for r in rows]
            merkle_root = build_merkle_tree(leaves) if leaves else ZERO_HASH_256

            mmr = MerkleMountainRange()
            for r in rows:
                mmr.append(r[0])
            mmr_root = mmr.get_root()

        integrity_verified = False
        try:
            integrity_verified = await self.verify_chain()
        except Exception:
            integrity_verified = False

        return {
            "total_entries": total_entries,
            "max_lamport": max_lamport,
            "max_seq": max_seq,
            "merkle_root": merkle_root,
            "mmr_root": mmr_root,
            "integrity_verified": integrity_verified,
            "attested_at": datetime.now(timezone.utc).isoformat(),
            "rekor_anchor": None,
        }

    async def anchor_to_rekor(
        self,
        rekor_client: Optional[Any] = None,
        seed_hex: Optional[str] = None,
    ) -> Optional[Dict[str, object]]:
        """
        Ancla el ledger-head (merkle_root + max_lamport + timestamp) en Sigstore Rekor.
        Satisface el requisito del Art. 12 EU AI Act de sellado temporal por terceros (P1).
        """
        attestation = await self.get_state_attestation()
        head_data = {
            "merkle_root": attestation["merkle_root"],
            "max_lamport": attestation["max_lamport"],
            "total_entries": attestation["total_entries"],
            "attested_at": attestation["attested_at"],
        }
        head_json = _canonical_json(head_data).encode("utf-8")
        payload_hash = hashlib.sha256(head_json).hexdigest()

        from nacl.signing import SigningKey

        seed = seed_hex or os.environ.get("BABYLON60_SIGNING_SEED", "").strip()
        if seed:
            try:
                sk = SigningKey(bytes.fromhex(seed))
            except Exception:
                sk = SigningKey.generate()
        else:
            sk = SigningKey.generate()

        signed = sk.sign(head_json)
        sig_b64 = base64.b64encode(signed.signature).decode("utf-8")
        pk_b64 = base64.b64encode(sk.verify_key.encode()).decode("utf-8")

        if rekor_client is None:
            try:
                from babylon60.crypto.rekor_client import RekorClient

                rekor_client = RekorClient()
            except ImportError:
                return None

        anchor_res = rekor_client.anchor_payload(payload_hash, sig_b64, pk_b64)
        return dict(anchor_res) if anchor_res else None

    def append_cortex_event(self, event: Any) -> asyncio.Future[LedgerEntryResult]:
        """
        Fachada de ingestión síncrona/asíncrona compatible con CortexEvent en BFTLedgerActor.
        Mapea el esquema simplificado de CortexEvent al contrato exhaustivo de LedgerEvent.
        """
        ledger_event = cortex_event_to_ledger_event(event)
        return self.append(ledger_event)

    async def _dispatch(
        self,
        db: aiosqlite.Connection,
        queue: asyncio.Queue[tuple[LedgerEvent, asyncio.Future[LedgerEntryResult]]],
        event: LedgerEvent,
        future: asyncio.Future[LedgerEntryResult],
    ) -> bool:
        cancellation_requested = False
        try:
            process = asyncio.create_task(self._process(db, event, future))
            # INV_C5_19: bounded by completion of the shielded process task.
            while not process.done():
                try:
                    await asyncio.shield(process)
                except asyncio.CancelledError:
                    if process.cancelled():
                        raise
                    # aiosqlite still runs SQL already queued to its thread.
                    self._state = "stopping"
                    self._stop_event.set()
                    cancellation_requested = True
            process.result()
        except (ValueError, aiosqlite.Error) as exc:
            if not future.done():
                future.set_exception(exc)
            if db.in_transaction:
                raise RuntimeError("FAIL-FAST: transaction cleanup left an active transaction") from exc
        except BaseException as exc:
            if not future.done():
                future.set_exception(
                    exc
                    if isinstance(exc, Exception)
                    else RuntimeError("BFTLedgerActor request interrupted; outcome may be committed")
                )
            if isinstance(exc, asyncio.CancelledError):
                raise
            raise RuntimeError("FAIL-FAST: General Exception intercepted on process") from exc
        finally:
            if not future.done():
                future.set_exception(RuntimeError("BFTLedgerActor process returned without a result"))
            queue.task_done()
        return cancellation_requested

    async def _worker(self) -> None:
        queue = self._queue
        try:
            async with aiosqlite.connect(self._db_path, isolation_level=None, timeout=5.0) as db:
                try:
                    await db.create_function("c5_compute_hash", 12, _compute_entry_hash_wrapper, deterministic=True)
                    await db.execute("PRAGMA journal_mode=WAL")
                    await db.execute("PRAGMA synchronous = FULL")
                    await db.execute("PRAGMA foreign_keys=ON")
                    await db.execute("PRAGMA busy_timeout=5000")
                    await self._init_db(db)
                    # INV_C5_19: stop requested AND queue drained is the explicit exit condition.
                    while not (self._stop_event.is_set() and queue.empty()):
                        if queue.empty():
                            self._wake_event.clear()
                            await self._wake_event.wait()
                            continue
                        event, future = queue.get_nowait()
                        if await self._dispatch(db, queue, event, future):
                            raise asyncio.CancelledError
                        try:
                            await db.execute("PRAGMA wal_checkpoint(TRUNCATE)")
                        except Exception as exc:
                            import logging
                            logging.warning("WAL checkpoint deferred: %s", exc)
                finally:
                    self._state = "stopping"
                    self._fail_pending(queue)
        finally:
            self._state = "stopping"
            self._fail_pending(queue)

    @staticmethod
    async def _hash_policy(db: aiosqlite.Connection) -> tuple[int, str] | None:
        cursor = await db.execute(
            "SELECT name FROM sqlite_master WHERE type='table' "
            "AND name IN ('ledger_entry_hashes', 'ledger_hash_policy')"
        )
        tables = {row[0] for row in await cursor.fetchall()}
        if not tables:
            return None  # An unmarked database is interpreted only with the exact legacy hash.
        if len(tables) != 2:
            raise BFTCausalInvariantError("INV_BFT_LEAN_04: Incomplete ledger hash migration")
        cursor = await db.execute(
            "SELECT singleton, schema_version, legacy_max_seq, legacy_tip_hash FROM ledger_hash_policy"
        )
        policies = list(await cursor.fetchall())
        if len(policies) != 1:
            raise BFTCausalInvariantError("INV_BFT_LEAN_04: Missing ledger hash policy")
        singleton, schema_version, legacy_max_seq, legacy_tip_hash = policies[0]
        if (singleton != 1 or schema_version != ACTOR_HASH_VERSION or type(legacy_max_seq) is not int
                or legacy_max_seq < 0 or not isinstance(legacy_tip_hash, str)
                or len(legacy_tip_hash) != 64 or any(c not in "0123456789abcdef" for c in legacy_tip_hash)
                or (legacy_max_seq == 0 and legacy_tip_hash != ZERO_HASH)):
            raise BFTCausalInvariantError("INV_BFT_LEAN_04: Unsupported or invalid ledger hash policy")
        return legacy_max_seq, legacy_tip_hash

    async def _init_db(self, db: aiosqlite.Connection) -> None:
        # Detection, additive migration and admission guards share the writer lock. Never rewrite
        # historical rows, their hashes, or sqlite_sequence; older clients cannot append legacy rows.
        try:
            await db.execute("BEGIN IMMEDIATE")
            await self._create_legacy_schema(db)
            if await self._hash_policy(db) is None:
                await db.execute(
                    "CREATE TABLE ledger_entry_hashes (event_id TEXT PRIMARY KEY NOT NULL "
                    "REFERENCES ledger_entries(event_id) DEFERRABLE INITIALLY DEFERRED, "
                    "hash_version INTEGER NOT NULL, hash_algorithm TEXT NOT NULL, payload_hash TEXT)"
                )
                await db.execute(
                    "CREATE TABLE ledger_hash_policy (singleton INTEGER PRIMARY KEY CHECK(singleton = 1), "
                    "schema_version INTEGER NOT NULL, legacy_max_seq INTEGER NOT NULL, legacy_tip_hash TEXT NOT NULL)"
                )
                await db.execute(
                    "INSERT INTO ledger_entry_hashes SELECT event_id, 1, 'sha3-256', NULL FROM ledger_entries"
                )
                await db.execute(
                    "INSERT INTO ledger_hash_policy VALUES (1, ?, "
                    "(SELECT COALESCE(MAX(seq), 0) FROM ledger_entries), "
                    "COALESCE((SELECT entry_hash FROM ledger_entries ORDER BY seq DESC LIMIT 1), ?))",
                    (ACTOR_HASH_VERSION, ZERO_HASH),
                )
            for table in ("ledger_entry_hashes", "ledger_hash_policy"):
                for action in ("UPDATE", "DELETE"):
                    await db.execute(
                        f"CREATE TRIGGER IF NOT EXISTS trg_{table}_immutable_{action.lower()} "
                        f"BEFORE {action} ON {table} BEGIN "
                        "SELECT RAISE(ABORT, 'C5 BFT: immutable hash metadata'); END"
                    )
            await db.execute(
                "CREATE TRIGGER IF NOT EXISTS trg_ledger_hash_v2_insert BEFORE INSERT ON ledger_entries "
                "WHEN NOT EXISTS (SELECT 1 FROM ledger_entry_hashes WHERE event_id=NEW.event_id "
                "AND hash_version=2 AND hash_algorithm='blake3' AND length(payload_hash)=64) "
                "BEGIN SELECT RAISE(ABORT, 'C5 BFT: new entries require hash version 2'); END"
            )
            await db.commit()
        except BaseException:
            if db.in_transaction:
                await db.rollback()
            if db.in_transaction:
                raise RuntimeError("FAIL-FAST: hash migration rollback could not be confirmed")
            raise

    async def _create_legacy_schema(self, db: aiosqlite.Connection) -> None:
        await db.execute(
            "\n            CREATE TABLE IF NOT EXISTS ledger_entries (\n                seq INTEGER PRIMARY KEY AUTOINCREMENT,\n                event_id TEXT NOT NULL UNIQUE,\n                stream TEXT NOT NULL CHECK (length(stream) > 0),\n                entity_id TEXT NOT NULL CHECK (length(entity_id) > 0),\n                event_type TEXT NOT NULL CHECK (length(event_type) > 0),\n                payload_json TEXT NOT NULL CHECK (length(payload_json) >= 2),\n                source_db TEXT NOT NULL CHECK (length(source_db) > 0),\n                source_table TEXT NOT NULL CHECK (length(source_table) > 0),\n                source_pk TEXT NOT NULL CHECK (length(source_pk) > 0),\n                cortex_taint TEXT NOT NULL CHECK (length(cortex_taint) > 0),\n                lamport_t INTEGER NOT NULL CHECK (lamport_t > 0),\n                prev_hash TEXT NOT NULL CHECK (length(prev_hash) = 64 AND prev_hash GLOB '[0-9a-f]*'),\n                entry_hash TEXT NOT NULL UNIQUE CHECK (length(entry_hash) = 64 AND entry_hash GLOB '[0-9a-f]*'),\n                created_at TEXT NOT NULL,\n                agent_id TEXT NOT NULL DEFAULT '',\n                UNIQUE(lamport_t, agent_id)\n            );\n        "
        )
        await db.execute(
            "\n            CREATE TRIGGER IF NOT EXISTS trg_ledger_immutable_update BEFORE UPDATE ON ledger_entries\n            BEGIN SELECT RAISE(ABORT, 'C5 BFT: immutable master ledger'); END;\n        "
        )
        await db.execute(
            "\n            CREATE TRIGGER IF NOT EXISTS trg_ledger_immutable_delete BEFORE DELETE ON ledger_entries\n            BEGIN SELECT RAISE(ABORT, 'C5 BFT: immutable master ledger'); END;\n        "
        )

    @staticmethod
    def _plaintext(stored_payload: str, vault: Fernet | None) -> str:
        if stored_payload.startswith("C5ENC:"):
            if vault is None:
                raise ValueError("C5ENC idempotency requires the original vault key")
            try:
                stored_payload = vault.decrypt(stored_payload[6:].encode("ascii")).decode("utf-8")
            except (InvalidToken, UnicodeError, ValueError) as exc:
                raise ValueError("C5ENC idempotency cannot authenticate stored payload") from exc
        try:
            canonical = _canonical_json(json.loads(stored_payload))
        except (TypeError, ValueError) as exc:
            raise ValueError("Invalid persisted canonical payload") from exc
        if canonical != stored_payload:
            raise ValueError("Noncanonical persisted payload")
        return canonical

    async def _existing_result(
        self, db: aiosqlite.Connection, event_id: str, event: LedgerEvent,
        payload_json: str, vault: Fernet | None,
    ) -> tuple[int, str] | None:
        cursor = await db.execute(
            "SELECT seq, entry_hash, payload_json, stream, entity_id, event_type, "
            "source_db, source_table, source_pk, cortex_taint, created_at "
            "FROM ledger_entries WHERE event_id = ?", (event_id,),
        )
        row = await cursor.fetchone()
        if row is None:
            return None
        semantics = (event.stream, event.entity_id, event.event_type, event.source_db,
                     event.source_table, event.source_pk, event.cortex_taint)
        if (self._plaintext(str(row[2]), vault) != payload_json or tuple(row[3:10]) != semantics
                or (event.created_at and row[10] != event.created_at)):
            raise ValueError(f"Fail-fast: INV_BFT_04 Collision on event_id {event_id}: payload or metadata mismatch")
        return int(row[0]), str(row[1])

    async def _check_vault_continuity(self, db: aiosqlite.Connection, vault: Fernet | None) -> None:
        if vault is None:
            return  # Plaintext appends do not introduce another encryption key.
        cursor = await db.execute(
            "SELECT e.payload_json, h.payload_hash FROM ledger_entries e "
            "JOIN ledger_entry_hashes h USING(event_id) "
            "WHERE h.hash_version=2 AND substr(e.payload_json, 1, 6)='C5ENC:' ORDER BY e.seq DESC LIMIT 1"
        )
        previous = await cursor.fetchone()
        if previous is not None:
            # V2 has a single current vault key, not a keyring. Reject a changed key before accepting
            # a new encrypted row whose content could not be verified with the preceding V2 rows.
            plaintext = self._plaintext(previous[0], vault)
            if _compute_payload_hash(plaintext) != previous[1]:
                raise ValueError("C5ENC previous V2 payload does not match its semantic commitment")

    async def _execute_insert_tx(
        self, db: aiosqlite.Connection, event_id: str, event: LedgerEvent, stored_payload: str, created_at: str,
        *, payload_json: str | None = None, vault: Fernet | None = None,
    ) -> tuple[int, str]:
        if db.in_transaction:
            raise RuntimeError("FAIL-FAST: writer entered with an active transaction")
        canonical_payload = payload_json if payload_json is not None else self._plaintext(stored_payload, vault)
        try:
            await db.execute("BEGIN IMMEDIATE")
            existing = await self._existing_result(db, event_id, event, canonical_payload, vault)
            if existing is not None:
                await db.commit()
                return existing
            await self._check_vault_continuity(db, vault)
            cursor = await db.execute(
                "SELECT COALESCE(MAX(lamport_t), 0) + 1, "
                "COALESCE((SELECT entry_hash FROM ledger_entries ORDER BY seq DESC LIMIT 1), ?) FROM ledger_entries",
                (ZERO_HASH,),
            )
            head = await cursor.fetchone()
            if head is None:
                raise RuntimeError("BFT ledger head unavailable")
            logical_tick, prev_hash = head
            payload_hash = _compute_payload_hash(canonical_payload)
            entry_hash = _compute_entry_hash_v2(
                event_id, event.stream, event.entity_id, event.event_type, payload_hash,
                event.source_db, event.source_table, event.source_pk, event.cortex_taint, logical_tick, prev_hash,
            )
            # Deferred FK permits the metadata first; the ledger insert guard requires this V2 marker.
            await db.execute(
                "INSERT INTO ledger_entry_hashes (event_id, hash_version, hash_algorithm, payload_hash) "
                "VALUES (?, ?, 'blake3', ?)", (event_id, ACTOR_HASH_VERSION, payload_hash),
            )
            cursor = await db.execute(
                "INSERT INTO ledger_entries (event_id, stream, entity_id, event_type, payload_json, "
                "source_db, source_table, source_pk, cortex_taint, lamport_t, prev_hash, entry_hash, created_at) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?) "
                "ON CONFLICT(event_id) DO NOTHING RETURNING seq, entry_hash",
                (
                    event_id,
                    event.stream,
                    event.entity_id,
                    event.event_type,
                    stored_payload,
                    event.source_db,
                    event.source_table,
                    event.source_pk,
                    event.cortex_taint,
                    logical_tick,
                    prev_hash,
                    entry_hash,
                    created_at,
                ),
            )
            db_row = await cursor.fetchone()
            if db_row is None:
                existing = await self._existing_result(db, event_id, event, canonical_payload, vault)
                if existing is None:
                    raise RuntimeError("Insertion failed: event_id not persisted and not found")
                await db.commit()
                return existing
            await db.commit()
            return int(db_row[0]), str(db_row[1])
        except BaseException:
            try:
                if db.in_transaction:
                    await db.rollback()
                if db.in_transaction:
                    raise RuntimeError("rollback left an active transaction")
            except BaseException as cleanup_error:
                raise RuntimeError("FAIL-FAST: transaction rollback could not be confirmed") from cleanup_error
            raise

    async def _process(
        self, db: aiosqlite.Connection, event: LedgerEvent, future: asyncio.Future[LedgerEntryResult]
    ) -> None:
        if not event.cortex_taint or not isinstance(event.cortex_taint, str):
            raise ValueError("INV_BFT_03: cortex_taint must be a non-empty string representing the causal trace")
        payload_json = _canonical_json(event.payload)
        created_at = event.created_at or datetime.now(timezone.utc).isoformat(timespec="microseconds").replace(
            "+00:00", "Z"
        )
        idempotent_key = (
            f"{event.source_db}\x1f{event.source_table}\x1f{event.source_pk}\x1f{payload_json}\x1f{event.cortex_taint}"
        )
        event_id = str(uuid.uuid5(NAMESPACE_UUID, idempotent_key))
        vault_key = os.environ.get("CORTEX_VAULT_KEY")
        vault = Fernet(vault_key.encode("utf-8")) if vault_key else None
        if vault is not None:
            stored_payload = vault.encrypt(payload_json.encode("utf-8")).decode("utf-8")
            stored_payload = f"C5ENC:{stored_payload}"
        else:
            stored_payload = payload_json
        seq, entry_hash = await self._execute_insert_tx(
            db, event_id, event, stored_payload, created_at, payload_json=payload_json, vault=vault,
        )

        # Broadcast to Rust via Iceoryx2 PyO3 FFI
        try:
            import strike_rs

            strike_rs.py_publish_exergy_packet(
                "BABYLON_BFT_LEDGER", "PYTHON_ORCHESTRATOR", "RUST_BFT_HYPERVISOR", seq
            )
        except ImportError:
            pass
        except Exception as e:
            import logging

            logging.warning(f"Failed to publish IPC binary packet via iceoryx2: {e}")

        if not future.done():
            future.set_result({"seq": seq, "event_id": event_id, "entry_hash": entry_hash})
