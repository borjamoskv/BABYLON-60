"""
Enterprise Audit Ledger (SOC 2 Compliance).

Append-only cryptographic ledger tracking all operations.
Secures the `tenant_id` and the identity of the operator, creating
a hash-chain to prove immutability of the audit logs.
"""

import asyncio
import json
import logging
import os
import sqlite3
import sys
import unicodedata
from datetime import datetime, timezone
from typing import Any, Optional

import aiosqlite
from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ed25519

from babylon60.crypto.hash_registry import cortex_hash
from babylon60.database.core import causal_write

logger = logging.getLogger("babylon60.audit.ledger")

_CREATE_AUDIT_SQL = """
CREATE TABLE IF NOT EXISTS cortex_agent_registry (
    agent_id TEXT PRIMARY KEY,
    role TEXT NOT NULL,
    public_key TEXT NOT NULL,
    status TEXT NOT NULL,
    created_at TEXT NOT NULL
) STRICT;

CREATE TABLE IF NOT EXISTS cortex_sessions (
    session_id TEXT PRIMARY KEY,
    agent_id TEXT NOT NULL REFERENCES cortex_agent_registry(agent_id),
    status TEXT NOT NULL,
    started_at TEXT NOT NULL
) STRICT;

CREATE TABLE IF NOT EXISTS security_audit_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    audit_id TEXT NOT NULL UNIQUE CHECK (length(audit_id) = 44 AND audit_id GLOB '[0-9a-zA-Z]*'),
    lamport_t INTEGER NOT NULL CHECK (lamport_t >= 0),
    timestamp TEXT NOT NULL,
    tenant_id TEXT NOT NULL,
    actor_role TEXT NOT NULL,
    actor_id TEXT NOT NULL,
    session_id TEXT,
    action TEXT NOT NULL,
    resource TEXT NOT NULL,
    status TEXT NOT NULL,
    idempotency_key TEXT UNIQUE,
    payload_canonical BLOB NOT NULL,
    payload_hash TEXT NOT NULL CHECK (length(payload_hash) = 44 AND payload_hash GLOB '[0-9a-zA-Z]*'),
    envelope_canonical BLOB NOT NULL,
    prev_hash TEXT NOT NULL CHECK (length(prev_hash) = 44 AND prev_hash GLOB '[0-9a-zA-Z]*'),
    signature TEXT NOT NULL,
    external_anchor TEXT,
    UNIQUE (prev_hash),
    UNIQUE (lamport_t, actor_id, action)
) STRICT;

CREATE UNIQUE INDEX IF NOT EXISTS idx_ledger_prev_hash_unique ON security_audit_log(prev_hash);
CREATE UNIQUE INDEX IF NOT EXISTS idx_ledger_audit_id_unique ON security_audit_log(audit_id);

CREATE TRIGGER IF NOT EXISTS ledger_no_update
BEFORE UPDATE ON security_audit_log
BEGIN
    SELECT RAISE(ABORT, 'LEDGER VIOLATION: security_audit_log is append-only (UPDATE blocked)');
END;

CREATE TRIGGER IF NOT EXISTS ledger_no_delete
BEFORE DELETE ON security_audit_log
BEGIN
    SELECT RAISE(ABORT, 'LEDGER VIOLATION: security_audit_log is append-only (DELETE blocked)');
END;

CREATE TRIGGER IF NOT EXISTS ledger_chain_link
BEFORE INSERT ON security_audit_log
BEGIN
    SELECT CASE
        WHEN (SELECT COUNT(*) FROM security_audit_log) = 0 AND NEW.prev_hash != '00000000000000000000000000000000000000000000'
        THEN RAISE(ABORT, 'invalid genesis prev_hash')

        WHEN (SELECT COUNT(*) FROM security_audit_log) > 0 AND NEW.prev_hash != (
            SELECT audit_id FROM security_audit_log ORDER BY id DESC LIMIT 1
        )
        THEN RAISE(ABORT, 'CHAIN BREAK: prev_hash does not match current ledger head')
    END;
END;

CREATE TRIGGER IF NOT EXISTS ledger_lamport_monotonic_global
BEFORE INSERT ON security_audit_log
BEGIN
    SELECT CASE
        WHEN NEW.lamport_t <= COALESCE((SELECT MAX(lamport_t) FROM security_audit_log), -1)
        THEN RAISE(ABORT, 'CAUSAL VIOLATION: global lamport clock regression')
    END;
END;
"""


