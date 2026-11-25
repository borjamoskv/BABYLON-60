"""OpenAI Responses function calls through CORTEX's generated Python interface.

The generated Protocol supplies names/arity, not a serializer or authorization.
Only explicitly supplied keywords cross MCP. Original schemas remain attached to
OpenAI tools with strict=False; canonical validation and permissions stay server-side.
The optional stdio connector uses the existing MCP 2.x SDK (gemini extra).
"""

from __future__ import annotations

import ast
from collections.abc import AsyncIterator, Mapping, Sequence
from contextlib import asynccontextmanager
from copy import deepcopy
from dataclasses import dataclass
import inspect
import json
import re
from types import SimpleNamespace
from typing import Any

import httpx

from babylon60.mcp.cortex_ptc_ralph import _safe_ident, render_mcp_tools_sdk_py


MAX_DISCOVERY_PAGES = 256


class ProjectionError(ValueError):
    """The original descriptor or call cannot be represented without loss."""


def _object_pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ProjectionError(f"Duplicate JSON key: {key}")
        result[key] = value
    return result


def _reject_constant(value: str) -> Any:
    raise ProjectionError(f"Non-JSON numeric constant: {value}")


@dataclass(frozen=True)
class _Binding:
    original_name: str
    signature: inspect.Signature
    # JSON property -> Python keyword, with collisions rejected during construction.
    keywords: dict[str, str]


