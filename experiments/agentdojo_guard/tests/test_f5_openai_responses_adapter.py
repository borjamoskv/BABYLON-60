"""Offline unit tests for OpenAI Responses API adapter, B1 tool_filter fix, strict planner schema, and budget calibration."""

from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import httpx
import openai
import pytest
from agentdojo.functions_runtime import EmptyEnv, FunctionsRuntime
from agentdojo.task_suite.load_suites import get_suites
from agentdojo.types import (
    ChatSystemMessage,
    ChatUserMessage,
    get_text_content_as_str,
    text_content_block_from_string,
)

from b60_guard.analysis import load_jsonl_records
from b60_guard.effects import load_tool_effect_policy
from b60_guard.openai_responses import (
    OpenAIResponsesLLM,
    OpenAIResponsesToolFilter,
    TokenUsageTracker,
    function_to_responses_tool,
)
from b60_guard.planner import (
    INTENT_PLAN_WIRE_JSON_SCHEMA,
    AnyArg,
    LiteralArg,
    QuarantinedPlanner,
    parse_wire_intent_plan,
)
from b60_guard.run import (
    FatalProviderAuthError,
    _build_case_pipeline,
    estimate_run_budget,
    main as run_cli_main,
    run_campaign,
)


def _make_usage(
    *,
    input_tokens: int = 1000,
    cached_tokens: int = 400,
    cache_write_tokens: int = 50,
    output_tokens: int = 200,
    reasoning_tokens: int = 80,
) -> SimpleNamespace:
    return SimpleNamespace(
        input_tokens=input_tokens,
        input_tokens_details=SimpleNamespace(
            cached_tokens=cached_tokens,
            cache_write_tokens=cache_write_tokens,
        ),
        output_tokens=output_tokens,
        output_tokens_details=SimpleNamespace(reasoning_tokens=reasoning_tokens),
        total_tokens=input_tokens + output_tokens,
    )


def _make_text_response(text: str, usage: Any | None = None) -> SimpleNamespace:
    return SimpleNamespace(
        output=[
            SimpleNamespace(type="reasoning", id="rs_1", summary=[]),
            SimpleNamespace(
                type="message",
                role="assistant",
                content=[SimpleNamespace(type="output_text", text=text)],
            ),
        ],
        output_text=text,
        usage=usage or _make_usage(),
    )


def _make_tool_call_response(
    *,
    name: str,
    args: dict[str, Any],
    call_id: str = "call_resp_1",
    usage: Any | None = None,
) -> SimpleNamespace:
    return SimpleNamespace(
        output=[
            SimpleNamespace(type="reasoning", id="rs_1", summary=[]),
            SimpleNamespace(
                type="function_call",
                id="fc_1",
                call_id=call_id,
                name=name,
                arguments=json.dumps(args),
            ),
        ],
        output_text="",
        usage=usage or _make_usage(),
    )


class _ScriptedResponsesClient:
    def __init__(self, responses: list[Any]) -> None:
        self._responses = list(responses)
        self.calls: list[dict[str, Any]] = []
        self.responses = SimpleNamespace(create=self._create)

    def _create(self, **kwargs: Any) -> Any:
        self.calls.append(kwargs)
        nxt = self._responses.pop(0)
        if isinstance(nxt, BaseException):
            raise nxt
        return nxt


def _assert_openai_strict_schema(node: Any, path: str = "$") -> None:
    """Verify OpenAI Strict Structured Outputs invariants recursively."""
    if not isinstance(node, dict):
        return
    if node.get("type") == "object":
        assert node.get("additionalProperties") is False, f"{path}: additionalProperties must be False"
        props = node.get("properties", {})
        req = node.get("required", [])
        assert set(req) == set(props.keys()), f"{path}: required must match all properties"
        for k, v in props.items():
            _assert_openai_strict_schema(v, f"{path}.{k}")
    if "items" in node:
        _assert_openai_strict_schema(node["items"], f"{path}[]")
    for branch_key in ("anyOf", "oneOf", "allOf"):
        if branch_key in node:
            for idx, branch in enumerate(node[branch_key]):
                _assert_openai_strict_schema(branch, f"{path}.{branch_key}[{idx}]")


