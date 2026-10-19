#!/usr/bin/env python3
"""C5-REAL Ring-0 Token Budget & Context Anergy Gate.

Audits Antigravity IDE rule files (global and workspace), AGENTS.md, and
conversation_summaries.db to prevent prompt prefill bloat, duplicate rule
injections, missing trigger frontmatters, and ghost listeners.
"""

from __future__ import annotations

import argparse
import glob
import os
from pathlib import Path
import sqlite3
import sys

MAX_ALWAYS_ON_BYTES = 40_000  # ~10,000 tokens inline budget ceiling


def parse_rule_trigger(path: Path) -> tuple[bool, str | None]:
    """Return (has_frontmatter, trigger_value)."""
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError:
        return False, None
    if not lines or lines[0].strip() != "---":
        return False, None
    for idx in range(1, min(25, len(lines))):
        line = lines[idx].strip()
        if line == "---":
            break
        if line.startswith("trigger:"):
            val = line.split(":", 1)[1].strip().strip('"').strip("'")
            return True, val
    return True, None


def scan_rules_dir(rules_dir: Path) -> list[dict[str, object]]:
    results: list[dict[str, object]] = []
    if not rules_dir.is_dir():
        return results
    for md_path in sorted(rules_dir.glob("*.md")):
        has_fm, trigger = parse_rule_trigger(md_path)
        size = md_path.stat().st_size
        results.append(
            {
                "name": md_path.name,
                "path": md_path,
                "size": size,
                "has_fm": has_fm,
                "trigger": trigger,
            }
        )
    return results


def audit_ghost_listeners(db_path: Path, fix: bool = False) -> tuple[int, int]:
    """Return (running_count, not_fully_idle_count)."""
    if not db_path.is_file():
        return 0, 0
    try:
        conn = sqlite3.connect(str(db_path))
        cur = conn.cursor()
        if fix:
            cur.execute(
                "UPDATE conversation_summaries "
                "SET status = 'CASCADE_RUN_STATUS_IDLE', not_fully_idle = 0 "
                "WHERE status = 'CASCADE_RUN_STATUS_RUNNING' OR not_fully_idle = 1"
            )
            conn.commit()
        cur.execute(
            "SELECT count(*) FROM conversation_summaries "
            "WHERE status = 'CASCADE_RUN_STATUS_RUNNING'"
        )
        running = int(cur.fetchone()[0])
        cur.execute(
            "SELECT count(*) FROM conversation_summaries WHERE not_fully_idle = 1"
        )
        not_idle = int(cur.fetchone()[0])
        conn.close()
        return running, not_idle
    except sqlite3.Error:
        return 0, 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--workspace",
        type=Path,
        default=Path(__file__).resolve().parents[2],
        help="Path to the workspace root",
    )
    parser.add_argument(
        "--global-config",
        type=Path,
        default=Path.home() / ".gemini" / "config",
        help="Path to ~/.gemini/config",
    )
    parser.add_argument(
        "--max-always-on-bytes",
        type=int,
        default=MAX_ALWAYS_ON_BYTES,
        help="Maximum allowed bytes for all always_on rules combined",
    )
    parser.add_argument(
        "--fix-ghosts",
        action="store_true",
        help="Reset ghost listeners in conversation_summaries.db to IDLE",
    )
    args = parser.parse_args()

    global_rules = scan_rules_dir(args.global_config / "rules")
    ws_rules = scan_rules_dir(args.workspace / ".agents" / "rules")

    errors: list[str] = []
    always_on_bytes = 0

    ws_agents = args.workspace / "AGENTS.md"
    if ws_agents.is_file():
        ws_agents_size = ws_agents.stat().st_size
        always_on_bytes += ws_agents_size
    else:
        ws_agents_size = 0

    global_always_on_names: set[str] = set()
    for r in global_rules:
        if not r["trigger"]:
            errors.append(f"GLOBAL RULE MISSING TRIGGER: {r['name']}")
        elif r["trigger"] == "always_on":
            always_on_bytes += int(r["size"])
            global_always_on_names.add(str(r["name"]))

    for r in ws_rules:
        if not r["trigger"]:
            errors.append(f"WORKSPACE RULE MISSING TRIGGER: {r['name']}")
        elif r["trigger"] == "always_on":
            always_on_bytes += int(r["size"])
            if str(r["name"]) in global_always_on_names:
                errors.append(
                    f"DUPLICATE ALWAYS_ON RULE IN GLOBAL & WORKSPACE: {r['name']}"
                )

    if always_on_bytes > args.max_always_on_bytes:
        errors.append(
            f"ALWAYS_ON BUDGET EXCEEDED: {always_on_bytes:,} B > {args.max_always_on_bytes:,} B"
        )

    db_path = Path.home() / ".gemini" / "antigravity" / "conversation_summaries.db"
    running, not_idle = audit_ghost_listeners(db_path, fix=args.fix_ghosts)

    tok = lambda b: b // 4
    print("=== [C5-REAL] AUDITORÍA DE PRESUPUESTO DE TOKENS ===")
    print(
        f"■ AGENTS.md (workspace): {ws_agents_size:,} B (~{tok(ws_agents_size):,} tok)"
    )
    g_ao = [r for r in global_rules if r["trigger"] == "always_on"]
    w_ao = [r for r in ws_rules if r["trigger"] == "always_on"]
    print(
        f"■ Reglas always_on (Global: {len(g_ao)}, Workspace: {len(w_ao)}): "
        f"{always_on_bytes - ws_agents_size:,} B (~{tok(always_on_bytes - ws_agents_size):,} tok)"
    )
    print(
        f"■ TOTAL PREFILL ALWAYS_ON: {always_on_bytes:,} B / {args.max_always_on_bytes:,} B "
        f"(~{tok(always_on_bytes):,} tok)"
    )
    g_md = [r for r in global_rules if r["trigger"] == "model_decision"]
    w_md = [r for r in ws_rules if r["trigger"] == "model_decision"]
    print(
        f"■ Reglas condicionales (model_decision): {len(g_md)} global + {len(w_md)} workspace "
        "(0 tokens de prefill fijo; solo descripción)"
    )
    print(
        f"■ Ghost Listeners (conversation_summaries.db): RUNNING={running}, not_fully_idle={not_idle}"
    )

    if errors:
        for err in errors:
            print(f"FAIL: {err}", file=sys.stderr)
        return 1

    print("PASS: Token budget within inline ceiling and zero duplicate always_on rules.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
