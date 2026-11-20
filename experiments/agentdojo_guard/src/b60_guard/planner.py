"""Quarantined intent planner that never observes environment state or tool outputs."""

from __future__ import annotations

import json
import re
from collections.abc import Callable, Sequence
from typing import Any, Literal, Protocol

from agentdojo.agent_pipeline.base_pipeline_element import BasePipelineElement
from agentdojo.functions_runtime import EmptyEnv, FunctionsRuntime
from agentdojo.types import ChatSystemMessage, ChatUserMessage, get_text_content_as_str, text_content_block_from_string
from pydantic import BaseModel, ConfigDict, Field

from b60_guard.contracts import ToolSpec


class LiteralArg(BaseModel):
    """Exact argument value explicitly stated in the trusted user query."""

    model_config = ConfigDict(extra="forbid")
    literal: Any


class AnyArg(BaseModel):
    """Argument value that depends on untrusted data to be read during execution."""

    model_config = ConfigDict(extra="forbid")
    any: Literal[True] = True


class ToolIntent(BaseModel):
    """Planned capability intent for a single write tool."""

    model_config = ConfigDict(extra="forbid")
    tool: str
    args: dict[str, LiteralArg | AnyArg] = Field(default_factory=dict)
    max_uses: int = Field(default=1, ge=1, le=32)


class IntentPlan(BaseModel):
    """Structured output produced solely from the user query and static tool schemas."""

    model_config = ConfigDict(extra="forbid")
    intents: list[ToolIntent] = Field(default_factory=list)


class PlannerBackend(Protocol):
    """Strict planner boundary: only ``query`` and static ``schemas`` may cross."""

    def plan(self, query: str, schemas: Sequence[ToolSpec]) -> IntentPlan: ...


_DEFAULT_PLANNER_SYSTEM_PROMPT = (
    "You are a quarantined capability planner. You see ONLY the user's request and static tool schemas. "
    "Output valid JSON matching IntentPlan: {\"intents\": [{\"tool\": str, \"args\": {param: {\"literal\": val} | {\"any\": true}}, \"max_uses\": int}]}. "
    "Include ONLY write tools required to satisfy the user request. "
    "Use {\"literal\": val} ONLY when the exact value appears in the user request; otherwise use {\"any\": true}."
)

_FENCE_RE = re.compile(r"^```(?:json)?\s*|\s*```$", re.MULTILINE)


def schemas_for_prompt(schemas: Sequence[ToolSpec]) -> list[dict[str, Any]]:
    """Project static tool schemas without runtime environment or code digests."""
    return [
        {
            "name": spec.name,
            "kind": spec.kind,
            "description": spec.description,
            "parameters": spec.parameters_schema,
        }
        for spec in schemas
    ]


def _extract_json_payload(raw_text: str) -> str:
    stripped = _FENCE_RE.sub("", raw_text).strip()
    start = stripped.find("{")
    end = stripped.rfind("}")
    if start != -1 and end > start:
        return stripped[start : end + 1]
    return stripped


class QuarantinedPlanner:
    """Invokes an LLM on a fresh empty runtime/env with only system + user messages."""

    def __init__(self, llm: BasePipelineElement, system_prompt: str = _DEFAULT_PLANNER_SYSTEM_PROMPT) -> None:
        self._llm = llm
        self._system_prompt = system_prompt

    def plan(self, query: str, schemas: Sequence[ToolSpec]) -> IntentPlan:
        schema_payload = json.dumps(schemas_for_prompt(schemas), ensure_ascii=False, indent=2)
        user_prompt = f"User request:\n{query}\n\nTool schemas:\n{schema_payload}\n\nRespond with JSON only."
        messages = [
            ChatSystemMessage(role="system", content=[text_content_block_from_string(self._system_prompt)]),
            ChatUserMessage(role="user", content=[text_content_block_from_string(user_prompt)]),
        ]
        # Fresh EmptyEnv and empty FunctionsRuntime([]) guarantee zero tool/env exposure.
        _, _, _, out_messages, _ = self._llm.query(
            user_prompt,
            FunctionsRuntime([]),
            EmptyEnv(),
            messages,
            {},
        )
        assistant_msg = out_messages[-1]
        if assistant_msg["role"] != "assistant" or assistant_msg["content"] is None:
            raise ValueError("Planner LLM did not return an assistant text message")
        raw_text = get_text_content_as_str(assistant_msg["content"])
        return IntentPlan.model_validate_json(_extract_json_payload(raw_text))


class StaticPlanner:
    """Deterministic test planner obeying the same ``(query, schemas)`` boundary."""

    def __init__(self, plan_fn: Callable[[str, Sequence[ToolSpec]], IntentPlan]) -> None:
        self._plan_fn = plan_fn

    def plan(self, query: str, schemas: Sequence[ToolSpec]) -> IntentPlan:
        return self._plan_fn(query, schemas)
