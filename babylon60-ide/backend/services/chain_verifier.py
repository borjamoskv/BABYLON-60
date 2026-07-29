"""
BABYLON60 IDE — Hash-chain integrity verifier.
Wraps the BFT ledger verification logic for the IDE frontend.
"""

from __future__ import annotations

import hashlib
import json
import sqlite3
from pathlib import Path
from typing import Any

from .db_pool import connect_readonly


ZERO_HASH = "0" * 64


def _canonical_json(data: Any) -> str:
    return json.dumps(
        data,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    )


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


def verify_chain(db_path: str | Path) -> dict[str, Any]:
    """Verify the entire hash chain of a ledger database.

    Returns verification result with per-entry status.
    """
    result: dict[str, Any] = {
        "valid": True,
        "total_entries": 0,
        "verified_entries": 0,
        "broken_at": None,
        "error": None,
        "entries": [],
    }

    try:
        conn = connect_readonly(db_path)
    except sqlite3.OperationalError as e:
        result["valid"] = False
        result["error"] = f"Cannot open database: {e}"
        return result

    try:
        cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='ledger_entries'")
        if not cursor.fetchone():
            result["error"] = "No ledger_entries table found"
            result["valid"] = False
            return result

        cursor = conn.execute("SELECT * FROM ledger_entries ORDER BY seq ASC")
        rows = cursor.fetchall()
        columns = [desc[0] for desc in cursor.description]
        result["total_entries"] = len(rows)

        prev_hash = ZERO_HASH
        last_lamport = 0

        for row in rows:
            row_dict = dict(zip(columns, row))
            seq = row_dict["seq"]
            entry_status: dict[str, Any] = {
                "seq": seq,
                "event_id": row_dict["event_id"],
                "stream": row_dict["stream"],
                "lamport_t": row_dict["lamport_t"],
                "entry_hash": row_dict["entry_hash"][:16] + "...",
                "valid": True,
                "errors": [],
            }

            # Check Lamport monotonicity
            if row_dict["lamport_t"] <= last_lamport:
                entry_status["valid"] = False
                entry_status["errors"].append(f"Lamport {row_dict['lamport_t']} <= {last_lamport}")

            # Check prev_hash linkage
            if row_dict["prev_hash"] != prev_hash:
                entry_status["valid"] = False
                entry_status["errors"].append("prev_hash chain break")

            # Recompute hash
            computed = _compute_entry_hash(
                event_id=row_dict["event_id"],
                stream=row_dict["stream"],
                entity_id=row_dict["entity_id"],
                event_type=row_dict["event_type"],
                payload_json=row_dict["payload_json"],
                source_db=row_dict["source_db"],
                source_table=row_dict["source_table"],
                source_pk=row_dict["source_pk"],
                cortex_taint=row_dict["cortex_taint"],
                lamport_t=row_dict["lamport_t"],
                prev_hash=row_dict["prev_hash"],
                created_at=row_dict["created_at"],
            )

            if computed != row_dict["entry_hash"]:
                entry_status["valid"] = False
                entry_status["errors"].append("Hash mismatch (tampered)")

            if entry_status["valid"]:
                result["verified_entries"] += 1
            elif result["broken_at"] is None:
                result["broken_at"] = seq
                result["valid"] = False

            result["entries"].append(entry_status)
            prev_hash = row_dict["entry_hash"]
            last_lamport = row_dict["lamport_t"]

    except sqlite3.OperationalError as e:
        result["valid"] = False
        result["error"] = str(e)
    finally:
        conn.close()

    return result
