#!/usr/bin/env python3
# ============================================================================
# BABYLON-60 v4.0 Sovereign Hardened
# █ AUTOCOGNITION-Ω | STATE: C5-REAL | AESTHETIC: INDUSTRIAL_NOIR_2026
# ============================================================================
"""
legion_swarm.py - Unified Sovereign Swarm Orchestrator CLI
Usage:
    ./scripts/legion_swarm.py --tenants 100
    ./scripts/legion_swarm.py --tenants 10000 --concurrency 500
"""

from __future__ import annotations

import argparse
import asyncio
import sys
from pathlib import Path

_DIR = Path(__file__).resolve().parent
if str(_DIR) not in sys.path:
    sys.path.insert(0, str(_DIR))

from sharur_swarm_core import run_legion_swarm


def main() -> None:
    parser = argparse.ArgumentParser(description="BABYLON-60 Sovereign Legion Swarm Orchestrator")
    parser.add_argument(
        "--tenants",
        "-n",
        type=int,
        default=100,
        help="Number of parallel subagent tenant scopes to instantiate in RAM (default: 100)",
    )
    parser.add_argument(
        "--concurrency",
        "-c",
        type=int,
        default=None,
        help="Optional concurrency semaphore limit to prevent OOM (e.g., 500)",
    )
    parser.add_argument(
        "--action",
        type=str,
        default="AST_ISOMORPHISM_SWARM_MUTATION",
        help="Action name for event projection",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit JSON payload for M2M communication",
    )
    args = parser.parse_args()

    asyncio.run(
        run_legion_swarm(
            num_tenants=args.tenants,
            concurrency_limit=args.concurrency or args.tenants,
            json_output=args.json
        )
    )

if __name__ == "__main__":
    main()
