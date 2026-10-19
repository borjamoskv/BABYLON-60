# ============================================================================
# BABYLON-60 v4.0 Sovereign Hardened
# █ AUTOCOGNITION-Ω | STATE: C5-REAL | AESTHETIC: INDUSTRIAL_NOIR_2026
# ============================================================================
# [Causal-Determinist] BFT consensus committer — Operador ortogonal (C) puro.
# No valida matemáticamente. Solo muta disco y persiste ledger (WAL).
import sqlite3
from typing import Dict, Mapping
from dataclasses import dataclass
from babylon60.database import core as database_core
from babylon60.core.crypto_utils import canonicalize_cbor


@dataclass(frozen=True)
class StateMutation:
    agent_id: str
    payload: Mapping[str, object] | Dict[str, object]
    timestamp: float
    signature: str
    causal_taint: str = "BFT_Consensus_Init"


class BFT_Committer:
    def __init__(self, db_path: str = "master_ledger.db") -> None:
        # [FRENTE-030] Acquire OS-level exclusive advisory lock to prevent dual-instance WAL races
        self._lock_file = None
        self._lock_fd = None
        try:
            import fcntl

            lock_path = f"{db_path}.lock"
            self._lock_fd = open(lock_path, "w")
            fcntl.flock(self._lock_fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError as e:
            # [FRENTE-030] Si fcntl falla por OSError (ej. lock ya adquirido), abortamos en Ring-0
            raise SystemExit(f"CRITICAL: No se pudo adquirir lock exclusivo: {e}")

        self.conn: sqlite3.Connection = database_core.connect_sync(db_path, synchronous="FULL")
        self._init_tables()

    def __del__(self) -> None:
        if self._lock_fd is not None:
            try:
                import fcntl

                fcntl.flock(self._lock_fd, fcntl.LOCK_UN)
                self._lock_fd.close()
            except Exception:
                pass

    def _init_tables(self) -> None:
        self.conn.execute(
            """
            CREATE TABLE IF NOT EXISTS state_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                mutation_hash TEXT UNIQUE NOT NULL,
                agent_id TEXT NOT NULL,
                payload BLOB NOT NULL,
                ts REAL NOT NULL,
                causal_taint TEXT NOT NULL DEFAULT 'untainted'
            )
            """
        )

    def commit_mutation(self, mutation: StateMutation, mutation_hash: str) -> bool:
        cbor_payload = canonicalize_cbor(mutation.payload)
        try:
            self.conn.execute(
                "INSERT INTO state_log (mutation_hash, agent_id, payload, ts, causal_taint) VALUES (?, ?, ?, ?, ?)",
                (
                    mutation_hash,
                    mutation.agent_id,
                    cbor_payload,
                    mutation.timestamp,
                    mutation.causal_taint,
                ),
            )
            return True
        except sqlite3.IntegrityError:
            cursor = self.conn.cursor()
            cursor.execute("SELECT payload FROM state_log WHERE mutation_hash = ?", (mutation_hash,))
            row = cursor.fetchone()
            if row and row[0] != cbor_payload:
                raise ValueError(
                    f"Fail-fast: INV_BFT_04 Collision for mutation_hash {mutation_hash}. Differing payload detected."
                )
            return True

    def get_audit_rows(self) -> list[tuple[int, str, bytes]] | None:
        cursor = self.conn.cursor()
        try:
            cursor.execute("SELECT id, mutation_hash, payload FROM state_log")
            return cursor.fetchall()
        except sqlite3.OperationalError:
            return None
