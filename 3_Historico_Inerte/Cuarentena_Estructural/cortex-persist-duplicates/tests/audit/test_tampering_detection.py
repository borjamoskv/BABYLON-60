# [C5-REAL] Exergy-Maximized — Tampering Detection Tests
import asyncio
import sqlite3
import pytest
import aiosqlite
from babylon60.audit.ledger import EnterpriseAuditLedger
from babylon60.database.core import causal_write


@pytest.fixture
async def conn():
    async with aiosqlite.connect(":memory:") as db:
        yield db


@pytest.fixture
async def ledger(conn):
    ledger = EnterpriseAuditLedger(conn)
    await ledger.ensure_table()
    yield ledger
    await ledger.close()


@pytest.mark.asyncio
async def test_tampering_unauthorized_update_blocked(conn, ledger):
    """Verify that SQLite triggers prevent direct UPDATE on the audit log."""
    await ledger.log_action(
        tenant_id="tenant-1",
        actor_role="admin",
        actor_id="agent-1",
        action="CREATE_USER",
        resource="user-123",
    )

    with pytest.raises(aiosqlite.IntegrityError, match="security_audit_log is append-only"):
        with causal_write(conn):
            await conn.execute(
                "UPDATE security_audit_log SET action = 'MALICIOUS_ACTION' WHERE id = 1"
            )
            await conn.commit()


@pytest.mark.asyncio
async def test_tampering_unauthorized_delete_blocked(conn, ledger):
    """Verify that SQLite triggers prevent direct DELETE on the audit log."""
    await ledger.log_action(
        tenant_id="tenant-1",
        actor_role="admin",
        actor_id="agent-1",
        action="CREATE_USER",
        resource="user-123",
    )

    with pytest.raises(aiosqlite.IntegrityError, match="security_audit_log is append-only"):
        with causal_write(conn):
            await conn.execute("DELETE FROM security_audit_log WHERE id = 1")
            await conn.commit()


@pytest.mark.asyncio
async def test_tampering_detects_reordered_events(conn, ledger):
    """Verify that verify_chain detects event reordering (chain linkage break)."""
    id1 = await ledger.log_action(
        tenant_id="tenant-1",
        actor_role="admin",
        actor_id="agent-1",
        action="ACTION_A",
        resource="res-1",
    )
    await asyncio.sleep(0.01)
    id2 = await ledger.log_action(
        tenant_id="tenant-1",
        actor_role="admin",
        actor_id="agent-1",
        action="ACTION_B",
        resource="res-2",
    )

    # Simular bypass de triggers (hacker con acceso directo a archivos tirando los triggers)
    with causal_write(conn):
        await conn.execute("DROP TRIGGER IF EXISTS ledger_no_update")
        # Cambiar el prev_hash del segundo registro a un valor inválido/aleatorio
        await conn.execute("UPDATE security_audit_log SET prev_hash = ? WHERE id = 2", ("a" * 44,))
        await conn.commit()

    # Verificación criptográfica debe fallar
    res = await ledger.verify_chain()
    assert res["status"] == "tampered"
    assert len(res["violations"]) > 0
    assert any("Hash chain linkage broken" in v["reason"] for v in res["violations"])


@pytest.mark.asyncio
async def test_tampering_detects_silent_payload_modification(conn, ledger):
    """Verify that verify_chain detects silent payload alterations."""
    await ledger.log_action(
        tenant_id="tenant-1",
        actor_role="admin",
        actor_id="agent-1",
        action="ACTION_A",
        resource="res-1",
        payload_dict={"key": "safe_value"},
    )

    # Simular bypass de triggers modificando el payload directamente en la DB
    with causal_write(conn):
        await conn.execute("DROP TRIGGER IF EXISTS ledger_no_update")
        await conn.execute(
            "UPDATE security_audit_log SET payload_canonical = ? WHERE id = 1",
            (b'{"key":"malicious_value"}',),
        )
        await conn.commit()

    # Verificación criptográfica debe detectar el desajuste del hash
    res = await ledger.verify_chain()
    assert res["status"] == "tampered"
    assert len(res["violations"]) > 0
    assert any("Payload hash mismatch" in v["reason"] for v in res["violations"])
