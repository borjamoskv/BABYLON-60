#!/usr/bin/env python3
# ============================================================================
# BABYLON-60 v4.0 Sovereign Hardened
# █ AUTOCOGNITION-Ω | STATE: C5-REAL | AESTHETIC: INDUSTRIAL_NOIR_2026
# ============================================================================
"""
MOSKV-1: SHARUR-3600 Audit Swarm Engine (INV_C5_18)
Async file auditor with bounded concurrency (INV_C5_THERMO_VALVE).
Scans workspace for mythological term violations and emits structured telemetry.
"""

import argparse
import asyncio
import json
import logging
import re
import sys
import time
from pathlib import Path
from typing import Any, NotRequired, TypedDict

MYTHOLOGICAL_TERMS: dict[str, str] = {
    r"Ineficiencia": "Ineficiencia",
    r"Filtro de Ruido": "Filtro de Ruido",
    r"Ambigüedad Semántica": "Ambigüedad Semántica",
    r"DSL Restringido": "DSL Restringido",
    r"Alta Densidad Estructural": "Alta Densidad Estructural",
    r"Worker Asíncrono": "Worker Asíncrono",
    r"Workers Asíncronos": "Workers Asíncronos",
    r"Limitado Estrictamente": "Limitado Estrictamente",
    r"Causal-Determinist": "Causal-Determinist",
    r"Sandbox Aislado": "Sandbox Aislado",
    r"Plataforma de Simulación": "Plataforma de Simulación",
    r"Auditor Pre-Commit": "Auditor Pre-Commit",
}

CANONICAL_BRANDS = frozenset({"MOSKV", "CORTEX", "BABYLON-60", "Moskv84"})

SKIP_DIRS = frozenset({".git", "node_modules", "target", "__pycache__", ".venv", ".ruff_cache"})

AUDIT_EXTENSIONS = frozenset({".py", ".rs", ".md", ".b60", ".toml", ".yaml", ".yml"})

MAX_FILE_BYTES = 2 * 1024 * 1024  # 2 MiB guard — skip oversized files


class AuditFileResult(TypedDict):
    path: str
    status: str
    matches: int
    reason: NotRequired[str]
    error: NotRequired[str]


def collect_targets(root: Path) -> list[Path]:
    """Walk directory tree, filtering by extension and skip-dirs."""
    targets: list[Path] = []
    for item in root.rglob("*"):
        if any(skip in item.parts for skip in SKIP_DIRS):
            continue
        if item.is_file() and item.suffix in AUDIT_EXTENSIONS:
            targets.append(item)
    return targets


async def audit_file(
    filepath: Path,
    semaphore: asyncio.Semaphore,
    dry_run: bool = False,
    logger: logging.Logger | None = None,
) -> AuditFileResult:
    """Audit a single file for mythological term violations."""
    result: AuditFileResult = {"path": str(filepath), "status": "CLEAN", "matches": 0}
    async with semaphore:
        try:
            stat = filepath.stat()
            if stat.st_size > MAX_FILE_BYTES:
                result["status"] = "SKIPPED"
                result["reason"] = "exceeds_max_size"
                return result
            if stat.st_size == 0:
                return result

            content = filepath.read_text(encoding="utf-8", errors="replace")
            new_content = content
            match_count = 0

            for pattern, replacement in MYTHOLOGICAL_TERMS.items():
                updated = re.sub(pattern, replacement, new_content, flags=re.IGNORECASE)
                if updated != new_content:
                    match_count += len(re.findall(pattern, new_content, flags=re.IGNORECASE))
                    new_content = updated

            result["matches"] = match_count

            if match_count > 0:
                if dry_run:
                    result["status"] = "DRY_RUN_MODIFIED"
                    if logger:
                        logger.info("[DRY-RUN] Would modify %s (%d matches)", filepath, match_count)
                else:
                    filepath.write_text(new_content, encoding="utf-8")
                    result["status"] = "MODIFIED"
                    if logger:
                        logger.info("[MODIFIED] %s (%d matches)", filepath, match_count)
            else:
                if logger:
                    logger.debug("[CLEAN] %s", filepath)

        except PermissionError:
            result["status"] = "ERROR"
            result["error"] = "permission_denied"
            if logger:
                logger.error("[ERROR] Permission denied: %s", filepath)
        except UnicodeDecodeError:
            result["status"] = "SKIPPED"
            result["reason"] = "binary_file"
        except Exception as exc:
            result["status"] = "ERROR"
            result["error"] = str(exc)
            if logger:
                logger.error("[ERROR] %s: %s", filepath, exc)

    return result


