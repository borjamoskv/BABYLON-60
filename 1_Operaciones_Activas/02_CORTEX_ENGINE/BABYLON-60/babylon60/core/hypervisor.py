# C5-REAL EXERGY CERTIFIED
# [C5-REAL] Exergy-Maximized AgencyHypervisor Core
"""
AgencyHypervisor — Multi-Tenant Agent Scope & Event Projection Engine.
Enforces INV_C5_18 (Zero-Worktree Swarm Scaling) & INV_BFT_02 (Single-Writer BFT Actor).
"""

from __future__ import annotations

import asyncio
import logging
import time
from dataclasses import dataclass, field
from typing import Any, Dict, Optional

from babylon60.bft.ledger_actor import BFTLedgerActor, LedgerEvent

logger = logging.getLogger("babylon60.core.hypervisor")


@dataclass
class TenantScope:
    tenant_id: str
    created_at: float
    metadata: Dict[str, Any] = field(default_factory=dict)
    event_queue: asyncio.Queue[Dict[str, Any]] = field(default_factory=asyncio.Queue)
    active: bool = True


class AgencyHypervisor:
    """
    In-Memory Multi-Tenant Agency Hypervisor.
    Manages N>=100 agent session scopes concurrently in memory without physical Git worktrees.
    """

    def __init__(self, ledger_actor: Optional[BFTLedgerActor] = None) -> None:
        self.tenants: Dict[str, TenantScope] = {}
        self.ledger_actor = ledger_actor
        self._lock = asyncio.Lock()

    async def register_tenant(self, tenant_id: str, metadata: Optional[Dict[str, Any]] = None) -> TenantScope:
        """Register a new in-memory tenant scope (INV_C5_18 zero-worktree constraint)."""
        async with self._lock:
            if tenant_id in self.tenants:
                scope = self.tenants[tenant_id]
                scope.active = True
                return scope

            scope = TenantScope(
                tenant_id=tenant_id,
                created_at=time.time(),
                metadata=metadata or {},
            )
            self.tenants[tenant_id] = scope
            logger.info(f"Registered in-memory tenant scope: {tenant_id}")
            return scope

    async def evict_tenant(self, tenant_id: str) -> bool:
        """Evict tenant scope from RAM to purge session entropy."""
        async with self._lock:
            if tenant_id in self.tenants:
                self.tenants[tenant_id].active = False
                del self.tenants[tenant_id]
                logger.info(f"Evicted tenant scope from memory: {tenant_id}")
                return True
            return False

    async def project_event(self, tenant_id: str, event_type: str, payload: Dict[str, Any]) -> bool:
        """Broadcast event to tenant's IPC queue and persist to BFT ledger if actor is set."""
        if tenant_id not in self.tenants or not self.tenants[tenant_id].active:
            return False

        event_data = {
            "tenant_id": tenant_id,
            "event_type": event_type,
            "payload": payload,
            "timestamp": time.time(),
        }

        await self.tenants[tenant_id].event_queue.put(event_data)

        if self.ledger_actor:
            ledger_event = LedgerEvent(
                stream="hypervisor",
                entity_id=tenant_id,
                event_type=event_type,
                payload=payload,
                cortex_taint=f"[CORTEX-TAINT:hypervisor:{tenant_id}]",
                source_db="hypervisor",
                source_table="events",
                source_pk=tenant_id,
            )
            await self.ledger_actor.append(ledger_event)

        return True

    def active_tenant_count(self) -> int:
        """Return total active in-memory tenants."""
        return sum(1 for t in self.tenants.values() if t.active)
