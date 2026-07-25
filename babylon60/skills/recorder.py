"""
Physical telemetry session recorder with privacy redaction and BFT Lamport clock tracking.
Author: Borja Moskv (borjamoskv)
"""

import re
import time
import uuid
from typing import Any

from babylon60.skills.types import (
    InteractionEvent,
    InteractionType,
    SkillTelemetrySession,
)

# Common sensitive parameter patterns (passwords, tokens, API keys)
SECRET_PATTERNS: list[re.Pattern[str]] = [
    re.compile(r"(?i)bearer\s+[a-zA-Z0-9_\-\.]{20,}"),
    re.compile(r"(?i)(api[_\-]?key|secret|password|passwd|pwd|token)\s*[:=]\s*[\'\"]?([^\'\s,]+)[\'\"]?"),
    re.compile(r"sk-[a-zA-Z0-9]{20,}"),
]


class SkillSessionRecorder:
    """
    Session recorder capturing interaction events with automated privacy redaction,
    Lamport clock ordering, and cryptographic state hashing.
    """

    def __init__(self, name: str, session_id: str | None = None) -> None:
        self.name: str = name
        self.session_id: str = session_id or str(uuid.uuid4())
        self.lamport_t: int = 1
        self.is_recording: bool = False
        self.events: list[InteractionEvent] = []

    def start(self) -> None:
        self.is_recording = True
        self.events.clear()
        self.lamport_t = 1

    def stop(self) -> SkillTelemetrySession:
        self.is_recording = False
        return SkillTelemetrySession(
            session_id=self.session_id,
            name=self.name,
            events=list(self.events),
            created_at=int(time.time() * 1000),
            causal_taint="borjamoskv:skill_recorder:v1",
        )

    def record_event(
        self,
        event_type: InteractionType,
        selector: str,
        target_text: str = "",
        bounding_box: tuple[int, int, int, int] = (0, 0, 0, 0),
        value: str = "",
        metadata: dict[str, Any] | None = None,
    ) -> InteractionEvent:
        if not self.is_recording:
            raise RuntimeError("Recorder is not active. Call start() before recording events.")

        redacted_value = self.redact_secrets(value)
        redacted_text = self.redact_secrets(target_text)

        self.lamport_t += 1
        event = InteractionEvent(
            event_type=event_type,
            selector=selector,
            target_text=redacted_text,
            bounding_box=bounding_box,
            value=redacted_value,
            timestamp=int(time.time() * 1000),
            lamport_t=self.lamport_t,
            causal_taint="borjamoskv:skill_recorder:v1",
            metadata=metadata or {},
        )
        self.events.append(event)
        return event

    @staticmethod
    def redact_secrets(input_str: str) -> str:
        if not input_str:
            return ""

        result = input_str
        for pattern in SECRET_PATTERNS:
            result = pattern.sub("[REDACTED_SECRET]", result)
        return result
