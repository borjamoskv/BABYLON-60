# █ SYS_ID: BABYLON-60 VOICE TRANSDUCER — TRANSPORTE DE AUDIO (C5-REAL)
# █ Duplex real (sounddevice) y duplex simulado (tests/benchmark). Kill de playback
# █ en <1 bloque (20ms) para barge-in.
# █ AUTHOR: Borja Moskv (borjamoskv)
from __future__ import annotations

import asyncio
import time
from collections import deque
from collections.abc import AsyncIterator
from typing import Protocol

import numpy as np

from .config import AudioConfig
from .frames import AudioFrame


class AudioTransport(Protocol):
    def frames(self) -> AsyncIterator[AudioFrame]: ...
    def play(self, pcm: np.ndarray, sample_rate: int) -> None: ...
    def stop_playback(self) -> None: ...
    async def drain_playback(self) -> None: ...
    @property
    def playing(self) -> bool: ...


def resample_linear(pcm: np.ndarray, src_rate: int, dst_rate: int) -> np.ndarray:
    if src_rate == dst_rate or pcm.size == 0:
        return pcm
    n_dst = int(round(pcm.shape[0] * dst_rate / src_rate))
    x_src = np.linspace(0.0, 1.0, num=pcm.shape[0], endpoint=False)
    x_dst = np.linspace(0.0, 1.0, num=n_dst, endpoint=False)
    return np.interp(x_dst, x_src, pcm.astype(np.float32)).astype(np.int16)


class SoundDeviceAudio:
    """Micrófono y altavoces reales vía PortAudio. Import perezoso de sounddevice."""

    def __init__(self, audio: AudioConfig, output_rate: int = 24_000, input_device=None, output_device=None) -> None:
        self._cfg = audio
        self._out_rate = output_rate
        self._input_device = input_device
        self._output_device = output_device
        self._frame_queue: asyncio.Queue[AudioFrame] = asyncio.Queue(maxsize=256)
        self._playback: deque[np.ndarray] = deque()
        self._loop: asyncio.AbstractEventLoop | None = None
        self._streams = None

    def _ensure_sd(self):
        try:
            import sounddevice as sd
        except ImportError as exc:
            raise ImportError("sounddevice ausente. Instalar: pip install -e '.[voice]'") from exc
        return sd

    def _start_streams(self) -> None:
        sd = self._ensure_sd()
        blocksize = self._cfg.frame_samples

        def on_input(indata, _frames, _time_info, _status) -> None:
            pcm = np.ascontiguousarray(indata[:, 0], dtype=np.int16)
            frame = AudioFrame(pcm=pcm, t_capture=time.monotonic())
            assert self._loop is not None
            self._loop.call_soon_threadsafe(self._push_frame, frame)

        def on_output(outdata, frames_needed, _time_info, _status) -> None:
            out = np.zeros(frames_needed, dtype=np.int16)
            filled = 0
            while filled < frames_needed and self._playback:
                head = self._playback.popleft()
                take = min(head.shape[0], frames_needed - filled)
                out[filled : filled + take] = head[:take]
                filled += take
                if take < head.shape[0]:
                    self._playback.appendleft(head[take:])
            outdata[:, 0] = out

        in_stream = sd.InputStream(
            samplerate=self._cfg.sample_rate,
            channels=1,
            dtype="int16",
            blocksize=blocksize,
            device=self._input_device,
            callback=on_input,
        )
        out_stream = sd.OutputStream(
            samplerate=self._out_rate,
            channels=1,
            dtype="int16",
            blocksize=0,
            device=self._output_device,
            callback=on_output,
        )
        in_stream.start()
        out_stream.start()
        self._streams = (in_stream, out_stream)

    def _push_frame(self, frame: AudioFrame) -> None:
        if self._frame_queue.full():
            self._frame_queue.get_nowait()
        self._frame_queue.put_nowait(frame)

    async def frames(self) -> AsyncIterator[AudioFrame]:
        self._loop = asyncio.get_running_loop()
        self._start_streams()
        try:
            while True:
                yield await self._frame_queue.get()
        finally:
            if self._streams:
                for stream in self._streams:
                    stream.stop()
                    stream.close()
                self._streams = None

    def play(self, pcm: np.ndarray, sample_rate: int) -> None:
        self._playback.append(resample_linear(pcm, sample_rate, self._out_rate))

    def stop_playback(self) -> None:
        self._playback.clear()

    async def drain_playback(self) -> None:
        while self._playback:
            await asyncio.sleep(0.01)
        await asyncio.sleep(0.05)

    @property
    def playing(self) -> bool:
        return bool(self._playback)


class SimulatedAudio:
    """Transporte sintético determinista: script de segmentos (silence|speech, ms).

    Genera frames en tiempo real escalado (time_scale<1 acelera tests). El playback
    es un deadline virtual: play() lo extiende, stop_playback() lo colapsa.
    """

    def __init__(
        self,
        audio: AudioConfig,
        script: list[tuple[str, float]],
        time_scale: float = 1.0,
        speech_amplitude: int = 9_000,
        noise_amplitude: int = 12,
        seed: int = 60,
    ) -> None:
        self._cfg = audio
        self._script = list(script)
        self._scale = time_scale
        self._amp = speech_amplitude
        self._noise = noise_amplitude
        self._rng = np.random.default_rng(seed)
        self._deadline = 0.0
        self.played_ms = 0.0
        self.stopped_playbacks = 0

    def _frame(self, kind: str) -> np.ndarray:
        n = self._cfg.frame_samples
        noise = self._rng.normal(0.0, self._noise, n)
        if kind == "speech":
            t = np.arange(n) / self._cfg.sample_rate
            tone = self._amp * np.sin(2 * np.pi * 180.0 * t) * (0.7 + 0.3 * np.sin(2 * np.pi * 4.0 * t))
            signal = tone + noise
        else:
            signal = noise
        return np.clip(signal, -32768, 32767).astype(np.int16)

    async def frames(self) -> AsyncIterator[AudioFrame]:
        frame_s = self._cfg.frame_ms / 1000.0
        for kind, dur_ms in self._script:
            for _ in range(max(1, int(dur_ms / self._cfg.frame_ms))):
                await asyncio.sleep(frame_s * self._scale)
                yield AudioFrame(pcm=self._frame(kind), t_capture=time.monotonic())

    def play(self, pcm: np.ndarray, sample_rate: int) -> None:
        dur = pcm.shape[0] / sample_rate
        now = time.monotonic()
        base = max(now, self._deadline)
        self._deadline = base + dur * self._scale
        self.played_ms += dur * 1000.0

    def stop_playback(self) -> None:
        if self.playing:
            self.stopped_playbacks += 1
        self._deadline = time.monotonic()

    async def drain_playback(self) -> None:
        remaining = self._deadline - time.monotonic()
        if remaining > 0:
            await asyncio.sleep(remaining)

    @property
    def playing(self) -> bool:
        return time.monotonic() < self._deadline
