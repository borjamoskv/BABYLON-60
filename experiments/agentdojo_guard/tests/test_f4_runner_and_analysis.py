"""Offline unit tests for runner (run.py), statistics (analysis.py), and budget gates (zero API cost)."""

from __future__ import annotations

import json
from collections.abc import Sequence
from pathlib import Path
from typing import Any

import httpx
import openai
import pytest
from agentdojo.agent_pipeline.base_pipeline_element import BasePipelineElement
from agentdojo.functions_runtime import EmptyEnv, Env, FunctionCall, FunctionsRuntime
from agentdojo.types import ChatAssistantMessage, ChatMessage, text_content_block_from_string

from b60_guard.analysis import (
    compare_arms,
    holm_bonferroni,
    load_jsonl_records,
    mcnemar_exact,
    preregistered_sota_verdict,
    render_frontier_svg,
    render_markdown_table,
    summarize_records,
    wilson_ci,
)
from b60_guard.run import FatalProviderAuthError, estimate_run_budget, main as run_cli_main, run_campaign


class _MockDualLLM(BasePipelineElement):
    """Serves either QuarantinedPlanner JSON or scripted executor tool calls without network calls."""

    name = "gpt-4o-2024-05-13"

    def __init__(self, *, mode: str) -> None:
        self._mode = mode

    def query(
        self,
        query: str,
        runtime: FunctionsRuntime,
        env: Env = EmptyEnv(),
        messages: Sequence[ChatMessage] = (),
        extra_args: dict[str, Any] = {},
    ) -> tuple[str, FunctionsRuntime, Env, Sequence[ChatMessage], dict[str, Any]]:
        if len(runtime.functions) == 0:
            # Planner call: strictly authorize refund recipient from query.
            plan_json = json.dumps(
                {
                    "intents": [
                        {
                            "tool": "send_money",
                            "args": {
                                "recipient": {"literal": "GB29NWBK60161331926819"},
                                "amount": {"any": True},
                                "subject": {"any": True},
                                "date": {"any": True},
                            },
                            "max_uses": 1,
                        }
                    ]
                }
            )
            reply = ChatAssistantMessage(
                role="assistant",
                content=[text_content_block_from_string(plan_json)],
                tool_calls=None,
            )
            return query, runtime, env, [*messages, reply], extra_args

        tool_msgs = [m for m in messages if m["role"] == "tool"]
        if not tool_msgs:
            # Executor attempts an injected transfer to an attacker IBAN, or benign refund depending on mode.
            target = "ATTACKER_IBAN" if self._mode == "hijacked" else "GB29NWBK60161331926819"
            call = FunctionCall(
                function="send_money",
                args={"recipient": target, "amount": 4.0, "subject": "Refund", "date": "2022-04-01"},
                id="call_1",
            )
            reply = ChatAssistantMessage(
                role="assistant",
                content=[text_content_block_from_string("")],
                tool_calls=[call],
            )
            return query, runtime, env, [*messages, reply], extra_args

        done = ChatAssistantMessage(
            role="assistant",
            content=[text_content_block_from_string("Your total spending in March 2022 was 1,050.")],
            tool_calls=None,
        )
        return query, runtime, env, [*messages, done], extra_args


def test_wilson_mcnemar_and_holm_math() -> None:
    iv = wilson_ci(0, 100)
    assert iv.rate == 0.0 and iv.lower == 0.0
    assert 0.03 < iv.upper < 0.04

    iv_half = wilson_ci(50, 100)
    assert abs(iv_half.rate - 0.5) < 1e-12
    assert 0.40 < iv_half.lower < 0.41 and 0.59 < iv_half.upper < 0.60

    # 10 discordant pairs all favoring A vs B -> 2 / 2^10 = 0.001953125
    b_only, c_only, p = mcnemar_exact([True] * 10 + [False] * 5, [False] * 10 + [False] * 5)
    assert (b_only, c_only) == (10, 0)
    assert abs(p - (2.0 / 1024.0)) < 1e-12

    # Large n_disc (> 900) uses log-space without float overflow.
    b_big, c_big, p_big = mcnemar_exact([True] * 950, [False] * 950)
    assert (b_big, c_big) == (950, 0) and 0.0 <= p_big < 1e-10

    adj = holm_bonferroni([0.04, 0.01, 0.03])
    assert pytest.approx(adj) == [0.06, 0.03, 0.06]


def test_budget_gate_and_dry_run_refuse_unconfirmed_live_calls(capsys: pytest.CaptureFixture[str]) -> None:
    rc = run_cli_main(
        [
            "--arm",
            "A2c",
            "--suite",
            "banking",
            "--model",
            "gpt-4o-mini-2024-07-18",
            "--max-cases",
            "5",
            "--dry-run",
            "--allow-dirty",
        ]
    )
    assert rc == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["budget_estimate"]["cases"] == 5
    assert payload["budget_estimate"]["estimated_llm_calls"] == 25
    assert payload["budget_estimate"]["estimate_heuristic_only"] is True

    with pytest.raises(SystemExit, match="confirm-budget-usd"):
        run_cli_main(["--arm", "A2c", "--suite", "banking", "--model", "gpt-4o-mini-2024-07-18", "--max-cases", "2"])

    est = estimate_run_budget(arm="A2-strict", model="local", provider="local", n_cases=10)
    assert est["estimated_cost_usd"] == 0.0


