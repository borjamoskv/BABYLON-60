"""Guarded AgentDojo tool executor. Never imports issuer or task ground truth."""

from __future__ import annotations

from ast import literal_eval
from collections.abc import Callable, Sequence
from typing import Any

from agentdojo.agent_pipeline.llms.google_llm import EMPTY_FUNCTION_NAME
from agentdojo.agent_pipeline.tool_execution import ToolsExecutor, is_string_list, tool_result_to_str
from agentdojo.functions_runtime import EmptyEnv, Env, FunctionReturnType, FunctionsRuntime
from agentdojo.types import ChatMessage, ChatToolResultMessage, text_content_block_from_string
from pydantic import ValidationError

from b60_guard.canon import (
    NestedFunctionCallError,
    UnexpectedToolArgumentError,
    canonicalize_args,
    contains_nested_function_call,
    normalize_tool_args,
)
from b60_guard.contracts import GuardSession, ToolCallTrace

SESSION_EXTRA_KEY = "_b60_guard_session"


def _error_result(tool_call: Any, error: str) -> ChatToolResultMessage:
    return ChatToolResultMessage(
        role="tool",
        content=[text_content_block_from_string("")],
        tool_call_id=tool_call.id,
        tool_call=tool_call,
        error=error,
    )


class GuardedToolsExecutor(ToolsExecutor):
    """Intercepts every tool invocation before ``runtime.run_function`` executes."""

    def __init__(self, tool_output_formatter: Callable[[FunctionReturnType], str] = tool_result_to_str) -> None:
        super().__init__(tool_output_formatter=tool_output_formatter)

    def query(
        self,
        query: str,
        runtime: FunctionsRuntime,
        env: Env = EmptyEnv(),
        messages: Sequence[ChatMessage] = (),
        extra_args: dict[str, Any] | None = None,
    ) -> tuple[str, FunctionsRuntime, Env, Sequence[ChatMessage], dict[str, Any]]:
        extra: dict[str, Any] = dict(extra_args) if extra_args is not None else {}
        if len(messages) == 0 or messages[-1]["role"] != "assistant":
            return query, runtime, env, messages, extra
        tool_calls = messages[-1]["tool_calls"]
        if not tool_calls:
            return query, runtime, env, messages, extra

        session_obj = extra.get(SESSION_EXTRA_KEY)
        session: GuardSession | None = session_obj if isinstance(session_obj, GuardSession) else None
        available_names = {tool.name for tool in runtime.functions.values()}
        tool_call_results: list[ChatToolResultMessage] = []

        for tool_call in tool_calls:
            if tool_call.function == EMPTY_FUNCTION_NAME:
                tool_call_results.append(
                    _error_result(tool_call, "Empty function name provided. Provide a valid function name.")
                )
                continue

            if tool_call.function not in available_names:
                tool_call_results.append(_error_result(tool_call, f"Invalid tool {tool_call.function} provided."))
                continue

            for arg_k, arg_v in list(tool_call.args.items()):
                if isinstance(arg_v, str) and is_string_list(arg_v):
                    tool_call.args[arg_k] = literal_eval(arg_v)

            if session is None:
                tool_call_results.append(
                    _error_result(tool_call, "PermissionError: Missing BABYLON GUARD session (fail-closed)")
                )
                continue

            raw_args = dict(tool_call.args)
            spec = session.tool_specs.get(tool_call.function)
            if spec is None:
                session.records.append(
                    ToolCallTrace(
                        tool_name=tool_call.function,
                        kind="write",
                        effect=None,
                        raw_args=raw_args,
                        canon_bytes=None,
                        allowed=False,
                        evidence_id=None,
                        reason=f"PermissionError: Unclassified tool {tool_call.function}",
                    )
                )
                tool_call_results.append(
                    _error_result(tool_call, f"PermissionError: Unclassified tool {tool_call.function}")
                )
                continue

            # Negative control C- runs identically to A0 while recording calls.
            if session.arm in ("A0", "C-"):
                result, error = runtime.run_function(env, tool_call.function, tool_call.args)
                session.records.append(
                    ToolCallTrace(
                        tool_name=spec.name,
                        kind=spec.kind,
                        effect=spec.effect,
                        raw_args=raw_args,
                        canon_bytes=None,
                        allowed=True,
                        evidence_id=None,
                        reason=f"Passthrough ({session.arm})",
                    )
                )
                tool_call_results.append(
                    ChatToolResultMessage(
                        role="tool",
                        content=[text_content_block_from_string(self.output_formatter(result))],
                        tool_call_id=tool_call.id,
                        tool_call=tool_call,
                        error=error,
                    )
                )
                continue

            # Close AgentDojo's nested FunctionCall bypass before any runtime call.
            if contains_nested_function_call(raw_args):
                reason = f"NestedFunctionCallDenied: nested FunctionCall in {spec.name}"
                session.records.append(
                    ToolCallTrace(
                        tool_name=spec.name,
                        kind=spec.kind,
                        effect=spec.effect,
                        raw_args=raw_args,
                        canon_bytes=None,
                        allowed=False,
                        evidence_id=None,
                        reason=reason,
                        nested_call_denied=True,
                    )
                )
                tool_call_results.append(_error_result(tool_call, f"PermissionError: {reason}"))
                continue

            # Positive control C+ denies every tool call (both reads and writes).
            if session.arm == "C+":
                reason = f"PolicyDenied (C+ deny-all): {spec.name}"
                session.records.append(
                    ToolCallTrace(
                        tool_name=spec.name,
                        kind=spec.kind,
                        effect=spec.effect,
                        raw_args=raw_args,
                        canon_bytes=None,
                        allowed=False,
                        evidence_id=None,
                        reason=reason,
                        broker_used=True,
                    )
                )
                tool_call_results.append(_error_result(tool_call, f"PermissionError: {reason}"))
                continue

            if spec.kind == "read":
                result, error = runtime.run_function(env, tool_call.function, tool_call.args)
                session.records.append(
                    ToolCallTrace(
                        tool_name=spec.name,
                        kind="read",
                        effect=None,
                        raw_args=raw_args,
                        canon_bytes=None,
                        allowed=True,
                        evidence_id=None,
                        reason="ReadAllowed",
                    )
                )
                tool_call_results.append(
                    ChatToolResultMessage(
                        role="tool",
                        content=[text_content_block_from_string(self.output_formatter(result))],
                        tool_call_id=tool_call.id,
                        tool_call=tool_call,
                        error=error,
                    )
                )
                continue

            try:
                normalized_args = normalize_tool_args(spec, raw_args)
            except (NestedFunctionCallError, UnexpectedToolArgumentError, ValidationError) as exc:
                reason = f"{type(exc).__name__}: {exc}"
                session.records.append(
                    ToolCallTrace(
                        tool_name=spec.name,
                        kind="write",
                        effect=spec.effect,
                        raw_args=raw_args,
                        canon_bytes=None,
                        allowed=False,
                        evidence_id=None,
                        reason=reason,
                        nested_call_denied=isinstance(exc, NestedFunctionCallError),
                    )
                )
                tool_call_results.append(_error_result(tool_call, reason))
                continue

            canon_bytes = canonicalize_args(normalized_args)
            if session.admitter is None:
                reason = "PermissionError: No admitter attached to session (fail-closed)"
                session.records.append(
                    ToolCallTrace(
                        tool_name=spec.name,
                        kind="write",
                        effect=spec.effect,
                        raw_args=raw_args,
                        canon_bytes=canon_bytes,
                        allowed=False,
                        evidence_id=None,
                        reason=reason,
                    )
                )
                tool_call_results.append(_error_result(tool_call, reason))
                continue

            decision = session.admitter.admit_write(spec, normalized_args, canon_bytes)
            evidence_id = decision.evidence_id
            allowed = decision.allowed
            reason = decision.reason
            hitl_requested = False
            hitl_granted = False

            if not allowed and session.approver is not None:
                is_interactive = bool(getattr(session.approver, "is_interactive", True))
                if is_interactive:
                    hitl_requested = True
                approval = session.approver.approve(spec, normalized_args, reason)
                if approval.approved:
                    allowed = True
                    hitl_granted = is_interactive
                    evidence_id = approval.evidence_id
                    reason = approval.reason
                else:
                    reason = approval.reason

            if not allowed:
                session.records.append(
                    ToolCallTrace(
                        tool_name=spec.name,
                        kind="write",
                        effect=spec.effect,
                        raw_args=raw_args,
                        canon_bytes=canon_bytes,
                        allowed=False,
                        evidence_id=None,
                        reason=reason,
                        hitl_requested=hitl_requested,
                        hitl_granted=False,
                        latency_ns=decision.latency_ns,
                        broker_used=decision.broker_used,
                    )
                )
                tool_call_results.append(_error_result(tool_call, f"PermissionError: {reason}"))
                continue

            result, error = runtime.run_function(env, tool_call.function, tool_call.args)
            session.records.append(
                ToolCallTrace(
                    tool_name=spec.name,
                    kind="write",
                    effect=spec.effect,
                    raw_args=raw_args,
                    canon_bytes=canon_bytes,
                    allowed=True,
                    evidence_id=evidence_id,
                    reason=reason,
                    hitl_requested=hitl_requested,
                    hitl_granted=hitl_granted,
                    latency_ns=decision.latency_ns,
                    broker_used=decision.broker_used,
                )
            )
            tool_call_results.append(
                ChatToolResultMessage(
                    role="tool",
                    content=[text_content_block_from_string(self.output_formatter(result))],
                    tool_call_id=tool_call.id,
                    tool_call=tool_call,
                    error=error,
                )
            )

        return query, runtime, env, [*messages, *tool_call_results], extra
