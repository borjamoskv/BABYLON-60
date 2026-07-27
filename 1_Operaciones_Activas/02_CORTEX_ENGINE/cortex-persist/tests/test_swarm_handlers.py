import pytest
from unittest.mock import MagicMock, AsyncMock
from babylon60.swarm.handlers import MemoryHandler, OracleHandler
from babylon60.swarm.runtime import SubagentRequest

@pytest.fixture
def memory_req():
    req = MagicMock(spec=SubagentRequest)
    req.prompt = "Test prompt"
    req.context = {
        "project_id": "test_proj",
        "fact_type": "info",
        "metadata": {"key": "val"},
        "layer": "test_layer",
        "query": "search q",
        "max_episodes": 3,
        "tenant_id": "tenant-1"
    }
    return req

@pytest.mark.asyncio
async def test_memory_handler_agent_dispatch(memory_req):
    agent = MagicMock()
    agent._dispatch = AsyncMock(return_value="dispatch_ok")
    handler = MemoryHandler(agent=agent)

    memory_req.context["op"] = "test_op"
    res = await handler.run(memory_req)
    assert res == "dispatch_ok"
    agent._dispatch.assert_called_once_with("test_op", {
        "content": "Test prompt",
        "project_id": "test_proj",
        "fact_type": "info",
        "metadata": {"key": "val"},
        "layer": "test_layer",
        "query": "search q",
        "max_episodes": 3,
        "tenant_id": "tenant-1"
    })

@pytest.mark.asyncio
async def test_memory_handler_engine_store(memory_req):
    engine = MagicMock()
    engine.store = AsyncMock(return_value="store_ok")
    handler = MemoryHandler(engine=engine)

    memory_req.context["op"] = "store"
    res = await handler.run(memory_req)
    assert res == "store_ok"
    engine.store.assert_called_once_with(
        tenant_id="tenant-1",
        project_id="test_proj",
        content="Test prompt",
        fact_type="info",
        metadata={"key": "val"},
        layer="test_layer"
    )

@pytest.mark.asyncio
async def test_memory_handler_engine_context(memory_req):
    engine = MagicMock()
    engine.assemble_context = AsyncMock(return_value="context_ok")
    handler = MemoryHandler(engine=engine)

    memory_req.context["op"] = "context"
    res = await handler.run(memory_req)
    assert res == "context_ok"
    engine.assemble_context.assert_called_once_with(
        tenant_id="tenant-1",
        project_id="test_proj",
        query="search q",
        max_episodes=3
    )

@pytest.mark.asyncio
async def test_memory_handler_engine_status(memory_req):
    engine = MagicMock()
    handler = MemoryHandler(engine=engine)

    memory_req.context["op"] = "status"
    res = await handler.run(memory_req)
    assert res == {"agent": "memory", "status": "ok", "bridge": "engine"}

@pytest.mark.asyncio
async def test_memory_handler_noop_status(memory_req):
    handler = MemoryHandler()

    memory_req.context["op"] = "status"
    res = await handler.run(memory_req)
    assert res == {"agent": "memory", "status": "ok", "bridge": "noop"}

@pytest.mark.asyncio
async def test_memory_handler_unknown_op(memory_req):
    handler = MemoryHandler()

    memory_req.context["op"] = "unknown_op"
    with pytest.raises(RuntimeError) as exc:
        await handler.run(memory_req)
    assert "cannot execute op='unknown_op'" in str(exc.value)

@pytest.mark.asyncio
async def test_oracle_handler_unavailable():
    llm = MagicMock()
    llm.available = False
    handler = OracleHandler(llm, "SysPrompt")

    with pytest.raises(RuntimeError) as exc:
        await handler.run(MagicMock())
    assert "LLM core unavailable" in str(exc.value)

@pytest.mark.asyncio
async def test_oracle_handler_success():
    llm = MagicMock()
    llm.available = True
    llm.complete = AsyncMock(return_value="Audit report")
    handler = OracleHandler(llm, "SysPrompt")

    req = MagicMock()
    req.context = {
        "target_url": "http://test",
        "depth": 2,
        "agent_type": "tester"
    }

    res = await handler.run(req)
    assert res == "Audit report"

    llm.complete.assert_called_once()
    kwargs = llm.complete.call_args.kwargs
    assert "http://test" in kwargs["prompt"]
    assert "TESTER" in kwargs["prompt"]
    assert "2/3" in kwargs["prompt"]
    assert kwargs["system"] == "SysPrompt"
    assert kwargs["temperature"] == 0.2
    assert kwargs["max_tokens"] == 2048
    assert kwargs["intent"] == "reasoning"
