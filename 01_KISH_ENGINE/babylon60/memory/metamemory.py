# ============================================================================
# BABYLON-60 v4.0 Sovereign Hardened
# █ AUTOCOGNITION-Ω | STATE: C5-REAL | AESTHETIC: INDUSTRIAL_NOIR_2026
# ============================================================================
# [Causal-Determinist] Exergy-Maximized

"""Metamemory monitor sub-system for cognitive Feeling-of-Knowing (FOK) and Epistemic Verdicts."""

from __future__ import annotations

from dataclasses import dataclass, field
from collections.abc import Sequence
from enum import Enum
from typing import List
from uuid import uuid4

from babylon60.bft.cortex_persist_ledger import CortexEvent, CortexPersistLedger


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

    def __init__(self, *, ledger: CortexPersistLedger | None = None) -> None:
        self._fok_scores: dict[tuple[str, str], float] = {}
        self._ledger = ledger

    def _outcomes(self, intent: str, context: str) -> list[dict[str, object]]:
        if self._ledger is None:
            return []
        history: list[dict[str, object]] = []
        page = self._ledger.query_events(event_type="METAMEMORY_OUTCOME", skill_id=intent, context=context, limit=1000)
        while page:
            for event in page:
                payload = event["payload"]
                if not isinstance(payload, dict):
                    raise ValueError("Invalid metamemory outcome payload")
                history.append(payload)
            seq = page[-1]["seq"]
            if not isinstance(seq, int):
                raise ValueError("Invalid metamemory outcome cursor")
            page = self._ledger.query_events(
                event_type="METAMEMORY_OUTCOME", skill_id=intent, context=context, limit=1000, before_seq=seq
            )
        return list(reversed(history))

    def get_feeling_of_knowing(self, intent: str, *, context: str = "") -> float:
        """Return a local outcome heuristic, not a calibrated probability."""
        if self._ledger is None:
            return self._fok_scores.get((intent, context), 0.85)
        score = 0.85
        for outcome in self._outcomes(intent, context):
            score = max(0.0, min(1.0, score + (0.05 if outcome["success"] is True else -0.1)))
        return score

    def judge_procedural_fok(self, intent: str, candidates: Sequence[object]) -> FokJudgment:
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

    def evaluate_epistemic_context(self, intent: str, memory_cards: List[MemoryCard] | None = None) -> MetaJudgment:
        """Evaluate epistemic judgment and confidence for a prompt context."""
        cards = memory_cards or []
        if not cards:
            return MetaJudgment(confidence=0.3, fok=0.4, jol=0.3, tip_of_tongue=False)

        avg_conf = sum(c.retrieval_confidence for c in cards) / len(cards)
        return MetaJudgment(confidence=avg_conf, fok=avg_conf, jol=avg_conf)

    def record_outcome(self, intent: str, success: bool, *, context: str = "", attempt_id: str | None = None) -> None:
        """Record caller supplied outcome metadata; persistence is opt-in."""
        if not isinstance(intent, str) or not intent.strip() or len(intent) > 256:
            raise ValueError("intent must be a nonempty string of at most 256 characters")
        if not isinstance(context, str) or len(context) > 256:
            raise ValueError("context must be a string of at most 256 characters")
        if not isinstance(success, bool):
            raise ValueError("success must be a boolean")
        if attempt_id is not None and (
            not isinstance(attempt_id, str) or not attempt_id.strip() or len(attempt_id) > 256
        ):
            raise ValueError("attempt_id must be a nonempty string of at most 256 characters")
        if self._ledger is None:
            current = self.get_feeling_of_knowing(intent, context=context)
            self._fok_scores[(intent, context)] = max(0.0, min(1.0, current + (0.05 if success else -0.1)))
            return
        identifier = attempt_id if attempt_id is not None else str(uuid4())

        def validate() -> None:
            for previous in self._outcomes(intent, context):
                if previous["attempt_id"] == identifier and previous["success"] is not success:
                    raise ValueError("attempt_id already names a different outcome")

        self._ledger.append_event(
            CortexEvent(
                "METAMEMORY_OUTCOME",
                {"skill_id": intent, "context": context, "attempt_id": identifier, "success": success},
                "metamemory:caller-outcome",
                agent_id="metamemory-monitor",
            ),
            precondition=validate,
        )
