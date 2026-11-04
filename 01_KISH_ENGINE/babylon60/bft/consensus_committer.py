# ============================================================================
# BABYLON-60 v4.0 Sovereign Hardened
# █ AUTOCOGNITION-Ω | STATE: C5-REAL | AESTHETIC: INDUSTRIAL_NOIR_2026
# ============================================================================
# [Causal-Determinist] BFT consensus committer — Operador ortogonal (C) puro.
# No valida matemáticamente. Solo muta disco y persiste ledger (WAL).
import sqlite3
import math
import os
import stat
from typing import Dict, Mapping
from dataclasses import dataclass
from babylon60.database import core as database_core
from babylon60.core.crypto_utils import canonicalize_cbor, hash_sha3_256


@dataclass(frozen=True)
class StateMutation:
    agent_id: str
    payload: Mapping[str, object] | Dict[str, object]
    timestamp: float
    signature: str
    causal_taint: str = "BFT_Consensus_Init"

    def signing_payload(self, f: int) -> dict[str, object]:
        """V1 vote scope. timestamp is caller-supplied metadata, never a host clock."""
        if type(f) is not int or f < 0:
            raise ValueError("BFT_INVALID_CONFIGURATION: f must be a non-negative integer")
        if not isinstance(self.agent_id, str) or not isinstance(self.causal_taint, str):
            raise ValueError("Mutation identity and causal taint must be strings")
        if not isinstance(self.payload, Mapping):
            raise ValueError("Mutation payload must be an object")
        if type(self.timestamp) not in (int, float):
            raise ValueError("Mutation timestamp must be a finite number")
        try:
            timestamp = float(self.timestamp)
        except OverflowError as exc:
            raise ValueError("Mutation timestamp must be a finite number") from exc
        if not math.isfinite(timestamp):
            raise ValueError("Mutation timestamp must be a finite number")
        if type(self.timestamp) is int and int(timestamp) != self.timestamp:
            raise ValueError("Integer timestamp loses precision in SQLite REAL")
        return {
            "schema": "babylon60:state-mutation:v1",
            "agent_id": self.agent_id,
            "payload": self.payload,
            "timestamp": timestamp if timestamp != 0 else 0.0,
            "causal_taint": self.causal_taint,
            "fault_budget": f,
        }

    def signing_hash(self, f: int) -> str:
        return hash_sha3_256(canonicalize_cbor(self.signing_payload(f)))