def parse_args() -> argparse.Namespace:
    """Parse CLI arguments."""
    parser = argparse.ArgumentParser(
        description="SHARUR-3600 Audit Swarm — async file auditor with bounded concurrency.",
    )
    parser.add_argument(
        "--target-dir",
        type=Path,
        default=Path("."),
        help="Root directory to audit (default: current directory)",
    )
    parser.add_argument(
        "--max-workers",
        type=int,
        default=50,
        help="Semaphore bound for concurrent file I/O (default: 50)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview changes without writing to disk.",
    )
    parser.add_argument(
        "--log-file",
        type=str,
        default="audit_swarm.log",
        help="Path to log file (default: audit_swarm.log)",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit structured JSON telemetry to stdout.",
    )
    return parser.parse_args()


async def run_swarm(args: argparse.Namespace) -> int:
    """Core swarm execution loop."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
        handlers=[logging.FileHandler(args.log_file), logging.StreamHandler()],
    )
    logger = logging.getLogger("audit_swarm")

    root = args.target_dir.resolve()
    logger.info(
        "[SWARM COMMANDER] Init Swarm (root=%s, max_workers=%d, dry_run=%s)",
        root,
        args.max_workers,
        args.dry_run,
    )

    targets = collect_targets(root)
    logger.info("[SWARM COMMANDER] Found %d files to audit.", len(targets))

    # INV_C5_THERMO_VALVE: bounded semaphore prevents OOM on large trees
    semaphore = asyncio.Semaphore(args.max_workers)
    start_time = time.perf_counter()

    tasks = [audit_file(fp, semaphore, dry_run=args.dry_run, logger=logger) for fp in targets]
    results = await asyncio.gather(*tasks)

    elapsed = time.perf_counter() - start_time

    # Aggregate metrics
    modified = [r for r in results if r["status"] in ("MODIFIED", "DRY_RUN_MODIFIED")]
    errors = [r for r in results if r["status"] == "ERROR"]
    skipped = [r for r in results if r["status"] == "SKIPPED"]
    total_matches = sum(r["matches"] for r in results)

    report: dict[str, Any] = {
        "total_files": len(targets),
        "modified": len(modified),
        "errors": len(errors),
        "skipped": len(skipped),
        "total_matches": total_matches,
        "elapsed_seconds": round(elapsed, 4),
        "throughput_files_per_sec": round(len(targets) / max(elapsed, 0.001), 1),
        "dry_run": args.dry_run,
    }

    if args.json:
        print(json.dumps({"report": report, "results": results}, indent=2))
    else:
        logger.info("[SWARM COMMANDER] Swarm completed in %.4fs", elapsed)
        logger.info(
            "[SWARM COMMANDER] Files=%d | Modified=%d | Errors=%d | Skipped=%d | Matches=%d | %.1f files/s",
            report["total_files"],
            report["modified"],
            report["errors"],
            report["skipped"],
            report["total_matches"],
            report["throughput_files_per_sec"],
        )
        if errors:
            logger.error("[SWARM COMMANDER] Error summary:")
            for e in errors:
                logger.error("  %s: %s", e["path"], e.get("error", "unknown"))

    # Exit code: 0=clean, 1=modifications, 2=errors
    if errors:
        return 2
    if modified:
        return 1
    return 0


def main() -> None:
    """Entry point."""
    args = parse_args()
    exit_code = asyncio.run(run_swarm(args))
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