class CortexOpenAIAdapter:
    """An explicit tool allowlist bound to one initialized MCP session.

    This adapter currently supports closed top-level object schemas. It refuses
    schemas whose arbitrary keywords the Protocol cannot express. It does not
    execute generated/model code. ``session`` is the official MCP SDK's dynamic
    boundary; its JSON models are converted with aliases and nulls preserved.
    """

    def __init__(
        self,
        session: Any,
        descriptors: Sequence[Mapping[str, Any]],
        *,
        metadata: Mapping[str, Any] | None = None,
    ) -> None:
        if not descriptors:
            raise ProjectionError("An explicit, non-empty tool allowlist is required")
        self._session = session
        self._metadata = deepcopy(dict(metadata)) if metadata is not None else None
        selected = deepcopy(list(descriptors))
        self.sdk_source = render_mcp_tools_sdk_py(selected)
        # Parse declarations only: no exec/eval of tool descriptions or model code.
        tree = ast.parse(self.sdk_source)
        protocol = next(node for node in tree.body if isinstance(node, ast.ClassDef) and node.name == "ToolsSDK")
        methods = [node for node in protocol.body if isinstance(node, ast.AsyncFunctionDef)]
        if len(methods) != len(selected):
            raise ProjectionError("Projection method count differs from tool descriptors")
        self._bindings: dict[str, _Binding] = {}
        self._openai_tools: list[dict[str, Any]] = []
        self.tools = SimpleNamespace()
        for descriptor, method in zip(selected, methods, strict=True):
            original_name = descriptor.get("name")
            if not isinstance(original_name, str) or not original_name:
                raise ProjectionError("Tool name must be a non-empty string")
            if method.name in self._bindings or not re.fullmatch(r"[A-Za-z][A-Za-z0-9_]{0,63}", method.name):
                raise ProjectionError("Duplicate or unsupported projected tool name")
            schema = descriptor.get("inputSchema", {})
            if not isinstance(schema, dict) or schema.get("type") != "object":
                raise ProjectionError("A top-level object schema is required")
            if schema.get("additionalProperties") is not False:
                raise ProjectionError("The typed adapter requires additionalProperties=false at the top level")
            props = schema.get("properties", {})
            if not isinstance(props, dict):
                raise ProjectionError("properties must be an object")
            keywords = {name: _safe_ident(name) for name in props}
            if len(set(keywords.values())) != len(keywords) or "self" in keywords.values():
                raise ProjectionError("Property names collide in the Python projection")
            required = schema.get("required", [])
            if not isinstance(required, list) or not set(required) <= set(props):
                raise ProjectionError("required must refer to declared properties")
            parameters = [
                inspect.Parameter(
                    arg.arg,
                    inspect.Parameter.KEYWORD_ONLY,
                    default=inspect.Parameter.empty if default is None else None,
                    annotation=ast.unparse(arg.annotation) if arg.annotation else inspect.Parameter.empty,
                )
                for arg, default in zip(method.args.kwonlyargs, method.args.kw_defaults, strict=True)
            ]
            signature = inspect.Signature(parameters)
            if set(signature.parameters) != set(keywords.values()):
                raise ProjectionError("Projected parameters differ from original properties")
            self._bindings[method.name] = _Binding(original_name, signature, keywords)
            setattr(self.tools, method.name, self._make_method(method.name, signature))
            self._openai_tools.append(
                {
                    "type": "function",
                    "name": method.name,
                    "description": descriptor.get("description") or "",
                    "parameters": schema,
                    "strict": False,
                }
            )

    @classmethod
    async def discover(
        cls, session: Any, *, allowed_tools: Sequence[str], metadata: Mapping[str, Any] | None = None
    ) -> CortexOpenAIAdapter:
        """Discover only the caller-selected tools, handling MCP pagination."""
        from mcp.types import PaginatedRequestParams

        wanted = set(allowed_tools)
        if not wanted or len(wanted) != len(allowed_tools):
            raise ProjectionError("The allowlist must be non-empty and unique")
        descriptors: list[dict[str, Any]] = []
        cursor: str | None = None
        seen: set[str] = set()
        for _ in range(MAX_DISCOVERY_PAGES):
            page = await session.list_tools(params=PaginatedRequestParams(cursor=cursor) if cursor else None)
            data = page.model_dump(mode="json", by_alias=True, exclude_none=False)
            descriptors.extend(tool for tool in data["tools"] if tool["name"] in wanted)
            cursor = data.get("nextCursor")
            if not cursor:
                break
            if cursor in seen:
                raise ProjectionError("MCP tools/list repeated its cursor")
            seen.add(cursor)
        else:
            raise ProjectionError(f"MCP tools/list exceeded {MAX_DISCOVERY_PAGES} pages")
        if {tool["name"] for tool in descriptors} != wanted:
            raise ProjectionError("An allowed tool is missing from tools/list")
        return cls(session, descriptors, metadata=metadata)

    @property
    def openai_tools(self) -> list[dict[str, Any]]:
        return deepcopy(self._openai_tools)

    def _make_method(self, name: str, signature: inspect.Signature) -> Any:
        async def invoke(**kwargs: Any) -> dict[str, Any]:
            binding = self._bindings[name]
            supplied = binding.signature.bind(**kwargs).arguments
            # Never apply_defaults(), drop None, or filter by truthiness.
            arguments = {original: supplied[alias] for original, alias in binding.keywords.items() if alias in supplied}
            result = await self._session.call_tool(binding.original_name, arguments, meta=deepcopy(self._metadata))
            dumped: dict[str, Any] = result.model_dump(mode="json", by_alias=True, exclude_none=False)
            return dumped

        invoke.__name__ = name
        # Runtime introspection agrees with the generated Protocol declaration.
        setattr(invoke, "__signature__", signature)
        return invoke

    async def execute_function_call(self, call: Mapping[str, Any]) -> dict[str, Any]:
        """Execute one completed Responses function_call, without retries.

        Call metadata never supplies MCP authorization. Trusted metadata is given
        by the application at construction; the original server still admits or
        rejects the effect. Applications own replay/idempotency across calls.
        """
        if call.get("type") != "function_call" or call.get("status", "completed") != "completed":
            raise ProjectionError("A completed function_call is required")
        name, call_id = call.get("name"), call.get("call_id")
        if not isinstance(name, str) or name not in self._bindings:
            raise ProjectionError("Function is not in the allowed projection")
        if not isinstance(call_id, str) or not call_id:
            raise ProjectionError("A non-empty call_id is required")
        raw = call.get("arguments")
        if not isinstance(raw, str):
            raise ProjectionError("Function arguments must be JSON text")
        arguments = json.loads(raw, object_pairs_hook=_object_pairs, parse_constant=_reject_constant)
        if not isinstance(arguments, dict):
            raise ProjectionError("Function arguments must be an object")
        binding = self._bindings[name]
        if set(arguments) - binding.keywords.keys():
            raise ProjectionError("Unknown argument in function call")
        kwargs = {binding.keywords[key]: value for key, value in arguments.items()}
        result = await getattr(self.tools, name)(**kwargs)
        output = {"type": "function_call_output", "call_id": call_id, "output": json.dumps(result, allow_nan=False)}
        if call.get("caller") is not None:
            output["caller"] = deepcopy(call["caller"])
        return output

    async def request_function_call(
        self, *, api_key: str, model: str, prompt: str, tool_name: str, max_output_tokens: int = 1024
    ) -> dict[str, Any]:
        """One real OpenAI request; return bounded evidence, not model reasoning.

        Network/API errors propagate. No automatic retry, fallback endpoint, or
        automatic execution: inspect the returned call, then execute explicitly.
        """
        if tool_name not in self._bindings:
            raise ProjectionError("Requested function is not in the allowed projection")
        if not api_key:
            raise ValueError("OPENAI_API_KEY is required")
        payload = {
            "model": model,
            "store": False,
            "instructions": (
                "Use this Python interface for the available tools:\n"
                + self.sdk_source
                + "\nA missing optional argument and an explicit null are distinct. "
                "Do not materialize defaults. The original JSON schemas govern allowed values."
            ),
            "input": prompt,
            "tools": self.openai_tools,
            "tool_choice": {"type": "function", "name": tool_name},
            "parallel_tool_calls": False,
            "max_output_tokens": max_output_tokens,
        }
        async with httpx.AsyncClient(timeout=45, follow_redirects=False, trust_env=False) as client:
            response = await client.post(
                "https://api.openai.com/v1/responses",
                headers={"Authorization": f"Bearer {api_key}"},
                json=payload,
            )
            response.raise_for_status()
            data = response.json()
        calls = [item for item in data.get("output", []) if item.get("type") == "function_call"]
        if data.get("status") != "completed" or len(calls) != 1:
            raise ProjectionError("OpenAI did not return exactly one completed function call")
        return {
            "response_id": data["id"],
            "model": data["model"],
            "usage": data.get("usage"),
            "function_call": calls[0],
        }


@asynccontextmanager
async def cortex_stdio_session(
    command: str, args: list[str], *, cwd: str, env: dict[str, str] | None = None
) -> AsyncIterator[Any]:
    """Connect/initialize/close an MCP stdio subprocess with the official SDK.

    env=None uses the SDK's minimal inherited environment, not os.environ.
    The OpenAI API key must not be forwarded to a tool subprocess.
    """
    from mcp import ClientSession
    from mcp.client.stdio import StdioServerParameters, stdio_client

    params = StdioServerParameters(command=command, args=args, cwd=cwd, env=env)
    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write, read_timeout_seconds=30) as session:
            await session.initialize()
            yield session
