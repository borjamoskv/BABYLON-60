#!/usr/bin/env python3
"""Audit instruction bytes and rule triggers; optionally inspect host listener telemetry.

Counts canonical root instructions once. Byte-based token estimates do not
measure the context actually loaded by an IDE or certify runtime behavior.
"""

from __future__ import annotations

import argparse
from contextlib import closing
from pathlib import Path
import sqlite3
import sys
from typing import TypedDict

if __package__:
    from .governance_documents import MAX_ROOT_INSTRUCTION_BYTES, ROOT_INSTRUCTIONS
else:
    from governance_documents import MAX_ROOT_INSTRUCTION_BYTES, ROOT_INSTRUCTIONS

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


class RuleMetadata(TypedDict):
    name: str
    path: Path
    size: int
    has_fm: bool
    trigger: str | None


def scan_rules_dir(rules_dir: Path) -> list[RuleMetadata]:
    results: list[RuleMetadata] = []
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


class LedgerTelemetryError(RuntimeError):
    """The listener database could not be checked."""


def audit_ghost_listeners(db_path: Path, fix: bool = False) -> tuple[int, int]:
    """Return (running_count, not_fully_idle_count)."""
    if not db_path.is_file():
        raise LedgerTelemetryError(f"NO_VERIFICADO: missing telemetry database: {db_path}")
    try:
        mode = "rw" if fix else "ro"
        with closing(sqlite3.connect(f"{db_path.absolute().as_uri()}?mode={mode}", uri=True, timeout=5.0)) as conn:
            with conn:
                if fix:
                    conn.execute(
                        "UPDATE conversation_summaries "
                        "SET status = 'CASCADE_RUN_STATUS_IDLE', not_fully_idle = 0 "
                        "WHERE status = 'CASCADE_RUN_STATUS_RUNNING' OR not_fully_idle = 1"
                    )
                running = conn.execute(
                    "SELECT count(*) FROM conversation_summaries WHERE status = 'CASCADE_RUN_STATUS_RUNNING'"
                ).fetchone()[0]
                not_idle = conn.execute(
                    "SELECT count(*) FROM conversation_summaries WHERE not_fully_idle = 1"
                ).fetchone()[0]
                return int(running), int(not_idle)
    except sqlite3.Error as exc:
        raise LedgerTelemetryError(f"NO_VERIFICADO: SQLite telemetry: {db_path}: {exc}") from exc


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--workspace",
        type=Path,
        default=Path(__file__).absolute().parents[2],
        help="Path to the workspace root",
    )
    parser.add_argument(
        "--global-config",
        type=Path,
        default=Path.home() / ".gemini" / "config",
        help="Path to ~/.gemini/config",
    )
    parser.add_argument("--workspace-only", action="store_true", help="Omit global rules; telemetry is controlled separately")
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
    parser.add_argument(
        "--skip-ghost-listeners",
        action="store_true",
        help="Explicitly omit host telemetry (e.g. CI); report NOT_CHECKED",
    )
    parser.add_argument(
        "--telemetry-db", type=Path, default=Path.home() / ".gemini/antigravity/conversation_summaries.db"
    )
    args = parser.parse_args()
    if args.skip_ghost_listeners and args.fix_ghosts:
        parser.error("--fix-ghosts cannot be combined with --skip-ghost-listeners")

    try:
        global_rules = [] if args.workspace_only else scan_rules_dir(args.global_config / "rules")
        ws_rules = scan_rules_dir(args.workspace / ".agents" / "rules")
        instruction_sizes = {}
        for name in ROOT_INSTRUCTIONS:
            path = args.workspace / name
            if path.is_symlink() or not path.is_file():
                raise ValueError(f"{path}: expected a regular instruction file")
            instruction_sizes[name] = len(path.read_bytes())
    except (OSError, ValueError) as exc:
        print(f"NO_VERIFICADO: {exc}", file=sys.stderr)
        return 2

    errors: list[str] = []
    instruction_bytes = sum(instruction_sizes.values())
    always_on_bytes = instruction_bytes
    if instruction_bytes > MAX_ROOT_INSTRUCTION_BYTES:
        errors.append(f"ROOT INSTRUCTIONS BUDGET EXCEEDED: {instruction_bytes:,} B > {MAX_ROOT_INSTRUCTION_BYTES:,} B")

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
                errors.append(f"DUPLICATE ALWAYS_ON RULE IN GLOBAL & WORKSPACE: {r['name']}")

    if always_on_bytes > args.max_always_on_bytes:
        errors.append(f"ALWAYS_ON BUDGET EXCEEDED: {always_on_bytes:,} B > {args.max_always_on_bytes:,} B")

    if args.skip_ghost_listeners:
        listener_status = "NOT_CHECKED (explicitly skipped)"
    else:
        try:
            running, not_idle = audit_ghost_listeners(args.telemetry_db, fix=args.fix_ghosts)
        except LedgerTelemetryError as exc:
            print(str(exc), file=sys.stderr)
            return 2
        listener_status = f"RUNNING={running}, not_fully_idle={not_idle}"

    def tok(size: int) -> int:
        return size // 4

    print("=== [C5-REAL] AUDITORÍA DE PRESUPUESTO DE TOKENS ===")
    for name, size in instruction_sizes.items():
        print(f"■ {name} (workspace, counted once): {size:,} B (~{tok(size):,} estimated tokens)")
    if args.workspace_only:
        print("■ Global rules: NOT_CHECKED (workspace-only)")
    g_ao = [r for r in global_rules if r["trigger"] == "always_on"]
    w_ao = [r for r in ws_rules if r["trigger"] == "always_on"]
    print(
        f"■ Reglas always_on (Global: {len(g_ao)}, Workspace: {len(w_ao)}): "
        f"{always_on_bytes - instruction_bytes:,} B (~{tok(always_on_bytes - instruction_bytes):,} estimated tokens)"
    )
    print(
        f"■ INSPECTED ALWAYS_ON: {always_on_bytes:,} B / {args.max_always_on_bytes:,} B "
        f"(~{tok(always_on_bytes):,} estimated tokens; actual client context not measured)"
    )
    g_md = [r for r in global_rules if r["trigger"] == "model_decision"]
    w_md = [r for r in ws_rules if r["trigger"] == "model_decision"]
    print(
        f"■ Reglas condicionales (model_decision): {len(g_md)} global + {len(w_md)} workspace "
        "(bodies excluded from this budget; client loading not measured)"
    )
    print(f"■ Ghost Listeners (conversation_summaries.db): {listener_status}")

    if errors:
        for err in errors:
            print(f"FAIL: {err}", file=sys.stderr)
        return 1

    if args.workspace_only:
        print("PASS: Workspace token budget within inline ceiling; global rules and cross-scope duplicates not checked.")
    else:
        print("PASS: Token budget within inline ceiling and zero duplicate always_on rules.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
