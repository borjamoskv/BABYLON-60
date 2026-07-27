# [C5-REAL] Exergy-Maximized

import pytest
from unittest.mock import AsyncMock

from babylon60.agents.bus import SqliteMessageBus
from babylon60.agents.manifest import AgentManifest
from babylon60.agents.tools import ToolRegistry

from babylon60.swarm.c5_epistemic_auditor import C5EpistemicAgent
from babylon60.swarm.entropy_daemon import EntropyDaemon
from babylon60.swarm.exergy_agent import ExergyAgentAdapter
from babylon60.swarm.gatekeeper import ZeroKnowledgeGatekeeper
from babylon60.swarm.generator_agent import GeneratorAgent

@pytest.fixture
def test_manifest():
    return AgentManifest(agent_id="test-agent", purpose="testing coverage")

@pytest.fixture
def mock_bus():
    bus = SqliteMessageBus()
    bus.send = AsyncMock()
    return bus

@pytest.fixture
def tool_registry():
    return ToolRegistry()

def test_instantiate_epistemic_auditor(mock_bus):
    agent = C5EpistemicAgent("test-agent", mock_bus)
    assert agent.agent_id == "test-agent"

def test_instantiate_entropy_daemon(mock_bus):
    agent = EntropyDaemon(mock_bus)
    assert agent is not None

def test_instantiate_exergy_agent(mock_bus):
    agent = ExergyAgentAdapter("test-agent", mock_bus)
    assert agent.agent_id == "test-agent"

def test_instantiate_gatekeeper():
    agent = ZeroKnowledgeGatekeeper()
    assert agent is not None

def test_instantiate_generator_agent(mock_bus):
    agent = GeneratorAgent("test-agent", mock_bus)
    assert agent.agent_id == "test-agent"
