#!/usr/bin/env python3
# ============================================================================
# BABYLON-60 v4.0 Sovereign Hardened
# █ AGENTS_ARCHI CLI PACKAGE (COMPATIBILITY FACADE) | STATE: C5-REAL
# ============================================================================
"""agents_archi compatibility CLI package forwarding to edin.cli."""

from typing import List, Optional


def main(argv: Optional[List[str]] = None) -> int:
    from edin.cli import main as _main

    return _main(argv)


__all__ = ["main"]
