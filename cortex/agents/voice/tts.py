# █ SYS_ID: BABYLON-60 VOICE TRANSDUCER — TTS LOCAL (C5-REAL)
# █ Kokoro-82M (neural, 24kHz) con fallback zero-dep a `say` de macOS.
# █ AUTHOR: Borja Moskv (borjamoskv)
from __future__ import annotations

import asyncio
import tempfile
import wave
from pathlib import Path
from typing import Protocol

import numpy as np


class TtsBackend(Protocol):
    async def synthesize(self, text: str) -> tuple[np.ndarray, int]: ...


class NullTts:
    """Sintetizador silencioso para tests/benchmark: duración proporcional al texto."""

    def __init__(self, latency_s: float = 0.0, seconds_per_char: float = 0.045, sample_rate: int = 24_000) -> None:
        self._latency = latency_s
        self._spc = seconds_per_char
        self._rate = sample_rate
        self.synthesized: list[str] = []

    async def synthesize(self, text: str) -> tuple[np.ndarray, int]:
        await asyncio.sleep(self._latency)
        self.synthesized.append(text)
        n = max(1, int(len(text) * self._spc * self._rate))
        return np.zeros(n, dtype=np.int16), self._rate


class SayTts:
    """Fallback macOS sin dependencias: binario `say` → WAV LEI16."""

    def __init__(self, voice: str = "Mónica", rate_wpm: int = 190, sample_rate: int = 22_050) -> None:
        self._voice = voice
        self._wpm = rate_wpm
        self._rate = sample_rate

    async def synthesize(self, text: str) -> tuple[np.ndarray, int]:
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "utt.wav"
            proc = await asyncio.create_subprocess_exec(
                "say",
                "-v",
                self._voice,
                "-r",
                str(self._wpm),
                "-o",
                str(out),
                f"--data-format=LEI16@{self._rate}",
                text,
            )
            code = await proc.wait()
            if code != 0:
                raise RuntimeError(f"`say` devolvió {code} para voz {self._voice!r}")
            with wave.open(str(out), "rb") as wav:
                rate = wav.getframerate()
                pcm = np.frombuffer(wav.readframes(wav.getnframes()), dtype=np.int16)
        return pcm, rate


class KokoroTts:
    """Kokoro-82M local: TTS neural 24kHz. Voz española por defecto."""

    def __init__(self, voice: str = "ef_dora", lang_code: str = "e", speed: float = 1.06) -> None:
        self._voice = voice
        self._lang = lang_code
        self._speed = speed
        self._pipeline = None

    def _ensure_pipeline(self):
        if self._pipeline is None:
            try:
                from kokoro import KPipeline
            except ImportError as exc:
                raise ImportError("kokoro ausente. Instalar: pip install -e '.[voice-full]'") from exc
            self._pipeline = KPipeline(lang_code=self._lang)
        return self._pipeline

    def _synth_blocking(self, text: str) -> np.ndarray:
        pipeline = self._ensure_pipeline()
        chunks = [np.asarray(audio, dtype=np.float32) for _, _, audio in pipeline(text, voice=self._voice, speed=self._speed)]
        if not chunks:
            return np.zeros(0, dtype=np.int16)
        audio = np.concatenate(chunks)
        return np.clip(audio * 32767.0, -32768, 32767).astype(np.int16)

    async def synthesize(self, text: str) -> tuple[np.ndarray, int]:
        pcm = await asyncio.to_thread(self._synth_blocking, text)
        return pcm, 24_000
