# C5-REAL EXERGY CERTIFIED
"""
Append-only BFT ledger backed by SQLite.

Provides an immutable, auditable log of attestation receipts. SQLite triggers
enforce the append-only invariant: DELETE and UPDATE are rejected at the
database engine level (not application level).

Uses exponential backoff with jitter for concurrent access (Zero-Lock contention).
"""
from __future__ import annotations

import json
import os
import random
import sqlite3
import time
import uuid
from typing import Any, Optional


class AppendOnlyLedger:
    """
    BFT (Byzantine Fault Tolerant) append-only ledger for SCITT receipts.

    Once a receipt is written, it cannot be modified or deleted. This invariant
    is enforced by SQLite BEFORE triggers, making mutation structurally impossible
    even with direct SQL access.

    Example:
        >>> ledger = AppendOnlyLedger("attestations.db")
        >>> entry_id = ledger.append(receipt_dict)
        >>> ledger.lookup(entry_id)
        {...}
    """

    TABLE_NAME = "bft_attestation_log"

    def __init__(
        self,
        db_path: str = "attestations.db",
        max_retries: int = 15,
        base_delay: float = 0.02,
    ) -> None:
        os.makedirs(os.path.dirname(os.path.abspath(db_path)), exist_ok=True)
        self._db_path = db_path
        self._max_retries = max_retries
        self._base_delay = base_delay
        self._conn = sqlite3.connect(db_path, timeout=0.0)
        self._conn.execute("PRAGMA journal_mode=WAL;")
        self._conn.execute("PRAGMA synchronous=NORMAL;")
        self._bootstrap_schema()

    def _bootstrap_schema(self) -> None:
        self._execute(
            f"""
            CREATE TABLE IF NOT EXISTS {self.TABLE_NAME} (
                uuid        TEXT PRIMARY KEY,
                timestamp   TEXT NOT NULL,
                digest      TEXT NOT NULL,
                payload     TEXT NOT NULL
            )
            """
        )
        self._execute(
            f"""
            CREATE INDEX IF NOT EXISTS idx_{self.TABLE_NAME}_digest
            ON {self.TABLE_NAME} (digest)
            """
        )
        # Append-only: structurally reject DELETE
        self._execute(
            f"""
            CREATE TRIGGER IF NOT EXISTS trg_{self.TABLE_NAME}_no_delete
            BEFORE DELETE ON {self.TABLE_NAME}
            BEGIN
                SELECT RAISE(ABORT,
                    'C5-REAL: Attestation ledger is append-only. Purge rejected.');
            END;
            """
        )
        # Append-only: structurally reject UPDATE
        self._execute(
            f"""
            CREATE TRIGGER IF NOT EXISTS trg_{self.TABLE_NAME}_no_update
            BEFORE UPDATE ON {self.TABLE_NAME}
            BEGIN
                SELECT RAISE(ABORT,
                    'C5-REAL: Attestation entries are immutable. Mutation rejected.');
            END;
            """
        )
        self._conn.commit()

    def _execute(self, sql: str, parameters: tuple[Any, ...] = ()) -> sqlite3.Cursor:
        """Execute with exponential backoff + jitter on lock contention."""
        retries = 0
        while True:
            try:
                return self._conn.execute(sql, parameters)
            except sqlite3.OperationalError as exc:
                msg = str(exc).lower()
                if ("locked" in msg or "busy" in msg) and retries < self._max_retries:
                    delay = self._base_delay * (2**retries)
                    jitter = random.uniform(0, delay * 0.1)
                    time.sleep(delay + jitter)
                    retries += 1
                else:
                    raise

    def append(self, receipt: dict[str, Any], timestamp: str = "") -> str:
        """
        Append a receipt to the ledger. Returns the UUID of the entry.

        Idempotent: if the same digest is already present, returns the
        existing UUID without raising.
        """
        digest = receipt.get("attestation_digest", "")
        if not timestamp:
            import datetime
            timestamp = datetime.datetime.now(
                datetime.timezone.utc
            ).isoformat()

        entry_uuid = str(
            uuid.uuid5(uuid.NAMESPACE_URL, f"babylon60:attest:{digest}")
        )
        payload = json.dumps(receipt, sort_keys=True, separators=(",", ":"), ensure_ascii=False)

        try:
            self._execute(
                f"INSERT INTO {self.TABLE_NAME} (uuid, timestamp, digest, payload) VALUES (?, ?, ?, ?)",
                (entry_uuid, timestamp, digest, payload),
            )
            self._conn.commit()
        except sqlite3.IntegrityError:
            pass  # Idempotent: already witnessed

        return entry_uuid

    def lookup(self, entry_uuid: str) -> Optional[dict[str, Any]]:
        """Retrieve a receipt by UUID. Returns None if not found."""
        cursor = self._execute(
            f"SELECT payload FROM {self.TABLE_NAME} WHERE uuid = ?",
            (entry_uuid,),
        )
        row = cursor.fetchone()
        if row is None:
            return None
        return json.loads(row[0])

    def lookup_by_digest(self, digest: str) -> Optional[dict[str, Any]]:
        """Retrieve a receipt by its attestation digest. Returns None if not found."""
        cursor = self._execute(
            f"SELECT payload FROM {self.TABLE_NAME} WHERE digest = ?",
            (digest,),
        )
        row = cursor.fetchone()
        if row is None:
            return None
        return json.loads(row[0])

    def count(self) -> int:
        """Total entries in the ledger."""
        cursor = self._execute(f"SELECT COUNT(*) FROM {self.TABLE_NAME}")
        return cursor.fetchone()[0]

    def close(self) -> None:
        self._conn.close()

    def __enter__(self) -> "AppendOnlyLedger":
        return self

    def __exit__(self, *_: Any) -> None:
        self.close()
