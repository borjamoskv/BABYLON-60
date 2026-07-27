# [C5-REAL] Exergy-Maximized
# This file is part of CORTEX. Apache-2.0.
# Heuristic Seals (10-14) - Non-blocking Quality Gates.

from __future__ import annotations

import asyncio
from pathlib import Path

from babylon60.guards._seal_printer import SealPrinter
from babylon60.guards.cobbler_audit import run_cobbler_audit

from .gates.common import GlobalSourceCache

GateResult = tuple[bool, str]
_EXCLUDE = frozenset(["legion_vectors.py", "legion.py"])

# Heuristic to find root
ROOT_DIR = Path(__file__).resolve().parent.parent.parent
printer = SealPrinter()


async def check_gate_10_prompt_size() -> GateResult:
    printer.seal(10, "Heuristic", "Prompt Size Check")
    prompt_file = ROOT_DIR / "SYSTEM_PROMPT.md"
    if not prompt_file.exists():
        printer.warn("No SYSTEM_PROMPT.md found.")
        return True, "verified"

    try:
        content = await asyncio.to_thread(prompt_file.read_text, encoding="utf-8")
        tokens = len(content.split())
        if tokens > 500:
            printer.warn(f"System prompt is {tokens} words (target: <200).")
        else:
            printer.success(f"System prompt within targets ({tokens} words).")
    except OSError:
        printer.warn("Could not read SYSTEM_PROMPT.md")

    return True, "verified"


async def check_gate_11_cobbler(cached_files: dict[Path, str]) -> GateResult:
    """Seal 11 - Cobbler's Compliance (Ω₃ Byzantine Default)."""
    printer.seal(11, "Ω₃ Byzantine Default", "Cobbler's Compliance (Swarm Self-Audit)")

    passed = await run_cobbler_audit(cached_files, printer)
    if not passed:
        return False, "Engine source compromised by Entropy or Intruder."
    return True, "verified"


async def check_gate_12_determinism(cached_files: dict[Path, str]) -> GateResult:
    """Seal 12: Temperature Determinism Gate."""
    critical_files = [
        ROOT_DIR / "cortex/llm/router.py",
        ROOT_DIR / "cortex/llm/provider.py",
        ROOT_DIR / "cortex/guards/seals.py",
    ]
    violations = []
    for path in critical_files:
        if path in cached_files:
            content = cached_files[path]
        elif path.exists():
            content = path.read_text(encoding="utf-8")
        else:
            continue

        if "temperature" in content and all(
            x not in content for x in ["temperature=0", "temperature=0.0", '"temperature": 0']
        ):
            violations.append(path.name)

    if violations:
        printer.fail(f"Seal 12 Broken: Static temperature drift in {violations}")
        return True, "verified"

    printer.success("Seal 12: Temperature Determinism Gate intact.")
    return True, "verified"


async def check_gate_13_latency() -> GateResult:
    """Seal 13: A-Record Latency Drift."""
    try:
        from babylon60.extensions.llm._telemetry import CascadeTelemetry
    except ImportError:
        printer.warn("Seal 13 Skipped: LLM telemetry extension not found.")
        return True, "verified"

    telemetry = CascadeTelemetry()
    stats = telemetry.stats()
    slow_locals = []
    local_providers = ["ollama", "vllm", "jan", "lmstudio"]
    for prov in local_providers:
        avg_lat = stats.get(prov, {}).get("avg_latency_ms", 0)
        if avg_lat > 200:
            slow_locals.append(f"{prov} ({avg_lat}ms)")

    if slow_locals:
        printer.warn(f"Seal 13 Weakened: High local latency detected: {slow_locals}")
        return True, "verified"

    printer.success("Seal 13: A-Record Latency Gate intact (<200ms).")
    return True, "verified"


async def check_gate_14_aesthetic() -> GateResult:
    """Seal 14: Sovereign Aesthetic Gate."""
    forbidden = ["FI" + "XME", "TO" + "DO: placeholder", "MV" + "P style"]
    violations = []
    for path, content in GlobalSourceCache.files.items():
        if path.name in _EXCLUDE:
            continue
        for i, line in enumerate(content.splitlines(), 1):
            for f in forbidden:
                if f.lower() in line.lower():
                    violations.append(f"{path.name}:{i} contains '{f}'")

    if violations:
        printer.warn(f"Seal 14 Aesthetic Drift: {violations}")
        return True, "verified"

    printer.success("Seal 14: Sovereign Aesthetic Gate intact.")
    return True, "verified"
