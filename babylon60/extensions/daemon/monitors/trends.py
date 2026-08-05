# ============================================================================
# BABYLON-60 v4.0 Sovereign Hardened
# █ AUTOCOGNITION-Ω | STATE: C5-REAL | AESTHETIC: INDUSTRIAL_NOIR_2026
# ============================================================================
# [Causal-Determinist] Exergy-Maximized

from __future__ import annotations

import logging
from typing import Any

from babylon60.extensions.daemon.models import TrendsAlert
from babylon60.extensions.daemon.monitors.base import BaseMonitor

logger = logging.getLogger("moskv-daemon")


class TrendsMonitor(BaseMonitor[TrendsAlert]):
    """Collects and reports real-time trends from the Trends Attestor."""

    def __init__(self, attestor: Any):
        """Initializes the monitor with a reference to the running Attestor."""
        self._oracle = attestor

    def check(self) -> list[TrendsAlert]:
        """Provides the pending alerts to the daemon."""
        if not self._oracle:
            return []

        try:
            # We fetch all alerts generated since the last cycle
            alerts = self._oracle.consume_alerts()
            return alerts
        except Exception as e:  # noqa: BLE001
            logger.error("TrendsMonitor check failed: %s", e)
            return []
