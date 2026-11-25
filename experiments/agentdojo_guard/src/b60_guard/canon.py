"""Canonical argument serialization, nested-call detection, and query grounding."""

from __future__ import annotations

import json
import re
import unicodedata
from collections.abc import Mapping
from typing import Any

from agentdojo.functions_runtime import FunctionCall
from pydantic import BaseModel

from b60_guard.contracts import ToolSpec


class NestedFunctionCallError(PermissionError):
    """Raised when tool arguments attempt to smuggle a nested ``FunctionCall``."""


class UnexpectedToolArgumentError(ValueError):
    """Raised when tool arguments include fields absent from the Pydantic schema."""


def contains_nested_function_call(value: Any) -> bool:
    """Return True if ``value`` contains an AgentDojo ``FunctionCall`` anywhere in its tree."""
    if isinstance(value, FunctionCall):
        return True
    if not isinstance(value, Mapping) and hasattr(value, "function") and hasattr(value, "args"):
        return True
    if isinstance(value, Mapping):
        return any(contains_nested_function_call(v) for v in value.values())
    if isinstance(value, list | tuple | set | frozenset):
        return any(contains_nested_function_call(v) for v in value)
    return False


def normalize_unicode(value: Any) -> Any:
    """Recursively normalize strings to NFC and unwrap Pydantic models."""
    if isinstance(value, str):
        return unicodedata.normalize("NFC", value)
    if isinstance(value, BaseModel):
        return normalize_unicode(value.model_dump())
    if isinstance(value, Mapping):
        return {unicodedata.normalize("NFC", str(k)): normalize_unicode(v) for k, v in value.items()}
    if isinstance(value, list):
        return [normalize_unicode(v) for v in value]
    if isinstance(value, tuple):
        return [normalize_unicode(v) for v in value]
    return value


def normalize_tool_args(tool: ToolSpec, raw_args: Mapping[str, Any]) -> dict[str, Any]:
    """Reject nested ``FunctionCall`` and normalize arguments via the tool Pydantic schema."""
    if contains_nested_function_call(raw_args):
        raise NestedFunctionCallError(f"Nested FunctionCall denied in arguments of {tool.name}")
    allowed_fields = set(tool.parameters_model.model_fields.keys())
    unknown_keys = set(raw_args.keys()) - allowed_fields
    if unknown_keys:
        raise UnexpectedToolArgumentError(f"Unknown arguments for {tool.name}: {sorted(unknown_keys)}")
    validated = tool.parameters_model.model_validate(dict(raw_args)).model_dump()
    return normalize_unicode(validated)


def canonicalize_args(args: Mapping[str, Any]) -> bytes:
    """Deterministic UTF-8 NFC JSON bytes with sorted keys and compact separators."""
    normalized = normalize_unicode(dict(args))
    return json.dumps(normalized, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def bind_use_index(canon_bytes: bytes, use_index: int) -> bytes:
    """Bind call-use ordinal ``#k`` to prevent deterministic token_id collisions."""
    if use_index < 0:
        raise ValueError("use_index must be non-negative")
    return canon_bytes + b"#" + str(use_index).encode("ascii")


_WS_RE = re.compile(r"\s+")


def normalize_text_for_grounding(text: str) -> str:
    return _WS_RE.sub(" ", unicodedata.normalize("NFC", text)).strip().casefold()


def literal_grounded_in_query(value: Any, query: str) -> bool:
    """Verify that planner-supplied literal values actually originate from the user query."""
    if value is None or isinstance(value, bool):
        return True
    norm_query = normalize_text_for_grounding(query)
    if isinstance(value, str):
        norm_val = normalize_text_for_grounding(value)
        if not norm_val:
            return True
        return norm_val in norm_query
    if isinstance(value, int | float):
        compact_query = norm_query.replace(",", "")
        candidates = {str(value)}
        if isinstance(value, float) and value.is_integer():
            candidates.add(str(int(value)))
        return any(c.casefold() in compact_query for c in candidates)
    if isinstance(value, list | tuple):
        return all(literal_grounded_in_query(item, query) for item in value)
    if isinstance(value, Mapping):
        return all(literal_grounded_in_query(v, query) for v in value.values())
    return False
