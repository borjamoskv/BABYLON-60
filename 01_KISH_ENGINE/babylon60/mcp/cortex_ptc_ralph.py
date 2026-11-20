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
import os
from pathlib import Path
import posixpath
import re
import unicodedata
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
    "prune_mcp_text_payload",
    "prune_tool_result",
    "render_mcp_tools_sdk_py",
    "resolve_prune_bounds",
    "scopes_overlap",
    "validate_ralph_handoff",
]

PRUNE_MARKER = "\n\n[... tool result middle pruned ...]\n\n"
DEFAULT_THRESHOLD_CHARS = 8192
DEFAULT_HEAD_CHARS = 4096
DEFAULT_TAIL_CHARS = 1024
DEFAULT_MAX_HANDOFF_CHARS = 16384
_DEFAULT_REPO_ROOT_POSIX = Path(__file__).absolute().parents[3].as_posix().rstrip("/") or "/"
_SCALAR_ENVELOPE_KEYS = ("admitted", "status", "ok", "reason", "isError", "tuple_id")

RalphStatus = Literal["continue", "complete", "blocked"]
_ALLOWED_REPORT_KEYS = frozenset({"status", "summary", "evidence", "nextSteps", "blocker"})
_VALID_IDENT = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")
_GLOB_CHARS = re.compile(r"[*?\[{]")


