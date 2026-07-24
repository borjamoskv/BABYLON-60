# [C5-REAL] Exergy-Maximized

"""Signal monitor for MOSKV daemon.

Polls the L1 Signal Bus and executes L2 reflexes via SignalReactor.
Converts reactor events into Daemon Alerts.
"""

from __future__ import annotations

import logging
import sqlite3
from typing import Any

from babylon60.database.core import connect as db_connect
from babylon60.extensions.daemon.models import SignalAlert

logger = logging.getLogger("moskv-daemon")


class SignalMonitor:
    """Watchdog for the Signal Bus - the L2 Reactor heart."""

    def __init__(self, db_path: str, engine: Any = None):
        self.db_path = db_path
        self._engine = engine
        self._reactor = None
        self._bus_conn = None

    def _ensure_reactor(self):
        if self._reactor:
            return

        try:
            from babylon60.extensions.signals.bus import SignalBus
            from babylon60.extensions.signals.reactor import SignalReactor

            self._bus_conn = db_connect(self.db_path)
            self._bus_conn.execute("PRAGMA journal_mode=WAL")

            bus = SignalBus(self._bus_conn)
            self._reactor = SignalReactor(bus, engine=self._engine)
            logger.info("SignalMonitor initialized L2 Reactor.")
        except (sqlite3.Error, ImportError) as e:
            logger.error("Failed to initialize SignalReactor: %s", e)

    def check(self) -> list[SignalAlert]:
        """Poll signals and process reflexes."""
        self._ensure_reactor()
        if not self._reactor:
            return []

        alerts: list[SignalAlert] = []
        try:



            signals_to_process = self._reactor.bus.peek(consumer="reactor", limit=20)

            count = self._reactor.process_once()

            if count > 0:  # type: ignore[reportOperatorIssue]
                for sig in signals_to_process[:count]:  # pyright: ignore[reportArgumentType,reportCallIssue]
                    alerts.append(
                        SignalAlert(
                            event_type=sig.event_type,
                            project=sig.project,
                            payload=sig.payload,
                            message=f"Reflex executed for {sig.event_type}",
                        )
                    )
        except Exception as e:  # noqa: BLE001
            logger.error("SignalMonitor check failed: %s", e)

        return alerts

    def shutdown(self):
        if self._bus_conn:
            self._bus_conn.close()
