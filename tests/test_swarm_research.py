# C5-REAL EXERGY CERTIFIED
import pytest
import asyncio
import os
import sys
import importlib.util
from unittest.mock import AsyncMock, patch

# Dynamic import for path with leading digits
route_path = os.path.abspath(os.path.join(
    os.path.dirname(__file__), "..",
    "1_Operaciones_Activas", "02_CORTEX_ENGINE", "BABYLON-60",
    "babylon60-ide", "backend", "routes", "swarm_research.py"
))

spec = importlib.util.spec_from_file_location("swarm_research_mod", route_path)
if spec is None or spec.loader is None:
    raise RuntimeError(f"Failed to load spec for {route_path}")

swarm_research_mod = importlib.util.module_from_spec(spec)
sys.modules["swarm_research_mod"] = swarm_research_mod
spec.loader.exec_module(swarm_research_mod)

@pytest.mark.asyncio
async def test_swarm_research_execution():
    req = swarm_research_mod.SwarmResearchRequest(
        topic="CORTEX Thermodynamic Topology",
        max_workers=3,
        enable_cloud_transduction=True,
        reasoning_effort="high"
    )

    mock_actor = AsyncMock()
    mock_actor.append.return_value = {"tx_hash": "0xDEADBEEF", "sequence": 1}

    with patch.object(swarm_research_mod, "get_bft_actor", return_value=mock_actor):
        resp = await swarm_research_mod.execute_swarm_research(req)

        assert resp["status"] == "SUCCESS"
        assert resp["mode"] == "ULTRATHINK_KIMI_K3_SWARM_ISOMORPHISM"
        assert resp["workers_dispatched"] == 3
        assert len(resp["synthesis"]) == 3
        assert mock_actor.append.called

@pytest.mark.asyncio
async def test_swarm_hysteresis_gating():
    # Test 10KB topic limit
    large_topic = "X" * (1024 * 11)
    req = swarm_research_mod.SwarmResearchRequest(
        topic=large_topic,
        max_workers=2
    )

    mock_actor = AsyncMock()
    with patch.object(swarm_research_mod, "get_bft_actor", return_value=mock_actor):
        with pytest.raises(swarm_research_mod.HTTPException) as exc_info:
            await swarm_research_mod.execute_swarm_research(req)
        assert exc_info.value.status_code == 413
