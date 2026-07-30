# [C5-REAL] Exergy-Maximized
import asyncio
import sqlite3
import pytest
import aiosqlite
from babylon60.audit.ledger import EnterpriseAuditLedger
from babylon60.database.core import causal_write
import uuid


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
async def test_idempotency_returns_original_audit_id(conn, ledger):
    """Verify that using the same idempotency_key returns the original audit_id without creating a new event."""
    idem_key = f"idem-{uuid.uuid4().hex}"

    # First insert
    id1 = await ledger.log_action(
        tenant_id="tenant-1",
        actor_role="admin",
        actor_id="agent-1",
        action="CHARGE_CARD",
        resource="order-123",
        idempotency_key=idem_key,
    )

    # Second insert with same key
    id2 = await ledger.log_action(
        tenant_id="tenant-1",
        actor_role="admin",
        actor_id="agent-1",
        action="CHARGE_CARD",
        resource="order-123",
        idempotency_key=idem_key,
    )

    assert id1 == id2, "Idempotency key did not return the original audit_id"

    # Verify only one event was created
    cursor = await conn.execute(
        "SELECT COUNT(*) FROM security_audit_log WHERE idempotency_key = ?", (idem_key,)
    )
    count = await cursor.fetchone()
    assert count[0] == 1, "Duplicate event created despite idempotency key"
