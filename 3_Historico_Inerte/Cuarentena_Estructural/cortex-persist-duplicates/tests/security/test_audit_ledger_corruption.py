# [C5-REAL] Exergy-Maximized
"""Corruption detection tests for EnterpriseAuditLedger.verify_ledger().

Each test injects a specific physical mutation into the SQLite ledger
(bypassing the immutability trigger) and asserts that verify_ledger()
catches the exact violation class.
"""
import asyncio
import json
import os
import tempfile

import pytest
from cryptography.hazmat.primitives.asymmetric import ed25519

from babylon60.audit.ledger import EnterpriseAuditLedger
from babylon60.database.core import connect, connect_async_ctx


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

async def _init_ledger(db_path: str) -> tuple:
    """Open async connection, authorize writes, init ledger, return (conn, ledger)."""
    conn = await connect_async_ctx(db_path).__aenter__()
    conn._conn.authorize_causal_writes()
    ledger = EnterpriseAuditLedger(conn)
    await ledger.ensure_table()
    return conn, ledger


async def _insert_events(ledger: EnterpriseAuditLedger, n: int) -> list[str]:
    """Insert *n* valid events and return their audit_ids."""
    ids = []
    for i in range(n):
        aid = await asyncio.wait_for(
            ledger.log_action(
                "tenant_1", "system", "actor_1", f"ACTION_{i}", f"fact:{i}"
            ),
            timeout=5.0,
        )
        ids.append(aid)
    return ids


def _corrupt(db_path: str, sql: str, params: tuple = ()) -> None:
    """Open a sync connection, drop the update trigger, execute *sql*, commit."""
    conn_sync = connect(db_path)
    conn_sync.authorize_causal_writes()
    cursor = conn_sync.cursor()
    cursor.execute("DROP TRIGGER IF EXISTS ledger_no_update")
    cursor.execute(sql, params)
    conn_sync.commit()
    conn_sync.close()


async def _verify(db_path: str) -> dict:
    """Re-open async, init ledger, run verify_ledger(), close, return result."""
    async with connect_async_ctx(db_path) as conn:
        conn._conn.authorize_causal_writes()
        ledger = EnterpriseAuditLedger(conn)
        await ledger.ensure_table()
        result = await ledger.verify_ledger()
        await ledger.close()
    return result


def _find_violation(result: dict, substring: str) -> dict | None:
    """Return the first violation whose reason contains *substring*, or None."""
    for v in result.get("violations", []):
        if substring in v.get("reason", ""):
            return v
    return None


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_clean_ledger_verifies():
    """Insert 5 valid events — verify_ledger must return status='verified'."""
    temp_dir = tempfile.mkdtemp()
    db_path = os.path.join(temp_dir, "clean.db")

    async with connect_async_ctx(db_path) as conn:
        conn._conn.authorize_causal_writes()
        ledger = EnterpriseAuditLedger(conn)
        await ledger.ensure_table()
        await _insert_events(ledger, 5)
        await asyncio.sleep(0.1)
        await ledger.close()

    result = await _verify(db_path)
    assert result["status"] == "verified", f"Expected verified, got {result}"
    assert result["verified_count"] == 5


@pytest.mark.asyncio
async def test_payload_canonical_tampering():
    """Mutate payload_canonical of event #1 → 'Payload hash mismatch'."""
    temp_dir = tempfile.mkdtemp()
    db_path = os.path.join(temp_dir, "payload.db")

    async with connect_async_ctx(db_path) as conn:
        conn._conn.authorize_causal_writes()
        ledger = EnterpriseAuditLedger(conn)
        await ledger.ensure_table()
        ids = await _insert_events(ledger, 2)
        await asyncio.sleep(0.1)
        await ledger.close()

    _corrupt(
        db_path,
        "UPDATE security_audit_log SET payload_canonical = ? WHERE audit_id = ?",
        (b'{"corrupted": true}', ids[0]),
    )

    result = await _verify(db_path)
    assert result["status"] == "failed", f"Expected failed, got {result}"
    hit = _find_violation(result, "Payload hash mismatch")
    assert hit is not None, f"No 'Payload hash mismatch' violation found: {result}"
    assert hit["audit_id"] == ids[0]


@pytest.mark.asyncio
async def test_envelope_canonical_tampering():
    """Corrupt envelope_canonical bytes → 'Envelope hash mismatch'."""
    temp_dir = tempfile.mkdtemp()
    db_path = os.path.join(temp_dir, "envelope.db")

    async with connect_async_ctx(db_path) as conn:
        conn._conn.authorize_causal_writes()
        ledger = EnterpriseAuditLedger(conn)
        await ledger.ensure_table()
        ids = await _insert_events(ledger, 2)
        await asyncio.sleep(0.1)
        await ledger.close()

    # Corrupt the envelope by appending garbage bytes
    _corrupt(
        db_path,
        "UPDATE security_audit_log SET envelope_canonical = CAST(envelope_canonical || X'DEADBEEF' AS BLOB) WHERE audit_id = ?",
        (ids[0],),
    )

    result = await _verify(db_path)
    assert result["status"] == "failed", f"Expected failed, got {result}"
    hit = _find_violation(result, "Envelope hash mismatch")
    assert hit is not None, f"No 'Envelope hash mismatch' violation found: {result}"
    assert hit["audit_id"] == ids[0]


