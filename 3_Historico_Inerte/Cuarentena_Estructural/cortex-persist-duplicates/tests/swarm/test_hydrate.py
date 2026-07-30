# [C5-REAL] Exergy-Maximized
"""Tests for swarm hydration bridge and LLM agent handler."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from babylon60.extensions.agents.registry import (
    AgentCatalogEntry,
    GuardrailsConfig,
    MemoryConfig,
)
from babylon60.swarm.hydrate import (
    _classify_tier,
    create_hydrated_runner,
    dispatch_to_agent,
    hydrate_swarm,
)
from babylon60.swarm.llm_agent_handler import LLMAgentHandler, _compute_max_tokens, _resolve_intent
from babylon60.swarm.runtime import AgentRegistry, SubagentRequest, SubagentRunner


def _make_entry(
    agent_id: str = "test_agent",
    name: str = "TEST-Ω",
    provider: str = "ollama",
    intent: str = "reasoning",
    model: str = "qwen2.5-coder:7b",
    system_prompt: str = "You are a test agent.",
    tools: list[str] | None = None,
    max_session_tokens: int = 100000,
    causal_memory: bool = False,
) -> AgentCatalogEntry:
    return AgentCatalogEntry(
        id=agent_id,
        name=name,
        model=model,
        system_prompt=system_prompt,
        provider=provider,
        intent=intent,
        memory=MemoryConfig(causal_memory=causal_memory),
        guardrails=GuardrailsConfig(max_session_tokens=max_session_tokens),
        tools=tools or [],
    )


# ─── Tier Classification ─────────────────────────────────────────────


class TestClassifyTier:
    def test_t0_with_many_tools(self) -> None:
        entry = _make_entry(tools=["a", "b", "c", "d", "e", "f"])
        assert _classify_tier(entry) == "T0"

    def test_t1_with_few_tools(self) -> None:
        entry = _make_entry(tools=["a", "b"])
        assert _classify_tier(entry) == "T1"

    def test_t1_with_causal_memory(self) -> None:
        entry = _make_entry(tools=[], causal_memory=True)
        assert _classify_tier(entry) == "T1"

    def test_t1_with_long_prompt_and_tools(self) -> None:
        entry = _make_entry(
            provider="",
            intent="",
            system_prompt="x" * 600,
            tools=["a"],
        )
        assert _classify_tier(entry) == "T1"

    def test_t2_bare_agent(self) -> None:
        entry = _make_entry(provider="", intent="", tools=[])
        assert _classify_tier(entry) == "T2"


# ─── Intent Resolution ──────────────────────────────────────────────


class TestResolveIntent:
    def test_known_intents(self) -> None:
        from babylon60.extensions.llm._models import IntentProfile

        assert _resolve_intent("code") == IntentProfile.CODE
        assert _resolve_intent("architect") == IntentProfile.ARCHITECT
        assert _resolve_intent("reasoning") == IntentProfile.REASONING
        assert _resolve_intent("creative") == IntentProfile.CREATIVE

    def test_unknown_falls_to_general(self) -> None:
        from babylon60.extensions.llm._models import IntentProfile

        assert _resolve_intent("nonexistent") == IntentProfile.GENERAL
        assert _resolve_intent("") == IntentProfile.GENERAL


# ─── Max Tokens Computation ─────────────────────────────────────────


class TestComputeMaxTokens:
    def test_standard(self) -> None:
        entry = _make_entry(max_session_tokens=100000)
        assert _compute_max_tokens(entry) == 10000

    def test_clamped_low(self) -> None:
        entry = _make_entry(max_session_tokens=1000)
        assert _compute_max_tokens(entry) == 512  # Clamped to min 512

    def test_clamped_high(self) -> None:
        entry = _make_entry(max_session_tokens=2097152)
        assert _compute_max_tokens(entry) == 16384  # Clamped to max 16384


# ─── LLM Agent Handler ──────────────────────────────────────────────


class TestLLMAgentHandler:
    def test_handler_properties(self) -> None:
        entry = _make_entry()
        handler = LLMAgentHandler(entry)
        assert handler.agent_id == "test_agent"
        assert handler.agent_name == "TEST-Ω"
        assert handler.turn_count == 0

    @pytest.mark.asyncio
    async def test_handler_run_returns_telemetry(self) -> None:
        entry = _make_entry()
        handler = LLMAgentHandler(entry)

        mock_llm = MagicMock()
        mock_llm.complete = AsyncMock(return_value="LLM response content")
        handler._llm = mock_llm

        req = SubagentRequest(
            task_id="test-001",
            kind="reason",
            prompt="What is 2+2?",
        )

        result = await handler.run(req)

        assert isinstance(result, dict)
        assert result["text"] == "LLM response content"
        assert result["status"] == "OK"
        assert result["agent_id"] == "test_agent"
        assert result["turn"] == 1
        assert "latency_ms" in result
        assert "guardrails" in result

    @pytest.mark.asyncio
    async def test_handler_injects_context(self) -> None:
        entry = _make_entry()
        handler = LLMAgentHandler(entry)

        mock_llm = MagicMock()
        mock_llm.complete = AsyncMock(return_value="ok")
        handler._llm = mock_llm

        req = SubagentRequest(
            task_id="test-002",
            kind="reason",
            prompt="Analyze this",
            context={"project": "babylon60", "scope": "engine"},
        )

        await handler.run(req)

        prompt_sent = mock_llm.complete.call_args.kwargs["prompt"]
        assert "project: babylon60" in prompt_sent
        assert "scope: engine" in prompt_sent

    @pytest.mark.asyncio
    async def test_handler_tracks_turns(self) -> None:
        entry = _make_entry()
        handler = LLMAgentHandler(entry)

        mock_llm = MagicMock()
        mock_llm.complete = AsyncMock(return_value="response")
        handler._llm = mock_llm

        req = SubagentRequest(task_id="t", kind="reason", prompt="p")
        await handler.run(req)
        await handler.run(req)

        assert handler.turn_count == 2

    @pytest.mark.asyncio
    async def test_handler_guardrail_max_turns(self) -> None:
        entry = _make_entry()
        entry.guardrails.max_turns = 1
        handler = LLMAgentHandler(entry)

        mock_llm = MagicMock()
        mock_llm.complete = AsyncMock(return_value="ok")
        handler._llm = mock_llm

        req = SubagentRequest(task_id="t", kind="reason", prompt="p")
        r1 = await handler.run(req)
        assert r1["status"] == "OK"

        r2 = await handler.run(req)
        assert r2["status"] == "GUARDRAIL_ABORT"
        assert "max_turns" in r2["text"]

    def test_reset_clears_state(self) -> None:
        entry = _make_entry()
        handler = LLMAgentHandler(entry)
        handler._turn_count = 5
        handler._total_tokens_estimate = 10000
        handler._history = [{"role": "user", "content": "test"}]

        handler.reset()

        assert handler.turn_count == 0
        assert handler._total_tokens_estimate == 0
        assert handler._history == []


# ─── Hydration ───────────────────────────────────────────────────────


class TestHydrateSwarm:
    @patch("babylon60.extensions.agents.registry.AgentCatalogLoader")
    def test_hydrate_tiers(self, mock_loader_cls: MagicMock) -> None:
        mock_loader = MagicMock()
        mock_loader.agents = {
            # T0: has provider+intent+6 tools
            "demiurge": _make_entry(
                "demiurge",
                "DEMIURGE-Ω",
                tools=["a", "b", "c", "d", "e", "f"],
            ),
            # T1: has provider+intent+2 tools
            "zeus": _make_entry("zeus", "ZEUS-Ω", tools=["a", "b"]),
            # T2: no provider/intent/tools
            "random": _make_entry("random", "RANDOM-Ω", provider="", intent="", tools=[]),
        }
        mock_loader_cls.return_value = mock_loader

        # T0 only
        registry = AgentRegistry()
        runner = SubagentRunner(registry)
        count = hydrate_swarm(runner, max_tier="T0")
        assert count == 1

        # T1
        registry = AgentRegistry()
        runner = SubagentRunner(registry)
        count = hydrate_swarm(runner, max_tier="T1")
        assert count == 2

        # T2 — all
        registry = AgentRegistry()
        runner = SubagentRunner(registry)
        count = hydrate_swarm(runner, max_tier="T2")
        assert count == 3


class TestCreateHydratedRunner:
    @patch("babylon60.extensions.agents.registry.AgentCatalogLoader")
    def test_creates_with_audit(self, mock_loader_cls: MagicMock) -> None:
        mock_loader = MagicMock()
        mock_loader.agents = {
            "athena": _make_entry("athena", "ATHENA-Ω", tools=["a"]),
        }
        mock_loader_cls.return_value = mock_loader

        runner = create_hydrated_runner(max_tier="T1")

        assert len(runner.registry.all()) == 1
        assert runner.audit_callback is not None  # Audit enabled by default

    @patch("babylon60.extensions.agents.registry.AgentCatalogLoader")
    def test_creates_without_audit(self, mock_loader_cls: MagicMock) -> None:
        mock_loader = MagicMock()
        mock_loader.agents = {"a": _make_entry("a", "A", tools=["x"])}
        mock_loader_cls.return_value = mock_loader

        runner = create_hydrated_runner(max_tier="T1", enable_audit=False)
        assert runner.audit_callback is None


class TestDispatchToAgent:
    @patch("babylon60.extensions.agents.registry.AgentCatalogLoader")
    async def _setup_and_dispatch(self, mock_loader_cls: MagicMock) -> dict:
        mock_loader = MagicMock()
        entry = _make_entry("test", "TEST", tools=["a"])
        mock_loader.agents = {"test": entry}
        mock_loader_cls.return_value = mock_loader

        # We can't actually dispatch without an LLM, so we verify the
        # error case (no handler registered because hydration uses real classes)
        result = await dispatch_to_agent("nonexistent", "hello", max_tier="T2")
        return result

    @pytest.mark.asyncio
    @patch("babylon60.extensions.agents.registry.AgentCatalogLoader")
    async def test_dispatch_nonexistent_agent(self, mock_loader_cls: MagicMock) -> None:
        mock_loader = MagicMock()
        mock_loader.agents = {}
        mock_loader_cls.return_value = mock_loader

        result = await dispatch_to_agent("ghost", "hello")
        assert result["status"] == "ERROR"
