# ============================================================================
# BABYLON-60 v4.0 Sovereign Hardened
# █ AUTOCOGNITION-Ω | STATE: C5-REAL | AESTHETIC: INDUSTRIAL_NOIR_2026
# ============================================================================
# [Causal-Determinist] Exergy-Maximized

"""Metamemory monitor sub-system for cognitive Feeling-of-Knowing (FOK) and Epistemic Verdicts."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, List


class Verdict(str, Enum):
    """Metacognitive decision verdict on memory retrieval & epistemic status."""

    RESPOND = "respond"
    SEARCH_MORE = "search_more"
    CLARIFY = "clarify"
    ABSTAIN = "abstain"


@dataclass
class MetaJudgment:
    """Detailed metacognitive judgment of confidence, FOK, and JOL."""

    confidence: float = 0.85
    fok: float = 0.85
    jol: float = 0.85
    tip_of_tongue: bool = False
    relevance_matches: List[str] = field(default_factory=list)


@dataclass
class MemoryCard:
    """Structured memory evidence card retrieved from comonadic store."""

    memory_id: str
    retrieval_confidence: float = 0.90
    existence_probability: float = 1.0
    consolidation_status: str = "CONSOLIDATED"
    repair_needed: bool = False
    emotional_weight: float = 0.0
    content: str = ""


@dataclass
class FokJudgment:
    """Judgment emitted by Metamemory regarding procedural readiness."""

    fok_score: float = 0.85
    tip_of_tongue: bool = False
    relevance_matches: List[str] = field(default_factory=list)


class MetamemoryMonitor:
    """Monitors Feeling-of-Knowing (FOK) and cognitive confidence for skill execution."""

    def __init__(self) -> None:
        self._fok_scores: dict[str, float] = {}

    def get_feeling_of_knowing(self, intent: str) -> float:
        """Return FOK confidence score (0.0 - 1.0) for an intent."""
        return self._fok_scores.get(intent, 0.85)

    def judge_procedural_fok(
        self, intent: str, candidates: list[Any]
    ) -> FokJudgment:
        """Evaluate procedural FOK confidence for intent given candidate skill surfaces."""
        if not candidates:
            return FokJudgment(fok_score=0.1, tip_of_tongue=False)

        intent_lower = intent.lower()
        matched = []
        highest_score = 0.5

        for c in candidates:
            surface = getattr(c, "_fok_surface", getattr(c, "name", "")).lower()
            terms = [t for t in intent_lower.split() if len(t) > 2]
            if not terms:
                score = 0.7
            else:
                hits = sum(1 for term in terms if term in surface)
                score = min(1.0, 0.4 + (hits / len(terms)) * 0.6)
            if score > highest_score:
                highest_score = score
            if score > 0.5:
                matched.append(getattr(c, "name", ""))

        tip_of_tongue = highest_score < 0.35 and len(matched) > 0
        return FokJudgment(
            fok_score=highest_score,
            tip_of_tongue=tip_of_tongue,
            relevance_matches=matched,
        )

    def evaluate_epistemic_context(
        self, intent: str, memory_cards: List[MemoryCard] | None = None
    ) -> MetaJudgment:
        """Evaluate epistemic judgment and confidence for a prompt context."""
        cards = memory_cards or []
        if not cards:
            return MetaJudgment(confidence=0.3, fok=0.4, jol=0.3, tip_of_tongue=False)

        avg_conf = sum(c.retrieval_confidence for c in cards) / len(cards)
        return MetaJudgment(confidence=avg_conf, fok=avg_conf, jol=avg_conf)

    def record_outcome(self, intent: str, success: bool) -> None:
        """Update FOK based on execution result."""
        current = self.get_feeling_of_knowing(intent)
        delta = 0.05 if success else -0.1
        self._fok_scores[intent] = max(0.0, min(1.0, current + delta))