class LedgerCorruption(Exception):
    pass


def normalize_json(value: Any) -> Any:
    if isinstance(value, str):
        return unicodedata.normalize("NFC", value)
    if isinstance(value, float):
        raise TypeError(
            "JSON object values must not be floats (use normalized strings or integer microunits)"
        )
    if isinstance(value, list):
        return [normalize_json(v) for v in value]
    if isinstance(value, dict):
        return {unicodedata.normalize("NFC", str(k)): normalize_json(v) for k, v in value.items()}
    if value is not None and not isinstance(value, (int, bool)):
        raise TypeError(f"Invalid JSON type: {type(value)}")
    return value


def canonical_json_bytes(payload: Any) -> bytes:
    normalized = normalize_json(payload)
    json_str = json.dumps(
        normalized, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False
    )
    return json_str.encode("utf-8")


def reject_duplicate_keys(pairs):
    seen = set()
    for key, _value in pairs:
        if key in seen:
            raise ValueError(f"duplicate JSON key: {key}")
        seen.add(key)
    return dict(pairs)


class LamportClock:
    """Reloj lógico de Lamport thread-safe para asyncio."""

    def __init__(self, initial: int = 0):
        self._time: int = initial
        self._lock = asyncio.Lock()

    @property
    def time(self) -> int:
        return self._time

    async def tick(self, incoming: Optional[int] = None) -> int:
        async with self._lock:
            if incoming is not None:
                self._time = max(self._time, incoming)
            else:
                self._time += 1
            return self._time