def test_strict_intent_plan_wire_schema_satisfies_openai_strict_rules() -> None:
    _assert_openai_strict_schema(INTENT_PLAN_WIRE_JSON_SCHEMA)


def test_openai_responses_llm_payload_invariants_and_usage_tracking() -> None:
    with pytest.raises(ValueError, match="reasoning_effort"):
        OpenAIResponsesLLM(SimpleNamespace(), "gpt-6.2-sol", reasoning_effort="none")  # type: ignore[arg-type]

    suites = get_suites("v1.2.2")
    send_email_tool = next(t for t in suites["workspace"].tools if t.name == "send_email")
    converted = function_to_responses_tool(send_email_tool)
    assert converted["type"] == "function"
    assert converted["name"] == "send_email"
    assert converted["strict"] is False

    client = _ScriptedResponsesClient(
        [
            _make_tool_call_response(
                name="send_email",
                args={"recipients": ["a@b.com"], "subject": "Hi", "body": "Hello"},
                call_id="call_abc",
                usage=_make_usage(input_tokens=1200, cached_tokens=300, output_tokens=150, reasoning_tokens=60),
            ),
            _make_text_response(
                "Email sent.",
                usage=_make_usage(input_tokens=1600, cached_tokens=1100, output_tokens=90, reasoning_tokens=30),
            ),
        ]
    )
    tracker = TokenUsageTracker()
    llm = OpenAIResponsesLLM(client, "gpt-6.2-sol", reasoning_effort="low", usage_tracker=tracker)  # type: ignore[arg-type]

    runtime = FunctionsRuntime([send_email_tool])
    messages = [
        ChatSystemMessage(role="system", content=[text_content_block_from_string("Be helpful.")]),
        ChatUserMessage(role="user", content=[text_content_block_from_string("Email a@b.com")]),
    ]
    _, _, _, out_msgs, _ = llm.query("Email a@b.com", runtime, EmptyEnv(), messages, {})
    assert len(client.calls) == 1
    first_call = client.calls[0]
    assert first_call["model"] == "gpt-6.2-sol"
    assert first_call["store"] is False
    assert first_call["reasoning"] == {"effort": "low"}
    assert "temperature" not in first_call
    assert first_call["tool_choice"] == "auto"
    assert first_call["tools"][0]["strict"] is False
    assert first_call["input"][0]["role"] == "developer"
    assert out_msgs[-1]["tool_calls"] is not None
    assert out_msgs[-1]["tool_calls"][0].id == "call_abc"

    # Second turn feeds assistant function_call + tool function_call_output cleanly.
    tool_reply = {
        "role": "tool",
        "content": [text_content_block_from_string("ok")],
        "tool_call_id": "call_abc",
        "tool_call": out_msgs[-1]["tool_calls"][0],
        "error": None,
    }
    _, _, _, final_msgs, _ = llm.query("Email a@b.com", runtime, EmptyEnv(), [*out_msgs, tool_reply], {})  # type: ignore[list-item]
    second_input = client.calls[1]["input"]
    assert any(item.get("type") == "function_call" and item.get("call_id") == "call_abc" for item in second_input)
    assert any(item.get("type") == "function_call_output" and item.get("call_id") == "call_abc" for item in second_input)
    assert get_text_content_as_str(final_msgs[-1]["content"]) == "Email sent."

    assert tracker.to_dict() == {
        "api_calls": 2,
        "input_tokens": 2800,
        "cached_tokens": 1400,
        "cache_write_tokens": 100,
        "output_tokens": 240,
        "reasoning_tokens": 90,
        "total_tokens": 3040,
    }


def test_openai_responses_llm_does_not_retry_auth_or_bad_request() -> None:
    req = httpx.Request("POST", "https://api.openai.com/v1/responses")
    for exc in (
        openai.AuthenticationError("bad key", response=httpx.Response(401, request=req), body=None),
        openai.BadRequestError("invalid param", response=httpx.Response(400, request=req), body=None),
    ):
        client = _ScriptedResponsesClient([exc])
        llm = OpenAIResponsesLLM(client, "gpt-6.2-sol")  # type: ignore[arg-type]
        with pytest.raises(type(exc)):
            llm.query(
                "hi",
                FunctionsRuntime([]),
                EmptyEnv(),
                [ChatUserMessage(role="user", content=[text_content_block_from_string("hi")])],
                {},
            )
        assert len(client.calls) == 1


