# ============================================================================
# BABYLON-60 v4.0 Sovereign Hardened
# █ AUTOCOGNITION-Ω | STATE: C5-REAL | AESTHETIC: INDUSTRIAL_NOIR_2026
# ============================================================================
# [Causal-Determinist] Exergy-Maximized
"""CORTEX PTC & Ralph Primitives (DSH 0.2.2-rc.1 Architectural Transfer).

Pure, deterministic, dependency-free primitives distilled from the in-memory
forensic audit of DeepSeek Harness 0.2.2-rc.1:

1. ``prune_tool_result``: Replay-safe, model-free head/middle/tail pruning for
   oversized tool outputs (default 8192 -> 4096 head + 1024 tail).
2. ``validate_ralph_handoff``: Strict fresh-agent round handoff contract
   (``continue`` / ``complete`` / ``blocked``, <= 16 KiB serialized JSON).
3. ``scopes_overlap`` & ``normalize_write_scope``: Deterministic path-prefix
   collision guard preventing concurrent multi-agent write races in task DAGs.
4. ``render_mcp_tools_sdk_py``: Projects MCP ``inputSchema`` tool definitions
   into a compact Python ``Protocol`` SDK stub for Programmatic Tool Calling
   (PTC), omitting verbose JSON Schemas from the model prompt.
"""

from __future__ import annotations

import json
import keyword
import posixpath
import re
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any, Literal

__all__ = [
    "DEFAULT_HEAD_CHARS",
    "DEFAULT_MAX_HANDOFF_CHARS",
    "DEFAULT_TAIL_CHARS",
    "DEFAULT_THRESHOLD_CHARS",
    "PRUNE_MARKER",
    "RalphRoundReport",
    "RalphStatus",
    "normalize_write_scope",
    "prune_tool_result",
    "render_mcp_tools_sdk_py",
    "scopes_overlap",
    "validate_ralph_handoff",
]

PRUNE_MARKER = "\n\n[... tool result middle pruned ...]\n\n"
DEFAULT_THRESHOLD_CHARS = 8192
DEFAULT_HEAD_CHARS = 4096
DEFAULT_TAIL_CHARS = 1024
DEFAULT_MAX_HANDOFF_CHARS = 16384

RalphStatus = Literal["continue", "complete", "blocked"]
_ALLOWED_REPORT_KEYS = frozenset({"status", "summary", "evidence", "nextSteps", "blocker"})
_VALID_IDENT = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


def prune_tool_result(
    text: str,
    *,
    threshold_chars: int = DEFAULT_THRESHOLD_CHARS,
    head_chars: int = DEFAULT_HEAD_CHARS,
    tail_chars: int = DEFAULT_TAIL_CHARS,
) -> str:
    """Replay-safe, model-free head/middle/tail pruning for tool-result payloads."""
    if not isinstance(text, str):
        raise TypeError("text must be a str")
    if (
        isinstance(threshold_chars, bool)
        or isinstance(head_chars, bool)
        or isinstance(tail_chars, bool)
        or head_chars < 0
        or tail_chars < 0
        or threshold_chars <= head_chars + tail_chars
    ):
        raise ValueError("Invalid pruner bounds: require threshold_chars > head_chars + tail_chars >= 0")
    if len(text) <= threshold_chars:
        return text
    tail_part = text[-tail_chars:] if tail_chars > 0 else ""
    return f"{text[:head_chars]}{PRUNE_MARKER}{tail_part}"


def normalize_write_scope(scope: str) -> str:
    """Normalize a relative or absolute write scope path without trailing slash."""
    if not isinstance(scope, str):
        raise TypeError("write_scope must be a str")
    cleaned = scope.strip().replace("\\", "/")
    if not cleaned or "\x00" in cleaned:
        raise ValueError("write_scope must be a non-empty path without NUL bytes")
    normed = posixpath.normpath(cleaned)
    if normed.startswith("//"):
        normed = "/" + normed.lstrip("/")
    if normed in (".", ""):
        return "."
    return normed.rstrip("/") or "/"


def scopes_overlap(left: str, right: str) -> bool:
    """Return True iff two normalized file or directory write scopes overlap."""
    nl = normalize_write_scope(left)
    nr = normalize_write_scope(right)
    if nl == nr:
        return True
    if nl == "." and not nr.startswith("/"):
        return True
    if nr == "." and not nl.startswith("/"):
        return True
    if nl == "/" and nr.startswith("/"):
        return True
    if nr == "/" and nl.startswith("/"):
        return True
    return nl.startswith(f"{nr}/") or nr.startswith(f"{nl}/")


def _is_normalized_text(value: object) -> bool:
    return isinstance(value, str) and len(value) > 0 and value == value.strip()


def _is_normalized_list(value: object) -> bool:
    return isinstance(value, list) and all(_is_normalized_text(item) for item in value)


@dataclass(frozen=True)
class RalphRoundReport:
    """Validated handoff payload produced by one fresh-agent Ralph round."""

    status: RalphStatus
    summary: str
    evidence: tuple[str, ...]
    next_steps: tuple[str, ...]
    blocker: str

    def to_dict(self) -> dict[str, object]:
        return {
            "status": self.status,
            "summary": self.summary,
            "evidence": list(self.evidence),
            "nextSteps": list(self.next_steps),
            "blocker": self.blocker,
        }


