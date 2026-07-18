import os
import sqlite3
import hashlib
from typing import Any
from datetime import datetime, timezone

PROJECT_ROOT = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
)
DEFAULT_DB_PATH = os.path.join(PROJECT_ROOT, "db", "agent_memory.db")


class AgentMemory:
    """
    Memoria persistente BFT (SQLite WAL) para agentes soberanos.
    Cumple con Ω11: Ledger inmutable (RAISE ABORT), prev_hash, y CORTEX-TAINT obligatorio.
    """

    def __init__(self, db_path: str = DEFAULT_DB_PATH) -> None:
        self.conn = sqlite3.connect(db_path, isolation_level=None)
        # Habilitar WAL para concurrencia BFT segura (R10)
        self.conn.execute("PRAGMA journal_mode=WAL;")
        self.conn.execute("PRAGMA busy_timeout=5000;")
        self._init_table()

    def _init_table(self) -> None:
        self.conn.execute("""
        CREATE TABLE IF NOT EXISTS decisions (
            id INTEGER PRIMARY KEY,
            issue_id INTEGER,
            agent_role TEXT,
            action TEXT,
            result TEXT,
            prev_hash TEXT UNIQUE,
            cortex_taint TEXT NOT NULL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
        """)

        # Trigger para garantizar inmutabilidad (Ω11)
        self.conn.execute("""
        CREATE TRIGGER IF NOT EXISTS prevent_update_decisions
        BEFORE UPDATE ON decisions
        BEGIN
            SELECT RAISE(ABORT, 'CORTEX_LEDGER_ERROR: Updates are strictly forbidden in C5-REAL ledger.');
        END;
        """)

        self.conn.execute("""
        CREATE TRIGGER IF NOT EXISTS prevent_delete_decisions
        BEFORE DELETE ON decisions
        BEGIN
            SELECT RAISE(ABORT, 'CORTEX_LEDGER_ERROR: Deletions are strictly forbidden in C5-REAL ledger.');
        END;
        """)

    def _get_last_hash(self) -> str:
        cursor = self.conn.execute(
            "SELECT cortex_taint FROM decisions ORDER BY id DESC LIMIT 1"
        )
        row = cursor.fetchone()
        return (
            row[0]
            if row
            else "GENESIS_BLOCK_00000000000000000000000000000000000000000000000000"
        )

    def log(self, issue_id: int, agent_role: str, action: str, result: str) -> str:
        try:
            self.conn.execute("BEGIN EXCLUSIVE TRANSACTION")
            prev_hash = self._get_last_hash()

            timestamp_iso = datetime.now(timezone.utc).isoformat()

            raw_payload = f"{prev_hash}|{issue_id}|{agent_role}|{action}|{result}|{timestamp_iso}".encode(
                "utf-8"
            )
            cortex_taint = f"CORTEX-TAINT:borjamoskv:swarm_ledger:{timestamp_iso}:{hashlib.sha3_256(raw_payload).hexdigest()}"

            self.conn.execute(
                "INSERT INTO decisions (issue_id, agent_role, action, result, prev_hash, cortex_taint) VALUES (?, ?, ?, ?, ?, ?)",
                (issue_id, agent_role, action, result, prev_hash, cortex_taint),
            )
            self.conn.execute("COMMIT")
            return cortex_taint
        except Exception:
            self.conn.execute("ROLLBACK")
            raise

    def query_similar(self, issue_text: str) -> list[Any]:
        # TODO: C5-REAL ChromaDB Vector Search embedding lookup
        cursor = self.conn.execute(
            "SELECT * FROM decisions ORDER BY timestamp DESC LIMIT 10"
        )
        return cursor.fetchall()
