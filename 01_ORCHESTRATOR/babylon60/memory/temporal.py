#!/usr/bin/env python3
# ============================================================================
# BABYLON-60 v4.0 Sovereign Hardened
# █ AUTOCOGNITION-Ω | STATE: C5-REAL | AESTHETIC: INDUSTRIAL_NOIR_2026
# ============================================================================
"""
temporal.py - Temporal Event Sourcing & Cognitive Timestamping

Módulo materializado vía Autopoiesis (Sello L0).
Soporta las 15 importaciones de `now_iso` a lo largo del monolito.
Proporciona timestamps estrictos en UTC para atestación SCITT y C5-REAL.
"""

from datetime import datetime, timezone


def now_iso() -> str:
    """
    Retorna el timestamp actual en formato ISO 8601 estricto (UTC).
    Garantiza el determinismo temporal en los registros de memoria del enjambre.

    Returns:
        str: Timestamp ISO 8601 (ej. '2026-08-11T18:52:49.123456+00:00')
    """
    return datetime.now(timezone.utc).isoformat()