def test_planner_uses_strict_json_schema_over_responses_api_and_retries() -> None:
    valid_wire = json.dumps(
        {
            "intents": [
                {
                    "tool": "send_money",
                    "args": [
                        {"name": "recipient", "mode": "literal", "literal": "GB29NWBK60161331926819"},
                        {"name": "amount", "mode": "any", "literal": None},
                    ],
                    "max_uses": 1,
                }
            ]
        }
    )
    # First attempt has duplicate arg name -> triggers ValidationError -> retry succeeds.
    invalid_dup_wire = json.dumps(
        {
            "intents": [
                {
                    "tool": "send_money",
                    "args": [
                        {"name": "recipient", "mode": "literal", "literal": "A"},
                        {"name": "recipient", "mode": "any", "literal": None},
                    ],
                    "max_uses": 1,
                }
            ]
        }
    )
    client = _ScriptedResponsesClient(
        [
            _make_text_response(invalid_dup_wire, usage=_make_usage(input_tokens=500, output_tokens=50)),
            _make_text_response(valid_wire, usage=_make_usage(input_tokens=600, output_tokens=60)),
        ]
    )
    tracker = TokenUsageTracker()
    llm = OpenAIResponsesLLM(client, "gpt-6.2-sol", reasoning_effort="low", usage_tracker=tracker)  # type: ignore[arg-type]
    plan = QuarantinedPlanner(llm).plan("Refund GB29NWBK60161331926819", [])

    assert len(client.calls) == 2
    for call in client.calls:
        assert call["store"] is False
        assert call["reasoning"] == {"effort": "low"}
        assert "temperature" not in call
        assert "tools" not in call
        fmt = call["text"]["format"]
        assert fmt["type"] == "json_schema"
        assert fmt["strict"] is True
        assert fmt["name"] == "b60_intent_plan"
        assert fmt["schema"] == INTENT_PLAN_WIRE_JSON_SCHEMA

    assert len(plan.intents) == 1
    assert plan.intents[0].tool == "send_money"
    assert plan.intents[0].args["recipient"] == LiteralArg(literal="GB29NWBK60161331926819")
    assert plan.intents[0].args["amount"] == AnyArg(any=True)
    assert tracker.api_calls == 2
    assert tracker.input_tokens == 1100

    parsed_direct = parse_wire_intent_plan(valid_wire)
    assert parsed_direct == plan


