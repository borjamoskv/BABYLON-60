"""
codegen_utils.py — Shared primitives for YAML-to-code generation pipeline.
Extracted from generate_*.py scripts (C5-REAL DRY enforcement).
DO NOT duplicate parse_yaml or write_output in individual generators.
"""
from __future__ import annotations

import os
import re
from typing import Any


def parse_yaml(yaml_path: str) -> tuple[dict[int, str], dict[int, str], dict[int, str]]:
    """Parse a 1000-primitive YAML taxonomy into (domains, primitives, modifiers).

    Expects YAML sections: Domains_Context, Primitives_Action, Modifiers_Constraint.
    Each section contains numbered string entries in the form: ``N: "value"``.

    Returns:
        Tuple of three dicts, each keyed 0-9 mapping to string labels.

    Raises:
        AssertionError: if any section does not yield exactly 10 entries.
    """
    with open(yaml_path) as f:
        content = f.read()

    domains: dict[int, str] = {}
    primitives: dict[int, str] = {}
    modifiers: dict[int, str] = {}
    current_section: str | None = None

    for line in content.splitlines():
        line = line.strip()
        if (
            not line
            or line.startswith("#")
            or line.startswith("Claim:")
            or line.startswith("Proof:")
            or line.startswith("Formula:")
        ):
            continue
        if line.startswith("Domains_Context:"):
            current_section = "domains"
            continue
        elif line.startswith("Primitives_Action:"):
            current_section = "primitives"
            continue
        elif line.startswith("Modifiers_Constraint:"):
            current_section = "modifiers"
            continue

        match = re.match(r"(\d+):\s*\"([^\"]+)\"", line)
        if match:
            idx = int(match.group(1))
            val = match.group(2)
            if current_section == "domains":
                domains[idx] = val
            elif current_section == "primitives":
                primitives[idx] = val
            elif current_section == "modifiers":
                modifiers[idx] = val

    assert len(domains) == 10, f"Expected 10 domains, got {len(domains)}"
    assert len(primitives) == 10, f"Expected 10 primitives, got {len(primitives)}"
    assert len(modifiers) == 10, f"Expected 10 modifiers, got {len(modifiers)}"

    return domains, primitives, modifiers


def write_output(path: str, lines: list[Any]) -> None:
    """Atomically write generated source lines to *path*, creating parent dirs."""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        f.write("\n".join(str(ln) for ln in lines))
    print(f"Generated: {path}")
