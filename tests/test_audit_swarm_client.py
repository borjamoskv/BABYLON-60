"""Isolated regressions for swarm failure classification and async HTTP lifecycle."""

import asyncio

import httpx
import pytest

from agents_archi.orchestrator import swarm


def config(
    *,
    p_cores: int = 4,
    max_retries: int = 1,
    request_timeout_s: float = 1,
    retry_base_delay_s: float = 0.5,
) -> swarm.SwarmConfig:
    return swarm.SwarmConfig(
        backend=swarm.InferenceBackend.LOCAL_VLLM,
        max_retries=max_retries,
        mcts_delay_s=0,
        request_timeout_s=request_timeout_s,
        p_cores=p_cores,
        retry_base_delay_s=retry_base_delay_s,
    )


@pytest.fixture
def install_transport(monkeypatch):
    original = httpx.AsyncClient

    def install(handler):
        transport = httpx.MockTransport(handler)
        monkeypatch.setattr(httpx, "AsyncClient", lambda **kw: original(transport=transport, **kw))

    return install


@pytest.mark.parametrize("failure", [401, 429, 503, "connection", "veto"])
def test_provider_failures_are_errors(failure, install_transport, monkeypatch):
    async def handler(request):
        if failure == "connection":
            raise httpx.ConnectError("unavailable", request=request)
        if failure == "veto":
            return httpx.Response(
                200, json={"model": "openai/gpt-4o-mini", "choices": [{"message": {"content": "discard"}}]}
            )
        return httpx.Response(failure, text="provider failure")

    install_transport(handler)
    orchestrator = swarm.SwarmOrchestrator(config())
    monkeypatch.setattr(orchestrator.client, "_is_strict_floor_required", lambda messages: failure == "veto")
    events = []
    result = asyncio.run(orchestrator.execute_dag(["task"], lambda *event: events.append(event)))
    assert result["results"][0]["status"] == "ERROR"
    assert isinstance(result["results"][0]["result"], swarm.LLMCallError)
    assert events[0][1] == "ERROR"


def test_success_text_is_not_a_status_protocol(install_transport):
    async def handler(request):
        return httpx.Response(200, json={"choices": [{"message": {"content": "Error analysis completed"}}]})

    install_transport(handler)
    result = asyncio.run(swarm.SwarmOrchestrator(config()).execute_dag(["task"]))
    assert result["results"][0]["status"] == "OK"


def test_requests_overlap_and_cancellation_cleans_up(install_transport):
    async def scenario():
        started = 0
        closed = 0
        both_started = asyncio.Event()

        async def handler(request):
            nonlocal started, closed
            started += 1
            if started == 2:
                both_started.set()
            try:
                await asyncio.Event().wait()
            finally:
                closed += 1

        install_transport(handler)
        task = asyncio.create_task(swarm.SwarmOrchestrator(config(p_cores=2)).execute_dag(["one", "two"]))
        try:
            await asyncio.wait_for(both_started.wait(), timeout=0.5)
        finally:
            task.cancel()
            with pytest.raises(asyncio.CancelledError):
                await task
        assert closed == 2

    asyncio.run(scenario())


def test_attempt_deadline_cancels_stalled_response(install_transport):
    async def scenario():
        closed = asyncio.Event()

        async def handler(request):
            try:
                await asyncio.Event().wait()
            finally:
                closed.set()

        install_transport(handler)
        client = swarm.RobustLLMClient(config(request_timeout_s=0.02))
        result = await asyncio.wait_for(client.call([{"role": "user", "content": "task"}]), timeout=0.5)
        assert isinstance(result, swarm.LLMCallError)
        assert closed.is_set()

    asyncio.run(scenario())


def test_rate_limit_retry_then_success(install_transport):
    calls = 0

    async def handler(request):
        nonlocal calls
        calls += 1
        if calls == 1:
            return httpx.Response(429, text="busy")
        return httpx.Response(200, json={"choices": [{"message": {"content": "recovered"}}]})

    install_transport(handler)
    client = swarm.RobustLLMClient(config(max_retries=2, retry_base_delay_s=0))
    result = asyncio.run(client.call([{"role": "user", "content": "task"}]))
    assert result == "recovered"
    assert not isinstance(result, swarm.LLMCallError)
    assert calls == 2


def test_circuit_breaker_rejects_without_network(install_transport):
    async def handler(request):
        pytest.fail("open circuit must not access the network")

    install_transport(handler)
    orchestrator = swarm.SwarmOrchestrator(config())
    orchestrator.client._consecutive_failures = orchestrator.config.circuit_breaker_threshold
    result = asyncio.run(orchestrator.execute_dag(["task"]))
    assert result["results"][0]["status"] == "ERROR"


def test_preflight_veto_is_typed(install_transport, monkeypatch):
    from agents_archi.clients.openrouter import SubThresholdModelVetoError

    async def handler(request):
        pytest.fail("preflight veto must not access the network")

    def veto(messages):
        raise SubThresholdModelVetoError("SUB_THRESHOLD_MODEL_VETO")

    install_transport(handler)
    orchestrator = swarm.SwarmOrchestrator(config())
    monkeypatch.setattr(orchestrator.client, "build_request_payload", veto)
    result = asyncio.run(orchestrator.execute_dag(["task"]))
    assert result["results"][0]["status"] == "ERROR"
