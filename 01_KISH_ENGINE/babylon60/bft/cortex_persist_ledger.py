# [Causal-Determinist] Exergy-Maximized
"""
CORTEX PERSIST LEDGER — ULTRATHINK Cryptographic BFT Ledger
============================================================
Modulo de persistencia criptográfica inmutable para BABYLON-60.
Combina firma digital Ed25519, encadenamiento SHA3-256, SQLite WAL
con busy_timeout=5000ms, idempotencia UUID v5 y ordenamiento Lamport.

Invariantes:
  - INV_BFT_02: WAL mode + busy_timeout=5000ms.
  - INV_BFT_03: Causal taint obligatorio en cada insert.
  - INV_BFT_04: Claves de idempotencia UUID v5.
  - INV_C5_10: Serialización PyNaCl limpia (sin _seed / _public_key).
  - INV_C5_17: 100% Soberano, Gratis y Auto-hospedado.

Authorship: Borja Moskv (borjamoskv)
"""

from __future__ import annotations

import base64
import hashlib
import json
import logging
import os
import sqlite3
import uuid
from collections.abc import Callable
from contextlib import closing
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, TypedDict

from babylon60.bft.cortex_crypto_kernel import (
    _canonical_json,
    canonical_idempotency_key,
    compute_cortex_hash as compute_cortex_hash,
    observation_commitment,
    build_merkle_tree,
    generate_merkle_proof,
    legacy_unit_separator_key,
    require_ed25519_seed,
    verify_merkle_proof,
    verify_row_invariants,
    ZERO_HASH_256,
    NAMESPACE_CORTEX,
    MerkleMountainRange,
    MerkleProof,
    MMRProofStep,
)
from babylon60.bft.integrity import LedgerCheckpoint

logger = logging.getLogger("babylon60.bft.cortex_persist")


def _event_ids(event: CortexEvent, payload_json: str) -> tuple[str, str]:
    """New length-prefixed id, plus the historical unit-separator id for replay."""
    fields = (event.event_type, payload_json, event.cortex_taint, event.agent_id, event.domain)
    current = str(uuid.uuid5(NAMESPACE_CORTEX, canonical_idempotency_key(*fields)))
    legacy = str(uuid.uuid5(NAMESPACE_CORTEX, legacy_unit_separator_key(*fields)))
    return current, legacy

CortexLedgerRow = Tuple[str, str, str, str, str, str, int, str, str, str, int, str]
CORTEX_HASH_VERSION = 3


class EventResult(TypedDict):
    seq: int
    event_id: str
    entry_hash: str
    lamport_t: int
    status: str


class BatchProcessResult(TypedDict):
    seq: int
    event_id: str
    entry_hash: str
    lamport_t: int
    status: str
    row: Optional[CortexLedgerRow]


class MMREventProof(TypedDict):
    leaf_index: int
    total_leaves: int
    peak_index: int
    inner_proof: list[MMRProofStep]
    other_peaks: list[str]
    mmr_root: str
    leaf_hash: str


class StateAttestation(TypedDict):
    total_entries: int
    max_lamport: int
    max_seq: int
    merkle_root: str
    mmr_root: str
    integrity_verified: bool
    attested_at: str
    rekor_anchor: Optional[Dict[str, object]]


@dataclass(frozen=True)
class CortexEvent:
    event_type: str
    payload: Dict[str, object]
    cortex_taint: str
    agent_id: str = "ULTRATHINK-APEX"
    domain: str = "babylon60.com"

    def to_ledger_event(self) -> Any:
        """Convierte este CortexEvent al contrato canónico LedgerEvent para BFTLedgerActor."""
        from babylon60.bft.ledger_actor import LedgerEvent

        return LedgerEvent(
            stream="cortex",
            entity_id=self.agent_id,
            event_type=self.event_type,
            payload=self.payload,
            cortex_taint=self.cortex_taint,
            source_db=self.domain,
            source_table="cortex_ledger",
            source_pk=self.agent_id,
            agent_id=self.agent_id,
        )


