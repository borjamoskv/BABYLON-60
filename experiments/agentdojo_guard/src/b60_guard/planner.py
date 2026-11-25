"""Quarantined intent planner that never observes environment state or tool outputs."""

from __future__ import annotations

import json
import re
from collections.abc import Callable, Sequence
from typing import Any, Literal, Protocol

from agentdojo.agent_pipeline.base_pipeline_element import BasePipelineElement
from agentdojo.agent_pipeline.llms.openai_llm import OpenAILLM, _message_to_openai
from agentdojo.functions_runtime import EmptyEnv, FunctionsRuntime
from agentdojo.types import ChatMessage, ChatSystemMessage, ChatUserMessage, get_text_content_as_str, text_content_block_from_string
from openai._types import NOT_GIVEN
from pydantic import BaseModel, ConfigDict, Field, ValidationError, model_validator

from b60_guard.contracts import ToolSpec
from b60_guard.openai_responses import OpenAIResponsesLLM


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

_RESPONSES_PLANNER_SYSTEM_PROMPT = (
    "You are a quarantined capability planner. You see ONLY the user's request and static tool schemas. "
    "Output strictly valid JSON matching the provided schema: "
    "{\"intents\": [{\"tool\": str, \"args\": [{\"name\": str, \"mode\": \"literal\" | \"any\", \"literal\": val_or_null}], \"max_uses\": int}]}. "
    "Include ONLY write tools required to satisfy the user request (max_uses between 1 and 32). "
    "Use mode=\"literal\" with the exact value ONLY when that exact value appears in the user request; "
    "otherwise use mode=\"any\" with literal=null."
)

INTENT_PLAN_WIRE_JSON_SCHEMA: dict[str, Any] = {
    "type": "object",
    "additionalProperties": False,
    "required": ["intents"],
    "properties": {
        "intents": {
            "type": "array",
            "items": {
                "type": "object",
                "additionalProperties": False,
                "required": ["tool", "args", "max_uses"],
                "properties": {
                    "tool": {"type": "string"},
                    "args": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "additionalProperties": False,
                            "required": ["name", "mode", "literal"],
                            "properties": {
                                "name": {"type": "string"},
                                "mode": {"type": "string", "enum": ["literal", "any"]},
                                "literal": {
                                    "anyOf": [
                                        {"type": "string"},
                                        {"type": "number"},
                                        {"type": "integer"},
                                        {"type": "boolean"},
                                        {"type": "null"},
                                        {
                                            "type": "array",
                                            "items": {
                                                "anyOf": [
                                                    {"type": "string"},
                                                    {"type": "number"},
                                                    {"type": "integer"},
                                                    {"type": "boolean"},
                                                    {"type": "null"},
                                                ]
                                            },
                                        },
                                    ]
                                },
                            },
                        },
                    },
                    "max_uses": {"type": "integer"},
                },
            },
        }
    },
}


class _WireArgBinding(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: str
    mode: Literal["literal", "any"]
    literal: Any = None


class _WireToolIntent(BaseModel):
    model_config = ConfigDict(extra="forbid")
    tool: str
    args: list[_WireArgBinding] = Field(default_factory=list)
    max_uses: int = Field(default=1, ge=1, le=32)

    @model_validator(mode="after")
    def _reject_duplicate_arg_names(self) -> _WireToolIntent:
        seen: set[str] = set()
        for binding in self.args:
            if binding.name in seen:
                raise ValueError(f"Duplicate argument binding for {binding.name!r}")
            seen.add(binding.name)
        return self


class _WireIntentPlan(BaseModel):
    model_config = ConfigDict(extra="forbid")
    intents: list[_WireToolIntent] = Field(default_factory=list)


def parse_wire_intent_plan(raw_text: str) -> IntentPlan:
    """Validate strict Responses API wire JSON and convert it into an ``IntentPlan``."""
    wire = _WireIntentPlan.model_validate_json(_extract_json_payload(raw_text))
    converted: list[ToolIntent] = []
    for item in wire.intents:
        args_map: dict[str, LiteralArg | AnyArg] = {}
        for binding in item.args:
            if binding.mode == "literal":
                args_map[binding.name] = LiteralArg(literal=binding.literal)
            else:
                args_map[binding.name] = AnyArg(any=True)
        converted.append(ToolIntent(tool=item.tool, args=args_map, max_uses=item.max_uses))
    return IntentPlan(intents=converted)

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

    def __init__(self, llm: BasePipelineElement, system_prompt: str | None = None) -> None:
        self._llm = llm
        if system_prompt is not None:
            self._system_prompt = system_prompt
        elif isinstance(llm, OpenAIResponsesLLM):
            self._system_prompt = _RESPONSES_PLANNER_SYSTEM_PROMPT
        else:
            self._system_prompt = _DEFAULT_PLANNER_SYSTEM_PROMPT

    def _call_llm_text(self, user_prompt: str, messages: Sequence[ChatMessage]) -> str:
        if isinstance(self._llm, OpenAIResponsesLLM):
            return self._llm.create_structured_json(
                messages=messages,
                schema_name="b60_intent_plan",
                schema=INTENT_PLAN_WIRE_JSON_SCHEMA,
                strict=True,
            )

        if isinstance(self._llm, OpenAILLM):
            openai_messages = [_message_to_openai(m, self._llm.model) for m in messages]
            completion = self._llm.client.chat.completions.create(
                model=self._llm.model,
                messages=openai_messages,
                response_format={"type": "json_object"},
                temperature=self._llm.temperature or NOT_GIVEN,
                reasoning_effort=self._llm.reasoning_effort or NOT_GIVEN,
            )
            return completion.choices[0].message.content or ""

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
        return get_text_content_as_str(assistant_msg["content"])

    def _parse_plan(self, raw_text: str) -> IntentPlan:
        if isinstance(self._llm, OpenAIResponsesLLM):
            return parse_wire_intent_plan(raw_text)
        return IntentPlan.model_validate_json(_extract_json_payload(raw_text))

    def plan(self, query: str, schemas: Sequence[ToolSpec]) -> IntentPlan:
        schema_payload = json.dumps(schemas_for_prompt(schemas), ensure_ascii=False, indent=2)
        user_prompt = f"User request:\n{query}\n\nTool schemas:\n{schema_payload}\n\nRespond with JSON only."
        messages: list[ChatMessage] = [
            ChatSystemMessage(role="system", content=[text_content_block_from_string(self._system_prompt)]),
            ChatUserMessage(role="user", content=[text_content_block_from_string(user_prompt)]),
        ]
        raw_text = self._call_llm_text(user_prompt, messages)
        try:
            return self._parse_plan(raw_text)
        except ValidationError:
            retry_prompt = (
                f"{user_prompt}\n\nYour previous output was invalid JSON/schema. "
                "Output strictly valid JSON matching {\"intents\": [...]}."
            )
            retry_messages: list[ChatMessage] = [
                messages[0],
                ChatUserMessage(role="user", content=[text_content_block_from_string(retry_prompt)]),
            ]
            raw_retry = self._call_llm_text(retry_prompt, retry_messages)
            return self._parse_plan(raw_retry)


class StaticPlanner:
    """Deterministic test planner obeying the same ``(query, schemas)`` boundary."""

    def __init__(self, plan_fn: Callable[[str, Sequence[ToolSpec]], IntentPlan]) -> None:
        self._plan_fn = plan_fn

    def plan(self, query: str, schemas: Sequence[ToolSpec]) -> IntentPlan:
        return self._plan_fn(query, schemas)
