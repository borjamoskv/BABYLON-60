"""C+/C- controls on 3 banking tasks and §6 broker properties beyond AgentDojo."""

from __future__ import annotations

import json
from collections.abc import Sequence
from typing import Any

import pytest
from agentdojo.agent_pipeline.base_pipeline_element import BasePipelineElement
from agentdojo.functions_runtime import EmptyEnv, Env, FunctionCall, FunctionsRuntime
from agentdojo.task_suite.load_suites import get_suites
from agentdojo.types import ChatAssistantMessage, ChatMessage, text_content_block_from_string

from b60_guard.canon import bind_use_index, canonicalize_args
from b60_guard.contracts import GuardSession
from b60_guard.effects import extract_tool_specs, load_tool_effect_policy
from b60_guard.native import blake3_bytes, new_native_broker
from b60_guard.pipeline import build_guarded_pipeline
from b60_guard.planner import IntentPlan, StaticPlanner
from b60_guard.run import main as run_cli_main


class _TaskReplayExecutor(BasePipelineElement):
    """Deterministically emits a user task's tool calls without calling an external LLM."""

    name = "task-replay-executor"

    def __init__(self, calls: list[FunctionCall], final_text: str) -> None:
        self._calls = calls
        self._final_text = final_text
        self._idx = 0

    def query(
        self,
        query: str,
        runtime: FunctionsRuntime,
        env: Env = EmptyEnv(),
        messages: Sequence[ChatMessage] = (),
        extra_args: dict[str, Any] = {},
    ) -> tuple[str, FunctionsRuntime, Env, Sequence[ChatMessage], dict[str, Any]]:
        if self._idx < len(self._calls):
            call = self._calls[self._idx]
            self._idx += 1
            call_copy = FunctionCall(function=call.function, args=dict(call.args), id=f"gt_{self._idx}")
            msg = ChatAssistantMessage(
                role="assistant",
                content=[text_content_block_from_string("")],
                tool_calls=[call_copy],
            )
            return query, runtime, env, [*messages, msg], extra_args
        done = ChatAssistantMessage(
            role="assistant",
            content=[text_content_block_from_string(self._final_text)],
            tool_calls=None,
        )
        return query, runtime, env, [*messages, done], extra_args


@pytest.mark.parametrize("task_id", ["user_task_0", "user_task_2", "user_task_3"])
def test_positive_and_negative_controls_on_banking_tasks(task_id: str) -> None:
    suite = get_suites("v1.2.2")["banking"]
    policy = load_tool_effect_policy()
    task = suite.user_tasks[task_id]

    def run_for_arm(arm: str) -> tuple[Any, Any, bool, GuardSession]:
        env = task.init_environment(suite.load_and_inject_default_environment({}))
        pre_env = env.model_copy(deep=True)
        gt_calls = task.ground_truth(pre_env)
        sessions: list[GuardSession] = []
        pipe = build_guarded_pipeline(
            arm=arm,  # type: ignore[arg-type]
            suite_name="banking",
            executor_llm=_TaskReplayExecutor(gt_calls, task.GROUND_TRUTH_OUTPUT or "done"),
            planner=StaticPlanner(lambda q, s: IntentPlan()),
            policy=policy,
            session_sink=sessions,
        )
        _, _, post_env, _, _ = pipe.query(task.PROMPT, FunctionsRuntime(suite.tools), env)
        util = task.utility(task.GROUND_TRUTH_OUTPUT or "done", pre_env, post_env)
        return pre_env, post_env, util, sessions[0]

    pre_a0, post_a0, util_a0, _ = run_for_arm("A0")
    pre_cm, post_cm, util_cm, _ = run_for_arm("C-")
    pre_cp, post_cp, util_cp, sess_cp = run_for_arm("C+")

    # C- reproduces A0 identically.
    assert util_a0 is True
    assert util_cm == util_a0
    assert post_cm.model_dump() == post_a0.model_dump()

    # C+ leaves environment untouched (zero writes) and zero utility.
    assert pre_cp.model_dump() == post_cp.model_dump()
    assert util_cp is False
    assert all(not r.allowed for r in sess_cp.records)


def test_broker_properties_beyond_agentdojo() -> None:
    """§6: code hash tamper detection, mid-task revocation, and token reuse denial."""
    suite = get_suites("v1.2.2")["banking"]
    policy = load_tool_effect_policy()
    specs = extract_tool_specs("banking", {t.name: t for t in suite.tools}, policy)
    spec = specs["send_money"]
    assert spec.effect == "NetTransmit"

    broker = new_native_broker()
    broker.discover(spec.name, spec.code_hash, spec.effect, spec.scope)
    broker.authorize(spec.name, spec.code_hash, spec.effect, spec.scope)

    bound = bind_use_index(
        canonicalize_args({"recipient": "GB29", "amount": 10.0, "subject": "s", "date": "2022-04-01"}),
        0,
    )
    tok1 = broker.issue(spec.name, spec.code_hash, spec.effect, bound, spec.scope, spec.scope)
    tok2 = broker.issue(spec.name, spec.code_hash, spec.effect, bound, spec.scope, spec.scope)

    # 1) Tool implementation replacement (tampered code_hash) -> rejected.
    tampered_hash = blake3_bytes(b"def send_money_backdoored(): pass")
    with pytest.raises(PermissionError, match="ToolIdentityMismatch"):
        broker.commit_once(tok1, spec.name, tampered_hash, spec.effect, bound, spec.scope, spec.scope)

    # 2) Valid commit produces 32B evidence, second use of tok1 fails replay check.
    ev = broker.commit_once(tok1, spec.name, spec.code_hash, spec.effect, bound, spec.scope, spec.scope)
    assert len(ev) == 32
    with pytest.raises(PermissionError, match="NonceAlreadyConsumed"):
        broker.commit_once(tok1, spec.name, spec.code_hash, spec.effect, bound, spec.scope, spec.scope)

    # 3) Mid-task revocation invalidates outstanding tok2 via epoch advance.
    broker.revoke(spec.name)
    with pytest.raises(PermissionError):
        broker.commit_once(tok2, spec.name, spec.code_hash, spec.effect, bound, spec.scope, spec.scope)


def test_cli_dry_run_emits_manifest_and_blocks_live_without_approval(capsys: pytest.CaptureFixture[str]) -> None:
    rc = run_cli_main(
        ["--arm", "A2-strict", "--suite", "banking", "--model", "dry-run", "--dry-run", "--allow-dirty"]
    )
    assert rc == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["arm"] == "A2-strict"
    assert payload["tool_effects_count"] == 74
    assert payload["policy_seal_verified"] is True

    with pytest.raises(SystemExit, match="confirm-budget-usd"):
        run_cli_main(["--arm", "A2-strict", "--suite", "banking", "--model", "gpt-4o", "--allow-dirty"])
