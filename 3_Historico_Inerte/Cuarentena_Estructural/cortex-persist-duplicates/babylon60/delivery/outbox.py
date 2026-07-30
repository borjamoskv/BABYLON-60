# [C5-REAL] Exergy-Maximized
"""
Sovereign Outbox - Atomic Task Queue via SQLite WAL.

Implements the C5-REAL outbox pattern with UPDATE...RETURNING
for zero-latency atomic task claiming. All mutations are
serialized through SQLite WAL mode for concurrent safety.

Reality Level: C5-REAL
"""

from __future__ import annotations

import sqlite3
import threading
import time
from pathlib import Path
from typing import Any

from babylon60.database.core import causal_write, connect


class SovereignOutbox:
    """Atomic task outbox using SQLite WAL mode.

    Provides enqueue/claim/complete lifecycle with UPDATE...RETURNING
    for lock-free atomic batch claiming.
    """

    _SCHEMA = """
    CREATE TABLE IF NOT EXISTS cortex_outbox_queue (
        id          INTEGER PRIMARY KEY AUTOINCREMENT,
        agent_id    TEXT    NOT NULL,
        payload     BLOB   NOT NULL,
        status      TEXT   DEFAULT 'pending',
        error       TEXT,
        created_at  REAL   DEFAULT (unixepoch('subsec')),
        claimed_at  REAL,
        completed_at REAL,
        taint       TEXT
    );
    CREATE INDEX IF NOT EXISTS idx_outbox_status ON cortex_outbox_queue(status);
    """

    def __init__(self, db_path: str | Path) -> None:
        self._db_path = str(db_path)
        self._local = threading.local()
        self._init_schema()

    def _get_conn(self) -> sqlite3.Connection:
        conn = getattr(self._local, "conn", None)
        if conn is None:
            # Enforce BUSY_TIMEOUT_MS = 5000 (Rule R10) and WAL mode via core connect()
            conn = connect(
                self._db_path,
                timeout=5,
                row_factory=sqlite3.Row,
            )
            self._local.conn = conn
        return conn

    def _init_schema(self) -> None:
        conn = self._get_conn()
        with causal_write(conn):
            conn.executescript(self._SCHEMA)
            conn.commit()

    # ── Core Operations ─────────────────────────────────────

    def enqueue(self, agent_id: str, payload: bytes, taint: str | None = None) -> int:
        """INSERT a task and return its id."""
        conn = self._get_conn()
        with causal_write(conn):
            cursor = conn.execute(
                "INSERT INTO cortex_outbox_queue (agent_id, payload, taint) VALUES (?, ?, ?)",
                (agent_id, payload, taint),
            )
            conn.commit()
        return cursor.lastrowid  # type: ignore[return-value]

    def fetch_pending(self, batch_size: int = 100) -> list[tuple[int, str, bytes, str | None]]:
        """Atomically claim pending tasks via UPDATE...RETURNING.

        Returns list of (id, agent_id, payload, taint) tuples.
        Uses UPDATE...RETURNING for single-statement atomicity -
        no race window between SELECT and UPDATE.
        """
        conn = self._get_conn()
        with causal_write(conn):
            try:
                rows = conn.execute(
                    """
                    UPDATE cortex_outbox_queue
                    SET status = 'claimed', claimed_at = unixepoch('subsec')
                    WHERE id IN (
                        SELECT id FROM cortex_outbox_queue
                        WHERE status = 'pending'
                        ORDER BY id
                        LIMIT ?
                    )
                    RETURNING id, agent_id, payload, taint
                    """,
                    (batch_size,),
                ).fetchall()
                conn.commit()
                return [(row[0], row[1], row[2], row[3]) for row in rows]
            except sqlite3.OperationalError:
                # Fallback for SQLite < 3.35.0 (no RETURNING)
                conn.execute("BEGIN IMMEDIATE")
                rows = conn.execute(
                    """
                    SELECT id, agent_id, payload, taint FROM cortex_outbox_queue
                    WHERE status = 'pending'
                    ORDER BY id LIMIT ?
                    """,
                    (batch_size,),
                ).fetchall()
                if rows:
                    ids = [row[0] for row in rows]
                    placeholders = ",".join("?" * len(ids))
                    conn.execute(
                        f"UPDATE cortex_outbox_queue SET status='claimed', claimed_at=? WHERE id IN ({placeholders})",
                        [time.time(), *ids],
                    )
                conn.commit()
                return [(row[0], row[1], row[2], row[3]) for row in rows]

    def complete(self, task_id: int) -> bool:
        """Mark a claimed task as completed."""
        conn = self._get_conn()
        with causal_write(conn):
            cursor = conn.execute(
                "UPDATE cortex_outbox_queue SET status='completed', completed_at=unixepoch('subsec') WHERE id=? AND status='claimed'",
                (task_id,),
            )
            conn.commit()
        return cursor.rowcount > 0

    def fail(self, task_id: int, error: str) -> bool:
        """Mark a claimed task as failed with error message."""
        conn = self._get_conn()
        with causal_write(conn):
            cursor = conn.execute(
                "UPDATE cortex_outbox_queue SET status='failed', error=?, completed_at=unixepoch('subsec') WHERE id=? AND status='claimed'",
                (error, task_id),
            )
            conn.commit()
        return cursor.rowcount > 0

    def requeue_stale(self, timeout_sec: float = 60.0) -> int:
        """Re-queue claimed tasks older than timeout_sec."""
        conn = self._get_conn()
        with causal_write(conn):
            cutoff = time.time() - timeout_sec
            cursor = conn.execute(
                "UPDATE cortex_outbox_queue SET status='pending', claimed_at=NULL WHERE status='claimed' AND claimed_at < ?",
                (cutoff,),
            )
            conn.commit()
        return cursor.rowcount

    def stats(self) -> dict[str, Any]:
        """Count tasks by status."""
        conn = self._get_conn()
        rows = conn.execute("SELECT status, COUNT(*) FROM cortex_outbox_queue GROUP BY status").fetchall()
        result: dict[str, Any] = {"pending": 0, "claimed": 0, "completed": 0, "failed": 0}
        for row in rows:
            result[row[0]] = row[1]
        result["total"] = sum(result.values())
        return result

    def purge_completed(self, older_than_sec: float = 3600.0) -> int:
        """Delete completed tasks older than threshold."""
        conn = self._get_conn()
        with causal_write(conn):
            cutoff = time.time() - older_than_sec
            cursor = conn.execute(
                "DELETE FROM cortex_outbox_queue WHERE status='completed' AND completed_at < ?",
                (cutoff,),
            )
            conn.commit()
        return cursor.rowcount

    def journal_mode(self) -> str:
        """Return current journal mode (should be 'wal')."""
        conn = self._get_conn()
        row = conn.execute("PRAGMA journal_mode").fetchone()
        return row[0] if row else "unknown"

    def close(self) -> None:
        conn = getattr(self._local, "conn", None)
        if conn:
            conn.close()
            self._local.conn = None

    def __enter__(self) -> SovereignOutbox:
        return self

    def __exit__(self, *args: Any) -> None:
        self.close()
