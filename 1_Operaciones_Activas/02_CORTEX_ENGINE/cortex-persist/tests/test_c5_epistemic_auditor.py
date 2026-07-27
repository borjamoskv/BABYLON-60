# [C5-REAL] Exergy-Maximized

import pytest
from unittest.mock import AsyncMock
from pathlib import Path

from babylon60.swarm.c5_epistemic_auditor import C5EpistemicAgent, EpistemicSquadron
from babylon60.swarm.legion import SwarmSignal

@pytest.fixture
def mock_bus():
    bus = AsyncMock()
    return bus

@pytest.mark.asyncio
async def test_epistemic_agent_execute_success(tmp_path, mock_bus):
    agent = C5EpistemicAgent(agent_id="auditor-1", bus=mock_bus)

    test_file = tmp_path / "test_file.py"
    test_file.write_text("print('C5-REAL')")

    signal = await agent.execute(str(test_file))

    assert signal.status == "SUCCESS"
    assert signal.agent_id == "auditor-1"
    assert signal.target == str(test_file)
    assert "hash" in signal.payload
    assert "bytes" in signal.payload

@pytest.mark.asyncio
async def test_epistemic_agent_execute_void(mock_bus):
    agent = C5EpistemicAgent(agent_id="auditor-2", bus=mock_bus)

    signal = await agent.execute("/tmp/does_not_exist_xyz123")

    assert signal.status == "VOID"
    assert signal.payload["error"] == "Target does not exist in physical reality."

@pytest.mark.asyncio
async def test_epistemic_squadron_map_and_crystallize():
    squadron = EpistemicSquadron()

    # test _map with target
    targets = await squadron._map(target_pattern="my_target.py")
    assert targets == ["my_target.py"]

    # test _crystallize
    signals = [
        SwarmSignal(agent_id="1", target="t1", status="SUCCESS", payload={"proof_of_work": "CORTEX-TAINT:C5"}, metrics={}),
        SwarmSignal(agent_id="2", target="t2", status="FAILURE", payload={"error": "e"}, metrics={}),
    ]
    report = await squadron._crystallize(signals)
    assert report["byzantine_faults"] == 1
    assert "success" in report