def validate_ralph_handoff(
    report: Mapping[str, Any],
    *,
    max_handoff_chars: int = DEFAULT_MAX_HANDOFF_CHARS,
) -> RalphRoundReport:
    """Validate a structured round report against the DSH Ralph loop contract."""
    if not isinstance(report, Mapping) or isinstance(report, (list, tuple)):
        raise ValueError("Ralph child returned no structured round report")
    if isinstance(max_handoff_chars, bool) or max_handoff_chars < 1:
        raise ValueError("max_handoff_chars must be a positive integer")

    keys = set(report.keys())
    missing = sorted(_ALLOWED_REPORT_KEYS - keys)
    extra = sorted(keys - _ALLOWED_REPORT_KEYS)
    if missing or extra:
        raise ValueError(f"Ralph round report keys mismatch: missing={missing}, extra={extra}")

    summary = report["summary"]
    evidence = report["evidence"]
    next_steps = report["nextSteps"]
    blocker = report["blocker"]
    status = report["status"]

    if not _is_normalized_text(summary):
        raise ValueError("Ralph round report summary must be non-empty and normalized")
    if not _is_normalized_list(evidence) or not _is_normalized_list(next_steps):
        raise ValueError("Ralph round report evidence and nextSteps must contain only non-empty normalized strings")
    if not isinstance(blocker, str) or blocker != blocker.strip():
        raise ValueError("Ralph round report blocker must be a normalized string")

    if status == "continue":
        if len(next_steps) == 0 or blocker != "":
            raise ValueError("a continuing Ralph report needs nextSteps and an empty blocker")
    elif status == "complete":
        if len(evidence) == 0 or len(next_steps) != 0 or blocker != "":
            raise ValueError("a complete Ralph report needs evidence, no nextSteps, and an empty blocker")
    elif status == "blocked":
        if not _is_normalized_text(blocker):
            raise ValueError("a blocked Ralph report needs a concrete blocker")
    else:
        raise ValueError("Ralph round report status is invalid")

    canonical_dict = {
        "status": status,
        "summary": summary,
        "evidence": list(evidence),
        "nextSteps": list(next_steps),
        "blocker": blocker,
    }
    serialized = json.dumps(canonical_dict, ensure_ascii=False, separators=(",", ":"))
    if len(serialized) > max_handoff_chars:
        raise ValueError(f"Ralph round report exceeds maxHandoffChars ({len(serialized)} > {max_handoff_chars})")

    return RalphRoundReport(
        status=status,
        summary=summary,
        evidence=tuple(evidence),
        next_steps=tuple(next_steps),
        blocker=blocker,
    )


def _json_type_to_py(spec: Mapping[str, Any]) -> str:
    raw_type = spec.get("type", "Any")
    types = raw_type if isinstance(raw_type, list) else [raw_type]
    mapping = {
        "string": "str",
        "integer": "int",
        "number": "float",
        "boolean": "bool",
        "null": "None",
        "object": "dict[str, Any]",
        "array": "list[Any]",
    }
    mapped = [mapping.get(str(t), "Any") for t in types]
    return " | ".join(mapped) if mapped else "Any"


def _safe_ident(name: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9_]", "_", name)
    if not _VALID_IDENT.match(cleaned):
        cleaned = f"_{cleaned}"
    if keyword.iskeyword(cleaned):
        cleaned = f"{cleaned}_"
    return cleaned


def render_mcp_tools_sdk_py(tools: Sequence[Mapping[str, Any]]) -> str:
    """Project MCP tool descriptors into a compact Python Protocol SDK stub (PTC mode)."""
    lines = [
        "# Auto-generated PTC Python SDK projection (tools:sdk)",
        "# Native tool JSON Schemas omitted; invoke tools programmatically via `tools.<name>(...)`.",
        "from typing import Any, Protocol",
        "",
        "class ToolsSDK(Protocol):",
    ]
    if not tools:
        lines.append("    pass")
        return "\n".join(lines) + "\n"

    for idx, tool in enumerate(tools):
        name = _safe_ident(str(tool.get("name", f"tool_{idx}")))
        desc = str(tool.get("description", "")).strip().replace("\n", " ")
        schema = tool.get("inputSchema")
        props: Mapping[str, Any] = schema.get("properties", {}) if isinstance(schema, Mapping) else {}
        req_raw = schema.get("required", []) if isinstance(schema, Mapping) else []
        required = set(req_raw) if isinstance(req_raw, list) else set()

        req_params: list[str] = []
        opt_params: list[str] = []
        for prop_name, prop_spec in props.items():
            ident = _safe_ident(str(prop_name))
            spec_map = prop_spec if isinstance(prop_spec, Mapping) else {}
            py_type = _json_type_to_py(spec_map)
            if prop_name in required:
                req_params.append(f"{ident}: {py_type}")
            else:
                if "None" not in py_type.split(" | "):
                    py_type = f"{py_type} | None"
                opt_params.append(f"{ident}: {py_type} = None")

        all_params = req_params + opt_params
        sig_args = ", ".join(["self", "*", *all_params]) if all_params else "self"
        if desc:
            lines.append(f"    # {desc}")
        lines.append(f"    async def {name}({sig_args}) -> dict[str, Any]: ...")
    lines.append("")
    lines.append("tools: ToolsSDK")
    return "\n".join(lines) + "\n"