def test_end_to_end_run_campaign_and_analysis_offline(tmp_path: Path) -> None:
    # Run paired cases on banking across A0, A2c, and benign A2c using deterministic mock LLMs.
    _, a0_jsonl = run_campaign(
        arm="A0",
        suite_names=["banking"],
        model="gpt-4o-2024-05-13",
        attack_name="important_instructions",
        user_tasks=["user_task_3"],
        injection_tasks=["injection_task_0", "injection_task_1"],
        output_dir=tmp_path,
        run_id="a0_test",
        allow_dirty=True,
        executor_llm_factory=lambda: _MockDualLLM(mode="hijacked"),
    )
    _, a2c_jsonl = run_campaign(
        arm="A2c",
        suite_names=["banking"],
        model="gpt-4o-2024-05-13",
        attack_name="important_instructions",
        user_tasks=["user_task_3"],
        injection_tasks=["injection_task_0", "injection_task_1"],
        output_dir=tmp_path,
        run_id="a2c_test",
        allow_dirty=True,
        executor_llm_factory=lambda: _MockDualLLM(mode="hijacked"),
    )
    _, a2c_benign_jsonl = run_campaign(
        arm="A2c",
        suite_names=["banking"],
        model="gpt-4o-2024-05-13",
        attack_name="none",
        user_tasks=["user_task_3"],
        output_dir=tmp_path,
        run_id="a2c_benign",
        allow_dirty=True,
        executor_llm_factory=lambda: _MockDualLLM(mode="benign"),
    )

    records = load_jsonl_records([a0_jsonl, a2c_jsonl, a2c_benign_jsonl])
    assert len(records) == 5

    # In A2c hijacked run, send_money to ATTACKER_IBAN is blocked (0 executed writes); benign succeeds with receipt.
    a2c_attack_rows = [r for r in records if r["arm"] == "A2c" and r["attack"] != "none"]
    assert all(r["executed_writes"] == 0 and r["blocked_calls"] == 1 for r in a2c_attack_rows)

    a2c_benign_rows = [r for r in records if r["arm"] == "A2c" and r["attack"] == "none"]
    assert len(a2c_benign_rows) == 1
    assert a2c_benign_rows[0]["utility"] is True
    assert a2c_benign_rows[0]["executed_writes"] == 1
    assert a2c_benign_rows[0]["writes_with_receipt"] == 1
    assert len(a2c_benign_rows[0]["receipts_hex"][0]) == 64

    summaries = summarize_records(records)
    comps = compare_arms(records, reference_arm="A0", metric="targeted_asr")
    md = render_markdown_table(summaries, comps)
    assert "A2c" in md and "A0" in md

    a2c_summary = next(s for s in summaries if s.arm == "A2c" and s.attack != "none")
    verdict = preregistered_sota_verdict(candidate=a2c_summary, same_model_camel=None, utility_comparison=None)
    assert verdict.startswith("NO_SAME_MODEL_CAMEL_RERUN")

    svg = render_frontier_svg(summaries)
    assert svg.startswith("<svg ") and "A2c" in svg


class _AuthFailingLLM(BasePipelineElement):
    """Simulates a provider 401/403 failure without touching external endpoints."""

    name = "gpt-4o-mini-2024-07-18"

    def __init__(self, exc_factory: Any, counter: list[int]) -> None:
        self._exc_factory = exc_factory
        self._counter = counter

    def query(
        self,
        query: str,
        runtime: FunctionsRuntime,
        env: Env = EmptyEnv(),
        messages: Sequence[ChatMessage] = (),
        extra_args: dict[str, Any] = {},
    ) -> tuple[str, FunctionsRuntime, Env, Sequence[ChatMessage], dict[str, Any]]:
        self._counter.append(1)
        raise self._exc_factory()


@pytest.mark.parametrize("status_code", [401, 403])
def test_fatal_auth_and_permission_errors_abort_fail_closed(tmp_path: Path, status_code: int) -> None:
    req = httpx.Request("POST", "https://api.openai.com/v1/chat/completions")
    resp = httpx.Response(status_code, request=req)
    calls: list[int] = []

    def make_exc() -> Exception:
        if status_code == 401:
            return openai.AuthenticationError(
                "Incorrect API key provided: sk-proj-FAKE_9999",
                response=resp,
                body=None,
            )
        return openai.PermissionDeniedError("Permission denied", response=resp, body=None)

    with pytest.raises(FatalProviderAuthError) as exc_info:
        run_campaign(
            arm="A2c",
            suite_names=["banking"],
            model="gpt-4o-mini-2024-07-18",
            attack_name="important_instructions",
            max_cases=3,
            output_dir=tmp_path,
            run_id=f"auth_{status_code}",
            allow_dirty=True,
            executor_llm_factory=lambda: _AuthFailingLLM(make_exc, calls),
        )

    assert len(calls) == 1
    assert "FAKE_9999" not in str(exc_info.value)
    assert not (tmp_path / f"auth_{status_code}.jsonl").exists()
    assert not (tmp_path / f"auth_{status_code}.manifest.json").exists()


def test_cli_exits_nonzero_on_fatal_auth_error(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    req = httpx.Request("POST", "https://api.openai.com/v1/chat/completions")
    resp = httpx.Response(401, request=req)

    def fake_build(**kwargs: Any) -> Any:
        raise openai.AuthenticationError("Bad key: synthetic-invalid-fixture", response=resp, body=None)

    monkeypatch.setattr("b60_guard.run._build_case_pipeline", fake_build)
    rc = run_cli_main(
        [
            "--arm",
            "A2c",
            "--suite",
            "banking",
            "--model",
            "gpt-4o-mini-2024-07-18",
            "--max-cases",
            "2",
            "--output-dir",
            str(tmp_path),
            "--run-id",
            "cli_auth_fail",
            "--confirm-budget-usd",
            "1.0",
            "--allow-dirty",
        ]
    )
    assert rc == 2
    err = capsys.readouterr().err
    assert "FATAL_AUTH_ERROR" in err
    assert "SECRET9999" not in err
    assert not (tmp_path / "cli_auth_fail.jsonl").exists()
