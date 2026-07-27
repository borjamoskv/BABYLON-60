# [C5-REAL] Exergy-Maximized
import pytest
from moskv_1.immunity import ImmunityLayer, ImmuneState
from moskv_1.memory import MemoryStore
from moskv_1.event_bus import CortexEvent

def test_shannon_entropy_calculation():
    # Empty string should yield 0
    assert ImmunityLayer.calculate_entropy("") == 0.0

    # Repeating strings should have very low entropy
    low_entropy = ImmunityLayer.calculate_entropy("aaaaaaa")
    assert low_entropy == 0.0

    # Diverse strings should have higher entropy
    high_entropy = ImmunityLayer.calculate_entropy("abcdefg")
    assert high_entropy > 2.5

def test_immunity_layer_evaluation():
    layer = ImmunityLayer(high_threshold=3.5, mid_threshold=2.5)

    # Low information density signal (necrotic)
    state, entropy = layer.evaluate_signal("aaaaa")
    assert state == ImmuneState.NECROTIC

    # Marginal information signal (quarantined)
    state, entropy = layer.evaluate_signal("abcdef abcdef")
    assert state == ImmuneState.QUARANTINED

    # High information density signal (promotable)
    state, entropy = layer.evaluate_signal("The quick brown fox jumps over the lazy dog.")
    assert state == ImmuneState.PROMOTABLE

@pytest.mark.asyncio
async def test_memory_store_auto_quarantine():
    store = MemoryStore()

    # Create low-entropy event (should trigger quarantine)
    low_entropy_event = CortexEvent(
        hash="hash_low",
        prevHash="genesis",
        timestamp=100.0,
        payload={"sourceRegion": "Reasoning", "content": "aaaaa"}
    )
    records_low = await store.crystallize(low_entropy_event)
    node_low = records_low[0]["n"]
    assert node_low.get("is_quarantined") is True
    assert node_low.get("immune_state") == ImmuneState.NECROTIC.value

    # Create high-entropy event (should pass to promotable)
    high_entropy_event = CortexEvent(
        hash="hash_high",
        prevHash="genesis",
        timestamp=100.0,
        payload={"sourceRegion": "Reasoning", "content": "The quick brown fox jumps over the lazy dog and creates a high-entropy distribution of characters."}
    )
    records_high = await store.crystallize(high_entropy_event)
    node_high = records_high[0]["n"]
    assert node_high.get("is_quarantined") is False
    assert node_high.get("immune_state") == ImmuneState.PROMOTABLE.value

@pytest.mark.asyncio
async def test_memory_store_manual_quarantine_lifecycle():
    store = MemoryStore()
    
    event = CortexEvent(
        hash="hash_node",
        prevHash="genesis",
        timestamp=100.0,
        payload={"sourceRegion": "Reasoning", "content": "The quick brown fox jumps over the lazy dog and creates a high-entropy distribution of characters."}
    )
    await store.crystallize(event)
    
    # Verify initially not quarantined
    assert store._nodes["hash_node"]["is_quarantined"] is False
    
    # Manually quarantine
    success = await store.quarantine("hash_node", "Failed downstream consensus validation")
    assert success is True
    assert store._nodes["hash_node"]["is_quarantined"] is True
    assert store._nodes["hash_node"]["quarantine_reason"] == "Failed downstream consensus validation"
    assert store._nodes["hash_node"]["immune_state"] == "quarantined"
    
    # Manually unquarantine
    success_lift = await store.unquarantine("hash_node")
    assert success_lift is True
    assert store._nodes["hash_node"]["is_quarantined"] is False
    assert "quarantine_reason" not in store._nodes["hash_node"]
    assert store._nodes["hash_node"]["immune_state"] == "promotable"
