#!/usr/bin/env python3
# ============================================================================
# BABYLON-60 v5.1 Sovereign Hardened
# █ AUTOCOGNITION-Ω | STATE: C5-REAL | CONVERSATION VAULT CONSOLIDATION CLI
# ============================================================================
"""CLI adapter for deterministic conversation consolidation (`SW100-C0478` fix).

Delegates to `babylon60.memory.conversation_consolidation` with explicit
`--brain-root` opt-in (`C0563`), BLAKE3 logical-tick provenance, SQLite WAL
`synchronous=FULL` persistence outside Git, and read-only source preservation.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Sequence

REPO_ROOT = Path(__file__).absolute().parents[2]
_ENGINE_ROOT = str(REPO_ROOT / "01_KISH_ENGINE")
if _ENGINE_ROOT not in sys.path:
    sys.path.insert(0, _ENGINE_ROOT)

from babylon60.memory.conversation_consolidation import (  # noqa: E402
    consolidate_conversations,
    render_markdown_catalog,
)


def consolidate_vault(
    json_output: bool = False,
    *,
    brain_root: Path | None = None,
    db_path: Path | None = None,
    catalog_ref: Path | None = None,
    catalog_out: Path | None = None,
    dry_run: bool = True,
    logical_tick: int = 60,
    summary_only: bool = False,
) -> int:
    try:
        report = consolidate_conversations(
            brain_root=brain_root,
            db_path=db_path,
            catalog_ref=catalog_ref,
            catalog_out=catalog_out,
            dry_run=dry_run,
            logical_tick=logical_tick,
        )
    except (OSError, ValueError) as exc:
        if json_output:
            print(json.dumps({"schema_version": "2.0", "status": "ERROR", "error": str(exc)}, indent=2))
        else:
            print(f"[!] Conversation consolidation refused: {exc}", file=sys.stderr)
        return 2

    if json_output:
        payload = report.to_dict(include_sessions=not summary_only)
        payload["type"] = "C5_VAULT_CONSOLIDATION"
        payload["metrics"] = {
            "sessions_scanned": report.sessions_scanned,
            "sessions_with_crystals": report.sessions_with_crystals,
            "sessions_already_in_catalog": report.sessions_already_in_catalog,
            "sessions_consolidated_now": report.sessions_persisted_now,
            "artifacts_indexed": report.artifacts_indexed,
            "crystal_md_count": report.crystal_md_count,
            "new_crystal_candidates": report.new_crystal_candidates,
            "already_indexed_crystals": report.already_indexed_crystals,
            "conflicts_count": report.conflicts_count,
        }
        print(json.dumps(payload, indent=2, ensure_ascii=False))
        return 0

    print(
        f"[CORTEX-VAULT] status={report.status} mode={report.mode} "
        f"sessions={report.sessions_scanned} crystals={report.crystal_md_count} "
        f"new={report.new_crystal_candidates} conflicts={report.conflicts_count} "
        f"manifest={report.manifest_b3}"
    )
    if report.brain_root is not None and not summary_only:
        print(render_markdown_catalog(report))
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Consolidate BABYLON-60 conversation vault deterministically")
    parser.add_argument("--brain-root", type=Path, default=None, help="Explicit conversation brain root directory")
    parser.add_argument("--db-path", type=Path, default=None, help="Target SQLite WAL vault DB path (outside repo)")
    parser.add_argument("--catalog-ref", type=Path, default=None, help="Existing Markdown catalog for deduplication")
    parser.add_argument("--catalog-out", type=Path, default=None, help="Target Markdown catalog path for --execute")
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--dry-run", action="store_true", help="Inspect and emit inventory without writing (default)")
    mode.add_argument("--execute", action="store_true", help="Persist consolidated records to WAL DB/catalog")
    parser.add_argument("--logical-tick", type=int, default=60, help="Canonical logical tick (default: 60)")
    parser.add_argument("--summary-only", action="store_true", help="Omit per-session details in output")
    parser.add_argument("--json", action="store_true", help="Emit JSON payload for M2M")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    return consolidate_vault(
        json_output=args.json,
        brain_root=args.brain_root,
        db_path=args.db_path,
        catalog_ref=args.catalog_ref,
        catalog_out=args.catalog_out,
        dry_run=not args.execute,
        logical_tick=args.logical_tick,
        summary_only=args.summary_only,
    )


if __name__ == "__main__":
    raise SystemExit(main())
