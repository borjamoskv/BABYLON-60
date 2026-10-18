#!/usr/bin/env python3
"""BABYLON-60 claim runner wrapper (delegates to canonical scripts/c5_quality_gates/verify_claims.py).

Modes:
  (default)   list declared claims (--list); no outcome is asserted.
  --execute   run every evidence command via canonical verifier (fail-closed).
  --strict    run every evidence command via canonical verifier (fail-closed).
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

CANONICAL_VERIFIER = (
    Path(__file__).absolute().parent / "c5_quality_gates" / "verify_claims.py"
)


def main() -> int:
    execute = "--execute" in sys.argv or "--strict" in sys.argv
    cmd = [sys.executable, str(CANONICAL_VERIFIER)]
    if not execute:
        cmd.append("--list")
    res = subprocess.run(cmd)
    return res.returncode


if __name__ == "__main__":
    sys.exit(main())
