#!/usr/bin/env python3
# ============================================================================
# BABYLON-60 v4.0 Sovereign Hardened
# █ TOPOLOGY ROUTER | DOMAIN: agents.archi | STATE: C5-REAL
# ============================================================================
"""
Swarm Topology Router & Typo-Tolerant Dispatcher (INV_C5_ROUTER_LEVENSHTEIN).

Directs natural language user intents to optimal agent execution topologies:
  - SHARUR_3600: Mass parallel verification
  - SOCRATIC_GRILL: Deep design interview / assumption falsification
  - SOTA_MEDIA: High-exergy audiovisual & DSP processing
  - SPRINT_DEV: Rapid deterministic code mutations
"""

from enum import Enum
from typing import Dict, List, Tuple


class TopologyTarget(Enum):
    SHARUR_3600 = "sharur_3600"
    EDIN_SWARM = "edin_swarm"
    SOCRATIC_GRILL = "socratic_grill"
    SOTA_MEDIA = "sota_media"
    AXIOMATIC_PROTOCOL = "axiomatic_protocol"
    STANDARD_WORKER = "standard_worker"


def levenshtein_distance(s1: str, s2: str) -> int:
    """Computes exact Levenshtein distance between two strings."""
    if len(s1) < len(s2):
        return levenshtein_distance(s2, s1)
    if len(s2) == 0:
        return len(s1)

    previous_row: list[int] = list(range(len(s2) + 1))
    for i, c1 in enumerate(s1):
        current_row = [i + 1]
        for j, c2 in enumerate(s2):
            insertions = previous_row[j + 1] + 1
            deletions = current_row[j] + 1
            substitutions = previous_row[j] + (c1 != c2)
            current_row.append(min(insertions, deletions, substitutions))
        previous_row = current_row

    return previous_row[-1]


class SwarmRouter:
    """Fuzzy matching dispatcher for agentic swarm topologies."""

    TARGET_TRIGGERS: Dict[TopologyTarget, List[str]] = {
        TopologyTarget.SHARUR_3600: [
            "sharur",
            "enjambre 100",
            "sharur-3600",
            "auditoría paralela",
            "mass parallel",
            "100 workers",
        ],
        TopologyTarget.EDIN_SWARM: [
            "edin",
            "edin audit",
            "enjambre",
            "enjmabres",
            "swarm",
            "swarms",
            "orquestar enjambre",
        ],
        TopologyTarget.SOCRATIC_GRILL: ["grill-me", "interrogatorio", "socratic", "falsar asunciones", "socrate"],
        TopologyTarget.SOTA_MEDIA: [
            "remotion",
            "renderizar video",
            "dsp audio",
            "spatial audio",
            "ambisonics",
            "ffmpeg sota",
        ],
        TopologyTarget.AXIOMATIC_PROTOCOL: [
            "axiomatizar",
            "axiomatizacion",
            "dac yaml",
            "psafe",
            "aof",
            "bucle deductivo",
        ],
    }

    @classmethod
    def route_query(cls, query: str, max_distance: int = 2) -> Tuple[TopologyTarget, float]:
        """
        Routes user prompt to optimal topology with typo tolerance.
        Returns target and normalized match confidence [0.0 - 1.0].
        """
        q_norm = query.lower().strip()
        words = q_norm.split()

        # 1. Exact substring matching (high confidence 1.0)
        for target, triggers in cls.TARGET_TRIGGERS.items():
            for trigger in triggers:
                if trigger in q_norm:
                    return target, 1.0

        # 2. Levenshtein fuzzy word match
        best_target = TopologyTarget.STANDARD_WORKER
        best_distance = 999
        matched_len = 1

        for target, triggers in cls.TARGET_TRIGGERS.items():
            for trigger in triggers:
                for word in words:
                    dist = levenshtein_distance(word, trigger)
                    if dist <= max_distance and dist < best_distance:
                        best_distance = dist
                        best_target = target
                        matched_len = max(len(word), len(trigger))

        if best_distance <= max_distance and matched_len > 0:
            confidence = max(0.5, 1.0 - (best_distance / matched_len))
            return best_target, confidence

        return TopologyTarget.STANDARD_WORKER, 0.2
