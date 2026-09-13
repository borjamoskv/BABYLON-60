"""
CORTEX PERSISTENT DUPLEX TUNNEL BUS
===================================
High-exergy, zero-lock/low-overhead message bus using SQLite in WAL mode.
Provides asynchronous, decoupled, bidirectional message passing between
Antigravity (Gemini) and Codex Desktop (GPT-6 Astra Ultra).

Invariants:
- INV_BFT_02: SQLite WAL mode + busy_timeout=5000ms.
- INV_BFT_04: Unique UUID tracking.
- INV_C5_17: Sovereign, local, zero-cloud intermediary.
"""

from __future__ import annotations

import json
import logging
import sqlite3
import time
import uuid
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Optional

logger = logging.getLogger("codex_tunnel.bus")

DEFAULT_BUS_DIR = Path.home() / ".cortex" / "tunnel"
DEFAULT_DB_PATH = DEFAULT_BUS_DIR / "tunnel_bus.sqlite"


@dataclass
class TunnelMessage:
    id: str
    source: str
    destination: str
    msg_type: str
    correlation_id: Optional[str]
    payload: dict[str, Any]
    created_at_ms: int
    status: str
    response_payload: Optional[dict[str, Any]] = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class TunnelBus:
    """Persistent bidirectional SQLite message broker."""

    def __init__(self, db_path: Optional[Path] = None):
        self.db_path = db_path or DEFAULT_DB_PATH
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(str(self.db_path), timeout=5.0)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL;")
        conn.execute("PRAGMA synchronous=NORMAL;")
        conn.execute("PRAGMA busy_timeout=5000;")
        return conn

    def _init_db(self) -> None:
        with self._get_connection() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS tunnel_messages (
                    id TEXT PRIMARY KEY,
                    source TEXT NOT NULL,
                    destination TEXT NOT NULL,
                    msg_type TEXT NOT NULL,
                    correlation_id TEXT,
                    payload TEXT NOT NULL,
                    created_at_ms INTEGER NOT NULL,
                    status TEXT NOT NULL,
                    response_payload TEXT
                );
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_tunnel_dest_status 
                ON tunnel_messages(destination, status, created_at_ms);
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_tunnel_correlation 
                ON tunnel_messages(correlation_id);
            """)
            conn.commit()

    def push_message(
        self,
        source: str,
        destination: str,
        payload: dict[str, Any],
        msg_type: str = "message",
        correlation_id: Optional[str] = None,
        msg_id: Optional[str] = None,
    ) -> TunnelMessage:
        """Enqueue a message onto the bus."""
        msg_id = msg_id or str(uuid.uuid4())
        created_at = int(time.time() * 1000)
        payload_str = json.dumps(payload, ensure_ascii=False)

        with self._get_connection() as conn:
            conn.execute(
                """
                INSERT INTO tunnel_messages (
                    id, source, destination, msg_type, correlation_id, payload, created_at_ms, status, response_payload
                ) VALUES (?, ?, ?, ?, ?, ?, ?, 'pending', NULL)
                """,
                (msg_id, source, destination, msg_type, correlation_id, payload_str, created_at),
            )
            conn.commit()

        return TunnelMessage(
            id=msg_id,
            source=source,
            destination=destination,
            msg_type=msg_type,
            correlation_id=correlation_id,
            payload=payload,
            created_at_ms=created_at,
            status="pending",
            response_payload=None,
        )

    def pull_messages(
        self,
        destination: str,
        status: str = "pending",
        limit: int = 10,
        mark_delivered: bool = True,
    ) -> list[TunnelMessage]:
        """Pull messages addressed to destination."""
        with self._get_connection() as conn:
            cur = conn.execute(
                """
                SELECT id, source, destination, msg_type, correlation_id, payload, created_at_ms, status, response_payload
                FROM tunnel_messages
                WHERE destination = ? AND status = ?
                ORDER BY created_at_ms ASC
                LIMIT ?
                """,
                (destination, status, limit),
            )
            rows = cur.fetchall()
            messages: list[TunnelMessage] = []
            for row in rows:
                try:
                    payload = json.loads(row["payload"])
                except Exception:
                    payload = {"raw": row["payload"]}
                resp_payload = None
                if row["response_payload"]:
                    try:
                        resp_payload = json.loads(row["response_payload"])
                    except Exception:
                        resp_payload = {"raw": row["response_payload"]}

                messages.append(
                    TunnelMessage(
                        id=row["id"],
                        source=row["source"],
                        destination=row["destination"],
                        msg_type=row["msg_type"],
                        correlation_id=row["correlation_id"],
                        payload=payload,
                        created_at_ms=row["created_at_ms"],
                        status=row["status"],
                        response_payload=resp_payload,
                    )
                )

            if mark_delivered and messages:
                ids = [m.id for m in messages]
                placeholders = ",".join("?" * len(ids))
                conn.execute(
                    f"UPDATE tunnel_messages SET status = 'delivered' WHERE id IN ({placeholders})",
                    ids,
                )
                conn.commit()

            return messages

    def mark_processed(
        self,
        msg_id: str,
        response_payload: Optional[dict[str, Any]] = None,
        status: str = "processed",
    ) -> None:
        """Mark message processed and store optional reply payload."""
        resp_str = json.dumps(response_payload, ensure_ascii=False) if response_payload is not None else None
        with self._get_connection() as conn:
            conn.execute(
                "UPDATE tunnel_messages SET status = ?, response_payload = ? WHERE id = ?",
                (status, resp_str, msg_id),
            )
            conn.commit()


def _row_to_tunnel_message(row: Any) -> TunnelMessage:
    try:
        payload = json.loads(row["payload"])
    except Exception:
        payload = {"raw": row["payload"]}

    resp_payload = None
    if row["response_payload"]:
        try:
            resp_payload = json.loads(row["response_payload"])
        except Exception:
            resp_payload = {"raw": row["response_payload"]}

    return TunnelMessage(
        id=row["id"],
        source=row["source"],
        destination=row["destination"],
        msg_type=row["msg_type"],
        correlation_id=row["correlation_id"],
        payload=payload,
        created_at_ms=row["created_at_ms"],
        status=row["status"],
        response_payload=resp_payload,
    )

    def wait_for_reply(
        self,
        correlation_id: str,
        timeout_sec: float = 30.0,
        poll_interval: float = 0.25,
    ) -> Optional[TunnelMessage]:
        """Poll until a message with correlation_id is marked processed or arrives as reply."""
        start_time = time.time()
        while time.time() - start_time < timeout_sec:
            with self._get_connection() as conn:
                # Check for either a message with matching correlation_id
                cur = conn.execute(
                    """
                    SELECT id, source, destination, msg_type, correlation_id, payload, created_at_ms, status, response_payload
                    FROM tunnel_messages
                    WHERE correlation_id = ? AND (status = 'processed' OR response_payload IS NOT NULL)
                    ORDER BY created_at_ms DESC
                    LIMIT 1
                    """,
                    (correlation_id,),
                )
                row = cur.fetchone()
                if row:
                    return _row_to_tunnel_message(row)

                # Check if original message itself has response_payload set
                cur2 = conn.execute(
                    """
                    SELECT id, source, destination, msg_type, correlation_id, payload, created_at_ms, status, response_payload
                    FROM tunnel_messages
                    WHERE id = ? AND (status = 'processed' OR response_payload IS NOT NULL)
                    """,
                    (correlation_id,),
                )
                row2 = cur2.fetchone()
                if row2 and row2["response_payload"]:
                    return _row_to_tunnel_message(row2)

            time.sleep(poll_interval)
        return None

    def get_status(self) -> dict[str, Any]:
        """Telemetry diagnostics for the bus."""
        with self._get_connection() as conn:
            cur = conn.execute(
                """
                SELECT 
                    COUNT(*) as total_messages,
                    SUM(CASE WHEN status = 'pending' THEN 1 ELSE 0 END) as pending_messages,
                    SUM(CASE WHEN status = 'delivered' THEN 1 ELSE 0 END) as delivered_messages,
                    SUM(CASE WHEN status = 'processed' THEN 1 ELSE 0 END) as processed_messages,
                    MAX(created_at_ms) as latest_created_at_ms
                FROM tunnel_messages
                """
            )
            row = cur.fetchone()
            return {
                "db_path": str(self.db_path),
                "total_messages": row["total_messages"] or 0,
                "pending_messages": row["pending_messages"] or 0,
                "delivered_messages": row["delivered_messages"] or 0,
                "processed_messages": row["processed_messages"] or 0,
                "latest_created_at_ms": row["latest_created_at_ms"],
            }
