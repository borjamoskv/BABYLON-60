import pytest
from unittest.mock import MagicMock, patch
from babylon60.swarm.c5_epistemic_auditor import C5EpistemicAgent, EpistemicSquadron
from babylon60.swarm.legion import SwarmSignal
import hashlib

@pytest.mark.asyncio
async def test_c5_agent_execute_success(tmp_path):
    agent = C5EpistemicAgent("agent-1", MagicMock(), MagicMock())
    test_file = tmp_path / "test.txt"
    test_file.write_text("Hello, World!")

    result = await agent.execute(str(test_file))

    assert result.status == "SUCCESS"
    assert result.target == str(test_file)
    assert result.metrics["entropy_len"] == 13
    assert result.payload["bytes"] == 13
    from babylon60.crypto.hash_registry import cortex_hash
    expected_hash = cortex_hash(b"Hello, World!")
    assert result.payload["hash"] == expected_hash

@pytest.mark.asyncio
async def test_c5_agent_execute_not_found(tmp_path):
    agent = C5EpistemicAgent("agent-1", MagicMock(), MagicMock())
    missing_file = tmp_path / "missing.txt"

    result = await agent.execute(str(missing_file))

    assert result.status == "VOID"
    assert "error" in result.payload

@pytest.mark.asyncio
async def test_c5_agent_execute_error(tmp_path):
    agent = C5EpistemicAgent("agent-1", MagicMock(), MagicMock())
    test_file = tmp_path / "test.txt"
    test_file.write_text("content")

    with patch("pathlib.Path.read_bytes", side_effect=PermissionError("Denied")):
        result = await agent.execute(str(test_file))

    assert result.status == "FAILURE"
    assert "Denied" in result.payload["error"]

def test_squadron_create_agent():
    squadron = EpistemicSquadron(engine=MagicMock())
    # Note: the test creates it with agent-1
    squadron.bus = MagicMock()
    agent = squadron._create_agent("agent-1")
    assert isinstance(agent, C5EpistemicAgent)
    assert agent.agent_id == "agent-1"

@pytest.mark.asyncio
async def test_squadron_map_with_target():
    squadron = EpistemicSquadron(engine=MagicMock())
    targets = await squadron._map("custom_target.py")
    assert targets == ["custom_target.py"]

@pytest.mark.asyncio
async def test_squadron_map_default():
    squadron = EpistemicSquadron(engine=MagicMock())
    with patch("pathlib.Path.exists", side_effect=lambda: True):
        # We need to bypass the actual exists check to return all mocked files
        with patch("babylon60.swarm.c5_epistemic_auditor.Path.exists", return_value=True):
            targets = await squadron._map()
            assert len(targets) == 3
            assert "babylon60/swarm/legion.py" in targets

@pytest.mark.asyncio
async def test_squadron_crystallize():
    squadron = EpistemicSquadron(engine=MagicMock())

    # Mock super()._crystallize
    async def mock_super_crystallize(self, sigs):
        return {"success": len(sigs), "total": len(sigs)}

    with patch("babylon60.swarm.legion.Squadron._crystallize", new=mock_super_crystallize):
        sigs = [
            SwarmSignal("agent-1", "t1", "SUCCESS", {}, {}),
            SwarmSignal("agent-2", "t2", "FAILURE", {}, {}),
            SwarmSignal("agent-3", "t3", "FAILURE", {}, {}),
        ]

        report = await squadron._crystallize(sigs)
        assert report["success"] == 3
        assert report["byzantine_faults"] == 2
