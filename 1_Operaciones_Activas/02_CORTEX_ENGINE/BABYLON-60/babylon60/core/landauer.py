# C5-REAL EXERGY CERTIFIED
# [C5-REAL] Exergy-Maximized Landauer Eviction Engine
"""
LandauerEvictionEngine — Thermodynamic Session & KV Cache Entropy Eviction.
Enforces Landauer principle: purging stale un-consolidated memory state to maintain maximum exergy.
"""

from __future__ import annotations

import logging
import time
from typing import Dict, List, Optional

from babylon60.core.hypervisor import AgencyHypervisor

logger = logging.getLogger("babylon60.core.landauer")


class LandauerEvictionEngine:
    """
    Thermodynamic Memory Eviction Engine.
    Monitors in-memory tenant entropy and purges idle or stale sessions to prevent memory leaks.
    """

    def __init__(
        self,
        hypervisor: AgencyHypervisor,
        max_tenants: int = 100,
        max_idle_seconds: float = 300.0,
    ) -> None:
        self.hypervisor = hypervisor
        self.max_tenants = max_tenants
        self.max_idle_seconds = max_idle_seconds

    async def evaluate_and_evict(self) -> List[str]:
        """Scans hypervisor active tenants and evicts idle or excess sessions."""
        now = time.time()
        evicted: List[str] = []

        active_tenants = list(self.hypervisor.tenants.items())

        for tenant_id, scope in active_tenants:
            if not scope.active:
                continue

            idle_time = now - scope.created_at
            if idle_time > self.max_idle_seconds:
                success = await self.hypervisor.evict_tenant(tenant_id)
                if success:
                    evicted.append(tenant_id)
                    logger.info(f"Landauer eviction triggered for idle tenant {tenant_id} ({idle_time:.1f}s idle)")

        # If tenant count still exceeds max capacity, evict oldest
        remaining = [t for t in self.hypervisor.tenants.values() if t.active]
        if len(remaining) > self.max_tenants:
            remaining.sort(key=lambda s: s.created_at)
            overflow_count = len(remaining) - self.max_tenants
            for scope in remaining[:overflow_count]:
                success = await self.hypervisor.evict_tenant(scope.tenant_id)
                if success:
                    evicted.append(scope.tenant_id)
                    logger.info(f"Landauer capacity eviction triggered for tenant {scope.tenant_id}")

        return evicted
