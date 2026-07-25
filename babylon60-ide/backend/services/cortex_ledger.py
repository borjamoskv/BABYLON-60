from __future__ import annotations

import hashlib
import json
import sqlite3
import time
import uuid
from pathlib import Path
from typing import Any

_NS = uuid.UUID("6ba7b812-9dad-11d1-80b4-00c04fd430c8")
_ZERO_HASH = "0" * 64
_BUSY_TIMEOUT_MS = 5000
DDL = "\nCREATE TABLE IF NOT EXISTS cortex_events (\n    seq          INTEGER PRIMARY KEY AUTOINCREMENT,\n    event_id     TEXT NOT NULL UNIQUE,\n    parent_hash  TEXT NOT NULL,\n    current_hash TEXT NOT NULL,\n    event_type   TEXT NOT NULL,\n    entity_ref   TEXT NOT NULL,\n    payload      TEXT NOT NULL,\n    metadata     TEXT,\n    created_at   INTEGER NOT NULL\n);\nCREATE INDEX IF NOT EXISTS idx_cortex_type ON cortex_events(event_type, seq DESC);\nCREATE INDEX IF NOT EXISTS idx_cortex_entity ON cortex_events(entity_ref, seq DESC);\n"


def _canonical(data: Any) -> str:
    return json.dumps(data, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False)


def _connect(db_path: str | Path) -> sqlite3.Connection:
    conn = sqlite3.connect(str(db_path), timeout=5.0, isolation_level=None)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA synchronous=NORMAL")
    conn.execute(f"PRAGMA busy_timeout={_BUSY_TIMEOUT_MS}")
    return conn


def _ledger_path(project_root: Path) -> Path:
    return project_root / "babylon60_ide.db"


def init(project_root: Path) -> None:
    conn = _connect(_ledger_path(project_root))
    try:
        conn.executescript(DDL)
        conn.commit()
    finally:
        conn.close()


def _row_to_event(row: sqlite3.Row) -> dict[str, Any]:
    payload: Any = {}
    metadata: dict[str, Any] = {}
    try:
        payload = json.loads(row["payload"])
    except (ValueError, TypeError):
        payload = row["payload"]
    if row["metadata"]:
        try:
            metadata = json.loads(row["metadata"])
        except (ValueError, TypeError):
            metadata = {}
    return {
        "seq": row["seq"],
        "event_id": row["event_id"],
        "parent_hash": row["parent_hash"],
        "current_hash": row["current_hash"],
        "event_type": row["event_type"],
        "entity_ref": row["entity_ref"],
        "payload": payload,
        "metadata": metadata,
        "created_at": row["created_at"],
    }


def append_event(
    project_root: Path,
    event_type: str,
    entity_ref: str,
    payload: dict[str, Any],
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    conn = _connect(_ledger_path(project_root))
    try:
        conn.executescript(DDL)
        conn.execute("BEGIN IMMEDIATE")
        try:
            row = conn.execute("SELECT current_hash FROM cortex_events ORDER BY seq DESC LIMIT 1").fetchone()
            parent_hash = row["current_hash"] if row else _ZERO_HASH
            created_at = int(time.time() * 1000)
            payload_c = _canonical(payload)
            event_id = str(uuid.uuid5(_NS, f"{parent_hash}|{event_type}|{entity_ref}|{payload_c}"))
            envelope = f"{parent_hash}|{created_at}|{event_type}|{entity_ref}|{payload_c}"
            current_hash = hashlib.sha256(envelope.encode("utf-8")).hexdigest()
            conn.execute(
                "INSERT INTO cortex_events (event_id, parent_hash, current_hash, event_type, entity_ref, payload, metadata, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    event_id,
                    parent_hash,
                    current_hash,
                    event_type,
                    entity_ref,
                    payload_c,
                    _canonical(metadata) if metadata else None,
                    created_at,
                ),
            )
            conn.execute("COMMIT")
        except sqlite3.IntegrityError:
            conn.execute("ROLLBACK")
            existing = conn.execute("SELECT * FROM cortex_events WHERE event_id = ?", (event_id,)).fetchone()
            if existing:
                return _row_to_event(existing)
            raise
        inserted = conn.execute("SELECT * FROM cortex_events WHERE event_id = ?", (event_id,)).fetchone()
        return _row_to_event(inserted)
    finally:
        conn.close()


def list_events(project_root: Path, limit: int = 100, offset: int = 0, event_type: str | None = None) -> dict[str, Any]:
    conn = _connect(_ledger_path(project_root))
    try:
        conn.executescript(DDL)
        if event_type:
            total = conn.execute(
                "SELECT COUNT(*) AS c FROM cortex_events WHERE event_type = ?", (event_type,)
            ).fetchone()["c"]
            rows = conn.execute(
                "SELECT * FROM cortex_events WHERE event_type = ? ORDER BY seq DESC LIMIT ? OFFSET ?",
                (event_type, limit, offset),
            ).fetchall()
        else:
            total = conn.execute("SELECT COUNT(*) AS c FROM cortex_events").fetchone()["c"]
            rows = conn.execute(
                "SELECT * FROM cortex_events ORDER BY seq DESC LIMIT ? OFFSET ?", (limit, offset)
            ).fetchall()
        return {"events": [_row_to_event(r) for r in rows], "total": total, "limit": limit, "offset": offset}
    finally:
        conn.close()


def claim(project_root: Path, key: str) -> bool:
    conn = _connect(_ledger_path(project_root))
    try:
        conn.execute("CREATE TABLE IF NOT EXISTS cortex_claims (key TEXT PRIMARY KEY, ts INTEGER NOT NULL)")
        conn.execute("BEGIN IMMEDIATE")
        try:
            conn.execute("INSERT INTO cortex_claims (key, ts) VALUES (?, ?)", (key, int(time.time() * 1000)))
            conn.execute("COMMIT")
            return True
        except sqlite3.IntegrityError:
            conn.execute("ROLLBACK")
            return False
    finally:
        conn.close()


def verify_chain(project_root: Path) -> dict[str, Any]:
    conn = _connect(_ledger_path(project_root))
    try:
        conn.executescript(DDL)
        rows = conn.execute("SELECT * FROM cortex_events ORDER BY seq ASC").fetchall()
        prev = _ZERO_HASH
        verified = 0
        broken_at: int | None = None
        for row in rows:
            payload_c = row["payload"]
            envelope = f"{prev}|{row['created_at']}|{row['event_type']}|{row['entity_ref']}|{payload_c}"
            recomputed = hashlib.sha256(envelope.encode("utf-8")).hexdigest()
            ok = row["parent_hash"] == prev and recomputed == row["current_hash"]
            if ok:
                verified += 1
            elif broken_at is None:
                broken_at = row["seq"]
            prev = row["current_hash"]
        return {
            "valid": broken_at is None,
            "total_entries": len(rows),
            "verified_entries": verified,
            "broken_at": broken_at,
        }
    finally:
        conn.close()
