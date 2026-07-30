# [C5-REAL] Exergy-Maximized
"""
Ledger Repository (DDD Pattern)

Consumes the cryptographic EnterpriseAuditLedger and the satellite context tables
(agent_registry, sessions) to provide a unified business interface respecting I1-I4 invariants.
"""

import json
import logging
from typing import Any

import aiosqlite

from babylon60.audit.ledger import EnterpriseAuditLedger
from babylon60.database.core import causal_write

logger = logging.getLogger("babylon60.audit.repository")


class LedgerRepository:
    """Business repository wrapping the immutable ledger and its satellite context."""

    def __init__(self, conn: aiosqlite.Connection, ledger: EnterpriseAuditLedger):
        self._conn = conn
        self._ledger = ledger

    async def register_agent(
        self, agent_id: str, tenant_id: str, role: str, capabilities: dict[str, Any]
    ) -> None:
        """Register an agent in the satellite registry."""
        with causal_write(self._conn):
            await self._conn.execute(
                """
                INSERT INTO agent_registry (agent_id, tenant_id, role, capabilities)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(agent_id) DO UPDATE SET
                    role = excluded.role,
                    capabilities = excluded.capabilities,
                    status = 'active'
                """,
                (agent_id, tenant_id, role, json.dumps(capabilities)),
            )
            await self._conn.commit()

    async def start_session(
        self, session_id: str, tenant_id: str, agent_id: str, context: dict[str, Any]
    ) -> None:
        """Start a new session for an agent."""
        with causal_write(self._conn):
            await self._conn.execute(
                """
                INSERT INTO sessions (session_id, tenant_id, agent_id, context)
                VALUES (?, ?, ?, ?)
                """,
                (session_id, tenant_id, agent_id, json.dumps(context)),
            )
            await self._conn.commit()

    async def log_session_event(
        self,
        session_id: str,
        tenant_id: str,
        agent_id: str,
        action: str,
        resource: str,
        status: str = "SUCCESS",
    ) -> str:
        """
        Log an event in the immutable ledger anchored to a session.
        Respects I1 (append-only), I2 (chain link), I3 (causal order), I4 (hash identity).
        """
        # Validate session exists and is active
        cursor = await self._conn.execute(
            "SELECT ended_at FROM sessions WHERE session_id = ? AND tenant_id = ?",
            (session_id, tenant_id),
        )
        row = await cursor.fetchone()
        if not row:
            raise ValueError(f"Session {session_id} not found for tenant {tenant_id}")
        if row[0] is not None:
            raise ValueError(f"Session {session_id} is already ended")

        # Write to the immutable cryptographic ledger
        event_id = await self._ledger.log_action(
            tenant_id=tenant_id,
            actor_role="session_agent",
            actor_id=agent_id,
            action=action,
            resource=f"{resource}#session:{session_id}",
            status=status,
        )

        return event_id

    async def end_session(self, session_id: str, tenant_id: str) -> None:
        """End an active session."""
        with causal_write(self._conn):
            await self._conn.execute(
                "UPDATE sessions SET ended_at = datetime('now') WHERE session_id = ? AND tenant_id = ?",
                (session_id, tenant_id),
            )
            await self._conn.commit()
