#!/usr/bin/env python3
# ============================================================================
# BABYLON-60 v4.0 Sovereign Hardened
# █ EDIN CLI PACKAGE | DOMAIN: edin.swarms | STATE: C5-REAL
# ============================================================================
"""EDIN Swarm CLI Package."""

from typing import List, Optional


def main(argv: Optional[List[str]] = None) -> int:
    from .swarm_cli import main as _main

    return _main(argv)


__all__ = ["main"]