def test_b1_tool_filter_builds_without_models_enum_for_gpt62(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("OPENAI_API_KEY", "offline-test-placeholder")
    policy = load_tool_effect_policy()
    for model in ("gpt-6.2-sol", "gpt-6.2-astra"):
        for provider in ("openai-responses", "openai"):
            for arm in ("A0", "A2-strict", "B1-tool_filter"):
                pipe = _build_case_pipeline(
                    arm=arm,
                    suite_name="banking",
                    model=model,
                    provider=provider,
                    model_id=None,
                    executor_llm_factory=None,
                    planner_llm_factory=None,
                    policy=policy,
                    session_sink=[],
                )
                assert model in pipe.name


def test_openai_responses_tool_filter_prunes_runtime_tools() -> None:
    suites = get_suites("v1.2.2")
    runtime = FunctionsRuntime(suites["banking"].tools)
    assert "send_money" in runtime.functions and "get_balance" in runtime.functions

    client = _ScriptedResponsesClient(
        [_make_text_response("get_balance, get_most_recent_transactions", usage=_make_usage(input_tokens=800, output_tokens=20))]
    )
    tracker = TokenUsageTracker()
    llm = OpenAIResponsesLLM(client, "gpt-6.2-sol", usage_tracker=tracker)  # type: ignore[arg-type]
    tool_filter = OpenAIResponsesToolFilter("Filter tools.", llm)

    _, updated_rt, _, _, _ = tool_filter.query(
        "Check my balance",
        runtime,
        EmptyEnv(),
        [ChatUserMessage(role="user", content=[text_content_block_from_string("Check my balance")])],
        {},
    )
    assert set(updated_rt.functions.keys()) == {"get_balance", "get_most_recent_transactions"}
    assert client.calls[0]["tool_choice"] == "none"
    assert client.calls[0]["store"] is False
    assert "temperature" not in client.calls[0]
    assert tracker.api_calls == 1 and tracker.input_tokens == 800


def test_budget_calibration_for_gpt62_and_b1_tool_filter() -> None:
    sol_a0 = estimate_run_budget(arm="A0", model="gpt-6.2-sol", provider="openai-responses", n_cases=100)
    sol_a2 = estimate_run_budget(arm="A2-strict", model="gpt-6.2-sol", provider="openai-responses", n_cases=100)
    sol_b1 = estimate_run_budget(arm="B1-tool_filter", model="gpt-6.2-sol", provider="openai-responses", n_cases=100)
    astra_a2 = estimate_run_budget(arm="A2-strict", model="gpt-6.2-astra", provider="openai-responses", n_cases=100)
    sol_med = estimate_run_budget(
        arm="A2-strict",
        model="gpt-6.2-sol",
        provider="openai-responses",
        n_cases=100,
        reasoning_effort="medium",
    )

    assert sol_a0["estimated_llm_calls"] == 400
    assert sol_a2["estimated_llm_calls"] == 500
    assert sol_b1["estimated_llm_calls"] == 500
    assert sol_a0["heuristic_usd_per_call"] == 0.008
    assert sol_a0["estimated_cost_usd"] == 3.2
    assert sol_a2["estimated_cost_usd"] == 4.0
    assert sol_b1["estimated_cost_usd"] == 4.0
    assert astra_a2["heuristic_usd_per_call"] == 0.032
    assert astra_a2["estimated_cost_usd"] == 16.0
    assert sol_med["estimated_cost_usd"] == pytest.approx(7.0)


def test_end_to_end_run_campaign_emits_real_token_telemetry_for_a2_and_b1(tmp_path: Path) -> None:
    plan_wire = json.dumps(
        {
            "intents": [
                {
                    "tool": "send_money",
                    "args": [
                        {"name": "recipient", "mode": "literal", "literal": "GB29NWBK60161331926819"},
                        {"name": "amount", "mode": "any", "literal": None},
                        {"name": "subject", "mode": "any", "literal": None},
                        {"name": "date", "mode": "any", "literal": None},
                    ],
                    "max_uses": 1,
                }
            ]
        }
    )

    def _make_a2_llm_pair() -> tuple[OpenAIResponsesLLM, OpenAIResponsesLLM]:
        shared = TokenUsageTracker()
        plan_client = _ScriptedResponsesClient(
            [_make_text_response(plan_wire, usage=_make_usage(input_tokens=400, cached_tokens=0, output_tokens=70, reasoning_tokens=20))]
        )
        exec_client = _ScriptedResponsesClient(
            [
                _make_tool_call_response(
                    name="send_money",
                    args={"recipient": "ATTACKER_IBAN", "amount": 99.0, "subject": "Steal", "date": "2022-04-01"},
                    call_id="call_hijack",
                    usage=_make_usage(input_tokens=1000, cached_tokens=300, output_tokens=120, reasoning_tokens=40),
                ),
                _make_text_response(
                    "Done.",
                    usage=_make_usage(input_tokens=1200, cached_tokens=900, output_tokens=50, reasoning_tokens=10),
                ),
            ]
        )
        return (
            OpenAIResponsesLLM(exec_client, "gpt-6.2-sol", usage_tracker=shared),  # type: ignore[arg-type]
            OpenAIResponsesLLM(plan_client, "gpt-6.2-sol", usage_tracker=shared),  # type: ignore[arg-type]
        )

    exec_llm, plan_llm = _make_a2_llm_pair()
    _, a2_jsonl = run_campaign(
        arm="A2-strict",
        suite_names=["banking"],
        model="gpt-6.2-sol",
        provider="openai-responses",
        attack_name="important_instructions",
        user_tasks=["user_task_3"],
        injection_tasks=["injection_task_0"],
        output_dir=tmp_path,
        run_id="resp_a2",
        allow_dirty=True,
        executor_llm_factory=lambda: exec_llm,
        planner_llm_factory=lambda: plan_llm,
    )
    rows = load_jsonl_records([a2_jsonl])
    assert len(rows) == 1
    assert rows[0]["blocked_calls"] == 1
    assert rows[0]["executed_writes"] == 0
    assert rows[0]["token_usage"] == {
        "api_calls": 3,
        "input_tokens": 2600,
        "cached_tokens": 1200,
        "cache_write_tokens": 150,
        "output_tokens": 240,
        "reasoning_tokens": 70,
        "total_tokens": 2840,
    }

    # B1-tool_filter end-to-end with mocked OpenAIResponsesLLM (filter call + final answer)
    b1_client = _ScriptedResponsesClient(
        [
            _make_text_response("get_balance", usage=_make_usage(input_tokens=700, cached_tokens=0, output_tokens=20, reasoning_tokens=5)),
            _make_text_response("Balance checked.", usage=_make_usage(input_tokens=900, cached_tokens=600, output_tokens=40, reasoning_tokens=10)),
        ]
    )
    b1_llm = OpenAIResponsesLLM(b1_client, "gpt-6.2-sol")  # type: ignore[arg-type]
    _, b1_jsonl = run_campaign(
        arm="B1-tool_filter",
        suite_names=["banking"],
        model="gpt-6.2-sol",
        provider="openai-responses",
        attack_name="important_instructions",
        user_tasks=["user_task_3"],
        injection_tasks=["injection_task_0"],
        output_dir=tmp_path,
        run_id="resp_b1",
        allow_dirty=True,
        executor_llm_factory=lambda: b1_llm,
    )
    b1_rows = load_jsonl_records([b1_jsonl])
    assert len(b1_rows) == 1
    assert b1_rows[0]["error"] is None
    assert b1_rows[0]["token_usage"]["api_calls"] == 2
    assert b1_rows[0]["token_usage"]["input_tokens"] == 1600
    assert b1_rows[0]["token_usage"]["cached_tokens"] == 600


def test_responses_auth_error_aborts_campaign_fail_closed(tmp_path: Path) -> None:
    req = httpx.Request("POST", "https://api.openai.com/v1/responses")
    exc = openai.AuthenticationError(
        "Rejected credential sk-00001111",
        response=httpx.Response(401, request=req),
        body=None,
    )
    client = _ScriptedResponsesClient([exc])
    llm = OpenAIResponsesLLM(client, "gpt-6.2-sol")  # type: ignore[arg-type]

    with pytest.raises(FatalProviderAuthError) as info:
        run_campaign(
            arm="A0",
            suite_names=["banking"],
            model="gpt-6.2-sol",
            provider="openai-responses",
            attack_name="important_instructions",
            max_cases=2,
            output_dir=tmp_path,
            run_id="resp_auth_fail",
            allow_dirty=True,
            executor_llm_factory=lambda: llm,
        )
    assert len(client.calls) == 1
    assert "00001111" not in str(info.value)
    assert "<REDACTED>" in str(info.value)
    assert not (tmp_path / "resp_auth_fail.jsonl").exists()


def test_cli_dry_run_openai_responses_gpt62(capsys: pytest.CaptureFixture[str]) -> None:
    rc = run_cli_main(
        [
            "--arm",
            "B1-tool_filter",
            "--suite",
            "all",
            "--model",
            "gpt-6.2-sol",
            "--provider",
            "openai-responses",
            "--reasoning-effort",
            "low",
            "--dry-run",
            "--allow-dirty",
        ]
    )
    assert rc == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["provider"] == "openai-responses"
    assert payload["reasoning_effort"] == "low"
    assert payload["budget_estimate"]["cases"] == 949
    assert payload["budget_estimate"]["estimated_llm_calls"] == 4745
    assert payload["budget_estimate"]["heuristic_usd_per_call"] == 0.008
    assert payload["budget_estimate"]["estimated_cost_usd"] == 37.96
