# █ SYS_ID: BABYLON-60 VOICE TRANSDUCER — STT LOCAL STREAMING (C5-REAL)
# █ faster-whisper con re-decodificación incremental para parciales. Cero red.
# █ prefinalize(): el decode final corre durante la ventana de hang (v2).
# █ AUTHOR: Borja Moskv (borjamoskv)
from __future__ import annotations

import asyncio
from typing import Protocol

import numpy as np


class StreamingStt(Protocol):
    async def start(self, language: str) -> None: ...
    def feed(self, pcm: np.ndarray) -> None: ...
    def poll_partial(self) -> str | None: ...
    def prefinalize(self) -> None: ...
    async def finalize(self) -> str: ...


class ScriptedStt:
    """STT determinista para tests y benchmark: parciales por ms de audio alimentado."""

    def __init__(
        self,
        final_text: str,
        partial_script: list[tuple[float, str]] | None = None,
        finalize_latency_s: float = 0.08,
        sample_rate: int = 16_000,
    ) -> None:
        self._final = final_text
        self._script = sorted(partial_script or [], key=lambda p: p[0])
        self._latency = finalize_latency_s
        self._rate = sample_rate
        self._fed_ms = 0.0
        self._cursor = 0
        self._pending: str | None = None
        self._prefinal_task: asyncio.Task | None = None
        self._prefinal_fed = -1.0
        self.prefinal_used = False
        self.utterances = 0

    async def start(self, language: str) -> None:
        self._fed_ms = 0.0
        self._cursor = 0
        self._pending = None
        if self._prefinal_task is not None:
            self._prefinal_task.cancel()
            self._prefinal_task = None
        self._prefinal_fed = -1.0
        self.utterances += 1

    def feed(self, pcm: np.ndarray) -> None:
        self._fed_ms += 1000.0 * pcm.shape[0] / self._rate
        while self._cursor < len(self._script) and self._script[self._cursor][0] <= self._fed_ms:
            self._pending = self._script[self._cursor][1]
            self._cursor += 1

    def poll_partial(self) -> str | None:
        partial, self._pending = self._pending, None
        return partial

    def prefinalize(self) -> None:
        if self._prefinal_task is not None and self._prefinal_fed == self._fed_ms:
            return
        if self._prefinal_task is not None:
            self._prefinal_task.cancel()
        self._prefinal_fed = self._fed_ms
        self._prefinal_task = asyncio.create_task(asyncio.sleep(self._latency))

    async def finalize(self) -> str:
        task, fed = self._prefinal_task, self._prefinal_fed
        self._prefinal_task = None
        self._prefinal_fed = -1.0
        self.prefinal_used = False
        if task is not None and fed == self._fed_ms and not task.cancelled():
            await task
            self.prefinal_used = True
            return self._final
        if task is not None:
            task.cancel()
        await asyncio.sleep(self._latency)
        return self._final


class FasterWhisperStt:
    """Backend local sobre faster-whisper (CTranslate2). Parciales por re-decode periódico."""

    def __init__(
        self,
        model_size: str = "small",
        device: str = "auto",
        compute_type: str = "int8",
        partial_interval_s: float = 0.45,
        sample_rate: int = 16_000,
    ) -> None:
        self._model_size = model_size
        self._device = device
        self._compute_type = compute_type
        self._interval = partial_interval_s
        self._rate = sample_rate
        self._model = None
        self._language = "es"
        self._chunks: list[np.ndarray] = []
        self._decoded_samples = 0
        self._partial: str | None = None
        self._loop_task: asyncio.Task | None = None
        self._active = False
        self._prefinal_task: asyncio.Task | None = None
        self._prefinal_samples = -1
        self.prefinal_used = False

    def _ensure_model(self):
        if self._model is None:
            try:
                from faster_whisper import WhisperModel
            except ImportError as exc:
                raise ImportError(
                    "faster-whisper ausente. Instalar: pip install -e '.[voice]'"
                ) from exc
            self._model = WhisperModel(self._model_size, device=self._device, compute_type=self._compute_type)
        return self._model

    def _decode(self, audio: np.ndarray, beam_size: int) -> str:
        model = self._ensure_model()
        segments, _ = model.transcribe(
            audio.astype(np.float32) / 32768.0,
            language=self._language,
            beam_size=beam_size,
            vad_filter=False,
            condition_on_previous_text=False,
        )
        return "".join(seg.text for seg in segments).strip()

    async def start(self, language: str) -> None:
        await asyncio.to_thread(self._ensure_model)
        self._language = language
        self._chunks = []
        self._decoded_samples = 0
        self._partial = None
        if self._prefinal_task is not None:
            self._prefinal_task.cancel()
            self._prefinal_task = None
        self._prefinal_samples = -1
        self._active = True
        self._loop_task = asyncio.create_task(self._partial_loop())

    def feed(self, pcm: np.ndarray) -> None:
        if self._active:
            self._chunks.append(pcm)

    def poll_partial(self) -> str | None:
        partial, self._partial = self._partial, None
        return partial

    async def _partial_loop(self) -> None:
        while self._active:
            await asyncio.sleep(self._interval)
            audio = np.concatenate(self._chunks) if self._chunks else np.zeros(0, dtype=np.int16)
            if audio.shape[0] <= self._decoded_samples or audio.shape[0] < self._rate // 2:
                continue
            self._decoded_samples = audio.shape[0]
            text = await asyncio.to_thread(self._decode, audio, 1)
            if self._active and text:
                self._partial = text

    def _total_samples(self) -> int:
        return sum(c.shape[0] for c in self._chunks)

    def prefinalize(self) -> None:
        total = self._total_samples()
        if self._prefinal_task is not None and self._prefinal_samples == total:
            return
        if self._prefinal_task is not None:
            self._prefinal_task.cancel()
        if total < self._rate // 10:
            return
        audio = np.concatenate(self._chunks)
        self._prefinal_samples = total
        self._prefinal_task = asyncio.create_task(asyncio.to_thread(self._decode, audio, 2))

    async def finalize(self) -> str:
        self._active = False
        if self._loop_task is not None:
            self._loop_task.cancel()
            try:
                await self._loop_task
            except asyncio.CancelledError:
                pass
            self._loop_task = None
        prefinal, samples = self._prefinal_task, self._prefinal_samples
        self._prefinal_task = None
        self._prefinal_samples = -1
        self.prefinal_used = False
        audio = np.concatenate(self._chunks) if self._chunks else np.zeros(0, dtype=np.int16)
        self._chunks = []
        if prefinal is not None and samples == audio.shape[0] and not prefinal.cancelled():
            text = await prefinal
            self.prefinal_used = True
            return text
        if prefinal is not None:
            prefinal.cancel()
        if audio.shape[0] < self._rate // 10:
            return ""
        return await asyncio.to_thread(self._decode, audio, 2)
