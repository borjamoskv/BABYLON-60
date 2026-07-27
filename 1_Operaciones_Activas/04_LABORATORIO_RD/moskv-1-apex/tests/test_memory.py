import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from moskv_1.memory import MemoryStore
from moskv_1.event_bus import CortexEvent

@pytest.mark.asyncio
async def test_memory_store_connect_mocked():
    store = MemoryStore()
    mock_driver = AsyncMock()
    
    with patch("moskv_1.memory.AsyncGraphDatabase") as mock_db_class:
        # If AsyncGraphDatabase is mocked, we simulate successful connect
        mock_db_class.driver.return_value = mock_driver
        await store.connect()
        mock_db_class.driver.assert_called_once_with(
            "bolt://localhost:7687",
            auth=("neo4j", "password"),
            max_connection_pool_size=50,
            connection_acquisition_timeout=20.0
        )
        mock_driver.verify_connectivity.assert_called_once()
        assert store.driver == mock_driver

@pytest.mark.asyncio
async def test_memory_store_crystallize_in_memory():
    store = MemoryStore()
    
    event = CortexEvent(
        hash="eventhash123",
        prevHash="genesis",
        timestamp=1000.0,
        payload={"sourceRegion": "Reasoning", "entropy": 0.95, "content": "Visual anomaly"}
    )
    
    # Store crystallizes in-memory since driver is None
    records = await store.crystallize(event)
    assert len(records) == 1
    record = records[0]
    node = record["n"]
    assert node.id == "eventhash123"
    assert node.get("entropy") == 0.95
    assert node.get("content") == "Visual anomaly"
    assert node.get("sourceRegion") == "Reasoning"
    assert store._nodes["eventhash123"]["entropy"] == 0.95

@pytest.mark.asyncio
async def test_memory_store_crystallize_mocked_driver():
    store = MemoryStore()
    
    mock_session = AsyncMock()
    mock_session.__aenter__.return_value = mock_session
    mock_driver = MagicMock()
    mock_driver.session = MagicMock(return_value=mock_session)
    store.driver = mock_driver
    
    # Setup execute_write to run the unit of work
    mock_tx = AsyncMock()
    mock_result = AsyncMock()
    # Mock result iteration inside execute_write callback
    async def mock_async_iter():
        yield {"n": "mock_node"}
    mock_result.__aiter__ = MagicMock(return_value=mock_async_iter())
    mock_tx.run.return_value = mock_result
    
    async def fake_execute_write(callback):
        return await callback(mock_tx)
    mock_session.execute_write.side_effect = fake_execute_write
    
    event = CortexEvent(
        hash="eventhash123",
        prevHash="genesis",
        timestamp=1000.0,
        payload={"sourceRegion": "Reasoning", "entropy": 0.95, "content": "Visual anomaly"}
    )
    
    records = await store.crystallize(event)
    assert len(records) == 1
    assert records[0]["n"] == "mock_node"
    mock_session.execute_write.assert_called_once()
    mock_tx.run.assert_called_once()

@pytest.mark.asyncio
async def test_memory_store_prune_in_memory():
    store = MemoryStore()
    
    # In-memory prune. Add one old node and one new node.
    import time
    now_ms = time.time() * 1000.0
    
    # Old high-entropy node (older than 24h, entropy > 0.9)
    store._nodes["old_node"] = {
        "id": "old_node",
        "entropy": 0.95,
        "content": "old",
        "lastUpdated": now_ms - 90000000.0, # ~25 hours
        "spawnHash": "old_hash",
        "sourceRegion": "Reasoning"
    }
    # New high-entropy node (newer than 24h, entropy > 0.9)
    store._nodes["new_node"] = {
        "id": "new_node",
        "entropy": 0.95,
        "content": "new",
        "lastUpdated": now_ms - 1000.0,
        "spawnHash": "new_hash",
        "sourceRegion": "Reasoning"
    }
    
    pruned_count = await store.prune(0.90)
    assert pruned_count == 1
    assert "old_node" not in store._nodes
    assert "new_node" in store._nodes

@pytest.mark.asyncio
async def test_memory_store_prune_mocked_driver():
    store = MemoryStore()
    
    mock_session = AsyncMock()
    mock_session.__aenter__.return_value = mock_session
    mock_driver = MagicMock()
    mock_driver.session = MagicMock(return_value=mock_session)
    store.driver = mock_driver
    
    mock_tx = AsyncMock()
    mock_result = AsyncMock()
    mock_result.single = AsyncMock(return_value={"pruned": 5})
    mock_tx.run.return_value = mock_result
    
    async def fake_execute_write(callback):
        return await callback(mock_tx)
    mock_session.execute_write.side_effect = fake_execute_write
    
    pruned_count = await store.prune(0.90)
    
    assert pruned_count == 5
    mock_session.execute_write.assert_called_once()
    mock_tx.run.assert_called_once()

@pytest.mark.asyncio
async def test_memory_store_close_mocked():
    store = MemoryStore()
    mock_driver = AsyncMock()
    store.driver = mock_driver
    
    await store.close()
    mock_driver.close.assert_called_once()
