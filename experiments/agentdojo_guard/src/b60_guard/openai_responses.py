"""OpenAI Responses API adapter, tool filter, and token usage telemetry for AgentDojo."""

from __future__ import annotations

import json
from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any

import openai
from agentdojo.agent_pipeline.base_pipeline_element import BasePipelineElement
from agentdojo.functions_runtime import EmptyEnv, Env, Function, FunctionCall, FunctionsRuntime
from agentdojo.types import (
    ChatAssistantMessage,
    ChatMessage,
    ChatUserMessage,
    get_text_content_as_str,
    text_content_block_from_string,
)
from tenacity import retry, retry_if_not_exception_type, stop_after_attempt, wait_random_exponential

VALID_REASONING_EFFORTS = ("low", "medium", "high", "xhigh", "max")
DEFAULT_REASONING_EFFORT = "low"

_NON_RETRYABLE_OPENAI_ERRORS = (
    openai.BadRequestError,
    openai.UnprocessableEntityError,
    openai.AuthenticationError,
    openai.PermissionDeniedError,
)


def _get_field(obj: Any, key: str, default: Any = None) -> Any:
    if obj is None:
        return default
    if isinstance(obj, dict):
        return obj.get(key, default)
    return getattr(obj, key, default)


def _as_int(value: Any) -> int:
    if value is None or isinstance(value, bool):
        return 0
    return int(value)


@dataclass
class TokenUsageTracker:
    """Mutable per-case accumulator for real OpenAI Responses API token telemetry."""

    api_calls: int = 0
    input_tokens: int = 0
    cached_tokens: int = 0
    cache_write_tokens: int = 0
    output_tokens: int = 0
    reasoning_tokens: int = 0
    total_tokens: int = 0

    def record_usage(self, usage: Any) -> None:
        self.api_calls += 1
        if usage is None:
            return
        in_toks = _as_int(_get_field(usage, "input_tokens"))
        out_toks = _as_int(_get_field(usage, "output_tokens"))
        tot_toks = _as_int(_get_field(usage, "total_tokens"))
        in_details = _get_field(usage, "input_tokens_details")
        out_details = _get_field(usage, "output_tokens_details")

        self.input_tokens += in_toks
        self.cached_tokens += _as_int(_get_field(in_details, "cached_tokens"))
        self.cache_write_tokens += _as_int(_get_field(in_details, "cache_write_tokens"))
        self.output_tokens += out_toks
        self.reasoning_tokens += _as_int(_get_field(out_details, "reasoning_tokens"))
        self.total_tokens += tot_toks if tot_toks > 0 else (in_toks + out_toks)

    def merge(self, other: TokenUsageTracker) -> None:
        self.api_calls += other.api_calls
        self.input_tokens += other.input_tokens
        self.cached_tokens += other.cached_tokens
        self.cache_write_tokens += other.cache_write_tokens
        self.output_tokens += other.output_tokens
        self.reasoning_tokens += other.reasoning_tokens
        self.total_tokens += other.total_tokens

    def to_dict(self) -> dict[str, int]:
        return {
            "api_calls": self.api_calls,
            "input_tokens": self.input_tokens,
            "cached_tokens": self.cached_tokens,
            "cache_write_tokens": self.cache_write_tokens,
            "output_tokens": self.output_tokens,
            "reasoning_tokens": self.reasoning_tokens,
            "total_tokens": self.total_tokens,
        }


def validate_reasoning_effort(effort: str) -> str:
    if effort not in VALID_REASONING_EFFORTS:
        raise ValueError(
            f"Unsupported reasoning_effort {effort!r}; valid values are {VALID_REASONING_EFFORTS}"
        )
    return effort


def function_to_responses_tool(func: Function) -> dict[str, Any]:
    """Convert an AgentDojo Function into a Responses API tool definition (strict=False)."""
    return {
        "type": "function",
        "name": func.name,
        "description": func.description,
        "parameters": func.parameters.model_json_schema(),
        "strict": False,
    }


