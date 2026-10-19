"""
CORTEX SQLite WAL Checkpoint Store (Ring-1 / 01_KISH_ENGINE).

Enforces:
  - INV_C5_WAL_SYNCHRONOUS_FULL: SQLite WAL with `PRAGMA synchronous = FULL`.
  - INV_C5_SHM: Explicit annihilation helper for SQLite WAL triplet (`.db`, `.db-wal`, `.db-shm`).
  - INV_C5_RING2_NO_SQLITE: Isolates `sqlite3` persistence inside 01_KISH_ENGINE so
    02_EDIN_SWARMS never imports `sqlite3` directly.
"""

from __future__ import annotations

import json
from pathlib import Path
import sqlite3
from typing import Any, Dict, List, Optional, Sequence, Set, Tuple


def annihilate_wal_triplet(db_path: Path | str) -> None:
    """
    Explicitly removes `.db`, `.db-wal`, and `.db-shm` artifacts (INV_C5_SHM).
    """
    base = Path(db_path)
    for suffix in ("", "-wal", "-shm"):
        candidate = Path(f"{base}{suffix}")
        if candidate.exists():
            candidate.unlink()


class CortexWalStore:
    """
    Append-only SQLite WAL state & evidence store for CORTEX (`PRAGMA synchronous = FULL`).
    Persists tool results and errors BEFORE context compaction so failures never vanish.
    """

    def __init__(self, db_path: Path | str) -> None:
        self.db_path = Path(db_path)
        self._conn = sqlite3.connect(str(self.db_path))
        self._conn.row_factory = sqlite3.Row
        self._configure_wal()
        self._init_schema()

    def _configure_wal(self) -> None:
        cur = self._conn.cursor()
        cur.execute("PRAGMA journal_mode = WAL;")
        cur.execute("PRAGMA synchronous = FULL;")
        cur.execute("PRAGMA foreign_keys = ON;")
        self._conn.commit()

    def verify_wal_pragmas(self) -> Tuple[str, int]:
        """Returns `(journal_mode, synchronous)` to falsify WAL configuration in tests."""
        cur = self._conn.cursor()
        mode = str(cur.execute("PRAGMA journal_mode;").fetchone()[0]).lower()
        sync_flag = int(cur.execute("PRAGMA synchronous;").fetchone()[0])
        return mode, sync_flag

    def _init_schema(self) -> None:
        cur = self._conn.cursor()
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS task_checkpoints (
                task_id TEXT PRIMARY KEY,
                last_completed_step INTEGER NOT NULL,
                logical_tick INTEGER NOT NULL,
                active_model TEXT NOT NULL,
                consecutive_failures INTEGER NOT NULL DEFAULT 0,
                compacted_error_summary TEXT NOT NULL DEFAULT '[]'
            );
            """
        )
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS audit_events (
                event_id TEXT PRIMARY KEY,
                task_id TEXT NOT NULL,
                step_index INTEGER NOT NULL,
                logical_tick INTEGER NOT NULL,
                idempotency_key TEXT NOT NULL UNIQUE,
                model_id TEXT NOT NULL,
                phase TEXT NOT NULL,
                gateway_decision TEXT NOT NULL,
                test_status TEXT NOT NULL,
                evidence_hash TEXT NOT NULL,
                error_detail TEXT NOT NULL DEFAULT ''
            );
            """
        )
        self._conn.commit()

    def close(self) -> None:
        self._conn.close()

    def get_checkpoint(self, task_id: str) -> Optional[Dict[str, Any]]:
        cur = self._conn.cursor()
        row = cur.execute(
            "SELECT * FROM task_checkpoints WHERE task_id = ?;",
            (task_id,),
        ).fetchone()
        if row is None:
            return None
        return dict(row)

    def has_idempotency_key(self, idempotency_key: str) -> Optional[Dict[str, Any]]:
        cur = self._conn.cursor()
        row = cur.execute(
            "SELECT * FROM audit_events WHERE idempotency_key = ?;",
            (idempotency_key,),
        ).fetchone()
        return dict(row) if row is not None else None

    def record_step_atomic(
        self,
        *,
        task_id: str,
        step_index: int,
        logical_tick: int,
        idempotency_key: str,
        model_id: str,
        phase: str,
        gateway_decision: str,
        test_status: str,
        evidence_hash: str,
        error_detail: str = "",
        update_completed_step: bool = True,
        consecutive_failures: int = 0,
    ) -> str:
        """
        Atomically appends an audit event (`EV_{logical_tick}_{step_index}`) and updates
        the task checkpoint under `PRAGMA synchronous = FULL`.
        """
        event_id = f"EV_{logical_tick}_{step_index}_{idempotency_key[:8]}"
        cur = self._conn.cursor()
        existing_cp = self.get_checkpoint(task_id)
        errors: List[str] = []
        if existing_cp is not None:
            errors = json.loads(existing_cp["compacted_error_summary"])
        if error_detail:
            entry = f"step={step_index}:{error_detail}"
            if entry not in errors:
                errors.append(entry)

        last_step = (
            step_index
            if update_completed_step
            else (existing_cp["last_completed_step"] if existing_cp is not None else -1)
        )

        cur.execute(
            """
            INSERT INTO audit_events (
                event_id, task_id, step_index, logical_tick, idempotency_key,
                model_id, phase, gateway_decision, test_status, evidence_hash, error_detail
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
            """,
            (
                event_id,
                task_id,
                step_index,
                logical_tick,
                idempotency_key,
                model_id,
                phase,
                gateway_decision,
                test_status,
                evidence_hash,
                error_detail,
            ),
        )
        cur.execute(
            """
            INSERT INTO task_checkpoints (
                task_id, last_completed_step, logical_tick, active_model,
                consecutive_failures, compacted_error_summary
            ) VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(task_id) DO UPDATE SET
                last_completed_step = excluded.last_completed_step,
                logical_tick = excluded.logical_tick,
                active_model = excluded.active_model,
                consecutive_failures = excluded.consecutive_failures,
                compacted_error_summary = excluded.compacted_error_summary;
            """,
            (
                task_id,
                last_step,
                logical_tick,
                model_id,
                consecutive_failures,
                json.dumps(errors),
            ),
        )
        self._conn.commit()
        return event_id

    def get_failed_action_signatures(self, task_id: str) -> Set[str]:
        """Returns action signatures that previously failed or were denied, preventing repeat loops."""
        cur = self._conn.cursor()
        rows = cur.execute(
            """
            SELECT idempotency_key FROM audit_events
            WHERE task_id = ? AND (gateway_decision = 'DENY' OR test_status = 'FAIL');
            """,
            (task_id,),
        ).fetchall()
        return {str(r["idempotency_key"]) for r in rows}

    def list_events(self, task_id: str) -> List[Dict[str, Any]]:
        cur = self._conn.cursor()
        rows = cur.execute(
            "SELECT * FROM audit_events WHERE task_id = ? ORDER BY logical_tick ASC;",
            (task_id,),
        ).fetchall()
        return [dict(r) for r in rows]

    def compact_context_preserving_errors(
        self,
        task_id: str,
        messages: Sequence[Dict[str, str]],
        max_tail: int = 4,
        blackboard_digest: Optional[Any] = None,
    ) -> List[Dict[str, str]]:
        """
        Compacts long conversation history while:
          1. Keeping the immutable prefix (`system` + initial user goal) intact for 96% cache reuse.
          2. Injecting the durable error ledger from SQLite WAL so zero error evidence is lost.
          3. Optionally injecting the compacted `BlackboardDigest` from `ColdPathCurator`.
        """
        if len(messages) <= max_tail + 2 and blackboard_digest is None:
            return list(messages)

        prefix = list(messages[:2])
        tail = list(messages[-max_tail:]) if len(messages) > 2 else []
        cp = self.get_checkpoint(task_id)
        errors: List[str] = json.loads(cp["compacted_error_summary"]) if cp else []
        last_step = cp["last_completed_step"] if cp else -1

        ledger_note = {
            "role": "system",
            "content": (
                f"[CORTEX-WAL-CHECKPOINT] last_completed_step={last_step} | preserved_errors={json.dumps(errors)}"
            ),
        }
        injected_notes = [ledger_note]
        if blackboard_digest is not None and hasattr(blackboard_digest, "to_system_note"):
            injected_notes.append(blackboard_digest.to_system_note())
        return prefix + injected_notes + tail
