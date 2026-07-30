# [C5-REAL] Exergy-Maximized
"""
API State.
Global instances and shared state for the API layer.
"""

from __future__ import annotations

from typing import Any

from babylon60.auth import AuthManager
from babylon60.engine import CortexEngine
from babylon60.extensions.timing import TimingTracker

# Globals initialized at startup in api.py lifespan
engine: CortexEngine | None = None
auth_manager: AuthManager | None = None
tracker: TimingTracker | None = None
notification_bus: Any | None = None
