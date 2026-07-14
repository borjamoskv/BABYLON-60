# █ SYS_ID: BABYLON-60 VOICE TRANSDUCER — FSM FULL-DUPLEX (C5-REAL)
# █ Tabla de transiciones inmutable. Transición inválida = crash determinista.
# █ AUTHOR: Borja Moskv (borjamoskv)
from __future__ import annotations

import enum
import time


class TurnState(enum.Enum):
    IDLE = "idle"
    LISTENING = "listening"
    THINKING = "thinking"
    SPEAKING = "speaking"


class TurnEvent(enum.Enum):
    WAKE = "wake"
    ENDPOINT_COMMIT = "endpoint_commit"
    RESPONSE_START = "response_start"
    PLAYBACK_DONE = "playback_done"
    BARGE_IN = "barge_in"
    RESET = "reset"


class TurnProtocolError(RuntimeError):
    pass


_TRANSITIONS: dict[tuple[TurnState, TurnEvent], TurnState] = {
    (TurnState.IDLE, TurnEvent.WAKE): TurnState.LISTENING,
    (TurnState.LISTENING, TurnEvent.ENDPOINT_COMMIT): TurnState.THINKING,
    (TurnState.THINKING, TurnEvent.RESPONSE_START): TurnState.SPEAKING,
    (TurnState.THINKING, TurnEvent.BARGE_IN): TurnState.LISTENING,
    (TurnState.THINKING, TurnEvent.PLAYBACK_DONE): TurnState.LISTENING,
    (TurnState.SPEAKING, TurnEvent.PLAYBACK_DONE): TurnState.LISTENING,
    (TurnState.SPEAKING, TurnEvent.BARGE_IN): TurnState.LISTENING,
}


class DuplexTurnFSM:
    """Máquina de turnos conversacional con soporte de interrupción (barge-in)."""

    def __init__(self) -> None:
        self._state = TurnState.IDLE
        self.history: list[tuple[float, TurnState, TurnEvent, TurnState]] = []

    @property
    def state(self) -> TurnState:
        return self._state

    def fire(self, event: TurnEvent) -> TurnState:
        if event is TurnEvent.RESET:
            target = TurnState.IDLE
        else:
            key = (self._state, event)
            if key not in _TRANSITIONS:
                raise TurnProtocolError(f"Transición inválida: {self._state.value} --{event.value}-->")
            target = _TRANSITIONS[key]
        self.history.append((time.monotonic(), self._state, event, target))
        self._state = target
        return target