@pytest.mark.asyncio
async def test_chain_break_prev_hash():
    """Overwrite prev_hash of event #2 → 'Hash chain linkage broken'."""
    temp_dir = tempfile.mkdtemp()
    db_path = os.path.join(temp_dir, "chain.db")

    async with connect_async_ctx(db_path) as conn:
        conn._conn.authorize_causal_writes()
        ledger = EnterpriseAuditLedger(conn)
        await ledger.ensure_table()
        ids = await _insert_events(ledger, 3)
        await asyncio.sleep(0.1)
        await ledger.close()

    fake_prev = "X" * 44
    _corrupt(
        db_path,
        "UPDATE security_audit_log SET prev_hash = ? WHERE audit_id = ?",
        (fake_prev, ids[1]),
    )

    result = await _verify(db_path)
    assert result["status"] == "failed", f"Expected failed, got {result}"
    hit = _find_violation(result, "Hash chain linkage broken")
    assert hit is not None, f"No 'Hash chain linkage broken' violation: {result}"
    assert hit["audit_id"] == ids[1]


@pytest.mark.asyncio
async def test_signature_forgery():
    """Replace signature with one from a different Ed25519 key → 'signature verification failed'."""
    temp_dir = tempfile.mkdtemp()
    db_path = os.path.join(temp_dir, "sig.db")

    async with connect_async_ctx(db_path) as conn:
        conn._conn.authorize_causal_writes()
        ledger = EnterpriseAuditLedger(conn)
        await ledger.ensure_table()
        ids = await _insert_events(ledger, 2)
        await asyncio.sleep(0.1)
        await ledger.close()

    # Read the original envelope_canonical to sign with a rogue key
    conn_sync = connect(db_path)
    conn_sync.authorize_causal_writes()
    cur = conn_sync.cursor()
    cur.execute(
        "SELECT envelope_canonical FROM security_audit_log WHERE audit_id = ?",
        (ids[0],),
    )
    envelope_bytes = cur.fetchone()[0]
    conn_sync.close()

    # Generate rogue signature
    rogue_key = ed25519.Ed25519PrivateKey.generate()
    rogue_sig = rogue_key.sign(envelope_bytes).hex()

    _corrupt(
        db_path,
        "UPDATE security_audit_log SET signature = ? WHERE audit_id = ?",
        (rogue_sig, ids[0]),
    )

    result = await _verify(db_path)
    assert result["status"] == "failed", f"Expected failed, got {result}"
    hit = _find_violation(result, "signature verification failed")
    assert hit is not None, f"No 'signature verification failed' violation: {result}"
    assert hit["audit_id"] == ids[0]


@pytest.mark.asyncio
async def test_lamport_regression():
    """Set lamport_t of event #3 below event #2 → 'Lamport regression'."""
    temp_dir = tempfile.mkdtemp()
    db_path = os.path.join(temp_dir, "lamport.db")

    async with connect_async_ctx(db_path) as conn:
        conn._conn.authorize_causal_writes()
        ledger = EnterpriseAuditLedger(conn)
        await ledger.ensure_table()
        ids = await _insert_events(ledger, 3)
        await asyncio.sleep(0.1)
        await ledger.close()

    # Read lamport_t of the 2nd event and set the 3rd event's lamport below it
    conn_sync = connect(db_path)
    conn_sync.authorize_causal_writes()
    cur = conn_sync.cursor()
    cur.execute(
        "SELECT lamport_t FROM security_audit_log WHERE audit_id = ?",
        (ids[1],),
    )
    lamport_2 = cur.fetchone()[0]
    conn_sync.close()

    regressed_lamport = lamport_2 - 1
    _corrupt(
        db_path,
        "UPDATE security_audit_log SET lamport_t = ? WHERE audit_id = ?",
        (regressed_lamport, ids[2]),
    )

    result = await _verify(db_path)
    assert result["status"] == "failed", f"Expected failed, got {result}"
    hit = _find_violation(result, "Lamport regression")
    assert hit is not None, f"No 'Lamport regression' violation: {result}"
    assert hit["audit_id"] == ids[2]


@pytest.mark.asyncio
async def test_envelope_field_divergence_v1():
    """Modify actor_id column without updating envelope_canonical → v1 divergence."""
    temp_dir = tempfile.mkdtemp()
    db_path = os.path.join(temp_dir, "v1div.db")

    async with connect_async_ctx(db_path) as conn:
        conn._conn.authorize_causal_writes()
        ledger = EnterpriseAuditLedger(conn)
        await ledger.ensure_table()
        ids = await _insert_events(ledger, 1)
        await asyncio.sleep(0.1)
        await ledger.close()

    # Confirm the envelope is v1 and contains actor_id
    conn_sync = connect(db_path)
    conn_sync.authorize_causal_writes()
    cur = conn_sync.cursor()
    cur.execute(
        "SELECT envelope_canonical FROM security_audit_log WHERE audit_id = ?",
        (ids[0],),
    )
    env_bytes = cur.fetchone()[0]
    env_data = json.loads(env_bytes)
    conn_sync.close()

    assert env_data.get("domain") == "babylon60.ledger.event.v1", (
        f"Expected v1 envelope, got domain={env_data.get('domain')}"
    )

    # Mutate actor_id column only — envelope_canonical still says 'actor_1'
    _corrupt(
        db_path,
        "UPDATE security_audit_log SET actor_id = ? WHERE audit_id = ?",
        ("rogue_actor", ids[0]),
    )

    result = await _verify(db_path)
    assert result["status"] == "failed", f"Expected failed, got {result}"
    hit = _find_violation(result, "actor_id")
    assert hit is not None, f"No actor_id divergence violation: {result}"
    assert "diverges" in hit["reason"]
    assert hit["audit_id"] == ids[0]
