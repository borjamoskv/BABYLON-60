# [C5-REAL] BFT consensus committer — Operador ortogonal (C) puro.
# No valida matemáticamente. Solo muta disco y persiste ledger (WAL).
import sqlite3
from typing import Any, Dict
from dataclasses import dataclass
from babylon60.database import core as database_core
from babylon60.core.crypto import canonicalize_cbor

@dataclass(frozen=True)
class StateMutation:
    agent_id: str
    payload: Dict[str, Any]
    timestamp: float
    signature: str
    causal_taint: str = "BFT_Consensus_Init"

class BFT_Committer:
    def __init__(self, db_path: str = "master_ledger.db") -> None:
        self.conn: sqlite3.Connection = database_core.connect_sync(db_path, synchronous="FULL")
        self._init_tables()

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
                raise ValueError(f"Fail-fast: INV_BFT_04 Collision for mutation_hash {mutation_hash}. Differing payload detected.")
            return True

    def get_audit_rows(self):
        cursor = self.conn.cursor()
        try:
            cursor.execute("SELECT id, mutation_hash, payload FROM state_log")
            return cursor.fetchall()
        except sqlite3.OperationalError:
            return None
