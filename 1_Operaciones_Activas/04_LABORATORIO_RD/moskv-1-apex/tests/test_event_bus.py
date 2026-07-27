import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from moskv_1.event_bus import EventBus, CortexEvent

def test_cortex_event_serialization():
    event = CortexEvent(
        hash="hash123",
        prevHash="prev123",
        timestamp=1234567890.0,
        payload={"data": "test"}
    )
    json_str = event.to_json()
    decoded = CortexEvent.from_json(json_str)
    assert decoded.hash == event.hash
    assert decoded.prevHash == event.prevHash
    assert decoded.timestamp == event.timestamp
    assert decoded.payload == event.payload

def test_event_bus_hash_chaining():
    bus = EventBus()
    # Initial state
    assert bus.last_hash == "GENESIS"
    
    # First hash
    p1 = {"step": 1}
    h1 = bus._hash(p1, "GENESIS")
    # We assert against a hardcoded expected value (to avoid self-certifying tests)
    assert h1 == "1fec6b83854049e8d0422e3be78b2efee6416a390e996c5be132fbcc9a5eb5c7"
    
    # Second hash depends on first hash
    p2 = {"step": 2}
    h2 = bus._hash(p2, h1)
    assert h2 == "d71eaf5fbdac8512be4a2855efbd350b356a057fd4c1da4653ec91be87bf6fcc"

@pytest.mark.asyncio
async def test_event_bus_publish_in_memory():
    bus = EventBus()
    await bus.connect()
    
    payload = {"value": 42}
    event = await bus.publish("cortex.test", payload)
    
    assert event.payload == payload
    assert event.prevHash == "GENESIS"
    assert bus.last_hash == event.hash

@pytest.mark.asyncio
async def test_event_bus_subscribe_in_memory():
    bus = EventBus()
    await bus.connect()
    
    received_events = []
    async def callback(event, msg):
        received_events.append(event)
        
    await bus.subscribe("cortex.test", callback)
    
    payload = {"value": 100}
    event = await bus.publish("cortex.test", payload)
    
    await asyncio.sleep(0.01)  # yield control to let dispatch run
    assert len(received_events) == 1
    assert received_events[0].payload == payload
    assert received_events[0].hash == event.hash

@pytest.mark.asyncio
async def test_event_bus_close():
    bus = EventBus()
    await bus.connect()
    await bus.close()
