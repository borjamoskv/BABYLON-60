# █ SYS_ID: BABYLON-60 VOICE TRANSDUCER — FRAMES (C5-REAL)
# █ AUTHOR: Borja Moskv (borjamoskv)
from __future__ import annotations

import dataclasses
from collections import deque

import numpy as np


@dataclasses.dataclass(frozen=True)
class AudioFrame:
    pcm: np.ndarray
    t_capture: float

    def __post_init__(self) -> None:
        if self.pcm.dtype != np.int16:
            raise TypeError(f"AudioFrame exige int16, recibido {self.pcm.dtype}")
        if self.pcm.ndim != 1:
            raise ValueError(f"AudioFrame exige mono 1-D, recibido ndim={self.pcm.ndim}")

    @property
    def samples(self) -> int:
        return int(self.pcm.shape[0])


class PrerollRing:
    """Anillo de pre-captura: retiene los últimos N frames previos al SPEECH_START."""

    def __init__(self, max_frames: int) -> None:
        if max_frames < 1:
            raise ValueError("PrerollRing exige max_frames >= 1")
        self._ring: deque[AudioFrame] = deque(maxlen=max_frames)

    def push(self, frame: AudioFrame) -> None:
        self._ring.append(frame)

    def dump(self) -> np.ndarray:
        if not self._ring:
            return np.zeros(0, dtype=np.int16)
        return np.concatenate([f.pcm for f in self._ring])

    def clear(self) -> None:
        self._ring.clear()

    def __len__(self) -> int:
        return len(self._ring)
