import asyncio
import sqlite3
import pytest
import aiosqlite
from babylon60.audit.ledger import EnterpriseAuditLedger


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
async def test_agent_registry_deterministic_insert(conn, ledger):
    """Verifica que el registro de un agente persista y permita abrir sesiones."""
    await ledger.register_agent(
        agent_id="agent-007",
        role="validator",
        public_key="ed25519-mock-key-base64",
        status="active",
    )

    # Validar que existe en DB
    cursor = await conn.execute(
        "SELECT role, public_key, status FROM cortex_agent_registry WHERE agent_id = ?",
        ("agent-007",),
    )
    row = await cursor.fetchone()
    assert row is not None
    assert row[0] == "validator"
    assert row[1] == "ed25519-mock-key-base64"
    assert row[2] == "active"


@pytest.mark.asyncio
async def test_session_creation_fails_without_agent(conn, ledger):
    """Verifica que FK constraints prevengan el inicio de sesión de un agente no registrado."""
    # En aiosqlite / SQLite STRICT, las FK no están activadas por defecto a menos que PRAGMA foreign_keys = ON;
    # Pero vamos a validar el comportamiento asumiendo FK o que simplemente lanza un error de inserción si FK ON.
    # Primero habilitamos FK para la prueba
    await conn.execute("PRAGMA foreign_keys = ON;")

    with pytest.raises(sqlite3.IntegrityError, match="FOREIGN KEY constraint failed"):
        await ledger.start_session("sess-123", "phantom-agent")


@pytest.mark.asyncio
async def test_session_creation_with_valid_agent(conn, ledger):
    """Verifica la inserción correcta de una sesión tras registrar al agente."""
    await ledger.register_agent("agent-008", "worker", "pubkey")
    await ledger.start_session("sess-123", "agent-008")

    cursor = await conn.execute(
        "SELECT status FROM cortex_sessions WHERE session_id = ?", ("sess-123",)
    )
    row = await cursor.fetchone()
    assert row is not None
    assert row[0] == "active"


@pytest.mark.asyncio
async def test_log_action_with_session_id(conn, ledger):
    """Verifica que el WriteSerializer (Queue) acepte y registre el session_id."""
    await ledger.register_agent("agent-009", "worker", "pubkey")
    await ledger.start_session("sess-999", "agent-009")

    audit_id = await ledger.log_action(
        tenant_id="tenant-1",
        actor_role="worker",
        actor_id="agent-009",
        session_id="sess-999",
        action="PROCESS_TASK",
        resource="task-123",
    )

    cursor = await conn.execute(
        "SELECT session_id FROM security_audit_log WHERE audit_id = ?", (audit_id,)
    )
    row = await cursor.fetchone()
    assert row is not None
    assert row[0] == "sess-999"