class CortexPersistLedger:
    """
    Motor de Persistencia CORTEX PERSIST (ULTRATHINK Edition).
    Actor de hilo único con SQLite WAL, hash-chaining SHA3-256 e inmutabilidad.
    """

    def __init__(self, db_path: Path | str) -> None:
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(str(self.db_path), timeout=5.0)
        try:
            conn.execute("PRAGMA journal_mode=WAL;")
            conn.execute("PRAGMA busy_timeout=5000;")
            conn.execute("PRAGMA synchronous = FULL;")
        except BaseException:
            conn.close()
            raise
        return conn

    def _init_db(self) -> None:
        with closing(self._get_connection()) as conn, conn:
            conn.execute("BEGIN IMMEDIATE")
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS cortex_ledger (
                    seq INTEGER PRIMARY KEY AUTOINCREMENT,
                    event_id TEXT NOT NULL UNIQUE,
                    event_type TEXT NOT NULL,
                    payload_json TEXT NOT NULL,
                    cortex_taint TEXT NOT NULL,
                    agent_id TEXT NOT NULL,
                    domain TEXT NOT NULL DEFAULT 'babylon60.com',
                    lamport_t INTEGER NOT NULL,
                    prev_hash TEXT NOT NULL,
                    entry_hash TEXT NOT NULL UNIQUE,
                    timestamp TEXT NOT NULL,
                    hash_version INTEGER NOT NULL DEFAULT 1,
                    observation_hash TEXT
                );
                """
            )
            # Preserve historical bytes/hashes. Existing rows remain v1; all
            # new inserts explicitly select v3 (logical chain plus observation seal).
            columns = {row[1] for row in conn.execute("PRAGMA table_info(cortex_ledger)")}
            if "hash_version" not in columns:
                conn.execute("ALTER TABLE cortex_ledger ADD COLUMN hash_version INTEGER NOT NULL DEFAULT 1")
                logger.info("Cortex hash schema upgraded: existing rows retain version 1")
            if "observation_hash" not in columns:
                conn.execute("ALTER TABLE cortex_ledger ADD COLUMN observation_hash TEXT")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_cortex_event_type_seq ON cortex_ledger (event_type, seq DESC)")
            # Triggers de inmutabilidad BFT
            conn.execute(
                """
                CREATE TRIGGER IF NOT EXISTS trg_cortex_no_update BEFORE UPDATE ON cortex_ledger
                BEGIN SELECT RAISE(ABORT, 'C5 BFT: CortexPersistLedger es estrictamente inmutable'); END;
                """
            )
            conn.execute(
                """
                CREATE TRIGGER IF NOT EXISTS trg_cortex_no_delete BEFORE DELETE ON cortex_ledger
                BEGIN SELECT RAISE(ABORT, 'C5 BFT: CortexPersistLedger prohibe purgas de registros'); END;
                """
            )
            conn.commit()

    def query_events(
        self,
        *,
        event_type: str | None = None,
        skill_id: str | None = None,
        context: str | None = None,
        status: str | None = None,
        limit: int = 100,
        before_seq: int | None = None,
    ) -> list[dict[str, object]]:
        """Read a filtered, newest-first page without changing ledger history.

        Payload filters match top-level JSON strings exactly. Pass the final
        row's ``seq`` as ``before_seq`` to continue an earlier page. A cursor
        excludes newer appends, so pagination does not repeat existing rows.
        """
        filters = {"event_type": event_type, "skill_id": skill_id, "context": context, "status": status}
        for name, value in filters.items():
            if value is not None and not isinstance(value, str):
                raise TypeError(f"{name} must be a string or None")
        if isinstance(limit, bool) or not isinstance(limit, int):
            raise TypeError("limit must be an integer")
        if not 1 <= limit <= 1000:
            raise ValueError("limit must be between 1 and 1000")
        if before_seq is not None:
            if isinstance(before_seq, bool) or not isinstance(before_seq, int):
                raise TypeError("before_seq must be an integer or None")
            if not 1 <= before_seq <= 2**63 - 1:
                raise ValueError("before_seq must be a positive SQLite integer")

        predicates: list[str] = []
        parameters: list[object] = []
        if event_type is not None:
            predicates.append("event_type = ?")
            parameters.append(event_type)
        for name, value in (("skill_id", skill_id), ("context", context), ("status", status)):
            if value is not None:
                # The JSON paths come only from fixed field names; all caller
                # values are bound parameters, including quotes and SQL text.
                predicates.append(f"json_type(payload_json, '$.{name}') = 'text'")
                predicates.append(f"json_extract(payload_json, '$.{name}') = ?")
                parameters.append(value)
        if before_seq is not None:
            predicates.append("seq < ?")
            parameters.append(before_seq)
        where = " WHERE " + " AND ".join(predicates) if predicates else ""
        parameters.append(limit)
        with closing(self._get_connection()) as conn, conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(
                "SELECT seq, event_id, event_type, payload_json, cortex_taint, agent_id, domain, "
                "lamport_t, prev_hash, entry_hash, timestamp, hash_version FROM cortex_ledger"
                + where
                + " ORDER BY seq DESC LIMIT ?",
                parameters,
            ).fetchall()
        events: list[dict[str, object]] = []
        for row in rows:
            event: dict[str, object] = dict(row)
            event["payload"] = json.loads(str(event.pop("payload_json")))
            events.append(event)
        return events

    def append_event(
        self,
        event: CortexEvent,
        *,
        precondition: Callable[[], None] | None = None,
        connection: sqlite3.Connection | None = None,
    ) -> EventResult:
        """
        Inserta un evento con hash v2 y reloj lógico Lamport transaccional.
        La hora física se conserva como metadato fuera del hash v2.
        Garantiza idempotencia vía UUID v5. Utiliza BEGIN IMMEDIATE (FIX C5-06).
        """
        if not event.cortex_taint:
            raise ValueError("INV_BFT_03: cortex_taint es obligatorio")

        payload_json = _canonical_json(event.payload)
        event_id, legacy_event_id = _event_ids(event, payload_json)
        timestamp = datetime.now(timezone.utc).isoformat()

        if connection is not None:
            # The owner must hold BEGIN IMMEDIATE on this ledger's database.
            # It also owns commit/rollback so ledger and domain changes are atomic.
            databases = connection.execute("PRAGMA database_list").fetchall()
            main_path = next((row[2] for row in databases if row[1] == "main"), "")
            if not connection.in_transaction or not main_path or not os.path.samefile(main_path, self.db_path):
                raise ValueError("Ledger append requires a transaction on the same database")
            if connection.execute("PRAGMA synchronous").fetchone()[0] not in (2, 3):
                raise ValueError("Ledger append requires synchronous=FULL or EXTRA")
            if precondition is not None:
                precondition()
            cursor = connection.cursor()
            existing = self._check_existing_event(cursor, event, payload_json, event_id, legacy_event_id)
            if existing:
                return existing
            return self._insert_new_event(cursor, connection, event, event_id, payload_json, timestamp)

        with closing(self._get_connection()) as conn:
            cursor = conn.cursor()
            cursor.execute("BEGIN IMMEDIATE")
            try:
                # Validate event-sourced transitions while holding SQLite's
                # writer lock, so another writer cannot invalidate the read.
                if precondition is not None:
                    precondition()
                existing = self._check_existing_event(cursor, event, payload_json, event_id, legacy_event_id)
                if existing:
                    conn.commit()
                    return existing
                result = self._insert_new_event(cursor, conn, event, event_id, payload_json, timestamp)
                conn.commit()
                return result
            except Exception:
                conn.rollback()
                raise

    @staticmethod
    def _check_existing_event(
        cursor: sqlite3.Cursor,
        event: CortexEvent,
        payload_json: str,
        event_id: str,
        legacy_event_id: str | None = None,
    ) -> Optional[EventResult]:
        identity = (event.event_type, payload_json, event.cortex_taint, event.agent_id, event.domain)
        candidates = [event_id]
        if legacy_event_id and legacy_event_id not in candidates:
            candidates.append(legacy_event_id)
        for candidate in candidates:
            cursor.execute(
                "SELECT seq, entry_hash, lamport_t, event_type, payload_json, cortex_taint, agent_id, domain "
                "FROM cortex_ledger WHERE event_id = ?",
                (candidate,),
            )
            row = cursor.fetchone()
            if row is None:
                continue
            if (row[3], row[4], row[5], row[6], row[7]) != identity:
                raise ValueError(
                    f"Fail-fast: INV_BFT_04 Collision on event_id {candidate}: payload or metadata mismatch"
                )
            return {
                "seq": row[0],
                "event_id": candidate,
                "entry_hash": row[1],
                "lamport_t": row[2],
                "status": "DUPLICATE_IGNORED",
            }
        return None

    @staticmethod
    def _insert_new_event(
        cursor: sqlite3.Cursor,
        conn: sqlite3.Connection,
        event: CortexEvent,
        event_id: str,
        payload_json: str,
        timestamp: str,
    ) -> EventResult:
        cursor.execute("SELECT lamport_t, entry_hash FROM cortex_ledger ORDER BY seq DESC LIMIT 1")
        last_row = cursor.fetchone()
        last_lamport = last_row[0] if (last_row and last_row[0] is not None) else 0
        prev_hash = last_row[1] if (last_row and last_row[1] is not None) else ZERO_HASH_256
        lamport_t = last_lamport + 1

        cursor.execute("SELECT COALESCE(MAX(seq), 0) + 1 FROM cortex_ledger")
        next_seq = cursor.fetchone()[0]

        entry_hash = compute_cortex_hash(
            seq=next_seq,
            event_id=event_id,
            event_type=event.event_type,
            payload_json=payload_json,
            cortex_taint=event.cortex_taint,
            lamport_t=lamport_t,
            prev_hash=prev_hash,
            timestamp=timestamp,
            agent_id=event.agent_id,
            domain=event.domain,
            hash_version=CORTEX_HASH_VERSION,
        )
        sealed = observation_commitment(entry_hash, timestamp, event.agent_id)

        cursor.execute(
            """
            INSERT INTO cortex_ledger (
                event_id, event_type, payload_json, cortex_taint,
                agent_id, domain, lamport_t, prev_hash, entry_hash, timestamp, hash_version,
                observation_hash
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                event_id,
                event.event_type,
                payload_json,
                event.cortex_taint,
                event.agent_id,
                event.domain,
                lamport_t,
                prev_hash,
                entry_hash,
                timestamp,
                CORTEX_HASH_VERSION,
                sealed,
            ),
        )
        return {
            "seq": next_seq,
            "event_id": event_id,
            "entry_hash": entry_hash,
            "lamport_t": lamport_t,
            "status": "C5_PERMANENT",
        }

    def _process_batch_event(
        self,
        ev: CortexEvent,
        cursor: sqlite3.Cursor,
        last_lamport: int,
        prev_hash: str,
        current_seq: int,
        timestamp: str,
        batch_index: Dict[str, Tuple[int, str, int, Tuple[str, str, str, str, str]]] | None = None,
    ) -> BatchProcessResult:
        if not ev.cortex_taint:
            raise ValueError("INV_BFT_03: cortex_taint es obligatorio")

        payload_json = _canonical_json(ev.payload)
        event_id, legacy_event_id = _event_ids(ev, payload_json)

        # FIX B-2 (audit 2026-09-10): duplicados DENTRO del mismo lote no son
        # visibles en la DB (las filas se insertan diferidas al final). Sin este
        # índice, el segundo ejemplar llegaba al executemany y abortaba todo el
        # lote con IntegrityError (UNIQUE event_id) en vez de DUPLICATE_IGNORED.
        identity = (ev.event_type, payload_json, ev.cortex_taint, ev.agent_id, ev.domain)
        if batch_index is not None and event_id in batch_index:
            orig_seq, orig_hash, orig_lamport, prior_identity = batch_index[event_id]
            if prior_identity != identity:
                raise ValueError(
                    f"Fail-fast: INV_BFT_04 Collision on event_id {event_id}: payload or metadata mismatch"
                )
            return {
                "seq": orig_seq,
                "event_id": event_id,
                "entry_hash": orig_hash,
                "lamport_t": orig_lamport,
                "status": "DUPLICATE_IGNORED",
                "row": None,
            }

        duplicate = self._check_existing_event(cursor, ev, payload_json, event_id, legacy_event_id)
        if duplicate is not None:
            return {
                "seq": duplicate["seq"],
                "event_id": duplicate["event_id"],
                "entry_hash": duplicate["entry_hash"],
                "lamport_t": duplicate["lamport_t"],
                "status": "DUPLICATE_IGNORED",
                "row": None,
            }

        last_lamport += 1
        current_seq += 1

        entry_hash = compute_cortex_hash(
            seq=current_seq,
            event_id=event_id,
            event_type=ev.event_type,
            payload_json=payload_json,
            cortex_taint=ev.cortex_taint,
            lamport_t=last_lamport,
            prev_hash=prev_hash,
            timestamp=timestamp,
            agent_id=ev.agent_id,
            domain=ev.domain,
            hash_version=CORTEX_HASH_VERSION,
        )
        sealed = observation_commitment(entry_hash, timestamp, ev.agent_id)

        row: CortexLedgerRow = (
            event_id,
            ev.event_type,
            payload_json,
            ev.cortex_taint,
            ev.agent_id,
            ev.domain,
            last_lamport,
            prev_hash,
            entry_hash,
            timestamp,
            CORTEX_HASH_VERSION,
            sealed,
        )
        if batch_index is not None:
            batch_index[event_id] = (current_seq, entry_hash, last_lamport, identity)
        return {
            "seq": current_seq,
            "event_id": event_id,
            "entry_hash": entry_hash,
            "lamport_t": last_lamport,
            "status": "C5_PERMANENT",
            "row": row,
        }

    def _build_batch_rows(
        self,
        events: List[CortexEvent],
        cursor: sqlite3.Cursor,
        last_lamport: int,
        prev_hash: str,
        current_seq: int,
        timestamp: str,
    ) -> Tuple[List[EventResult], List[CortexLedgerRow]]:
        results: List[EventResult] = []
        rows_to_insert: List[CortexLedgerRow] = []
        batch_index: Dict[str, Tuple[int, str, int, Tuple[str, str, str, str, str]]] = {}
        for ev in events:
            res = self._process_batch_event(ev, cursor, last_lamport, prev_hash, current_seq, timestamp, batch_index)
            row = res["row"]
            event_res: EventResult = {
                "seq": res["seq"],
                "event_id": res["event_id"],
                "entry_hash": res["entry_hash"],
                "lamport_t": res["lamport_t"],
                "status": res["status"],
            }
            results.append(event_res)
            if row:
                rows_to_insert.append(row)
                prev_hash = row[8]
                last_lamport = row[6]
                current_seq = res["seq"]
            # FIX B-1 (audit 2026-09-10): un DUPLICATE_IGNORED NUNCA reancla la
            # cadena. prev_hash/lamport del próximo evento nuevo deben apuntar a
            # la última fila REALMENTE insertada; adoptar el hash del duplicado
            # rompía la cadena (verify_integrity() -> False permanente) sin
            # intervención de ningún atacante.
        return results, rows_to_insert

    def append_batch(self, events: List[CortexEvent]) -> List[EventResult]:
        """
        Inserta un lote masivo de eventos en una única transacción BFT atómica.
        Cada evento nuevo recibe un tick lógico persistido; la hora física del
        lote queda fuera del hash v2. La durabilidad usa synchronous = FULL.
        """
        if not events:
            return []

        timestamp = datetime.now(timezone.utc).isoformat()

        with closing(self._get_connection()) as conn, conn:
            cursor = conn.cursor()
            cursor.execute("BEGIN IMMEDIATE")

            # Obtener estado inicial del hash-chain desde el último seq
            cursor.execute("SELECT lamport_t, entry_hash, seq FROM cortex_ledger ORDER BY seq DESC LIMIT 1")
            last_row = cursor.fetchone()

            last_lamport = last_row[0] if (last_row and last_row[0] is not None) else 0
            prev_hash = last_row[1] if (last_row and last_row[1] is not None) else ZERO_HASH_256
            current_seq = last_row[2] if (last_row and last_row[2] is not None) else 0

            results, rows_to_insert = self._build_batch_rows(
                events, cursor, last_lamport, prev_hash, current_seq, timestamp
            )

            if rows_to_insert:
                cursor.executemany(
                    """
                    INSERT INTO cortex_ledger (
                        event_id, event_type, payload_json, cortex_taint,
                        agent_id, domain, lamport_t, prev_hash, entry_hash, timestamp, hash_version,
                        observation_hash
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    rows_to_insert,
                )

            conn.commit()
            return results

    @staticmethod
    def _check_duplicate(cursor: sqlite3.Cursor, event_id: str) -> Optional[Tuple[int, str, int]]:
        cursor.execute("SELECT seq, entry_hash, lamport_t FROM cortex_ledger WHERE event_id = ?", (event_id,))
        row = cursor.fetchone()
        if row is None:
            return None
        return (int(row[0]), str(row[1]), int(row[2]))

    def verify_integrity(
        self,
        chunk_size: int = 1000,
        *,
        expected_checkpoint: LedgerCheckpoint | None = None,
    ) -> bool:
        """
        Verifica la cadena SHA3-256, la contigüidad de seq y el high-water de sqlite_sequence.

        ``expected_checkpoint`` es el conteo y el hash de cabeza conservados fuera
        de SQLite. Si se pasa y no coincide, el resultado es False. Sin ese pin,
        una reescritura completa que recalcula la cadena es indetectable:
        sqlite_sequence solo delata un borrado ordinario de la cola.
        """
        if expected_checkpoint is not None and not isinstance(expected_checkpoint, LedgerCheckpoint):
            raise TypeError("expected_checkpoint must be a LedgerCheckpoint")
        with closing(self._get_connection()) as conn, conn:
            cursor = conn.cursor()
            if not conn.in_transaction:
                conn.execute("BEGIN")
            cursor.execute(
                "SELECT seq, event_id, event_type, payload_json, cortex_taint, agent_id, domain, lamport_t, prev_hash, entry_hash, timestamp, hash_version, observation_hash FROM cortex_ledger ORDER BY seq ASC"
            )

            prev_hash = ZERO_HASH_256
            last_lamport = 0
            expected_seq = 1

            while rows := cursor.fetchmany(chunk_size):
                for row in rows:
                    (
                        seq,
                        event_id,
                        event_type,
                        payload_json,
                        cortex_taint,
                        agent_id,
                        domain,
                        lamport_t,
                        row_prev_hash,
                        entry_hash,
                        timestamp,
                        hash_version,
                        observation_hash,
                    ) = row

                    is_valid, error = verify_row_invariants(
                        seq=seq,
                        event_id=event_id,
                        event_type=event_type,
                        payload_json=payload_json,
                        cortex_taint=cortex_taint,
                        agent_id=agent_id,
                        domain=domain,
                        lamport_t=lamport_t,
                        prev_hash=row_prev_hash,
                        entry_hash=entry_hash,
                        timestamp=timestamp,
                        expected_seq=expected_seq,
                        last_lamport=last_lamport,
                        expected_prev_hash=prev_hash,
                        hash_version=hash_version,
                        observation_hash=observation_hash,
                    )

                    if not is_valid:
                        logger.error(f"🔴 {error}")
                        return False

                    prev_hash = entry_hash
                    last_lamport = lamport_t
                    expected_seq += 1

            high_water = cursor.execute("SELECT seq FROM sqlite_sequence WHERE name='cortex_ledger'").fetchone()
            if (int(high_water[0]) if high_water and high_water[0] is not None else 0) != expected_seq - 1:
                logger.error("Ledger truncation detected: sqlite_sequence does not match the verified tail")
                return False

        count = expected_seq - 1
        if expected_checkpoint is not None and (
            type(expected_checkpoint.entries) is not int
            or expected_checkpoint.entries != count
            or expected_checkpoint.head_hash != prev_hash
        ):
            logger.error("Trusted checkpoint mismatch")
            return False
        return True

    def get_merkle_root(self) -> str:
        """
        Calcula la Raiz de Merkle sobre todos los hashes de entrada.
        Utiliza kernel puro con FIX C5-05 (Domain Separation).
        """
        with closing(self._get_connection()) as conn, conn:
            cursor = conn.cursor()
            cursor.execute("SELECT entry_hash FROM cortex_ledger ORDER BY seq ASC")
            entry_hashes = [row[0] for row in cursor.fetchall()]

        return build_merkle_tree(entry_hashes)

    def get_event_proof(self, seq: int) -> MerkleProof:
        """
        Genera una prueba de inclusión de Merkle O(log N) para un evento específico por seq.
        Cumple con el estándar de evidencia verificable del EU AI Act.
        """
        with closing(self._get_connection()) as conn, conn:
            cursor = conn.cursor()
            cursor.execute("SELECT entry_hash FROM cortex_ledger ORDER BY seq ASC")
            leaves = [row[0] for row in cursor.fetchall()]

        if seq < 1 or seq > len(leaves):
            raise IndexError(f"seq {seq} fuera de rango (total eventos: {len(leaves)})")

        target_index = seq - 1
        return generate_merkle_proof(leaves, target_index)

    @staticmethod
    def verify_event_proof(proof_packet: MerkleProof, merkle_root: str) -> bool:
        """
        Verifica una prueba de inclusión de Merkle O(log N) sin requerir acceso a la base de datos.
        """
        if type(proof_packet.get("target_index")) is not int:
            return False
        return verify_merkle_proof(
            leaf_hash=proof_packet["leaf_hash"],
            proof=proof_packet["proof"],
            expected_root=merkle_root,
            total_leaves=proof_packet["total_leaves"],
            target_index=proof_packet["target_index"],
        )

    def get_mmr(self) -> MerkleMountainRange:
        """
        Construye un acumulador MerkleMountainRange sobre todos los eventos del ledger.
        """
        with closing(self._get_connection()) as conn, conn:
            cursor = conn.cursor()
            cursor.execute("SELECT entry_hash FROM cortex_ledger ORDER BY seq ASC")
            leaves = [row[0] for row in cursor.fetchall()]

        mmr = MerkleMountainRange()
        for h in leaves:
            mmr.append(h)
        return mmr

    def get_mmr_root(self) -> str:
        """
        Retorna la raíz del acumulador MMR O(log N).
        """
        return self.get_mmr().get_root()

    def get_mmr_event_proof(self, seq: int) -> MMREventProof:
        """
        Genera una prueba de inclusión MMR O(log N) para un evento específico por seq.
        Cumple con el estándar de evidencia forense append-only (arXiv:2609.04017 / EU AI Act).
        """
        with closing(self._get_connection()) as conn, conn:
            cursor = conn.cursor()
            cursor.execute("SELECT entry_hash FROM cortex_ledger ORDER BY seq ASC")
            leaves = [row[0] for row in cursor.fetchall()]

        if seq < 1 or seq > len(leaves):
            raise IndexError(f"seq {seq} fuera de rango (total eventos: {len(leaves)})")

        mmr = MerkleMountainRange()
        for h in leaves:
            mmr.append(h)

        target_index = seq - 1
        proof = mmr.generate_proof(target_index)
        event_proof: MMREventProof = {
            "leaf_index": proof["leaf_index"],
            "total_leaves": proof["total_leaves"],
            "peak_index": proof["peak_index"],
            "inner_proof": proof["inner_proof"],
            "other_peaks": proof["other_peaks"],
            "mmr_root": proof["mmr_root"],
            "leaf_hash": leaves[target_index],
        }
        return event_proof

    @staticmethod
    def verify_mmr_event_proof(proof_packet: MMREventProof, mmr_root: str) -> bool:
        """
        Verifica una prueba de inclusión MMR O(log N) contra una raíz MMR esperada.
        """
        return MerkleMountainRange.verify_proof(
            leaf_hash=proof_packet["leaf_hash"],
            proof_packet=proof_packet,
            expected_root=mmr_root,
        )

    def get_state_attestation(self) -> StateAttestation:
        """
        Retorna un manifiesto de atestación del estado actual del ledger (Causal-Determinist).
        """
        with closing(self._get_connection()) as conn, conn:
            conn.execute("BEGIN DEFERRED")
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*), COALESCE(MAX(lamport_t), 0), COALESCE(MAX(seq), 0) FROM cortex_ledger")
            row = cursor.fetchone()
            total_entries = row[0]
            max_lamport = row[1]
            max_seq = row[2]

            cursor.execute("SELECT entry_hash FROM cortex_ledger ORDER BY seq ASC")
            leaves = [r[0] for r in cursor.fetchall()]

            merkle_root = build_merkle_tree(leaves)
            mmr = MerkleMountainRange()
            for h in leaves:
                mmr.append(h)
            mmr_root = mmr.get_root()

            cursor.execute(
                "SELECT seq, event_id, event_type, payload_json, cortex_taint, agent_id, domain, lamport_t, prev_hash, entry_hash, timestamp, hash_version, observation_hash FROM cortex_ledger ORDER BY seq ASC"
            )

            prev_hash = ZERO_HASH_256
            last_lamport = 0
            expected_seq = 1
            is_valid = True

            while rows := cursor.fetchmany(1000):
                for r_row in rows:
                    (
                        seq,
                        event_id,
                        event_type,
                        payload_json,
                        cortex_taint,
                        agent_id,
                        domain,
                        lamport_t,
                        row_prev_hash,
                        entry_hash,
                        timestamp,
                        hash_version,
                        observation_hash,
                    ) = r_row

                    row_is_valid, _ = verify_row_invariants(
                        seq=seq,
                        event_id=event_id,
                        event_type=event_type,
                        payload_json=payload_json,
                        cortex_taint=cortex_taint,
                        agent_id=agent_id,
                        domain=domain,
                        lamport_t=lamport_t,
                        prev_hash=row_prev_hash,
                        entry_hash=entry_hash,
                        timestamp=timestamp,
                        expected_seq=expected_seq,
                        expected_prev_hash=prev_hash,
                        last_lamport=last_lamport,
                        hash_version=hash_version,
                        observation_hash=observation_hash,
                    )

                    if not row_is_valid:
                        is_valid = False
                        break

                    prev_hash = entry_hash
                    last_lamport = lamport_t
                    expected_seq += 1
                if not is_valid:
                    break

            if is_valid:
                high_water = cursor.execute("SELECT seq FROM sqlite_sequence WHERE name='cortex_ledger'").fetchone()
                if (int(high_water[0]) if high_water and high_water[0] is not None else 0) != expected_seq - 1:
                    is_valid = False

            conn.commit()

        return {
            "total_entries": total_entries,
            "max_lamport": max_lamport,
            "max_seq": max_seq,
            "merkle_root": merkle_root,
            "mmr_root": mmr_root,
            "integrity_verified": is_valid,
            "attested_at": datetime.now(timezone.utc).isoformat(),
            "rekor_anchor": None,
        }

    def anchor_to_rekor(
        self,
        rekor_client: Optional[Any] = None,
        seed_hex: Optional[str] = None,
    ) -> Optional[Dict[str, object]]:
        """
        Publica el ledger-head (merkle_root + max_lamport + timestamp) en Sigstore Rekor.
        Satisface el requisito del Art. 12 EU AI Act de sellado temporal por terceros (P1).
        """
        attestation = self.get_state_attestation()
        head_data = {
            "merkle_root": attestation["merkle_root"],
            "max_lamport": attestation["max_lamport"],
            "total_entries": attestation["total_entries"],
            "attested_at": attestation["attested_at"],
        }
        head_json = _canonical_json(head_data).encode("utf-8")
        payload_hash = hashlib.sha256(head_json).hexdigest()

        from nacl.signing import SigningKey

        sk = SigningKey(require_ed25519_seed(seed_hex))
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


class CortexPersistFacade:
    """
    Fachada síncrona de compatibilidad sobre BFTLedgerActor (R-8).
    Permite ejecutar operaciones sobre el actor asíncrono desde entornos síncronos (CLI, scripts).
    """

    def __init__(self, db_path: Path | str) -> None:
        self.db_path = Path(db_path)
        from babylon60.bft.ledger_actor import BFTLedgerActor

        self._actor = BFTLedgerActor(self.db_path)

    def append_event(self, event: CortexEvent) -> EventResult:
        import asyncio

        async def _run() -> EventResult:
            await self._actor.start()
            try:
                fut = self._actor.append_cortex_event(event)
                res = await fut
                return {
                    "seq": res["seq"],
                    "event_id": res["event_id"],
                    "entry_hash": res["entry_hash"],
                    "lamport_t": res["seq"],
                    "status": "C5_PERMANENT",
                }
            finally:
                await self._actor.stop()

        return asyncio.run(_run())

    def verify_integrity(self, *, expected_checkpoint: LedgerCheckpoint | None = None) -> Tuple[bool, str]:
        import asyncio

        async def _run() -> Tuple[bool, str]:
            try:
                valid = await self._actor.verify_chain(expected_checkpoint=expected_checkpoint)
                return valid, "CADENA_INTEGRA" if valid else "CADENA_CORRUPTA"
            except Exception as e:
                return False, f"VERIFICATION_ERROR: {e}"

        return asyncio.run(_run())

    def get_state_attestation(self) -> StateAttestation:
        import asyncio

        async def _run() -> StateAttestation:
            return await self._actor.get_state_attestation()

        return asyncio.run(_run())
