"""Explicit procedural lessons backed by operator supplied validation evidence.

Activation records a local policy decision. It does not train model weights or
establish that the supplied validator or its evidence is independently trusted.
"""

from __future__ import annotations

import json
from collections.abc import Callable
from dataclasses import dataclass, field

from babylon60.bft.cortex_persist_ledger import CortexEvent, CortexPersistLedger

_PROPOSED = "SKILL_LESSON_PROPOSED"
_ATTEMPT = "SKILL_LESSON_ATTEMPT"
_PROMOTED = "SKILL_LESSON_PROMOTED"


def _text(value: object, name: str, maximum: int = 256) -> str:
    if not isinstance(value, str) or not value.strip() or len(value) > maximum:
        raise ValueError(f"{name} must be a nonempty string of at most {maximum} characters")
    return value


@dataclass
class _Lesson:
    proposal: dict[str, object]
    attempts: list[dict[str, object]] = field(default_factory=list)
    active: bool = False

    def validation_ready(self) -> bool:
        window: list[dict[str, object]] = []
        for attempt in self.attempts:
            if attempt["success"] is False:
                window.clear()
            else:
                window.append(attempt)
        practice = [attempt for attempt in window if attempt["held_out"] is False]
        held_out = [attempt for attempt in window if attempt["held_out"] is True]
        first_exposure: dict[object, dict[str, object]] = {}
        for attempt in practice:
            first_exposure.setdefault(attempt["variant_id"], attempt)
        for first in first_exposure.values():
            for second in first_exposure.values():
                if first["variant_id"] == second["variant_id"] or first["session_id"] == second["session_id"]:
                    continue
                practice_variants = {attempt["variant_id"] for attempt in practice}
                practice_sessions = {attempt["session_id"] for attempt in practice}
                if any(
                    test["variant_id"] not in practice_variants and test["session_id"] not in practice_sessions
                    for test in held_out
                ):
                    return True
        return False

    def export(self) -> dict[str, object]:
        return {
            **self.proposal,
            "status": "active" if self.active else "candidate",
            "attempt_count": len(self.attempts),
            "validation_ready": self.validation_ready(),
        }


class _Unchanged(Exception):
    """A durable transition already exists with the same meaning."""


