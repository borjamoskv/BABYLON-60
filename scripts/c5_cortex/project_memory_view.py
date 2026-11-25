#!/usr/bin/env python3
# ============================================================================
# BABYLON-60 v5.1 Sovereign Hardened
# █ AUTOCOGNITION-Ω | STATE: C5-REAL | CORTEX MEMORY VIEW PROJECTION CLI
# ============================================================================
"""CLI adapter for the deterministic read-only Markdown view of CORTEX memory.

Delegates to `babylon60.memory.memory_view`. The memory root is an explicit
opt-in; the default mode inspects the sources and writes nothing.
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

from babylon60.memory.memory_view import (  # noqa: E402
    check_view,
    project_memory,
    write_view,
)


def project_view(
    memory_root: Path,
    *,
    out_dir: Path | None = None,
    mode: str = "dry-run",
    json_output: bool = False,
) -> int:
    """Run one mode (`dry-run`, `check` or `execute`); returns the process exit code."""
    try:
        if mode != "dry-run" and out_dir is None:
            raise ValueError(f"--out is required with --{mode}")
        projection = project_memory(memory_root)
        if mode == "execute" and out_dir is not None:
            drift = write_view(projection, memory_root, out_dir)
        elif out_dir is not None:
            drift = check_view(projection, out_dir)
        else:
            drift = []
    except (OSError, ValueError) as exc:
        if json_output:
            print(json.dumps({"schema_version": "1.0", "status": "ERROR", "error": str(exc)}, indent=2))
        else:
            print(f"[!] Memory view projection refused: {exc}", file=sys.stderr)
        return 2

    in_sync = not drift
    if mode == "execute":
        status = "WRITTEN"
    elif out_dir is None:
        status = "PROJECTED"
    else:
        status = "IN_SYNC" if in_sync else "DRIFT"
    if json_output:
        payload = {
            "schema_version": "1.0",
            "type": "C5_MEMORY_VIEW",
            "status": status,
            "mode": mode,
            "manifest_b3": projection.manifest_b3,
            "sources": len(projection.sources),
            "blocks": projection.block_count,
            "pages": sorted(projection.pages),
            "drift": [{"page": item.page, "kind": item.kind} for item in drift],
        }
        print(json.dumps(payload, indent=2, ensure_ascii=False))
    else:
        print(
            f"[CORTEX-VIEW] status={status} mode={mode} sources={len(projection.sources)} "
            f"blocks={projection.block_count} pages={len(projection.pages)} manifest={projection.manifest_b3}"
        )
        for item in drift:
            print(f"  {item.kind:8} {item.page}")
    return 1 if mode == "check" and not in_sync else 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Project CORTEX JSON memory into a read-only Markdown view")
    parser.add_argument("--memory-root", type=Path, required=True, help="Explicit memory directory to read")
    parser.add_argument("--out", type=Path, default=None, help="View directory (required with --check/--execute)")
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--dry-run", action="store_true", help="Read sources and report without writing (default)")
    mode.add_argument("--check", action="store_true", help="Exit 1 if the view on disk differs from the sources")
    mode.add_argument("--execute", action="store_true", help="Write the view and prune pages with no source")
    parser.add_argument("--json", action="store_true", help="Emit JSON payload for M2M")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    mode = "execute" if args.execute else "check" if args.check else "dry-run"
    return project_view(args.memory_root, out_dir=args.out, mode=mode, json_output=args.json)


if __name__ == "__main__":
    raise SystemExit(main())
