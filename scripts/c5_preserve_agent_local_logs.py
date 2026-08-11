#!/usr/bin/env python3
# ============================================================================
# BABYLON-60 v4.0 Sovereign Hardened
# █ AUTOCOGNITION-Ω | STATE: C5-REAL | AESTHETIC: INDUSTRIAL_NOIR_2026
# ============================================================================
"""
c5_preserve_agent_local_logs.py - Wrapper delegando en c5_preserve_logs.py
"""

from c5_preserve_logs import harvest_provider_logs


def main() -> None:
    harvest_provider_logs("agent")


if __name__ == "__main__":
    main()

