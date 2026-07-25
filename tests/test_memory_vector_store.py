import pytest

from babylon60.memory.models import CortexFactModel
from babylon60.memory.sqlite_vec_store import SovereignVectorStoreL2


@pytest.mark.asyncio
async def test_memorize_and_recall():
    store = SovereignVectorStoreL2()
    fact = CortexFactModel(id="1", content="Hello world")
    await store.memorize(fact)
    assert await store.count() == 1
    
    results = await store.recall("Hello world")
    assert len(results) == 1
    assert results[0].id == "1"

@pytest.mark.asyncio
async def test_recall_empty():
    store = SovereignVectorStoreL2()
    results = await store.recall("Anything")
    assert results == []

@pytest.mark.asyncio
async def test_recall_most_similar():
    store = SovereignVectorStoreL2()
    fact1 = CortexFactModel(id="1", content="Apples are red")
    fact2 = CortexFactModel(id="2", content="Sky is blue")
    await store.memorize(fact1)
    await store.memorize(fact2)
    
    results = await store.recall("Apples are red")
    assert results[0].id == "1"

@pytest.mark.asyncio
async def test_forget():
    store = SovereignVectorStoreL2()
    fact = CortexFactModel(id="1", content="Hello world")
    await store.memorize(fact)
    assert await store.forget("1") is True
    assert await store.count() == 0
    assert await store.forget("1") is False

@pytest.mark.asyncio
async def test_count():
    store = SovereignVectorStoreL2()
    assert await store.count() == 0
    await store.memorize(CortexFactModel(id="1", content="A"))
    assert await store.count() == 1
    await store.memorize(CortexFactModel(id="2", content="B"))
    assert await store.count() == 2
