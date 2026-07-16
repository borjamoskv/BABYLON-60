# █ SYS_ID: BABYLON-60 VOICE TRANSDUCER — VAD ADAPTATIVO (C5-REAL)
# █ Detección de actividad vocal: suelo de ruido asimétrico + histéresis + modo barge-in.
# █ AUTHOR: Borja Moskv (borjamoskv)
from __future__ import annotations

import dataclasses
import enum
import math

import numpy as np

from .config import AudioConfig, VadConfig

_EPS = 1e-9


class VadEvent(enum.Enum):
    NONE = "none"
    SPEECH_START = "speech_start"


@dataclasses.dataclass(frozen=True)
class VadFrame:
    event: VadEvent
    active: bool
    in_run: bool
    speech_ms: float
    silence_ms: float
    energy_dbfs: float
    noise_floor_dbfs: float
    prosody_terminal: bool = False


def frame_dbfs(pcm: np.ndarray) -> float:
    x = pcm.astype(np.float32) / 32768.0
    rms = float(np.sqrt(np.mean(x * x))) if x.size else 0.0
    return 20.0 * math.log10(rms + _EPS)


def frame_zcr(pcm: np.ndarray) -> float:
    if pcm.size < 2:
        return 0.0
    x = pcm.astype(np.float32)
    x = x - np.mean(x)
    crossings = np.sum(np.abs(np.diff(np.signbit(x))))
    return float(crossings) / len(x)


class VoiceActivityDetector:
    """VAD por energía con suelo de ruido adaptativo asimétrico.

    El suelo baja rápido (alpha_down) y sube lento (alpha_up, solo fuera de voz),
    de modo que el habla nunca contamina la referencia de silencio. La histéresis
    on/off elimina el parpadeo. En modo barge-in los márgenes suben y el ataque se
    alarga para ignorar el sangrado del altavoz sin AEC.
    """

    def __init__(self, cfg: VadConfig, audio: AudioConfig) -> None:
        self._cfg = cfg
        self._frame_ms = float(audio.frame_ms)
        self._floor = cfg.floor_init_dbfs
        self._gate_active = False
        self._barge = False
        self._attack_count = 0
        self._in_run = False
        self._speech_ms = 0.0
        self._silence_ms = 0.0
        self._speech_energy_buf: list[float] = []
        self._speech_zcr_buf: list[float] = []
        self._latched_prosody_terminal = False

    @property
    def in_run(self) -> bool:
        return self._in_run

    def set_barge_mode(self, on: bool) -> None:
        if on != self._barge:
            self._barge = on
            self._attack_count = 0

    def end_run(self) -> None:
        self._in_run = False
        self._speech_ms = 0.0
        self._silence_ms = 0.0
        self._attack_count = 0
        self._gate_active = False
        self._latched_prosody_terminal = False
        self._speech_energy_buf.clear()
        self._speech_zcr_buf.clear()

    def _margins(self) -> tuple[float, float, int]:
        boost = self._cfg.barge_margin_boost_db if self._barge else 0.0
        attack = self._cfg.barge_attack_frames if self._barge else self._cfg.attack_frames
        return self._cfg.margin_on_db + boost, self._cfg.margin_off_db + boost, attack

    def process(self, pcm: np.ndarray) -> VadFrame:
        energy = frame_dbfs(pcm)
        zcr = frame_zcr(pcm)
        margin_on, margin_off, attack = self._margins()

        if energy < self._floor:
            self._floor += self._cfg.floor_alpha_down * (energy - self._floor)
        elif not self._gate_active:
            self._floor += self._cfg.floor_alpha_up * (energy - self._floor)

        prev_gate = self._gate_active
        threshold = self._floor + (margin_off if self._gate_active else margin_on)
        self._gate_active = energy > threshold

        event = VadEvent.NONE
        if self._gate_active:
            self._latched_prosody_terminal = False
            self._speech_energy_buf.append(energy)
            self._speech_zcr_buf.append(zcr)
            if len(self._speech_energy_buf) > self._cfg.prosody_window_frames:
                self._speech_energy_buf.pop(0)
                self._speech_zcr_buf.pop(0)

            self._attack_count += 1
            if not self._in_run and self._attack_count >= attack:
                self._in_run = True
                self._speech_ms = self._attack_count * self._frame_ms
                event = VadEvent.SPEECH_START
            elif self._in_run:
                self._speech_ms += self._frame_ms
            self._silence_ms = 0.0
        else:
            if prev_gate and self._in_run and len(self._speech_energy_buf) >= 10:
                peak_energy = max(self._speech_energy_buf[:-3])
                current_energy = np.mean(self._speech_energy_buf[-3:])
                energy_drop = current_energy - peak_energy

                peak_zcr = max(self._speech_zcr_buf[:-3])
                current_zcr = np.mean(self._speech_zcr_buf[-3:])
                zcr_ratio = current_zcr / (peak_zcr + 1e-9)

                if (energy_drop < self._cfg.prosody_energy_gradient_db and 
                    zcr_ratio < self._cfg.prosody_zcr_gradient_ratio):
                    self._latched_prosody_terminal = True

            self._attack_count = 0
            if self._in_run:
                self._silence_ms += self._frame_ms

        return VadFrame(
            event=event,
            active=self._gate_active,
            in_run=self._in_run,
            speech_ms=self._speech_ms,
            silence_ms=self._silence_ms,
            energy_dbfs=energy,
            noise_floor_dbfs=self._floor,
            prosody_terminal=self._latched_prosody_terminal,
        )
