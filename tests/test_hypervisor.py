"""Unit tests for AgencyHypervisor core."""

import pytest
from babylon60.core.hypervisor import AgencyHypervisor


@pytest.mark.asyncio
async def test_hypervisor_tenant_registration_and_eviction() -> None:
    hypervisor = AgencyHypervisor()
    scope1 = await hypervisor.register_tenant("tenant_01", {"role": "worker"})
    assert scope1.tenant_id == "tenant_01"
    assert hypervisor.active_tenant_count() == 1

    # Project event
    projected = await hypervisor.project_event("tenant_01", "TASK_SUBMITTED", {"data": "payload"})
    assert projected is True
    assert scope1.event_queue.qsize() == 1

    # Evict
    evicted = await hypervisor.evict_tenant("tenant_01")
    assert evicted is True
    assert hypervisor.active_tenant_count() == 0