class EnterpriseAuditLedger:
    """Immutable Audit Ledger (CORTEX-PERSIST) using Single-Writer Queue."""

    def __init__(self, conn: aiosqlite.Connection) -> None:
        self._conn = conn
        self._ready = False
        self._last_hash = "0" * 44

        self._lamport = LamportClock()
        self._write_queue: asyncio.Queue = asyncio.Queue()
        self._writer_task: Optional[asyncio.Task] = None
        self._forensic_queue: asyncio.Queue = asyncio.Queue()
        self._forensic_task: Optional[asyncio.Task] = None

        from babylon60.crypto.keys import KeyManager

        self._km = KeyManager(service_name="babylon60_ledger_enterprise")
        self.actor_id = "ledger_master"

        priv_b64 = self._km.get_private_key_b64(self.actor_id)
        if not priv_b64:
            self._km.generate_and_store_key(self.actor_id)
            priv_b64 = self._km.get_private_key_b64(self.actor_id)

        priv_bytes = __import__("base64").b64decode(priv_b64)
        try:
            self.private_key = ed25519.Ed25519PrivateKey.from_private_bytes(priv_bytes)
        except ValueError:
            key = serialization.load_pem_private_key(priv_bytes, password=None)
            assert isinstance(key, ed25519.Ed25519PrivateKey)
            self.private_key = key

        self.public_key = self.private_key.public_key()
        self._lock = asyncio.Lock()

    async def ensure_table(self) -> None:
        if not hasattr(self, "_lamport"):
            self._lamport = LamportClock()
        if self._ready:
            return
        # [C5-REAL] Non-destructive schema migration / Fail-closed audit check
        _CRITICAL_COLUMNS = {"audit_id", "lamport_t", "prev_hash", "signature"}
        _MIGRATABLE_COLUMNS = {"payload_canonical", "session_id"}
        try:
            cursor = await self._conn.execute("PRAGMA table_info(security_audit_log)")
            cols = await cursor.fetchall()
            if cols:
                col_names = {c[1] for c in cols}

                # Apoptosis check: if critical columns are missing, halt immediately
                critical_missing = _CRITICAL_COLUMNS - col_names
                if critical_missing:
                    raise LedgerCorruption(
                        f"[C5-REAL] FATAL: SCHEMA DRIFT DETECTED - Critical columns missing: {sorted(critical_missing)}. "
                        f"Refusing to start. Evidentiary integrity compromised."
                    )


                # Non-destructive migration for rest of missing columns
                missing_migratable = _MIGRATABLE_COLUMNS - col_names
                if missing_migratable:
                    logger.warning(
                        "[C5-REAL] Schema drift detected. Applying non-destructive migration for: %s",
                        sorted(missing_migratable)
                    )
                    await self._backup_ledger_to_jsonl()
                    if "payload_canonical" not in col_names:
                        await self._conn.execute(
                            "ALTER TABLE security_audit_log"
                            " ADD COLUMN payload_canonical BLOB NOT NULL DEFAULT x''"
                        )
                        logger.info("[C5-REAL] Added missing column: payload_canonical")
                    if "session_id" not in col_names:
                        await self._conn.execute(
                            "ALTER TABLE security_audit_log ADD COLUMN session_id TEXT"
                        )
                        logger.info("[C5-REAL] Added missing column: session_id")
                    await self._conn.commit()
                    logger.info("[C5-REAL] Non-destructive ledger migration applied.")
        except LedgerCorruption:
            raise
        except Exception as e:
            logger.error(f"Schema migration failed (ledger data preserved): {e}")
            raise LedgerCorruption(
                f"Cannot migrate ledger schema: {e}. Manual intervention required."
            ) from e

        await self._conn.executescript(_CREATE_AUDIT_SQL)
        await self._conn.commit()

        # Recover Lamport Clock and last hash from Persistence
        cursor = await self._conn.execute("SELECT MAX(lamport_t) FROM security_audit_log")
        row = await cursor.fetchone()
        if row and row[0] is not None:
            await self._lamport.tick(row[0])

        cursor = await self._conn.execute(
            "SELECT audit_id FROM security_audit_log ORDER BY id DESC LIMIT 1"
        )
        row_hash = await cursor.fetchone()
        self._last_hash = row_hash[0] if row_hash else "0" * 44

        self._ready = True
        if self._writer_task is None or self._writer_task.done():
            self._writer_task = asyncio.create_task(self._writer_loop())
        if getattr(self, "_forensic_task", None) is None or self._forensic_task.done():
            self._forensic_task = asyncio.create_task(self._forensic_loop())

    async def close(self) -> None:
        if self._writer_task and not self._writer_task.done():
            await self._write_queue.put(None)
            await self._writer_task
        if getattr(self, "_forensic_task", None) and not self._forensic_task.done():
            await self._forensic_queue.put(None)
            await self._forensic_task

    async def _backup_ledger_to_jsonl(self) -> None:
        """Backup existing ledger rows to JSONL before schema migration."""
        try:
            cursor = await self._conn.execute(
                "SELECT * FROM security_audit_log ORDER BY id ASC"
            )
            rows = await cursor.fetchall()
            if not rows:
                return

            col_cursor = await self._conn.execute("PRAGMA table_info(security_audit_log)")
            col_info = await col_cursor.fetchall()
            col_names = [c[1] for c in col_info]

            cortex_base = EdgeEnv.get("CORTEX_DIR") or EdgeEnv.get("BABYLON_DIR")
            if cortex_base:
                backup_dir = os.path.join(cortex_base, ".babylon60", "ledger_backups")
            else:
                backup_dir = os.path.join(
                    os.path.expanduser("~"), ".babylon60", "ledger_backups"
                )
            os.makedirs(backup_dir, exist_ok=True)

            timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
            backup_path = os.path.join(backup_dir, f"ledger_backup_{timestamp}.jsonl")

            with open(backup_path, "w", encoding="utf-8") as f:
                for row in rows:
                    record = {}
                    for i, col_name in enumerate(col_names):
                        val = row[i]
                        if isinstance(val, bytes):
                            val = val.hex()
                        record[col_name] = val
                    f.write(json.dumps(record, ensure_ascii=False) + "\n")

            logger.info(
                "[C5-REAL] Ledger backed up to %s (%d rows)", backup_path, len(rows)
            )
        except Exception as e:
            logger.error(f"Ledger backup failed (non-fatal): {e}")


    async def register_agent(
        self, agent_id: str, role: str, public_key: str, status: str = "active"
    ) -> None:
        await self.ensure_table()
        with causal_write(self._conn):
            await self._conn.execute(
                "INSERT INTO cortex_agent_registry (agent_id, role, public_key, status, created_at) VALUES (?, ?, ?, ?, ?)",
                (agent_id, role, public_key, status, datetime.now(timezone.utc).isoformat()),
            )
            await self._conn.commit()

    async def start_session(self, session_id: str, agent_id: str, status: str = "active") -> None:
        await self.ensure_table()
        with causal_write(self._conn):
            await self._conn.execute(
                "INSERT INTO cortex_sessions (session_id, agent_id, status, started_at) VALUES (?, ?, ?, ?)",
                (session_id, agent_id, status, datetime.now(timezone.utc).isoformat()),
            )
            await self._conn.commit()

    async def _forensic_loop(self) -> None:
        cortex_base = os.environ.get("CORTEX_DIR") or os.environ.get("BABYLON_DIR")
        if cortex_base:
            cortex_dir = os.path.join(cortex_base, ".babylon60")
        else:
            home_dir = os.path.expanduser("~")
            cortex_dir = os.path.join(home_dir, ".babylon60")
        os.makedirs(cortex_dir, exist_ok=True)
        forensic_file = os.path.join(cortex_dir, "forensic_quarantine.log")

        while True:
            try:
                item = await self._forensic_queue.get()
                if item is None:
                    self._forensic_queue.task_done()
                    break
                timestamp = datetime.now(timezone.utc).isoformat()
                with open(forensic_file, "a") as f:
                    f.write(f"{timestamp} | [RA-09 QUARANTINE] {json.dumps(item)}\n")
                self._forensic_queue.task_done()
            except asyncio.CancelledError:
                break
            except Exception as e:  # noqa: BLE001
                logger.error(f"Error in forensic loop: {e}")

    async def _writer_loop(self) -> None:
        while True:
            try:
                task = await self._write_queue.get()
                if task is None:
                    self._write_queue.task_done()
                    break

                (
                    tenant_id,
                    actor_role,
                    actor_id,
                    session_id,
                    action,
                    resource,
                    status,
                    payload_data,
                    idempotency_key,
                    in_tx_before,
                    future,
                ) = task

                try:
                    with causal_write(self._conn):
                        if not in_tx_before:
                            await self._conn.execute("BEGIN IMMEDIATE")

                        # 1. Read head
                        cursor = await self._conn.execute(
                            "SELECT audit_id, lamport_t FROM security_audit_log ORDER BY id DESC LIMIT 1"
                        )
                        row = await cursor.fetchone()
                        if row is None:
                            prev_hash = "0" * 44
                            previous_lamport = 0
                        else:
                            prev_hash = row[0]
                            previous_lamport = row[1]

                        lamport_t = max(self._lamport.time, previous_lamport) + 1

                        # 2. Canonicalize payload
                        payload_bytes = canonical_json_bytes(payload_data)
                        payload_hash = cortex_hash(payload_bytes)

                        # 3. Construct envelope
                        timestamp = datetime.now(timezone.utc).isoformat()

                        envelope = {
                            "domain": "babylon60.ledger.event.v1",
                            "prev_hash": prev_hash,
                            "lamport_t": lamport_t,
                            "actor_id": actor_id,
                            "action": action,
                            "payload_hash": payload_hash,
                            "idempotency_key": idempotency_key,
                        }
                        envelope_bytes = canonical_json_bytes(envelope)
                        audit_id = cortex_hash(envelope_bytes)
                        # 4. Sign envelope (audit_id is the hash of the envelope)
                        signature = self.private_key.sign(envelope_bytes).hex()

                        anchor_val = "sqlite_wal:~/.babylon60/anchors.db"

                        sys.stdout.write(f"[C5-ANCHOR] {audit_id}\n")
                        sys.stdout.flush()

                        try:
                            cortex_base = os.environ.get("CORTEX_DIR") or os.environ.get(
                                "BABYLON_DIR"
                            )
                            if cortex_base:
                                cortex_dir = os.path.join(cortex_base, ".babylon60")
                            else:
                                home_dir = os.path.expanduser("~")
                                cortex_dir = os.path.join(home_dir, ".babylon60")
                            os.makedirs(cortex_dir, exist_ok=True)
                            anchor_db = os.path.join(cortex_dir, "anchors.db")
                            with sqlite3.connect(anchor_db, timeout=5.0) as anchor_conn:
                                anchor_conn.execute("PRAGMA journal_mode=WAL;")
                                anchor_conn.execute("PRAGMA synchronous=NORMAL;")
                                anchor_conn.execute(
                                    "CREATE TABLE IF NOT EXISTS anchors (timestamp TEXT, audit_id TEXT)"
                                )
                                anchor_conn.execute(
                                    "INSERT INTO anchors (timestamp, audit_id) VALUES (?, ?)",
                                    (timestamp, audit_id)
                                )
                                anchor_file = os.path.join(cortex_dir, "anchors.log")
                                with open(anchor_file, "a") as f:
                                    f.write(f"{timestamp} | {audit_id}\n")
                        except Exception as e:  # noqa: BLE001
                            self._forensic_queue.put_nowait({"error": str(e), "context": "anchor_log_write"})

                        sql = """
                        INSERT INTO security_audit_log (
                            audit_id, lamport_t, timestamp, tenant_id, actor_role,
                            actor_id, session_id, action, resource, status,
                            idempotency_key, payload_canonical, payload_hash,
                            envelope_canonical, prev_hash, signature, external_anchor
                        ) VALUES (
                            ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?
                        )
                        """
                        params = (
                            audit_id,
                            lamport_t,
                            timestamp,
                            tenant_id,
                            actor_role,
                            actor_id,
                            session_id,
                            action,
                            resource,
                            status,
                            idempotency_key,
                            payload_bytes,
                            payload_hash,
                            envelope_bytes,
                            prev_hash,
                            signature,
                            anchor_val,
                        )

                        await self._conn.execute(sql, params)
                        if not in_tx_before:
                            await self._conn.commit()

                        self._last_hash = audit_id
                        await self._lamport.tick(lamport_t)

                        future.set_result(audit_id)
                except sqlite3.OperationalError as e:
                    if not in_tx_before:
                        try:
                            await self._conn.rollback()
                        except Exception as rb_err:  # noqa: BLE001
                            self._forensic_queue.put_nowait({"error": str(rb_err), "context": "rollback_operational_error"})
                    if not future.done():
                        future.set_exception(e)
                except sqlite3.IntegrityError as e:
                    if not in_tx_before:
                        try:
                            await self._conn.rollback()
                        except Exception as rb_err:  # noqa: BLE001
                            self._forensic_queue.put_nowait({"error": str(rb_err), "context": "rollback_integrity_error"})
                    msg = str(e).lower()
                    if "security_audit_log.idempotency_key" in msg and idempotency_key:
                        cursor = await self._conn.execute(
                            "SELECT audit_id FROM security_audit_log WHERE idempotency_key=?",
                            (idempotency_key,),
                        )
                        row = await cursor.fetchone()
                        if row and not future.done():
                            future.set_result(row[0])
                        else:
                            if not future.done():
                                future.set_exception(e)
                    else:
                        if not future.done():
                            future.set_exception(e)
                except Exception as write_err:  # noqa: BLE001
                    if not in_tx_before:
                        try:
                            await self._conn.rollback()
                        except Exception as rb_err:  # noqa: BLE001
                            self._forensic_queue.put_nowait({"error": str(rb_err), "context": "rollback_general_error"})
                    if not future.done():
                        future.set_exception(write_err)
                finally:
                    self._write_queue.task_done()
            except asyncio.CancelledError:
                break

    async def log_action(
        self,
        tenant_id: str,
        actor_role: str,
        actor_id: str,
        action: str,
        resource: str,
        status: str = "SUCCESS",
        payload_dict: Optional[dict[str, Any]] = None,
        idempotency_key: Optional[str] = None,
        session_id: Optional[str] = None,
    ) -> str:
        """Enqueue an event to the WriteSerializer and await its cryptographic commitment."""
        await self.ensure_table()
        import copy
        payload_data = copy.deepcopy(payload_dict) if payload_dict else {}

        in_tx_before = self._conn.in_transaction
        future = asyncio.get_running_loop().create_future()

        task = (
            tenant_id,
            actor_role,
            actor_id,
            session_id,
            action,
            resource,
            status,
            payload_data,
            idempotency_key,
            in_tx_before,
            future,
        )

        await self._write_queue.put(task)
        return await future

    async def verify_chain(self) -> dict[str, Any]:
        pinned_pem = os.environ.get("CORTEX_LEDGER_PUBLIC_KEY") or os.environ.get(
            "BABYLON_LEDGER_PUBLIC_KEY"
        )
        if pinned_pem:
            try:
                from cryptography.hazmat.primitives.serialization import load_pem_public_key

                pinned_key = load_pem_public_key(pinned_pem.encode("utf-8"))

                self_bytes = self.public_key.public_bytes(
                    encoding=serialization.Encoding.Raw, format=serialization.PublicFormat.Raw
                )
                pinned_bytes = pinned_key.public_bytes(
                    encoding=serialization.Encoding.Raw, format=serialization.PublicFormat.Raw
                )
                if self_bytes != pinned_bytes:
                    return {"status": "tampered", "reason": "ledger_public_key_mismatch"}
            except Exception:  # noqa: BLE001
                return {"status": "tampered", "reason": "ledger_public_key_mismatch"}
        res = await self.verify_ledger()
        if res.get("status") == "failed":
            res["status"] = "tampered"
            if res.get("violations"):
                res["corrupted_audit_id"] = res["violations"][0]["audit_id"]
                first_reason = res["violations"][0]["reason"]
                if "diverges from stored" in first_reason or "verification failed" in first_reason:
                    res["reason"] = "row_hash_mismatch"
                else:
                    res["reason"] = first_reason
        return res

    async def verify_ledger(self) -> dict[str, Any]:
        """Verify the integrity of the entire cryptographic ledger chain.

        Re-canonicalizes payloads from stored bytes and recomputes all hashes
        to detect silent modifications by a corrupt or compromised writer.
        """
        violations = []
        count = 0
        expected_prev_hash = "0" * 44
        expected_lamport = 0

        cursor = await self._conn.execute(
            """
            SELECT id, audit_id, lamport_t, timestamp, prev_hash, payload_canonical, payload_hash, envelope_canonical, signature, action, actor_id, status
            FROM security_audit_log ORDER BY id ASC
            """
        )
        rows = await cursor.fetchall()
        seen_hashes = set()

        for row in rows:
            (
                db_id,
                audit_id,
                lamport_t,
                timestamp,
                prev_hash,
                payload_canonical,
                payload_hash,
                envelope_canonical,
                signature_hex,
                action,
                actor_id,
                status,
            ) = row
            count += 1

            if prev_hash != expected_prev_hash:
                violations.append(
                    {
                        "id": db_id,
                        "audit_id": audit_id,
                        "reason": f"Hash chain linkage broken: prev_hash '{prev_hash}' does not match expected '{expected_prev_hash}'.",
                    }
                )

            if audit_id in seen_hashes:
                violations.append(
                    {
                        "id": db_id,
                        "audit_id": audit_id,
                        "reason": f"Duplicate event hash detected: {audit_id}",
                    }
                )

            if lamport_t <= expected_lamport:
                if count != 1 or lamport_t != 1:
                    violations.append(
                        {
                            "id": db_id,
                            "audit_id": audit_id,
                            "reason": f"Lamport regression or duplication at seq={db_id}",
                        }
                    )

            # Re-canonicalize payload and verify hash
            recanon_payload_hash = cortex_hash(payload_canonical)
            if recanon_payload_hash != payload_hash:
                violations.append(
                    {
                        "id": db_id,
                        "audit_id": audit_id,
                        "reason": "Payload hash mismatch (re-canonicalization failed)",
                    }
                )

            # Verify envelope hash = audit_id
            computed_envelope_hash = cortex_hash(envelope_canonical)
            if computed_envelope_hash != audit_id:
                violations.append(
                    {
                        "id": db_id,
                        "audit_id": audit_id,
                        "reason": f"Envelope hash mismatch: stored={audit_id} computed={computed_envelope_hash}",
                    }
                )

            # Verify envelope internal consistency: prev_hash and payload_hash inside envelope match stored columns
            try:
                envelope_data = json.loads(envelope_canonical)
                if envelope_data.get("prev_hash") != prev_hash:
                    violations.append(
                        {
                            "id": db_id,
                            "audit_id": audit_id,
                            "reason": "Envelope prev_hash diverges from stored prev_hash",
                        }
                    )
                if envelope_data.get("payload_hash") != payload_hash:
                    violations.append(
                        {
                            "id": db_id,
                            "audit_id": audit_id,
                            "reason": "Envelope payload_hash diverges from stored payload_hash",
                        }
                    )
                if envelope_data.get("lamport_t") != lamport_t:
                    violations.append(
                        {
                            "id": db_id,
                            "audit_id": audit_id,
                            "reason": "Envelope lamport_t diverges from stored lamport_t",
                        }
                    )
                if envelope_data.get("action") != action:
                    violations.append(
                        {
                            "id": db_id,
                            "audit_id": audit_id,
                            "reason": f"Envelope action '{envelope_data.get('action')}' diverges from stored action '{action}'",
                        }
                    )
                if envelope_data.get("actor_id") != actor_id:
                    violations.append(
                        {
                            "id": db_id,
                            "audit_id": audit_id,
                            "reason": f"Envelope actor_id '{envelope_data.get('actor_id')}' diverges from stored actor_id '{actor_id}'",
                        }
                    )
            except (ValueError, TypeError):
                violations.append(
                    {
                        "id": db_id,
                        "audit_id": audit_id,
                        "reason": "Envelope canonical bytes are not valid JSON",
                    }
                )

            # Check Ed25519 signature
            try:
                self.public_key.verify(bytes.fromhex(signature_hex), envelope_canonical)
            except Exception as sig_err:  # noqa: BLE001
                violations.append(
                    {
                        "id": db_id,
                        "audit_id": audit_id,
                        "reason": f"Cryptographic signature verification failed: {sig_err}",
                    }
                )

            seen_hashes.add(audit_id)
            if action == "COMPACTION_NODE":
                expected_prev_hash = status
            else:
                expected_prev_hash = audit_id
            expected_lamport = lamport_t

        if violations:
            return {"status": "failed", "violations": violations, "verified_count": count}

        return {
            "status": "verified",
            "verified_count": count,
            "head": expected_prev_hash,
            "lamport": expected_lamport,
        }

    def verify_zk_seal(self, payload: str, signature_hex: str) -> bool:
        """Verifies a cryptographic seal against the Audit Authority public key."""
        try:
            self.public_key.verify(bytes.fromhex(signature_hex), payload.encode("utf-8"))
            return True
        except (InvalidSignature, ValueError):
            return False
