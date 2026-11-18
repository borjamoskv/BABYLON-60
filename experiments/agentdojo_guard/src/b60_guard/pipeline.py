"""AgentDojo pipeline assembly separating quarantined planning from execution."""

from __future__ import annotations

from collections.abc import Callable, Sequence
from typing import Any

from agentdojo.agent_pipeline.agent_pipeline import (
    AgentPipeline,
    PipelineConfig,
    get_llm,
    load_system_message,
)
from agentdojo.agent_pipeline.base_pipeline_element import BasePipelineElement
from agentdojo.agent_pipeline.basic_elements import InitQuery, SystemMessage
from agentdojo.agent_pipeline.tool_execution import ToolsExecutionLoop, tool_result_to_str
from agentdojo.functions_runtime import EmptyEnv, Env, FunctionReturnType, FunctionsRuntime
from agentdojo.models import MODEL_PROVIDERS, ModelsEnum
from agentdojo.types import ChatMessage

from b60_guard.approver import DenyApprover
from b60_guard.contracts import ApprovalHandler, GuardArm, GuardSession
from b60_guard.effects import ToolEffectPolicy, extract_tool_specs, load_tool_effect_policy
from b60_guard.executor import SESSION_EXTRA_KEY, GuardedToolsExecutor
from b60_guard.issuer import build_guard_session
from b60_guard.native import NativeBroker, blake3_bytes, new_native_broker
from b60_guard.planner import IntentPlan, PlannerBackend


class PlanAndIssueElement(BasePipelineElement):
    """Runs once per task before the executor LLM to issue capabilities from ``query`` alone."""

    def __init__(
        self,
        *,
        arm: GuardArm,
        suite_name: str,
        planner: PlannerBackend | None,
        policy: ToolEffectPolicy,
        blake3_fn: Callable[[bytes], bytes] = blake3_bytes,
        broker_factory: Callable[[], NativeBroker] = new_native_broker,
        approver_factory: Callable[[Callable[[Any, bytes], bytes]], ApprovalHandler] | None = None,
        approver: ApprovalHandler | None = None,
        session_sink: list[GuardSession] | None = None,
    ) -> None:
        self._arm = arm
        self._suite_name = suite_name
        self._planner = planner
        self._policy = policy
        self._blake3_fn = blake3_fn
        self._broker_factory = broker_factory
        self._approver_factory = approver_factory
        self._approver = approver
        self._session_sink = session_sink

    def query(
        self,
        query: str,
        runtime: FunctionsRuntime,
        env: Env = EmptyEnv(),
        messages: Sequence[ChatMessage] = (),
        extra_args: dict[str, Any] | None = None,
    ) -> tuple[str, FunctionsRuntime, Env, Sequence[ChatMessage], dict[str, Any]]:
        specs = extract_tool_specs(
            self._suite_name,
            runtime.functions,
            self._policy,
            blake3_fn=self._blake3_fn,
        )
        if self._arm in ("A0", "C+"):
            plan = IntentPlan()
        else:
            if self._planner is None:
                raise ValueError(f"Guard arm {self._arm} requires a planner")
            # Boundary: ONLY (query, static specs) are passed; env and messages never leave here.
            plan = self._planner.plan(query, list(specs.values()))

        session = build_guard_session(
            self._arm,
            self._suite_name,
            query,
            specs,
            plan,
            broker_factory=self._broker_factory,
            approver_factory=self._approver_factory,
            approver=self._approver or DenyApprover(),
        )
        if self._session_sink is not None:
            self._session_sink.append(session)
        new_extra = dict(extra_args) if extra_args is not None else {}
        new_extra[SESSION_EXTRA_KEY] = session
        return query, runtime, env, messages, new_extra


def build_guarded_pipeline(
    *,
    arm: GuardArm,
    suite_name: str,
    executor_llm: BasePipelineElement,
    planner: PlannerBackend | None = None,
    policy: ToolEffectPolicy | None = None,
    system_message: str | None = None,
    model_name: str | None = None,
    tool_output_formatter: Callable[[FunctionReturnType], str] = tool_result_to_str,
    max_iters: int = 15,
    approver_factory: Callable[[Callable[[Any, bytes], bytes]], ApprovalHandler] | None = None,
    approver: ApprovalHandler | None = None,
    session_sink: list[GuardSession] | None = None,
) -> AgentPipeline:
    """Build an AgentDojo ``AgentPipeline`` mediated by ``GuardedToolsExecutor``."""
    resolved_policy = policy or load_tool_effect_policy()
    sys_msg = system_message if system_message is not None else load_system_message(None)
    plan_and_issue = PlanAndIssueElement(
        arm=arm,
        suite_name=suite_name,
        planner=planner,
        policy=resolved_policy,
        approver_factory=approver_factory,
        approver=approver,
        session_sink=session_sink,
    )
    tools_loop = ToolsExecutionLoop(
        [GuardedToolsExecutor(tool_output_formatter=tool_output_formatter), executor_llm],
        max_iters=max_iters,
    )
    pipeline = AgentPipeline(
        [
            SystemMessage(sys_msg),
            InitQuery(),
            plan_and_issue,
            executor_llm,
            tools_loop,
        ]
    )
    llm_name = (
        model_name
        or getattr(executor_llm, "name", None)
        or getattr(executor_llm, "model", None)
        or type(executor_llm).__name__
    )
    pipeline.name = f"{llm_name}-b60-{arm}"
    return pipeline


def resolve_llm_element(
    *,
    model: str,
    provider: str | None = None,
    model_id: str | None = None,
    tool_delimiter: str = "tool",
) -> tuple[BasePipelineElement, str]:
    """Instantiate an AgentDojo LLM element and return ``(element, canonical_pipeline_model_name)``."""
    if provider is None:
        enum_val = ModelsEnum(model)
        resolved_provider = MODEL_PROVIDERS[enum_val]
        llm = get_llm(resolved_provider, model, model_id, tool_delimiter)
        return llm, model
    llm = get_llm(provider, model, model_id, tool_delimiter)
    return llm, model


def build_baseline_pipeline(
    *,
    llm: str | BasePipelineElement,
    defense: str | None = None,
    model_id: str | None = None,
    model_name: str | None = None,
    system_message: str | None = None,
) -> AgentPipeline:
    """Wrap AgentDojo's standard baseline/defense factory for A0 and B1-B4."""
    config = PipelineConfig(
        llm=llm,
        model_id=model_id,
        defense=defense,
        system_message_name=None,
        system_message=system_message,
    )
    pipeline = AgentPipeline.from_config(config)
    if model_name is not None and not isinstance(llm, str):
        suffix = f"-{defense}" if defense else ""
        pipeline.name = f"{model_name}{suffix}"
    return pipeline