def _proportional_head_tail(threshold_chars: int) -> tuple[int, int]:
    head = max(1, (threshold_chars * 4) // 8)
    tail = max(0, min(threshold_chars - head - 1, threshold_chars // 8))
    return head, tail


def _coerce_non_bool_int(value: object, fallback: int) -> int:
    if isinstance(value, bool) or not isinstance(value, (int, str)):
        raise ValueError("Pruner bound must be an integer")
    return int(value) if value is not None else fallback


def resolve_prune_bounds(prune_cfg: object) -> tuple[int, int, int]:
    """Resolve fail-safe (threshold, head, tail) bounds from _meta['babylon60/prune']."""
    defaults = (DEFAULT_THRESHOLD_CHARS, DEFAULT_HEAD_CHARS, DEFAULT_TAIL_CHARS)
    if not isinstance(prune_cfg, Mapping):
        return defaults
    try:
        threshold = _coerce_non_bool_int(
            prune_cfg.get("threshold_chars", DEFAULT_THRESHOLD_CHARS), DEFAULT_THRESHOLD_CHARS
        )
        if threshold < 2:
            return defaults
        has_head = "head_chars" in prune_cfg
        has_tail = "tail_chars" in prune_cfg
        auto_head, auto_tail = _proportional_head_tail(threshold)
        default_head = DEFAULT_HEAD_CHARS if threshold > DEFAULT_HEAD_CHARS + DEFAULT_TAIL_CHARS else auto_head
        default_tail = DEFAULT_TAIL_CHARS if threshold > DEFAULT_HEAD_CHARS + DEFAULT_TAIL_CHARS else auto_tail
        head = _coerce_non_bool_int(prune_cfg["head_chars"], default_head) if has_head else default_head
        tail = _coerce_non_bool_int(prune_cfg["tail_chars"], default_tail) if has_tail else default_tail
    except (TypeError, ValueError):
        return defaults
    if head < 0 or tail < 0 or threshold <= head + tail:
        return (threshold, *_proportional_head_tail(threshold))
    return threshold, head, tail


def prune_tool_result(
    text: str,
    *,
    threshold_chars: int = DEFAULT_THRESHOLD_CHARS,
    head_chars: int | None = None,
    tail_chars: int | None = None,
) -> str:
    """Replay-safe, model-free head/middle/tail pruning for tool-result payloads."""
    if not isinstance(text, str):
        raise TypeError("text must be a str")
    if (
        head_chars is None
        and tail_chars is None
        and not isinstance(threshold_chars, bool)
        and isinstance(threshold_chars, int)
        and 2 <= threshold_chars <= DEFAULT_HEAD_CHARS + DEFAULT_TAIL_CHARS
    ):
        resolved_head, resolved_tail = _proportional_head_tail(threshold_chars)
    else:
        resolved_head = DEFAULT_HEAD_CHARS if head_chars is None else head_chars
        resolved_tail = DEFAULT_TAIL_CHARS if tail_chars is None else tail_chars
    if (
        isinstance(threshold_chars, bool)
        or isinstance(resolved_head, bool)
        or isinstance(resolved_tail, bool)
        or resolved_head < 0
        or resolved_tail < 0
        or threshold_chars <= resolved_head + resolved_tail
    ):
        raise ValueError("Invalid pruner bounds: require threshold_chars > head_chars + tail_chars >= 0")
    if len(text) <= threshold_chars:
        return text
    tail_part = text[-resolved_tail:] if resolved_tail > 0 else ""
    return f"{text[:resolved_head]}{PRUNE_MARKER}{tail_part}"


def _build_json_pruned_envelope(parsed: object, raw_text: str, pruned_preview: str) -> str:
    envelope: dict[str, object] = {}
    if isinstance(parsed, Mapping):
        for key in _SCALAR_ENVELOPE_KEYS:
            val = parsed.get(key)
            if isinstance(val, (bool, int, float)) or val is None or (isinstance(val, str) and len(val) <= 256):
                envelope[key] = val
    envelope["_pruned"] = True
    envelope["original_type"] = "list" if isinstance(parsed, list) else "dict"
    envelope["original_chars"] = len(raw_text)
    envelope["pruned_preview"] = pruned_preview
    return json.dumps(envelope, ensure_ascii=False)


def prune_mcp_text_payload(
    text: str,
    *,
    threshold_chars: int = DEFAULT_THRESHOLD_CHARS,
    head_chars: int | None = None,
    tail_chars: int | None = None,
) -> str:
    """Prune an MCP text block while preserving valid JSON syntax for structured payloads."""
    if len(text) <= threshold_chars:
        return text
    stripped = text.lstrip()
    if stripped.startswith(("{", "[")):
        try:
            parsed = json.loads(text)
        except json.JSONDecodeError:
            parsed = None
        if isinstance(parsed, (Mapping, list)):
            compact = json.dumps(parsed, ensure_ascii=False, separators=(",", ":"))
            if len(compact) <= threshold_chars:
                return compact
            preview = prune_tool_result(
                compact,
                threshold_chars=threshold_chars,
                head_chars=head_chars,
                tail_chars=tail_chars,
            )
            return _build_json_pruned_envelope(parsed, text, preview)
    return prune_tool_result(
        text,
        threshold_chars=threshold_chars,
        head_chars=head_chars,
        tail_chars=tail_chars,
    )


def _resolve_root_posix(base_dir: str | Path | None) -> str:
    if base_dir is None:
        raw_base = _DEFAULT_REPO_ROOT_POSIX
    else:
        raw_base = base_dir.as_posix() if isinstance(base_dir, Path) else str(base_dir).replace("\\", "/")
    return _canonical_posix(raw_base).rstrip("/") or "/"


def _canonical_posix(path: str) -> str:
    """Resolve symlinks of existing prefixes for absolute paths; lexical normpath otherwise."""
    normed = os.path.realpath(path) if path.startswith("/") else posixpath.normpath(path)
    return "/" + normed.lstrip("/") if normed.startswith("//") else normed


def _scope_key(normed: str, root_posix: str) -> str:
    """Anchored, case- and Unicode-insensitive comparison key (fail-closed over-approximation)."""
    anchored = normed if normed.startswith("/") else posixpath.normpath(posixpath.join(root_posix, normed))
    return unicodedata.normalize("NFD", unicodedata.normalize("NFD", anchored).casefold())


def normalize_write_scope(scope: str, *, base_dir: str | Path | None = None) -> str:
    """Normalize a relative or absolute write scope path without trailing slash."""
    if not isinstance(scope, str):
        raise TypeError("write_scope must be a str")
    cleaned = scope.strip().replace("\\", "/")
    if not cleaned or "\x00" in cleaned:
        raise ValueError("write_scope must be a non-empty path without NUL bytes")
    if cleaned.startswith("~"):
        cleaned = posixpath.expanduser(cleaned)
        if cleaned.startswith("~"):
            raise ValueError("write_scope has an unresolvable '~' home prefix")
    parts = cleaned.split("/")
    for idx, part in enumerate(parts):
        if _GLOB_CHARS.search(part):
            # Fail-closed: a wildcard scope is widened to its literal parent directory.
            cleaned = "/".join(parts[:idx]) or ("/" if cleaned.startswith("/") else ".")
            break
    root_posix = _resolve_root_posix(base_dir)
    normed = _canonical_posix(cleaned if cleaned.startswith("/") else posixpath.join(root_posix, cleaned))
    if normed == root_posix:
        return "."
    if root_posix != "/" and normed.startswith(f"{root_posix}/"):
        rel = normed[len(root_posix) + 1 :].rstrip("/")
        return rel or "."
    if normed in (".", ""):
        return "."
    return normed.rstrip("/") or "/"


def scopes_overlap(left: str, right: str, *, base_dir: str | Path | None = None) -> bool:
    """Return True iff two normalized file or directory write scopes overlap."""
    nl = normalize_write_scope(left, base_dir=base_dir)
    nr = normalize_write_scope(right, base_dir=base_dir)
    root_posix = _resolve_root_posix(base_dir)
    kl = _scope_key(nl, root_posix)
    kr = _scope_key(nr, root_posix)
    if kl == kr or kl == "/" or kr == "/":
        return True
    if kl.startswith("/") != kr.startswith("/"):
        return True  # Fail-closed: an absolute and an unanchored relative scope are not comparable.
    return kl.startswith(f"{kr}/") or kr.startswith(f"{kl}/")


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


def _safe_comment(text: str) -> str:
    """Collapse all whitespace/line separators and escape non-printable chars for a one-line comment."""
    flat = " ".join(text.split())
    return "".join(ch if ch.isprintable() else ch.encode("unicode_escape").decode("ascii") for ch in flat)


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
        desc = _safe_comment(str(tool.get("description", "")))
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
