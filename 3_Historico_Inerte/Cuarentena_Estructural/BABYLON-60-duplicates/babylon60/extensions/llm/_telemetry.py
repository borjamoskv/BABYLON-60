# C5-REAL EXERGY CERTIFIED
# [C5-REAL] Exergy-Maximized
from __future__ import annotations

import logging
from typing import Any

from babylon60.extensions.llm._models import CascadeEvent, CascadeTier

logger = logging.getLogger("babylon60_extensions.llm.telemetry")


_GLOBAL_ENGINE: Any | None = None


def set_engine(engine: Any) -> None:
    """Inject the CortexEngine to persist events for all CascadeTelemetry instances."""
    global _GLOBAL_ENGINE
    _GLOBAL_ENGINE = engine


class CascadeTelemetry:
    """Manages the structured logs and stats for cascade execution.

    Axiom: Ω₄ Aesthetic Integrity (visualizing entropy) + Ω₃ Byzantine
           Grounding (tracing failures).
    """

    def __init__(self, engine: Any | None = None) -> None:
        self.events: list[CascadeEvent] = []
        self._engine = engine

    def _get_engine(self) -> Any | None:
        return self._engine or _GLOBAL_ENGINE

    def emit(self, event: CascadeEvent) -> None:
        """Record structured telemetry for this cascade resolution."""
        # Truncate history to prevent memory leaks (sliding window)
        if len(self.events) >= 1000:
            self.events.pop(0)

        self.events.append(event)

        # Log visual forensic summary
        msg = f"Cascade: intent={event.intent.value} | res={event.resolved_by or 'FAIL'}"
        msg += f" | tier={event.tier.value} | depth={event.depth} | lat={event.latency_ms:.1f}ms"

        if not event.resolved_by:
            logger.error("Ω₃ Byzantine Failure: %s | errors=%s", msg, event.errors)
        elif event.tier == CascadeTier.SAFETY_NET:
            logger.warning("Ω₄ Entropy Elevated (Safety-Net Active): %s", msg)
        else:
            logger.info("Ω₃ Byzantine Validated: %s", msg)

        if self._get_engine():
            self._persist_to_db(event)

    def _persist_to_db(self, event: CascadeEvent) -> None:
        """Sovereign Persistence (Ω₃): Drive telemetry to the physical ledger asynchronously."""
        meta = {
            "intent": event.intent.value,
            "resolved_by": event.resolved_by,
            "project": event.project,
            "tier": event.tier.value,
            "depth": event.depth,
            "latency_ms": event.latency_ms,
            "errors": event.errors,
            "timestamp": event.timestamp,
            "prompt_tokens": event.prompt_tokens,
            "completion_tokens": event.completion_tokens,
        }

        try:
            import asyncio

            loop = asyncio.get_running_loop()
            loop.create_task(self._async_store(event, meta))
        except RuntimeError:
            pass

    async def _async_store(self, event: CascadeEvent, meta: dict[str, Any]) -> None:
        try:
            content = f"[LLM_TELEMETRY] {event.intent.value} | res={event.resolved_by or 'FAIL'} | lat={event.latency_ms:.1f}ms"
            engine = self._get_engine()
            if not engine:
                return
            await engine.store(
                project="__system__",
                content=content,
                fact_type="system_health",
                tags=["telemetry", "llm", event.intent.value],
                confidence="verified",
                source="llm_telemetry",
                meta=meta,
            )
        except Exception as e:  # noqa: BLE001
            logger.warning("Ω₄ Persistence Stall: Could not write LLM telemetry: %s", e)

    def stats(self) -> dict[str, Any]:
        """Aggregate cascade metrics across the sliding window."""
        counts = {t.value: 0 for t in CascadeTier}
        latencies: list[float] = []
        total = len(self.events)

        if not total:
            return {
                "total": 0,
                "breakdown": counts,
                "avg_latency_ms": 0.0,
                "success_rate": 0.0,
                "entropy_elevation_count": 0,
            }

        entropy_inc = 0
        successes = 0

        for ev in self.events:
            if ev.resolved_by:
                successes += 1
                counts[ev.tier.value] += 1
                latencies.append(ev.latency_ms)
                if ev.tier == CascadeTier.SAFETY_NET:
                    entropy_inc += 1

        avg_lat = sum(latencies) / len(latencies) if latencies else 0.0

        return {
            "total": total,
            "successes": successes,
            "success_rate": round(successes / total, 3),
            "avg_latency_ms": round(avg_lat, 2),
            "breakdown": counts,
            "entropy_elevation_count": entropy_inc,
            "reliability_index": round((successes - entropy_inc) / total, 3) if total else 0.0,
        }
