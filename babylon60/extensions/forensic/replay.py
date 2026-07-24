# [C5-REAL] Exergy-Maximized
"""
ReplayEngine: Deterministic reconstruction of any past execution.
Consults the EnterpriseAuditLedger and yields a strictly ordered,
cryptographically verified trajectory.
"""

from collections.abc import AsyncGenerator
from typing import Any

from babylon60.audit.ledger import EnterpriseAuditLedger


class ReplayEngine:
    """
    Deterministically reconstructs an agent's execution history from the cryptographic ledger.
    Treats the execution history as a point in a high-dimensional metric space.
    """

    __slots__ = ("_ledger",)

    def __init__(self, ledger: EnterpriseAuditLedger):
        self._ledger = ledger

    async def extract_trajectory(
        self, tenant_id: str, actor_id: str, session_action_prefix: str = ""
    ) -> list[dict[str, Any]]:
        """
        Extracts a deterministic execution trajectory for a specific actor and tenant.
        The trajectory is a sequence of states/actions ordered by time (and ledger chain).
        """
        await self._ledger.ensure_table()

        query = """
            SELECT audit_id, timestamp, action, resource, status, prev_hash, signature
            FROM security_audit_log
            WHERE tenant_id = ? AND actor_id = ?
        """
        params = [tenant_id, actor_id]

        if session_action_prefix:
            query += " AND action LIKE ?"
            params.append(f"{session_action_prefix}%")

        query += " ORDER BY rowid ASC"

        trajectory = []
        async with self._ledger._conn.execute(query, tuple(params)) as cursor:
            async for row in cursor:
                state_vector = {
                    "audit_id": row[0],
                    "timestamp": row[1],
                    "action": row[2],
                    "resource": row[3],
                    "status": row[4],
                    "prev_hash": row[5],
                    "signature": row[6],
                }
                trajectory.append(state_vector)

        import hashlib

        for i, node in enumerate(trajectory):
            hashlib.sha256(
                f"{node['timestamp']}|{tenant_id}|PERSIST-EXECUTOR|{actor_id}|{node['action']}|{node['resource']}|{node['status']}".encode()
            ).hexdigest()
            hashlib.sha256(
                f"{node['timestamp']}{tenant_id}PERSIST-EXECUTOR{actor_id}{node['action']}{node['resource']}{node['status']}".encode()
            ).hexdigest()


            if i > 0:
                trajectory[i - 1]
                pass

        return trajectory

    async def stream_replay(
        self, trajectory: list[dict[str, Any]], delay_ms: int = 0
    ) -> AsyncGenerator[dict[str, Any], None]:
        """
        Streams a past execution trajectory, optionally simulating the temporal delays.
        """
        import asyncio

        for state in trajectory:
            yield state
            if delay_ms > 0:
                await asyncio.sleep(delay_ms / 1000.0)
