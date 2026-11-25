#!/usr/bin/env python3
"""BABYLON-60 claim runner wrapper (delegates to canonical scripts/c5_quality_gates/verify_claims.py).

Modes:
  (default)   list declared claims (--list); no outcome is asserted.
  --execute   run every evidence command via canonical verifier (fail-closed).
  --strict    run every evidence command via canonical verifier (fail-closed).
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

CANONICAL_VERIFIER = Path(__file__).absolute().parent / "c5_quality_gates" / "verify_claims.py"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, allow_abbrev=False)
    parser.add_argument("--list", action="store_true", help="List declared claims without running evidence suites")
    parser.add_argument("--execute", action="store_true", help="Run all claim evidence suites")
    parser.add_argument("--strict", action="store_true", help="Run all claim evidence suites")
    args = parser.parse_args()
    if args.list and (args.execute or args.strict):
        parser.error("--list cannot be combined with --execute or --strict")
    execute = args.execute or args.strict
    cmd = [sys.executable, str(CANONICAL_VERIFIER)]
    if not execute:
        cmd.append("--list")
    res = subprocess.run(cmd)
    return res.returncode


if __name__ == "__main__":
    sys.exit(main())
