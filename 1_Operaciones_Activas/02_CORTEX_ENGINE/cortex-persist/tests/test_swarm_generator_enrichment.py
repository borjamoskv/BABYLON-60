import pytest
import asyncio
from unittest.mock import AsyncMock, patch

from babylon60.swarm.enrichment_worker import run_enrichment_worker, process_next_job
from babylon60.swarm.generator_agent import GeneratorAgent

@pytest.fixture
def mock_bus():
    return AsyncMock()

@pytest.mark.asyncio
@patch("babylon60.swarm.enrichment_worker.CapabilityRegistry")
async def test_enrichment_worker_process_next_job(mock_cap_reg):
    # Setup mock
    mock_instance = mock_cap_reg.get_instance.return_value
    mock_instance.capabilities.embeddings = False

    mock_engine = AsyncMock()

    result = await process_next_job(mock_engine)
    assert result is False

@pytest.mark.asyncio
@patch("babylon60.swarm.generator_agent.Signer")
@patch("babylon60.swarm.generator_agent.KeyManager")
async def test_generator_agent_execute(mock_km_class, mock_signer, mock_bus):
    mock_km = mock_km_class.return_value
    mock_km.get_public_key_b64.return_value = None
    mock_km.get_private_key_b64.return_value = "dummy_priv_key"

    mock_signer.sign_payload.return_value = "dummy_signature"

    agent = GeneratorAgent(agent_id="gen-1", bus=mock_bus, km=mock_km)

    signal = await agent.execute("test_target")
    assert signal.agent_id == "gen-1"
    assert signal.status == "SUCCESS"
    assert "ast_code" in signal.payload
