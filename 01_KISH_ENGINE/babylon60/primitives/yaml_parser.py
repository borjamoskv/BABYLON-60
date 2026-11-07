#!/usr/bin/env python3
# ============================================================================
# BABYLON-60 v4.0 Sovereign Hardened
# █ AUTOCOGNITION-Ω | STATE: C5-REAL | AESTHETIC: INDUSTRIAL_NOIR_2026
# ============================================================================
"""
yaml_parser.py - Zero-Dependency YAML Subset Scanner & Parser.

Provides clean, safe parsing and dumping of standard YAML configuration structures
without external third-party dependencies under C5-REAL nesting depth invariants.
"""

import re
from typing import Any, Dict, List, Tuple


def _parse_scalar(val: str) -> Any:
    val = val.strip()
    if not val or val.lower() in ("null", "~"):
        return None
    if val.lower() in ("true", "yes", "on"):
        return True
    if val.lower() in ("false", "no", "off"):
        return False
    if (val.startswith('"') and val.endswith('"')) or (val.startswith("'") and val.endswith("'")):
        return val[1:-1]

    try:
        return int(val)
    except ValueError:
        pass

    try:
        return float(val)
    except ValueError:
        pass

    return val


def _pop_stack(stack: List[Tuple[int, Any, Any, Any]], indent: int) -> None:
    while len(stack) > 1 and stack[-1][0] >= indent:
        stack.pop()


def _handle_list_item(stripped: str, stack: List[Tuple[int, Any, Any, Any]]) -> None:
    item_str = stripped[2:].strip()
    item_val = _parse_scalar(item_str)
    cur_indent, parent, p_dict, p_key = stack[-1]

    if isinstance(parent, dict) and not parent and p_dict is not None and p_key is not None:
        new_list: List[Any] = []
        p_dict[p_key] = new_list
        stack[-1] = (cur_indent, new_list, p_dict, p_key)
        parent = new_list

    if isinstance(parent, list):
        parent.append(item_val)


def _handle_key_value(stripped: str, indent: int, stack: List[Tuple[int, Any, Any, Any]]) -> None:
    key_part, val_part = stripped.split(":", 1)
    key = key_part.strip()
    val_str = val_part.strip()
    _, parent, _, _ = stack[-1]

    if not val_str:
        new_dict: Dict[str, Any] = {}
        if isinstance(parent, dict):
            parent[key] = new_dict
        stack.append((indent, new_dict, parent, key))
    elif isinstance(parent, dict):
        parent[key] = _parse_scalar(val_str)


def parse_yaml(content: str) -> Dict[str, Any]:
    """Parses a subset of YAML into Python dicts (Nesting depth <= 4)."""
    lines = content.splitlines()
    root: Dict[str, Any] = {}
    stack: List[Tuple[int, Any, Any, Any]] = [(-1, root, None, None)]

    for line_raw in lines:
        line = re.sub(r"#.*$", "", line_raw).rstrip()
        if not line.strip():
            continue

        indent = len(line_raw) - len(line_raw.lstrip(" "))
        stripped = line.strip()

        _pop_stack(stack, indent)

        if stripped.startswith("- "):
            _handle_list_item(stripped, stack)
        elif ":" in stripped:
            _handle_key_value(stripped, indent, stack)

    return root


def dump_yaml(data: Any, indent_level: int = 0) -> str:
    """Serializes a Python dict/list structure into clean YAML string."""
    lines = []
    prefix = "  " * indent_level

    if isinstance(data, dict):
        for k, v in data.items():
            if isinstance(v, (dict, list)):
                lines.append(f"{prefix}{k}:")
                lines.append(dump_yaml(v, indent_level + 1))
            else:
                fmt_v = "null" if v is None else str(v).lower() if isinstance(v, bool) else str(v)
                lines.append(f"{prefix}{k}: {fmt_v}")
    elif isinstance(data, list):
        for item in data:
            if isinstance(item, (dict, list)):
                lines.append(f"{prefix}-")
                lines.append(dump_yaml(item, indent_level + 1))
            else:
                fmt_v = "null" if item is None else str(item).lower() if isinstance(item, bool) else str(item)
                lines.append(f"{prefix}- {fmt_v}")

    return "\n".join(lines)
