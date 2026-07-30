import asyncio
import logging
from typing import Any

logger = logging.getLogger(__name__)


class CortexTelemetry:
    """C5-REAL Runtime Event Logger for CORTEX skills and workflows.

    Persiste la telemetría directamente en la capa BFT del Master Ledger,
    eliminando sumideros de Anergía de red o disco (JSONL locales).
    """

    def __init__(self):
        self._engine: Any = None

    def set_engine(self, engine: Any) -> None:
        """Inject the CortexEngine to persist events."""
        self._engine = engine

    def log_event(
        self,
        session_id: str,
        call_id: str,
        skill: str,
        event_type: str,
        source: str = "unknown",
        duration_ms: int | None = None,
        success: bool | None = None,
        trigger: str = "hook",
        **kwargs,
    ):
        """Logs a single skill execution event into the BFT ledger via SAGA-4."""
        if self._engine is None:
            return

        entry: dict[str, Any] = {
            "session_id": session_id,
            "call_id": call_id,
            "skill": skill,
            "source": source,
            "event_type": event_type,
            "trigger": trigger,
        }

        if duration_ms is not None:
            entry["duration_ms"] = duration_ms
        if success is not None:
            entry["success"] = success

        entry.update(kwargs)

        try:
            loop = asyncio.get_running_loop()
            loop.create_task(self._persist(skill, event_type, entry))
        except RuntimeError:
            pass

    async def _persist(self, skill: str, event_type: str, meta: dict[str, Any]) -> None:
        try:
            content = f"[TELEMETRY] {skill} | {event_type}"
            await self._engine.store(
                project="__system__",
                content=content,
                fact_type="system_health",
                tags=["telemetry", skill, event_type],
                confidence="verified",
                source="telemetry_engine",
                meta=meta,
            )
        except Exception:  # noqa: BLE001
            logger.warning("Failed to persist telemetry event", exc_info=True)


telemetry = CortexTelemetry()
