import pytest
from unittest.mock import AsyncMock, MagicMock
from moskv_1.brain import BrainRegion
from moskv_1.event_bus import CortexEvent

@pytest.mark.asyncio
async def test_brain_region_emit_enrichment():
    region = BrainRegion("TestRegion")
    # Mock the internal EventBus publish method
    region.bus.publish = AsyncMock()
    
    payload = {"info": "hello"}
    await region.emit("cortex.test", payload)
    
    # Verify the internal event bus was called with enriched payload
    expected_payload = {"info": "hello", "sourceRegion": "TestRegion"}
    region.bus.publish.assert_called_once_with("cortex.test", expected_payload)

@pytest.mark.asyncio
async def test_brain_region_listen_routing():
    region = BrainRegion("TestRegion")
    # Mock EventBus subscribe method
    region.bus.subscribe = AsyncMock()
    
    await region.listen("cortex.test", "durable_test")
    region.bus.subscribe.assert_called_once()
    assert len(region.subscriptions) == 1

@pytest.mark.asyncio
async def test_brain_region_run_and_shutdown():
    region = BrainRegion("TestRegion")
    region.bus.connect = AsyncMock()
    region.bus.close = AsyncMock()
    
    await region.run()
    region.bus.connect.assert_called_once()
    
    mock_sub = AsyncMock()
    region.subscriptions.append(mock_sub)
    
    await region.shutdown()
    mock_sub.unsubscribe.assert_called_once()
    region.bus.close.assert_called_once()
