# █ SYS_ID: BABYLON-60 VOICE TRANSDUCER — ENDPOINTER SEMÁNTICO (C5-REAL)
# █ El hang-time no es fijo: se modula con la completitud sintáctica del parcial STT.
# █ Frase terminada → corte a 200ms. Conector colgante → espera 900ms. Esto elimina
# █ los 300-500ms de colchón fijo que arrastran los stacks comerciales.
# █ AUTHOR: Borja Moskv (borjamoskv)
from __future__ import annotations

import enum

from .config import EndpointConfig
from .vad import VadFrame

_TERMINAL_CHARS = ".?!…"
_CONTINUATION_TOKENS = frozenset(
    {
        "y", "e", "o", "u", "ni", "pero", "que", "de", "del", "en", "con", "para", "por",
        "porque", "entonces", "como", "si", "aunque", "cuando", "donde", "el", "la", "los",
        "las", "un", "una", "mi", "tu", "su", "al", "a", "es", "muy", "más", "menos",
        "and", "or", "but", "the", "to", "of", "with", "because", "so", "if", "when",
        "where", "my", "your", "very", "then", "than",
    }
)


class EndpointDecision(enum.Enum):
    WAIT = "wait"
    COMMIT = "commit"


class SemanticEndpointer:
    """Decide el fin de turno combinando silencio acústico y semántica del parcial."""

    def __init__(self, cfg: EndpointConfig) -> None:
        self._cfg = cfg
        self._last_partial = ""

    def reset(self) -> None:
        self._last_partial = ""

    def update_partial(self, text: str) -> None:
        self._last_partial = text.strip()

    def hang_ms(self) -> float:
        partial = self._last_partial
        if not partial:
            return self._cfg.base_hang_ms
        if partial[-1] in _TERMINAL_CHARS:
            return self._cfg.fast_hang_ms
        if partial.endswith(","):
            return self._cfg.slow_hang_ms
        last_token = partial.rsplit(None, 1)[-1].lower().strip(",;:")
        if last_token in _CONTINUATION_TOKENS:
            return self._cfg.slow_hang_ms
        return self._cfg.base_hang_ms

    def observe(self, frame: VadFrame) -> EndpointDecision:
        if not frame.in_run:
            return EndpointDecision.WAIT
        total_ms = frame.speech_ms + frame.silence_ms
        if total_ms >= self._cfg.max_utterance_ms:
            return EndpointDecision.COMMIT
        if frame.speech_ms < self._cfg.min_speech_ms:
            return EndpointDecision.WAIT
        if frame.silence_ms >= self.hang_ms():
            return EndpointDecision.COMMIT
        return EndpointDecision.WAIT