def messages_to_responses_input(messages: Sequence[ChatMessage]) -> list[dict[str, Any]]:
    """Convert AgentDojo ChatMessage history into Responses API input items."""
    items: list[dict[str, Any]] = []
    for msg in messages:
        role = msg["role"]
        if role == "system":
            items.append(
                {
                    "type": "message",
                    "role": "developer",
                    "content": get_text_content_as_str(msg["content"]),
                }
            )
        elif role == "user":
            items.append(
                {
                    "type": "message",
                    "role": "user",
                    "content": get_text_content_as_str(msg["content"]),
                }
            )
        elif role == "assistant":
            text = get_text_content_as_str(msg["content"]) if msg["content"] is not None else ""
            tool_calls = msg.get("tool_calls") or []
            if text or not tool_calls:
                items.append(
                    {
                        "type": "message",
                        "role": "assistant",
                        "content": text,
                    }
                )
            for tc in tool_calls:
                if not tc.id:
                    raise ValueError(f"FunctionCall {tc.function!r} is missing a call_id for Responses API")
                items.append(
                    {
                        "type": "function_call",
                        "call_id": tc.id,
                        "name": tc.function,
                        "arguments": json.dumps(dict(tc.args), ensure_ascii=False),
                    }
                )
        elif role == "tool":
            call_id = msg.get("tool_call_id")
            if not call_id:
                raise ValueError("`tool_call_id` must be specified for OpenAI Responses API tool results")
            output_str = msg["error"] if msg.get("error") else get_text_content_as_str(msg["content"])
            items.append(
                {
                    "type": "function_call_output",
                    "call_id": call_id,
                    "output": output_str,
                }
            )
        else:
            raise ValueError(f"Unsupported AgentDojo message role {role!r}")
    return items


def response_to_assistant_message(response: Any) -> ChatAssistantMessage:
    """Parse a Responses API response object into an AgentDojo ChatAssistantMessage."""
    text_parts: list[str] = []
    tool_calls: list[FunctionCall] = []

    for item in _get_field(response, "output") or []:
        item_type = _get_field(item, "type")
        if item_type == "message":
            for part in _get_field(item, "content") or []:
                part_text = _get_field(part, "text")
                if isinstance(part_text, str) and part_text:
                    text_parts.append(part_text)
        elif item_type == "function_call":
            name = _get_field(item, "name")
            call_id = _get_field(item, "call_id") or _get_field(item, "id")
            raw_args = _get_field(item, "arguments") or ""
            if not isinstance(name, str) or not name:
                raise ValueError("Responses API function_call item is missing function name")
            if not isinstance(call_id, str) or not call_id:
                raise ValueError(f"Responses API function_call {name!r} is missing call_id")
            if isinstance(raw_args, dict):
                parsed_args = raw_args
            elif isinstance(raw_args, str):
                stripped = raw_args.strip()
                parsed = json.loads(stripped) if stripped else {}
                if not isinstance(parsed, dict):
                    raise ValueError(f"Expected JSON object arguments for {name!r}, got {type(parsed).__name__}")
                parsed_args = parsed
            else:
                raise ValueError(f"Unsupported arguments payload type for {name!r}: {type(raw_args).__name__}")
            tool_calls.append(FunctionCall(function=name, args=parsed_args, id=call_id))
        elif item_type == "reasoning":
            continue

    if not text_parts:
        fallback_text = _get_field(response, "output_text")
        if isinstance(fallback_text, str) and fallback_text:
            text_parts.append(fallback_text)

    joined_text = "\n".join(text_parts)
    content = [text_content_block_from_string(joined_text)] if joined_text else []
    return ChatAssistantMessage(
        role="assistant",
        content=content,
        tool_calls=tool_calls or None,
    )


@retry(
    wait=wait_random_exponential(multiplier=1, max=40),
    stop=stop_after_attempt(3),
    reraise=True,
    retry=retry_if_not_exception_type(_NON_RETRYABLE_OPENAI_ERRORS),
)
def _responses_create_with_retry(client: Any, payload: dict[str, Any]) -> Any:
    return client.responses.create(**payload)


