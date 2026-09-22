#!/usr/bin/env python3
# ============================================================================
# BABYLON-60 v4.0 Sovereign Hardened
# █ AGENTS_ARCHI SWARM CLI (COMPATIBILITY FACADE) | STATE: C5-REAL
# ============================================================================
"""Compatibility facade forwarding swarm CLI to edin.cli.swarm_cli."""

import sys
from edin.cli.swarm_cli import main

if __name__ == "__main__":
    sys.exit(main())
