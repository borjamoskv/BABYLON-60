# ============================================================================
# BABYLON-60 v4.0 Sovereign Hardened
# █ AUTOCOGNITION-Ω | STATE: C5-REAL | AESTHETIC: INDUSTRIAL_NOIR_2026
# ============================================================================
# [Causal-Determinist] Exergy-Maximized

"""Procedural memory store for tool and skill execution routines."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Optional


@dataclass
class ProceduralEngram:
    """Memory representation of a skill's procedural execution valuation."""

    skill_slug: str
    striatal_value: float = 0.5
    usage_count: int = 0
    success_count: int = 0
    permanent: bool = False


class ProceduralMemory:
    """Store for procedural execution sequences and learned skill chains."""

    def __init__(self) -> None:
        self._routines: Dict[str, Any] = {}
        self._engrams: Dict[str, ProceduralEngram] = {}

    def get_routine(self, skill_name: str) -> Any:
        return self._routines.get(skill_name)

    def save_routine(self, skill_name: str, routine: Any) -> None:
        self._routines[skill_name] = routine

    def get_engram(self, skill_slug: str) -> Optional[ProceduralEngram]:
        """Return the procedural engram for a skill slug."""
        return self._engrams.get(skill_slug)

    def record_execution(
        self,
        skill_slug: str,
        success: bool = True,
        latency_ms: float = 0.0,
        permanent: bool = False,
    ) -> ProceduralEngram:
        """Record an execution event and update striatal valuation."""
        engram = self._engrams.get(skill_slug)
        if not engram:
            engram = ProceduralEngram(skill_slug=skill_slug, permanent=permanent)
            self._engrams[skill_slug] = engram

        engram.usage_count += 1
        if success:
            engram.success_count += 1
            engram.striatal_value = min(1.0, engram.striatal_value + 0.05)
        else:
            engram.striatal_value = max(0.1, engram.striatal_value - 0.1)

        if permanent:
            engram.permanent = True
            engram.striatal_value = max(0.9, engram.striatal_value)

        return engram