class BFT_Committer:
    def __init__(self, db_path: str = "master_ledger.db") -> None:
        self._owner_pid = os.getpid()
        self._lock_fd: int | None = None
        try:
            import fcntl

            # Lock the database that connect_sync actually opens, including its
            # centralized routing and aliases through symlinked directories.
            resolved_path = database_core.resolve_db_path(db_path).resolve()
            flags = os.O_CREAT | os.O_RDWR | os.O_NOFOLLOW | os.O_NONBLOCK | getattr(os, "O_CLOEXEC", 0)
            self._lock_fd = os.open(f"{resolved_path}.lock", flags, 0o600)
            if not stat.S_ISREG(os.fstat(self._lock_fd).st_mode):
                raise OSError("Ledger lock must be a regular file")
            fcntl.flock(self._lock_fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError as e:
            self._release_lock()
            raise SystemExit(f"CRITICAL: No se pudo adquirir lock exclusivo: {e}") from e

        try:
            self._conn: sqlite3.Connection = database_core.connect_sync(resolved_path, synchronous="FULL")
            self._init_tables()
        except BaseException:
            self.close()
            raise

    def _release_lock(self) -> None:
        descriptor = self._lock_fd
        self._lock_fd = None
        if descriptor is not None:
            try:
                # A forked descriptor refers to the parent's lock as well.
                # Close the child's copy without issuing LOCK_UN on that lock.
                if os.getpid() == self._owner_pid:
                    import fcntl

                    fcntl.flock(descriptor, fcntl.LOCK_UN)
            finally:
                os.close(descriptor)

    @property
    def conn(self) -> sqlite3.Connection:
        if os.getpid() != self._owner_pid:
            raise sqlite3.ProgrammingError("Inherited ledger connection cannot be used after fork; reopen it")
        return self._conn

    def __del__(self) -> None:
        try:
            self.close()
        except (OSError, sqlite3.Error):
            pass  # Explicit close reports errors; finalization cannot report them reliably.

    def close(self) -> None:
        if os.getpid() != self._owner_pid:
            self._release_lock()
            return  # Never invoke SQLite methods on the inherited connection.
        connection = getattr(self, "_conn", None)
        if connection is not None:
            connection.close()
        # Keep ownership if SQLite rejects closing (e.g. a foreign thread).
        self._release_lock()

    def require_autocommit(self) -> None:
        if self.conn.in_transaction:
            raise sqlite3.ProgrammingError("Ledger operation requires no active caller transaction")

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
        # Historical rows remain untouched and explicitly unauthenticated. Never
        # manufacture quorum evidence while migrating a pre-v1 database.
        columns = {row[1] for row in self.conn.execute("PRAGMA table_info(state_log)")}
        for name, sql_type in (("fault_budget", "INTEGER"), ("quorum_votes", "BLOB")):
            if name not in columns:
                self.conn.execute(f"ALTER TABLE state_log ADD COLUMN {name} {sql_type}")

    def commit_mutation(self, mutation: StateMutation, mutation_hash: str, f: int, signatures: Dict[str, str]) -> bool:
        self.require_autocommit()
        expected = (
            canonicalize_cbor(mutation.payload),
            mutation.agent_id,
            float(mutation.timestamp),
            mutation.causal_taint,
            f,
            canonicalize_cbor(signatures),
        )
        select_record = (
            "SELECT id, payload, agent_id, ts, causal_taint, fault_budget, quorum_votes "
            "FROM state_log WHERE mutation_hash = ?"
        )
        self.conn.execute("BEGIN IMMEDIATE")
        try:
            existing = self.conn.execute(select_record, (mutation_hash,)).fetchone()
            if existing is not None:
                if existing[1:] != expected:
                    raise ValueError(f"Fail-fast: INV_BFT_04 Collision for mutation_hash {mutation_hash}")
                self.conn.commit()
                return True
            changes_before = self.conn.total_changes
            cursor = self.conn.execute(
                "INSERT INTO state_log (mutation_hash, agent_id, payload, ts, causal_taint, fault_budget, quorum_votes) "
                "VALUES (?, ?, ?, ?, ?, ?, ?)",
                (mutation_hash, mutation.agent_id, expected[0], expected[2], mutation.causal_taint, f, expected[5]),
            )
            inserted_id, affected = cursor.lastrowid, cursor.rowcount
            cursor.close()
            actual = self.conn.execute(select_record, (mutation_hash,)).fetchone()
            # SQLite can suppress an INSERT without raising, and AFTER triggers
            # can alter or remove it. Acceptance requires the exact approved row.
            if affected != 1 or self.conn.total_changes - changes_before != 1 or actual != (inserted_id, *expected):
                raise ValueError("Signed mutation was not persisted exactly as approved")
            self.conn.commit()
            return True
        except BaseException as failure:
            try:
                self.conn.rollback()
            except BaseException as rollback_failure:
                # A connection with unknown pending effects cannot be reused.
                # SQLite close rolls back the transaction before releasing ownership.
                self.close()
                raise rollback_failure from failure
            raise

    def get_audit_rows(self) -> list[tuple] | None:
        cursor = self.conn.cursor()
        try:
            cursor.execute(
                "SELECT id, mutation_hash, agent_id, payload, ts, causal_taint, fault_budget, quorum_votes "
                "FROM state_log ORDER BY id"
            )
            return cursor.fetchall()
        except sqlite3.OperationalError:
            return None
