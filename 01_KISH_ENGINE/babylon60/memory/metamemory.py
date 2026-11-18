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
import math
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
        self._in_memory_attempts: dict[str, tuple[str, str, bool]] = {}
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
        terms = [t for t in intent_lower.split() if len(t) > 2]
        matched: list[str] = []
        matched_scores: list[float] = []

        for c in candidates:
            name = str(getattr(c, "name", getattr(c, "skill_slug", "")))
            surface = str(getattr(c, "_fok_surface", name)).lower()
            striatal = getattr(c, "striatal_value", None)
            if striatal is not None:
                if (
                    isinstance(striatal, bool)
                    or not isinstance(striatal, (int, float))
                    or not math.isfinite(float(striatal))
                ):
                    raise ValueError("striatal_value must be a finite number in [0.0, 1.0]")
                striatal_f = float(striatal)
                if striatal_f < 0.0 or striatal_f > 1.0:
                    raise ValueError("striatal_value must be in [0.0, 1.0]")
            else:
                striatal_f = None

            if not terms:
                has_hit = bool(surface.strip())
                ratio = 1.0 if has_hit else 0.0
                score = 0.7 if has_hit else 0.2
            else:
                hits = sum(1 for term in terms if term in surface)
                has_hit = hits > 0
                ratio = hits / len(terms)
                if not has_hit:
                    score = 0.2
                elif ratio >= 0.5:
                    score = min(1.0, 0.4 + ratio * 0.6)
                else:
                    score = 0.2 + ratio * 0.3

            if striatal_f is not None and has_hit:
                score = min(score, striatal_f) if striatal_f < 0.35 else score * striatal_f

            if has_hit:
                matched.append(name)
                matched_scores.append(score)

        highest_score = max(matched_scores) if matched_scores else 0.2
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

        invalid_statuses = {"REVOKED", "REVOKED_DEPENDENCY", "DISBELIEVED", "DISBELIEVED_DEPENDENCY", "CORRUPTED"}
        effective_scores: list[float] = []
        matched_ids: list[str] = []
        any_repair_or_weak = False

        for c in cards:
            for field_name, val in (
                ("retrieval_confidence", c.retrieval_confidence),
                ("existence_probability", c.existence_probability),
            ):
                if isinstance(val, bool) or not isinstance(val, (int, float)) or not math.isfinite(float(val)):
                    raise ValueError(f"{field_name} must be a finite number in [0.0, 1.0]")
                if float(val) < 0.0 or float(val) > 1.0:
                    raise ValueError(f"{field_name} must be in [0.0, 1.0]")

            status_upper = str(c.consolidation_status).upper()
            if status_upper in invalid_statuses:
                eff = 0.0
                any_repair_or_weak = True
            else:
                eff = float(c.retrieval_confidence) * float(c.existence_probability)
                if c.repair_needed:
                    eff *= 0.5
                    any_repair_or_weak = True
                if status_upper == "STALE":
                    eff *= 0.5
                    any_repair_or_weak = True
                if 0.0 < float(c.existence_probability) < 0.35:
                    any_repair_or_weak = True
            effective_scores.append(eff)
            if eff > 0.0:
                matched_ids.append(c.memory_id)

        avg_conf = sum(effective_scores) / len(effective_scores)
        tip_of_tongue = any_repair_or_weak or (0.0 < avg_conf < 0.35)
        return MetaJudgment(
            confidence=avg_conf,
            fok=avg_conf,
            jol=avg_conf,
            tip_of_tongue=tip_of_tongue,
            relevance_matches=matched_ids,
        )

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
            if attempt_id is not None:
                prev = self._in_memory_attempts.get(attempt_id)
                if prev is not None:
                    if prev != (intent, context, success):
                        raise ValueError("attempt_id already names a different outcome")
                    return
                self._in_memory_attempts[attempt_id] = (intent, context, success)
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
