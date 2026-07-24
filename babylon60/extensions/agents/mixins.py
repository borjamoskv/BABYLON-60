# [C5-REAL] Exergy-Maximized
"""Engine-aware mixin for CORTEX sovereign agents."""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger("babylon60_extensions.agents.mixins")


class EngineAwareMixin:
    """Mixin for agents requiring a reference to the Cortex Engine."""

    def __init__(self, db_path: str | None = None) -> None:
        self._db_path = db_path
        self._engine: Any = None

    def _ensure_engine(self) -> None:
        """Lazy-initialize CortexEngine if not already assigned."""
        if self._engine is not None:
            return
        try:
            from babylon60.engine.core.cortex_engine import CortexEngine

            self._engine = CortexEngine(db_path=getattr(self, "_db_path", None))
        except (ImportError, ValueError, TypeError, RuntimeError) as e:
            logger.debug("CortexEngine lazy initialization deferred: %s", e)
