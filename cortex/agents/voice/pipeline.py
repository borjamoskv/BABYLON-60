# █ SYS_ID: BABYLON-60 VOICE TRANSDUCER — PIPELINE FULL-DUPLEX (C5-REAL)
# █ Orquestador asyncio: VAD → endpointer semántico → STT streaming → especulación
# █ LLM → chunker de cláusulas → TTS incremental → playback interrumpible.
# █ Todo turno colapsa en un TurnReceipt con deltas de latencia por etapa.
# █ AUTHOR: Borja Moskv (borjamoskv)
from __future__ import annotations

import asyncio
import dataclasses
import time
import uuid
from typing import Any, Callable

from .audio_io import AudioTransport
from .chunker import ClauseChunker
from .config import VoiceAgentConfig
from .endpointing import EndpointDecision, SemanticEndpointer
from .frames import AudioFrame, PrerollRing
from .fsm import DuplexTurnFSM, TurnEvent, TurnState
from .ledger import TurnReceipt, VoiceLedger
from .speculative import BrainBackend, Message, SpeculativeExecutor
from .stt import StreamingStt
from .tts import TtsBackend
from .vad import VadEvent, VadFrame, VoiceActivityDetector

EventSink = Callable[[str, Any], None]


@dataclasses.dataclass
class _TurnClock:
    t_speech_start: float | None = None
    t_speech_end: float | None = None
    t_endpoint_commit: float | None = None
    t_stt_final: float | None = None
    t_first_token: float | None = None
    t_first_audio: float | None = None


