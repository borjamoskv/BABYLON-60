import pytest
import asyncio
from unittest.mock import patch
from babylon60.swarm.aleph_omega import AxiomaticLeapEngine, AlephLeapResult

@pytest.mark.asyncio
async def test_execute_leap_low_entropy():
    engine = AxiomaticLeapEngine(base_entropy=0.1)

    with patch("random.choice", return_value="Test Paradigm"):
        result = await engine.execute_leap("Test Mission", prior_failed_attempts=1)

    assert result["status"] == "breakthrough"
    assert "Test Paradigm" in result["paradigm_shift"]
    assert result["entropy_applied"] == 0.2  # 0.1 + (0.1 * 1)

@pytest.mark.asyncio
async def test_execute_leap_max_entropy():
    engine = AxiomaticLeapEngine(base_entropy=0.8)

    with patch("random.choice", return_value="Test Paradigm"):
        result = await engine.execute_leap("Test Mission", prior_failed_attempts=5)

    # 0.8 + 0.5 = 1.3, but capped at 0.99
    assert result["entropy_applied"] == 0.99
    assert result["status"] == "breakthrough"

@pytest.mark.asyncio
async def test_execute_leap_sleep_time():
    engine = AxiomaticLeapEngine(base_entropy=0.5)

    with patch("asyncio.sleep") as mock_sleep:
        with patch("random.choice", return_value="Test Paradigm"):
            await engine.execute_leap("Test Mission", prior_failed_attempts=1)

    # current_entropy = 0.6
    # execution_time = 2.0 * (1.0 - 0.6) = 0.8
    mock_sleep.assert_called_once()
    args, _ = mock_sleep.call_args
    assert round(args[0], 2) == 0.8
