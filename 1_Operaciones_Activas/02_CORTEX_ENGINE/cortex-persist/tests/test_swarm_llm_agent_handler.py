import pytest
from unittest.mock import MagicMock, patch, AsyncMock
from babylon60.swarm.llm_agent_handler import _resolve_intent, _compute_max_tokens, LLMAgentHandler

def test_resolve_intent():
    from babylon60.extensions.llm._models import IntentProfile
    assert _resolve_intent("code") == IntentProfile.CODE
    assert _resolve_intent("unknown") == IntentProfile.GENERAL

def test_compute_max_tokens():
    class DummyGuardrails:
        max_session_tokens = 20000
    class DummyEntry:
        guardrails = DummyGuardrails()

    assert _compute_max_tokens(DummyEntry()) == 2000

def test_handler_init():
    entry = MagicMock()
    entry.id = "agent-1"
    entry.name = "Test Agent"
    handler = LLMAgentHandler(entry)

    assert handler.agent_id == "agent-1"
    assert handler.agent_name == "Test Agent"
    assert handler.turn_count == 0

def test_check_guardrails_turns():
    entry = MagicMock()
    entry.id = "agent-1"
    entry.guardrails.max_turns = 2
    handler = LLMAgentHandler(entry)

    handler._turn_count = 2
    err = handler._check_guardrails()
    assert err is not None
    assert "max_turns=2 reached" in err

def test_check_guardrails_tokens():
    entry = MagicMock()
    entry.id = "agent-1"
    entry.guardrails.max_turns = 5
    entry.guardrails.max_session_tokens = 1000
    entry.guardrails.warn_threshold = 0.8
    handler = LLMAgentHandler(entry)

    handler._total_tokens_estimate = 1000
    err = handler._check_guardrails()
    assert err is not None
    assert "exhausted" in err

    handler._total_tokens_estimate = 800
    err = handler._check_guardrails()
    assert err is None  # Warns but doesn't abort

@pytest.mark.asyncio
async def test_run_success():
    entry = MagicMock()
    entry.id = "agent-1"
    entry.name = "Test Agent"
    entry.provider = "ollama"
    entry.resolved_model = "llama3"
    entry.intent = "code"
    entry.system_prompt = "SysPrompt"
    entry.guardrails.max_turns = 5
    entry.guardrails.max_session_tokens = 10000
    entry.guardrails.warn_threshold = 0.8

    handler = LLMAgentHandler(entry)

    req = MagicMock()
    req.prompt = "Write code"
    req.context = {"file": "main.py"}

    mock_llm = MagicMock()
    mock_llm.complete = AsyncMock(return_value="Code output")

    import sys

    mock_module = MagicMock()
    mock_module.LLMProvider = MagicMock(return_value=mock_llm)

    with patch.dict("sys.modules", {"babylon60.extensions.llm.provider": mock_module}):
        res = await handler.run(req)

    assert res["status"] == "OK"
    assert res["text"] == "Code output"
    assert handler.turn_count == 1
    assert len(handler._history) == 2

@pytest.mark.asyncio
async def test_run_guardrail_abort():
    entry = MagicMock()
    entry.guardrails.max_turns = 1
    handler = LLMAgentHandler(entry)
    handler._turn_count = 1

    req = MagicMock()
    res = await handler.run(req)

    assert res["status"] == "GUARDRAIL_ABORT"

def test_reset():
    entry = MagicMock()
    handler = LLMAgentHandler(entry)
    handler._turn_count = 5
    handler._history = [{"a": "b"}]
    handler._total_tokens_estimate = 500

    handler.reset()
    assert handler.turn_count == 0
    assert handler._history == []
    assert handler._total_tokens_estimate == 0