class VoiceAgentPipeline:
    def __init__(
        self,
        cfg: VoiceAgentConfig,
        audio: AudioTransport,
        stt: StreamingStt,
        brain: BrainBackend,
        tts: TtsBackend,
        ledger: VoiceLedger | None = None,
        on_event: EventSink | None = None,
    ) -> None:
        self.cfg = cfg
        self.audio = audio
        self.stt = stt
        self.brain = brain
        self.tts = tts
        self.ledger = ledger
        self.fsm = DuplexTurnFSM()
        self.vad = VoiceActivityDetector(cfg.vad, cfg.audio)
        self.endpointer = SemanticEndpointer(cfg.endpoint)
        self.spec = SpeculativeExecutor(brain, cfg.speculative, tts=tts, chunker_cfg=cfg.chunker)
        self._frame_ms = float(cfg.audio.frame_ms)
        self.history: list[Message] = []
        self.receipts: list[TurnReceipt] = []
        self.session_id = uuid.uuid4().hex
        self._on_event = on_event
        self._turn_index = 0
        self._capturing = False
        self._clock = _TurnClock()
        self._reply_parts: list[str] = []
        self._turn_final = ""
        self._respond_task: asyncio.Task | None = None
        self._preroll = PrerollRing(cfg.audio.preroll_frames)
        self._gap: list = []

    def _emit(self, name: str, payload: Any = None) -> None:
        if self._on_event is not None:
            self._on_event(name, payload)

    async def run(self) -> None:
        if self.ledger is not None:
            await self.ledger.open()
        self.fsm.fire(TurnEvent.WAKE)
        self._emit("state", self.fsm.state)
        try:
            async for frame in self.audio.frames():
                await self._on_frame(frame)
            if self._respond_task is not None and not self._respond_task.done():
                await self._respond_task
        finally:
            await self.spec.cancel()
            if self.ledger is not None:
                await self.ledger.close()

    async def _on_frame(self, frame: AudioFrame) -> None:
        verdict = self.vad.process(frame.pcm)
        state = self.fsm.state
        if state is TurnState.LISTENING:
            await self._frame_listening(frame, verdict)
        elif state in (TurnState.THINKING, TurnState.SPEAKING):
            await self._frame_duplex(frame, verdict)

    async def _frame_listening(self, frame: AudioFrame, v: VadFrame) -> None:
        self._preroll.push(frame)
        if not self._capturing:
            if v.event is VadEvent.SPEECH_START:
                await self._begin_capture(frame, v)
            return
        threshold = self.cfg.endpoint.prefinal_silence_ms
        if threshold is not None and v.silence_ms > threshold:
            self._gap.append(frame.pcm)
        else:
            if self._gap:
                for pcm in self._gap:
                    self.stt.feed(pcm)
                self._gap.clear()
            self.stt.feed(frame.pcm)
        partial = self.stt.poll_partial()
        if partial:
            self.endpointer.update_partial(partial)
            self._emit("partial", partial)
            self.spec.launch(partial, self.history, self.cfg.system_prompt)
        if threshold is not None and v.silence_ms >= threshold > v.silence_ms - self._frame_ms:
            self.stt.prefinalize()
        if self.endpointer.observe(v) is EndpointDecision.COMMIT:
            self._commit_endpoint(frame, v)

    async def _begin_capture(self, frame: AudioFrame, v: VadFrame) -> None:
        self._capturing = True
        self._clock = _TurnClock(t_speech_start=frame.t_capture - v.speech_ms / 1000.0)
        self._reply_parts = []
        self._turn_final = ""
        self._gap.clear()
        await self.stt.start(self.cfg.language)
        preroll = self._preroll.dump()
        if preroll.size:
            self.stt.feed(preroll)
        self._emit("speech_start", None)

    def _commit_endpoint(self, frame: AudioFrame, v: VadFrame) -> None:
        self._clock.t_speech_end = frame.t_capture - v.silence_ms / 1000.0
        self._clock.t_endpoint_commit = time.monotonic()
        self._capturing = False
        self._gap.clear()
        self.vad.end_run()
        self.endpointer.reset()
        self.vad.set_barge_mode(True)
        self.fsm.fire(TurnEvent.ENDPOINT_COMMIT)
        self._emit("state", self.fsm.state)
        self._respond_task = asyncio.create_task(self._respond())

    async def _frame_duplex(self, frame: AudioFrame, v: VadFrame) -> None:
        self._preroll.push(frame)
        if v.event is not VadEvent.SPEECH_START:
            return
        assert self._respond_task is not None
        self._respond_task.cancel()
        try:
            await self._respond_task
        except asyncio.CancelledError:
            pass
        self._respond_task = None
        self.audio.stop_playback()
        await self.spec.cancel()
        self.fsm.fire(TurnEvent.BARGE_IN)
        self.vad.set_barge_mode(False)
        self._emit("barge_in", None)
        self._emit("state", self.fsm.state)
        await self._write_receipt(barge_in=True, spec_hit=False)
        await self._begin_capture(frame, v)

    async def _respond(self) -> None:
        clock = self._clock
        final = await self.stt.finalize()
        clock.t_stt_final = time.monotonic()
        self._turn_final = final
        self._emit("final", final)
        if not final.strip():
            await self.spec.cancel()
            self.fsm.fire(TurnEvent.PLAYBACK_DONE)
            self.vad.set_barge_mode(False)
            self._emit("discard", None)
            self._emit("state", self.fsm.state)
            return
        outcome = await self.spec.resolve(final, self.history, self.cfg.system_prompt)
        self.history.append({"role": "user", "content": final})
        chunker = ClauseChunker(self.cfg.chunker)
        prefetch_used = False

        async def synth(text: str) -> tuple:
            nonlocal prefetch_used
            task = outcome.prefetch_task
            if not prefetch_used and task is not None and text == outcome.prefetch_text:
                prefetch_used = True
                if not task.done() or (not task.cancelled() and task.exception() is None):
                    return await task
            return await self.tts.synthesize(text)

        async for token in outcome.stream:
            if clock.t_first_token is None:
                clock.t_first_token = (
                    outcome.draft_first_token_at
                    if outcome.hit and outcome.draft_first_token_at is not None
                    else time.monotonic()
                )
            self._reply_parts.append(token)
            for chunk in chunker.feed(token):
                await self._speak(chunk, clock, synth)
        tail = chunker.flush()
        if tail:
            await self._speak(tail, clock, synth)
        if not prefetch_used and outcome.prefetch_task is not None:
            outcome.prefetch_task.cancel()
        await self.audio.drain_playback()
        reply = "".join(self._reply_parts).strip()
        if reply:
            self.history.append({"role": "assistant", "content": reply})
        self.fsm.fire(TurnEvent.PLAYBACK_DONE)
        self.vad.set_barge_mode(False)
        self._emit("state", self.fsm.state)
        await self._write_receipt(barge_in=False, spec_hit=outcome.hit)

    async def _speak(self, text: str, clock: _TurnClock, synth=None) -> None:
        pcm, rate = await (synth(text) if synth is not None else self.tts.synthesize(text))
        if clock.t_first_audio is None:
            clock.t_first_audio = time.monotonic()
            self.fsm.fire(TurnEvent.RESPONSE_START)
            self._emit("state", self.fsm.state)
        self._emit("chunk", text)
        self.audio.play(pcm, rate)

    async def _write_receipt(self, barge_in: bool, spec_hit: bool) -> None:
        clock = self._clock
        receipt = TurnReceipt(
            session_id=self.session_id,
            turn_index=self._turn_index,
            user_text=self._turn_final,
            agent_text="".join(self._reply_parts).strip(),
            t_speech_start=clock.t_speech_start,
            t_speech_end=clock.t_speech_end,
            t_endpoint_commit=clock.t_endpoint_commit,
            t_stt_final=clock.t_stt_final,
            t_first_token=clock.t_first_token,
            t_first_audio=clock.t_first_audio,
            speculative_hit=spec_hit,
            barge_in=barge_in,
        )
        self.receipts.append(receipt)
        self._turn_index += 1
        if self.ledger is not None:
            await self.ledger.commit(receipt)
        self._emit("receipt", receipt)