class SkillLearning:
    """Persist candidates, validation attempts and explicit activation decisions."""

    def __init__(self, ledger: CortexPersistLedger) -> None:
        self.ledger = ledger

    def _history(self, event_type: str) -> list[tuple[int, dict[str, object]]]:
        history: list[tuple[int, dict[str, object]]] = []
        page = self.ledger.query_events(event_type=event_type, limit=1000)
        while page:
            for event in page:
                seq, payload = event["seq"], event["payload"]
                if not isinstance(seq, int) or not isinstance(payload, dict):
                    raise ValueError("Invalid lesson event in ledger")
                history.append((seq, payload))
            page = self.ledger.query_events(event_type=event_type, limit=1000, before_seq=history[-1][0])
        return history

    def _load(self, lesson_id: str) -> _Lesson:
        proposals = [
            (seq, payload) for seq, payload in self._history(_PROPOSED) if payload.get("lesson_id") == lesson_id
        ]
        if not proposals:
            raise KeyError(lesson_id)
        proposal_seq, proposal = min(proposals, key=lambda event: event[0])
        lesson = _Lesson(proposal)
        transitions = [
            (seq, event_type, payload)
            for event_type in (_ATTEMPT, _PROMOTED)
            for seq, payload in self._history(event_type)
            if seq > proposal_seq and payload.get("lesson_id") == lesson_id
        ]
        for _, event_type, payload in sorted(transitions, key=lambda event: event[0]):
            if event_type == _ATTEMPT:
                lesson.attempts.append(payload)
                if payload["success"] is False:
                    lesson.active = False
            else:
                lesson.active = True
        return lesson

    def _write(
        self, event_type: str, payload: dict[str, object], cortex_taint: str, validate: Callable[[], None]
    ) -> None:
        taint = _text(cortex_taint, "cortex_taint", 1024)
        try:
            self.ledger.append_event(
                CortexEvent(event_type, payload, taint, agent_id="skill-learning"), precondition=validate
            )
        except _Unchanged:
            pass

    def propose_lesson(
        self, *, lesson_id: str, skill_id: str, context: str, procedure: str, cortex_taint: str
    ) -> dict[str, object]:
        payload: dict[str, object] = {
            "lesson_id": _text(lesson_id, "lesson_id"),
            "skill_id": _text(skill_id, "skill_id"),
            "context": _text(context, "context"),
            "procedure": _text(procedure, "procedure", 8192),
        }

        def validate() -> None:
            try:
                existing = self._load(lesson_id)
            except KeyError:
                return
            if existing.proposal != payload:
                raise ValueError("lesson_id already names a different lesson")
            raise _Unchanged

        self._write(_PROPOSED, payload, cortex_taint, validate)
        return self.get_lesson(lesson_id)

    def get_lesson(self, lesson_id: str) -> dict[str, object]:
        return self._load(_text(lesson_id, "lesson_id")).export()

    def retrieve_lessons(
        self, *, skill_id: str | None = None, context: str | None = None, active_only: bool = False
    ) -> list[dict[str, object]]:
        if skill_id is not None:
            _text(skill_id, "skill_id")
        if context is not None:
            _text(context, "context")
        if not isinstance(active_only, bool):
            raise ValueError("active_only must be a boolean")
        lesson_ids: list[str] = []
        for _, proposal in self._history(_PROPOSED):
            if skill_id is not None and proposal["skill_id"] != skill_id:
                continue
            if context is not None and proposal["context"] != context:
                continue
            lesson_id = proposal["lesson_id"]
            if isinstance(lesson_id, str) and lesson_id not in lesson_ids:
                lesson_ids.append(lesson_id)
        lessons = [self.get_lesson(lesson_id) for lesson_id in lesson_ids]
        return [lesson for lesson in lessons if not active_only or lesson["status"] == "active"]

    def record_attempt(
        self,
        *,
        lesson_id: str,
        attempt_id: str,
        variant_id: str,
        session_id: str,
        success: bool,
        held_out: bool = False,
        evidence: dict[str, object],
        cortex_taint: str,
    ) -> dict[str, object]:
        if not isinstance(success, bool) or not isinstance(held_out, bool):
            raise ValueError("success and held_out must be booleans")
        if not isinstance(evidence, dict) or evidence.get("passed") is not success:
            raise ValueError("evidence must contain a boolean passed matching success")
        _text(evidence.get("validator"), "evidence.validator")
        _text(evidence.get("reference"), "evidence.reference", 2048)
        try:
            encoded = json.dumps(evidence, allow_nan=False)
        except (TypeError, ValueError) as error:
            raise ValueError("evidence must be finite JSON data") from error
        if len(encoded) > 8192:
            raise ValueError("evidence exceeds 8192 characters")
        payload: dict[str, object] = {
            "lesson_id": _text(lesson_id, "lesson_id"),
            "attempt_id": _text(attempt_id, "attempt_id"),
            "variant_id": _text(variant_id, "variant_id"),
            "session_id": _text(session_id, "session_id"),
            "success": success,
            "held_out": held_out,
            "evidence": evidence,
        }

        def validate() -> None:
            lesson = self._load(lesson_id)
            for previous in lesson.attempts:
                if previous["attempt_id"] == attempt_id:
                    if previous != payload:
                        raise ValueError("attempt_id already names different evidence")
                    raise _Unchanged
                if previous["variant_id"] == variant_id and previous["held_out"] != held_out:
                    raise ValueError("held-out variant must be separate from practice")

        self._write(_ATTEMPT, payload, cortex_taint, validate)
        return self.get_lesson(lesson_id)

    def promote_lesson(self, *, lesson_id: str, cortex_taint: str) -> dict[str, object]:
        _text(lesson_id, "lesson_id")
        attempt_count = len(self._load(lesson_id).attempts)

        def validate() -> None:
            lesson = self._load(lesson_id)
            if lesson.active:
                raise _Unchanged
            if len(lesson.attempts) != attempt_count:
                raise ValueError("lesson evidence changed; retry activation")
            if not lesson.validation_ready():
                raise ValueError("lesson validation requires varied practice and a separate held-out session")

        # The number of attempts distinguishes a later reactivation
        # after failed evidence from an idempotent retry of the same decision.
        payload: dict[str, object] = {"lesson_id": lesson_id, "attempt_count": attempt_count}
        self._write(_PROMOTED, payload, cortex_taint, validate)
        return self.get_lesson(lesson_id)
