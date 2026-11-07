"""C29: bounded rate-limit recovery without network or real sleeps."""

import asyncio
import time

import httpx
import pytest

from babylon60.kernel import swarm_orchestrator as swarm


def test_exhausted_rate_limits_open_circuit_without_final_sleep(monkeypatch):
    calls = 0
    sleeps = []

    async def reject(*args):
        nonlocal calls
        calls += 1
        response = httpx.Response(429, request=httpx.Request("POST", "https://example.invalid"))
        response.raise_for_status()

    async def sleep(delay):
        sleeps.append(delay)

    monkeypatch.setattr(swarm, "_http_post_single_attempt", reject)
    monkeypatch.setattr(asyncio, "sleep", sleep)
    client = swarm.RobustLLMClient(swarm.SwarmConfig(max_retries=3, circuit_breaker_threshold=2))

    async def scenario():
        for _ in range(2):
            assert (await client.call([])).startswith("Error HTTP 429")
        assert client.is_circuit_breaker_tripped
        assert (await client.call([])).startswith("🔴 Circuit breaker")

    asyncio.run(scenario())
    assert calls == 6
    assert sleeps == [1.0, 2.0, 1.0, 2.0]
    assert client._consecutive_failures == 2


@pytest.mark.parametrize(
    "header,expected",
    [
        ("12", 12.0),
        ("999999", 60.0),
        ("-2", 0.0),
        ("invalid", 3.0),
        ("nan", 3.0),
        ("inf", 3.0),
        ("Thu, 01 Jan 1970 00:00:15 GMT", 5.0),
        ("Thu, 01 Jan 1970 00:00:05 GMT", 0.0),
    ],
)
def test_retry_after_is_bounded(header, expected, monkeypatch):
    monkeypatch.setattr(time, "time", lambda: 10.0)
    response = httpx.Response(429, headers={"Retry-After": header})
    assert swarm._rate_limit_delay(response, 3.0) == expected


def test_retry_after_applied_and_success_resets_failures(monkeypatch):
    calls = 0
    sleeps = []

    async def request(*args):
        nonlocal calls
        calls += 1
        if calls == 1:
            response = httpx.Response(
                429, headers={"Retry-After": "7"}, request=httpx.Request("POST", "https://example.invalid")
            )
            response.raise_for_status()
        return {"choices": [{"message": {"content": "recovered"}}]}

    async def sleep(delay):
        sleeps.append(delay)

    monkeypatch.setattr(swarm, "_http_post_single_attempt", request)
    monkeypatch.setattr(asyncio, "sleep", sleep)
    client = swarm.RobustLLMClient(swarm.SwarmConfig(max_retries=2))
    client._consecutive_failures = 1
    assert asyncio.run(client.call([])) == "recovered"
    assert client._consecutive_failures == 0
    assert sleeps == [7.0]
    assert calls == 2