class OpenAIResponsesLLM(BasePipelineElement):
    """AgentDojo LLM element backed by OpenAI's `/v1/responses` API (GPT-6.2 compatible)."""

    def __init__(
        self,
        client: openai.OpenAI,
        model: str,
        *,
        reasoning_effort: str = DEFAULT_REASONING_EFFORT,
        store: bool = False,
        usage_tracker: TokenUsageTracker | None = None,
    ) -> None:
        self.client = client
        self.model = model
        self.name = model
        self.reasoning_effort = validate_reasoning_effort(reasoning_effort)
        self.store = store
        self.usage_tracker = usage_tracker if usage_tracker is not None else TokenUsageTracker()

    def create_response(
        self,
        *,
        input_items: Sequence[dict[str, Any]],
        tools: Sequence[dict[str, Any]] | None = None,
        tool_choice: str | None = None,
        text: dict[str, Any] | None = None,
    ) -> Any:
        """Invoke `/v1/responses` without `temperature`, enforcing `store` and `reasoning.effort`."""
        payload: dict[str, Any] = {
            "model": self.model,
            "input": list(input_items),
            "store": self.store,
            "reasoning": {"effort": self.reasoning_effort},
        }
        if tools:
            payload["tools"] = list(tools)
            if tool_choice is not None:
                payload["tool_choice"] = tool_choice
        if text is not None:
            payload["text"] = text

        response = _responses_create_with_retry(self.client, payload)
        self.usage_tracker.record_usage(_get_field(response, "usage"))
        return response

    def create_structured_json(
        self,
        *,
        messages: Sequence[ChatMessage],
        schema_name: str,
        schema: dict[str, Any],
        strict: bool = True,
    ) -> str:
        """Request strict JSON Schema output over Responses API with zero tools exposed."""
        input_items = messages_to_responses_input(messages)
        response = self.create_response(
            input_items=input_items,
            text={
                "format": {
                    "type": "json_schema",
                    "name": schema_name,
                    "strict": strict,
                    "schema": schema,
                }
            },
        )
        msg = response_to_assistant_message(response)
        return get_text_content_as_str(msg["content"])

    def query(
        self,
        query: str,
        runtime: FunctionsRuntime,
        env: Env = EmptyEnv(),
        messages: Sequence[ChatMessage] = (),
        extra_args: dict[str, Any] = {},
    ) -> tuple[str, FunctionsRuntime, Env, Sequence[ChatMessage], dict[str, Any]]:
        input_items = messages_to_responses_input(messages)
        tools = [function_to_responses_tool(tool) for tool in runtime.functions.values()]
        response = self.create_response(
            input_items=input_items,
            tools=tools or None,
            tool_choice="auto" if tools else None,
        )
        output = response_to_assistant_message(response)
        return query, runtime, env, [*messages, output], extra_args


class OpenAIResponsesToolFilter(BasePipelineElement):
    """B1 tool_filter defense backed by `OpenAIResponsesLLM` (avoids Chat Completions + ModelsEnum)."""

    def __init__(self, prompt: str, llm: OpenAIResponsesLLM) -> None:
        self.prompt = prompt
        self.llm = llm
        self.name = f"{llm.model}-tool_filter"

    def query(
        self,
        query: str,
        runtime: FunctionsRuntime,
        env: Env = EmptyEnv(),
        messages: Sequence[ChatMessage] = (),
        extra_args: dict[str, Any] = {},
    ) -> tuple[str, FunctionsRuntime, Env, Sequence[ChatMessage], dict[str, Any]]:
        filter_messages = [
            *messages,
            ChatUserMessage(role="user", content=[text_content_block_from_string(self.prompt)]),
        ]
        input_items = messages_to_responses_input(filter_messages)
        tools = [function_to_responses_tool(tool) for tool in runtime.functions.values()]
        response = self.llm.create_response(
            input_items=input_items,
            tools=tools or None,
            tool_choice="none" if tools else None,
        )
        output = response_to_assistant_message(response)
        output_text = get_text_content_as_str(output["content"]) if output["content"] is not None else ""

        new_tools = {
            tool_name: tool
            for tool_name, tool in runtime.functions.items()
            if tool_name in output_text
        }
        runtime.update_functions(new_tools)
        return query, runtime, env, [*filter_messages, output], extra_args
