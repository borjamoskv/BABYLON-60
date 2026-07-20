#!/usr/bin/env python3
"""
anergy_ratio.py — C5-REAL Anergy Ratio Instrument
===================================================
Falsification tool based on Robinson Resolution isomorphism.
Measures the thermodynamic dead-weight fraction of LLM output.

Metric:
    A(n) = 1 - |{steps with Δ_disk ≠ ∅}| / |{model steps}|

Classification heuristic:
    EXERGY (Δ_disk ≠ ∅):
        - Tool calls: run_command, write_to_file, replace_file_content,
          multi_replace_file_content, call_mcp_tool (write ops)
        - Git mutations detected in command output
    ANERGY (Δ_disk = ∅):
        - Pure prose responses without tool calls
        - view_file, grep_search, list_dir (read-only, no state mutation)
        - ask_question, ask_permission (meta-ops, no disk change)
        - Error loops (repeated identical commands)

Usage:
    python3 scripts/anergy_ratio.py <transcript.jsonl> [--output results.json]
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any


# Tools that mutate disk state
EXERGY_TOOLS: frozenset[str] = frozenset({
    "run_command",
    "write_to_file",
    "replace_file_content",
    "multi_replace_file_content",
    "call_mcp_tool",
    "invoke_subagent",
    "generate_image",
})

# Tools that are read-only (no state mutation)
ANERGY_TOOLS: frozenset[str] = frozenset({
    "view_file",
    "grep_search",
    "list_dir",
    "search_web",
    "read_url_content",
    "ask_question",
    "ask_permission",
    "list_permissions",
    "list_resources",
    "command_status",
    "manage_subagents",
    "manage_task",
    "schedule",
    "send_message",
    "read_resource",
})

# Commands that are read-only even via run_command
READ_ONLY_COMMANDS: tuple[str, ...] = (
    "cat ", "ls ", "find ", "head ", "tail ", "wc ",
    "grep ", "stat ", "echo ", "which ", "type ",
    "python3 -c", "vm_stat", "sysctl ", "top ",
    "memory_pressure", "git log", "git status",
    "git diff", "git branch", "git show",
)


def classify_tool_call(tool: dict[str, Any]) -> str:
    """Classify a single tool call as 'exergy' or 'anergy'."""
    name = tool.get("name", "")

    if name in ANERGY_TOOLS:
        return "anergy"

    if name in EXERGY_TOOLS:
        if name == "run_command":
            args = tool.get("args", {})
            cmd = args.get("CommandLine", "")
            if any(cmd.strip().startswith(prefix) for prefix in READ_ONLY_COMMANDS):
                return "anergy"
            return "exergy"
        return "exergy"

    # Unknown tool → conservative: anergy
    return "anergy"


def classify_step(step: dict[str, Any]) -> dict[str, Any]:
    """Classify a transcript step and return enriched record."""
    step_type = step.get("type", "")
    source = step.get("source", "")
    step_index = step.get("step_index", -1)
    tool_calls = step.get("tool_calls", []) or []
    content = step.get("content", "") or ""

    # Only classify MODEL responses
    if source != "MODEL":
        return {
            "step_index": step_index,
            "type": step_type,
            "source": source,
            "classification": "skip",
            "reason": "non-model step",
        }

    if not tool_calls:
        # Pure prose response — anergy by definition
        content_len = len(content)
        return {
            "step_index": step_index,
            "type": step_type,
            "source": source,
            "classification": "anergy",
            "reason": "pure prose, no tool calls",
            "content_bytes": content_len,
        }

    # Classify based on tool calls
    tool_classifications: list[str] = []
    tool_names: list[str] = []
    for tc in tool_calls:
        c = classify_tool_call(tc)
        tool_classifications.append(c)
        tool_names.append(tc.get("name", "?"))

    # If ANY tool call is exergy, the step is exergy
    has_exergy = "exergy" in tool_classifications
    classification = "exergy" if has_exergy else "anergy"

    return {
        "step_index": step_index,
        "type": step_type,
        "source": source,
        "classification": classification,
        "tools": tool_names,
        "tool_classifications": tool_classifications,
        "reason": f"tools: {', '.join(tool_names)}",
    }


def compute_anergy_ratio(transcript_path: Path) -> dict[str, Any]:
    """Compute the Anergy Ratio A(n) for a transcript."""
    steps: list[dict[str, Any]] = []
    with open(transcript_path) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                steps.append(json.loads(line))
            except json.JSONDecodeError:
                continue  # skip malformed lines

    classified: list[dict[str, Any]] = []
    model_steps = 0
    exergy_steps = 0
    anergy_steps = 0
    running_ratios: list[float] = []

    for step in steps:
        record = classify_step(step)
        classified.append(record)

        if record["classification"] == "skip":
            continue

        model_steps += 1
        if record["classification"] == "exergy":
            exergy_steps += 1
        else:
            anergy_steps += 1

        # Running A(n)
        a_n = 1.0 - (exergy_steps / model_steps)
        running_ratios.append(round(a_n, 4))

    # Final metrics
    final_anergy = running_ratios[-1] if running_ratios else 0.0
    final_exergy = 1.0 - final_anergy

    # Detect loops: consecutive identical tool sequences
    loop_count = 0
    prev_tools: list[str] | None = None
    for rec in classified:
        if rec["classification"] == "skip":
            continue
        curr_tools = rec.get("tools")
        if curr_tools and curr_tools == prev_tools:
            loop_count += 1
        prev_tools = curr_tools

    return {
        "transcript": str(transcript_path),
        "total_steps": len(steps),
        "model_steps": model_steps,
        "exergy_steps": exergy_steps,
        "anergy_steps": anergy_steps,
        "anergy_ratio": round(final_anergy, 4),
        "exergy_ratio": round(final_exergy, 4),
        "loop_count": loop_count,
        "curve_A_n": running_ratios,
        "classified_steps": classified,
    }


def main() -> None:
    if len(sys.argv) < 2:
        print(f"Usage: {sys.argv[0]} <transcript.jsonl> [--output results.json]")
        sys.exit(1)

    transcript_path = Path(sys.argv[1])
    if not transcript_path.exists():
        print(f"ERROR: {transcript_path} not found")
        sys.exit(1)

    output_path: Path | None = None
    if "--output" in sys.argv:
        idx = sys.argv.index("--output")
        if idx + 1 < len(sys.argv):
            output_path = Path(sys.argv[idx + 1])

    result = compute_anergy_ratio(transcript_path)

    # Summary to stdout
    print(f"{'='*60}")
    print("  ANERGY RATIO INSTRUMENT — C5-REAL")
    print(f"{'='*60}")
    print(f"  Transcript:    {result['transcript']}")
    print(f"  Total steps:   {result['total_steps']}")
    print(f"  Model steps:   {result['model_steps']}")
    print(f"  Exergy steps:  {result['exergy_steps']}")
    print(f"  Anergy steps:  {result['anergy_steps']}")
    print(f"  Loop repeats:  {result['loop_count']}")
    print(f"{'='*60}")
    print(f"  ANERGY RATIO A(n) = {result['anergy_ratio']:.4f}")
    print(f"  EXERGY RATIO E(n) = {result['exergy_ratio']:.4f}")
    print(f"{'='*60}")

    # Curve summary (last 10 points)
    curve = result["curve_A_n"]
    if len(curve) > 10:
        print(f"\n  A(n) curve (last 10 of {len(curve)} points):")
        for i, val in enumerate(curve[-10:]):
            n = len(curve) - 10 + i + 1
            bar = "█" * int(val * 40)
            print(f"    n={n:4d}  A={val:.4f}  {bar}")
    elif curve:
        print(f"\n  A(n) curve ({len(curve)} points):")
        for i, val in enumerate(curve):
            bar = "█" * int(val * 40)
            print(f"    n={i+1:4d}  A={val:.4f}  {bar}")

    if output_path:
        # Write full results (exclude classified_steps for compact output)
        compact = {k: v for k, v in result.items() if k != "classified_steps"}
        with open(output_path, "w") as f:
            json.dump(compact, f, indent=2)
        print(f"\n  Results written to: {output_path}")


if __name__ == "__main__":
    main()
