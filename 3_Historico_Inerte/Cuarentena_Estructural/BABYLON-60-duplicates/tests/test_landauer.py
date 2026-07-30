# C5-REAL EXERGY CERTIFIED
"""Unit tests for LandauerEvictionEngine core."""

import pytest
from babylon60.core.hypervisor import AgencyHypervisor
from babylon60.core.landauer import LandauerEvictionEngine


@pytest.mark.asyncio
async def test_landauer_idle_and_capacity_eviction() -> None:
    hypervisor = AgencyHypervisor()
    engine = LandauerEvictionEngine(hypervisor, max_tenants=2, max_idle_seconds=0.1)

    # Register 3 tenants
    await hypervisor.register_tenant("t1")
    await hypervisor.register_tenant("t2")
    await hypervisor.register_tenant("t3")

    assert hypervisor.active_tenant_count() == 3

    # Evict capacity overflow (max_tenants = 2)
    evicted = await engine.evaluate_and_evict()
    assert len(evicted) >= 1
    assert hypervisor.active_tenant_count() <= 2
