import pytest
import sqlite3
from unittest.mock import patch, MagicMock
from babylon60.swarm.agent_mixin import AgentMixin, _get_raw_conn, build_health_probes

class DummyEngine:
    def _get_sync_conn(self):
        return "conn"

def test_get_raw_conn():
    engine = DummyEngine()
    assert _get_raw_conn(engine) == "conn"

def test_build_health_probes():
    assert build_health_probes(None, None, "v1") == {}

@pytest.fixture
def mock_session():
    class MockCursor:
        async def fetchone(self):
            return {"id": "agent-1", "name": "Agent Smith"}

        async def fetchall(self):
            return [{"id": "agent-1", "name": "Agent Smith"}]

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc_val, exc_tb):
            pass

    class MockExecuteContext:
        def __init__(self, cursor):
            self.cursor = cursor
        async def __aenter__(self):
            return self.cursor
        async def __aexit__(self, exc_type, exc_val, exc_tb):
            pass

    class MockConn:
        def __init__(self):
            self.row_factory = None
            self.executed = []
            self.committed = False
            self.rollbacked = False

        def execute(self, query, params=None):
            self.executed.append((query, params))
            class AsyncResult:
                def __await__(self):
                    async def _coro():
                        return MockCursor()
                    return _coro().__await__()
                async def __aenter__(self):
                    return MockCursor()
                async def __aexit__(self, exc_type, exc_val, exc_tb):
                    pass
            return AsyncResult()

        async def commit(self):
            self.committed = True

        async def rollback(self):
            self.rollbacked = True

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc_val, exc_tb):
            pass

    return MockConn()

class ConcreteAgentMixin(AgentMixin):
    def __init__(self, mock_conn):
        self.mock_conn = mock_conn

    def session(self):
        return self.mock_conn

@pytest.mark.asyncio
async def test_register_agent(mock_session):
    mixin = ConcreteAgentMixin(mock_session)

    mock_moltbook = MagicMock()
    mock_client_instance = MagicMock()
    from unittest.mock import AsyncMock
    mock_client_instance.register = AsyncMock()
    mock_client_instance.close = AsyncMock()
    mock_moltbook.MoltbookClient.return_value = mock_client_instance

    with patch("babylon60.swarm.agent_mixin.uuid.uuid4", return_value="agent-123"):
        with patch.dict("sys.modules", {"babylon60.extensions.moltbook.client": mock_moltbook}):
            agent_id = await mixin.register_agent("Test Agent")

            assert agent_id == "agent-123"
            assert mock_session.committed is True
            assert mock_session.executed[0][0] == "BEGIN IMMEDIATE"
            assert "INSERT INTO agents" in mock_session.executed[1][0]

            mock_client_instance.register.assert_called_once()
            mock_client_instance.close.assert_called_once()

@pytest.mark.asyncio
async def test_register_agent_moltbook_fail(mock_session):
    mixin = ConcreteAgentMixin(mock_session)

    mock_moltbook = MagicMock()
    mock_client_instance = MagicMock()
    async def mock_register(*args, **kwargs):
        raise ValueError("Moltbook error")
    mock_client_instance.register = mock_register
    mock_moltbook.MoltbookClient.return_value = mock_client_instance

    with patch.dict("sys.modules", {"babylon60.extensions.moltbook.client": mock_moltbook}):
        agent_id = await mixin.register_agent("Test Agent")

        assert isinstance(agent_id, str)
        assert mock_session.committed is True

@pytest.mark.asyncio
async def test_register_agent_db_fail(mock_session):
    mixin = ConcreteAgentMixin(mock_session)

    async def failing_execute(query, params=None):
        if "INSERT" in query:
            raise sqlite3.Error("DB error")
        return MagicMock()

    mock_session.execute = failing_execute

    with pytest.raises(sqlite3.Error):
        await mixin.register_agent("Test Agent")

    assert mock_session.rollbacked is True

@pytest.mark.asyncio
async def test_get_agent(mock_session):
    mixin = ConcreteAgentMixin(mock_session)
    agent = await mixin.get_agent("agent-1")
    assert agent["id"] == "agent-1"
    assert "SELECT id, name" in mock_session.executed[0][0]

@pytest.mark.asyncio
async def test_list_agents(mock_session):
    mixin = ConcreteAgentMixin(mock_session)
    agents = await mixin.list_agents("default")
    assert len(agents) == 1
    assert agents[0]["id"] == "agent-1"
    assert "SELECT id, name" in mock_session.executed[0][0]
