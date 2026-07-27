import pytest
import asyncio
import json
from unittest.mock import AsyncMock, MagicMock, patch
from moskv_1.event_bus import EventBus, CortexEvent
from moskv_1.memory import MemoryStore

# =====================================================================
# 1. TEST: Hash Chain Gap on Publish Failure (Fixed)
# =====================================================================
@pytest.mark.asyncio
async def test_hash_chain_gap_on_publish_failure():
    """
    Verifies that a failed publish does NOT mutate `last_hash`,
    leaving NO gaps in the published chain.
    """
    bus = EventBus()
    bus.js = AsyncMock()
    
    # First publish succeeds
    await bus.publish("cortex.test", {"step": 1})
    hash_1 = bus.last_hash
    
    # Second publish fails (e.g. NATS connection error or timeout)
    bus.js.publish.side_effect = Exception("NATS write timeout")
    with pytest.raises(Exception, match="NATS write timeout"):
        await bus.publish("cortex.test", {"step": 2})
        
    hash_failed = bus.last_hash
    # Fixed behavior: last_hash is NOT mutated on failed publishes!
    assert hash_failed == hash_1, "last_hash should NOT have been mutated on failure"
    
    # Third publish succeeds
    bus.js.publish.side_effect = None
    event_3 = await bus.publish("cortex.test", {"step": 3})
    
    # The third event is correctly chained to the first event's hash
    assert event_3.prevHash == hash_1
    assert event_3.prevHash != "genesis_failed"


# =====================================================================
# 2. TEST: Non-deterministic Payload & Crash State Mutation (Fixed)
# =====================================================================
@pytest.mark.asyncio
async def test_non_serializable_payload_crashes_and_mutates():
    """
    Verifies that a non-serializable payload (e.g., set) causes
    publish to crash, and `last_hash` is not mutated.
    """
    bus = EventBus()
    bus.js = AsyncMock()
    
    initial_hash = bus.last_hash
    
    # Publish with a set (non-serializable in standard JSON)
    bad_payload = {"tags": {"entropy", "anergy"}}
    with pytest.raises(TypeError):
        await bus.publish("cortex.test", bad_payload)
        
    assert bus.last_hash == initial_hash, "last_hash should not have mutated since serialization failed"


# =====================================================================
# 3. TEST: Concurrent Publish Race Condition (Fixed with asyncio.Lock)
# =====================================================================
@pytest.mark.asyncio
async def test_concurrent_publish_race_condition():
    """
    Verifies that concurrent publishing is safely serialized using asyncio.Lock,
    ensuring that events are chained and recorded sequentially without race conditions.
    """
    bus = EventBus()
    events_published = []
    
    # We mock js.publish to yield control, simulating network latency
    async def delayed_publish(topic, data):
        event = CortexEvent.from_json(data.decode('utf-8'))
        # If it's step 1, sleep longer. If step 2, sleep shorter.
        if event.payload["step"] == 1:
            await asyncio.sleep(0.05)
        else:
            await asyncio.sleep(0.01)
        events_published.append(event)
        
    mock_js = AsyncMock()
    mock_js.publish = AsyncMock(side_effect=delayed_publish)
    bus.js = mock_js
    
    # Trigger concurrent publishes. With the lock, Step 1 will complete publishing before
    # Step 2 can acquire the lock and calculate its hash.
    await asyncio.gather(
        bus.publish("cortex.test", {"step": 1}),
        bus.publish("cortex.test", {"step": 2})
    )
    
    # With locking, Step 1 is fully completed and published before Step 2 publishes.
    assert len(events_published) == 2
    assert events_published[0].payload["step"] == 1
    assert events_published[1].payload["step"] == 2
    
    # Verify the chain: the 2nd item has prevHash equal to the 1st item's hash
    assert events_published[1].prevHash == events_published[0].hash


# =====================================================================
# 4. TEST: Neo4j Transaction Lifecycle Violation (Fixed)
# =====================================================================
class MockClosedTransactionError(Exception):
    pass

@pytest.mark.asyncio
async def test_neo4j_transaction_lifecycle_violation():
    """
    Verifies that MemoryStore.crystallize and MemoryStore.prune access
    transaction results INSIDE the execute_write transaction context,
    preventing ClosedTransactionError in production.
    """
    store = MemoryStore()
    
    # A realistic mock of the Neo4j session/transaction behavior
    class RealisticTx:
        def __init__(self):
            self.closed = False
            
        async def run(self, cypher, **kwargs):
            if self.closed:
                raise MockClosedTransactionError("Transaction is closed")
            return self
            
        async def __anext__(self):
            if self.closed:
                raise MockClosedTransactionError("Result consumed outside transaction context")
            # Return dummy record
            raise StopAsyncIteration
            
        def __aiter__(self):
            return self
            
        async def single(self):
            if self.closed:
                raise MockClosedTransactionError("Result consumed outside transaction context")
            return {"pruned": 10}

    class RealisticSession:
        def __init__(self):
            self.tx = RealisticTx()
            
        async def execute_write(self, unit_of_work):
            # Execute unit of work
            res = await unit_of_work(self.tx)
            # After unit of work returns, the session commits the tx and closes it
            self.tx.closed = True
            return res
            
        async def __aenter__(self):
            return self
            
        async def __aexit__(self, exc_type, exc_val, exc_tb):
            pass

    mock_driver = MagicMock()
    mock_driver.session = MagicMock(side_effect=RealisticSession)
    store.driver = mock_driver
    
    event = CortexEvent(
        hash="test_hash",
        prevHash="prev_hash",
        timestamp=1000.0,
        payload={"sourceRegion": "Test", "content": "test"}
    )
    
    # The transaction context operations must succeed without MockClosedTransactionError
    records = await store.crystallize(event)
    assert isinstance(records, list)
    
    pruned_count = await store.prune(0.90)
    assert pruned_count == 10
