# █ SYS_ID: BABYLON-60 VOICE TRANSDUCER — TEST DE VIOLACIÓN (C5-REAL)
# █ Suite sin hardware de audio: VAD sintético, FSM, especulación, ledger, E2E.
# █ AUTHOR: Borja Moskv (borjamoskv)
from __future__ import annotations

import asyncio

import numpy as np
import pytest

from cortex.agents.voice import (
    AudioConfig,
    ChunkerConfig,
    ClauseChunker,
    DuplexTurnFSM,
    EchoBrain,
    EndpointConfig,
    NullTts,
    ScriptedStt,
    SemanticEndpointer,
    SimulatedAudio,
    SpeculativeConfig,
    SpeculativeExecutor,
    TurnEvent,
    TurnProtocolError,
    TurnReceipt,
    TurnState,
    VadConfig,
    VoiceActivityDetector,
    VoiceAgent,
    VoiceAgentConfig,
    VoiceAgentPipeline,
    VoiceLedger,
    transcript_similarity,
)
from cortex.agents.voice.vad import VadEvent, VadFrame

_AUDIO = AudioConfig()
_UTTERANCE = "cuál es el estado del ledger."


def _tone(amp: float) -> np.ndarray:
    t = np.arange(_AUDIO.frame_samples) / _AUDIO.sample_rate
    return np.clip(amp * np.sin(2 * np.pi * 200.0 * t), -32768, 32767).astype(np.int16)


def _noise(amp: float = 10.0) -> np.ndarray:
    rng = np.random.default_rng(7)
    return np.clip(rng.normal(0, amp, _AUDIO.frame_samples), -32768, 32767).astype(np.int16)


def test_vad_detects_speech_run_and_silence_accumulation():
    vad = VoiceActivityDetector(VadConfig(), _AUDIO)
    events = [vad.process(_noise()).event for _ in range(30)]
    assert VadEvent.SPEECH_START not in events

    started = False
    for _ in range(10):
        if vad.process(_tone(9000)).event is VadEvent.SPEECH_START:
            started = True
            break
    assert started and vad.in_run

    frame = None
    for _ in range(25):
        frame = vad.process(_noise())
    assert frame is not None and frame.in_run and frame.silence_ms >= 400.0


def test_semantic_endpointer_adaptive_hang():
    cfg = EndpointConfig()
    ep = SemanticEndpointer(cfg)
    assert ep.hang_ms() == cfg.base_hang_ms
    ep.update_partial("el ledger está íntegro.")
    assert ep.hang_ms() == cfg.fast_hang_ms
    ep.update_partial("quiero que revises el ledger y")
    assert ep.hang_ms() == cfg.slow_hang_ms
    ep.update_partial("revisa el estado general")
    assert ep.hang_ms() == cfg.base_hang_ms

    frame = VadFrame(
        event=VadEvent.NONE, active=False, in_run=True,
        speech_ms=1000.0, silence_ms=cfg.fast_hang_ms + 20.0,
        energy_dbfs=-30.0, noise_floor_dbfs=-60.0,
    )
    ep.update_partial("terminado.")
    assert ep.observe(frame).value == "commit"


def test_clause_chunker_boundaries_and_flush():
    chunker = ClauseChunker(ChunkerConfig(first_chunk_min_chars=8, next_chunk_min_chars=20, max_chunk_chars=80))
    out = chunker.feed("Ledger íntegro. Cero anergía detectada, todo")
    assert out[0] == "Ledger íntegro."
    assert chunker.flush() is not None
    assert chunker.flush() is None


def test_fsm_full_duplex_and_invalid_transition():
    fsm = DuplexTurnFSM()
    fsm.fire(TurnEvent.WAKE)
    fsm.fire(TurnEvent.ENDPOINT_COMMIT)
    fsm.fire(TurnEvent.RESPONSE_START)
    assert fsm.state is TurnState.SPEAKING
    fsm.fire(TurnEvent.BARGE_IN)
    assert fsm.state is TurnState.LISTENING
    with pytest.raises(TurnProtocolError):
        fsm.fire(TurnEvent.RESPONSE_START)


def test_speculative_hit_serves_draft_without_second_call():
    async def scenario() -> tuple[bool, int, str]:
        brain = EchoBrain(template="OK: {text}")
        spec = SpeculativeExecutor(brain, SpeculativeConfig(min_partial_chars=4))
        spec.launch("cuál es el estado del ledger", [], "sys")
        await asyncio.sleep(0.05)
        outcome = await spec.resolve(_UTTERANCE, [], "sys")
        text = "".join([tok async for tok in outcome.stream])
        return outcome.hit, len(brain.calls), text

    hit, calls, text = asyncio.run(scenario())
    assert hit is True and calls == 1 and text.startswith("OK:")


def test_speculative_miss_relaunches_fresh():
    async def scenario() -> tuple[bool, int]:
        brain = EchoBrain(template="OK: {text}")
        spec = SpeculativeExecutor(brain, SpeculativeConfig(min_partial_chars=4))
        spec.launch("háblame del clima en bilbao", [], "sys")
        await asyncio.sleep(0.05)
        outcome = await spec.resolve(_UTTERANCE, [], "sys")
        _ = "".join([tok async for tok in outcome.stream])
        return outcome.hit, len(brain.calls)

    hit, calls = asyncio.run(scenario())
    assert hit is False and calls == 2
    assert transcript_similarity("Cuál es el estado del ledger.", "cuál es el estado del ledger") > 0.98


def test_ledger_idempotent_commit(tmp_path):
    receipt = TurnReceipt(
        session_id="s1", turn_index=0, user_text="hola", agent_text="mundo",
        t_speech_start=100.0, t_speech_end=101.2, t_endpoint_commit=101.4,
        t_stt_final=101.5, t_first_token=101.55, t_first_audio=101.65,
        speculative_hit=True, barge_in=False,
    )

    async def scenario() -> tuple[int, float | None]:
        ledger = VoiceLedger(tmp_path / "voice.db")
        await ledger.open()
        await ledger.commit(receipt)
        await ledger.commit(receipt)
        rows = await ledger.recent()
        await ledger.close()
        return len(rows), receipt.ttfa_ms

    count, ttfa = asyncio.run(scenario())
    assert count == 1
    assert ttfa is not None and abs(ttfa - 450.0) < 1e-6


def _build_pipeline(
    script: list[tuple[str, float]], scale: float = 0.25, cfg: VoiceAgentConfig | None = None
) -> VoiceAgentPipeline:
    cfg = cfg or VoiceAgentConfig()
    audio = SimulatedAudio(_AUDIO, script=script, time_scale=scale)
    stt = ScriptedStt(
        final_text=_UTTERANCE,
        partial_script=[(700.0, "cuál es el estado"), (1500.0, _UTTERANCE)],
        finalize_latency_s=0.08 * scale,
    )
    brain = EchoBrain(first_token_latency_s=0.15 * scale, inter_token_s=0.002)
    tts = NullTts(latency_s=0.11 * scale)
    return VoiceAgentPipeline(cfg, audio, stt, brain, tts)


def test_pipeline_e2e_single_turn_receipt():
    pipeline = _build_pipeline([("silence", 400), ("speech", 1400), ("silence", 2400)])
    asyncio.run(pipeline.run())

    assert len(pipeline.receipts) == 1
    r = pipeline.receipts[0]
    assert r.user_text == _UTTERANCE
    assert r.agent_text and not r.barge_in and r.speculative_hit
    assert r.t_speech_start < r.t_speech_end < r.t_endpoint_commit <= r.t_stt_final
    assert r.t_first_audio is not None and r.ttfa_ms is not None and r.ttfa_ms > 0
    assert [m["role"] for m in pipeline.history] == ["user", "assistant"]
    assert pipeline.fsm.state is TurnState.LISTENING


def test_pipeline_barge_in_kills_playback_and_opens_new_turn():
    script = [
        ("silence", 400), ("speech", 1200), ("silence", 600),
        ("speech", 900), ("silence", 1400),
    ]
    pipeline = _build_pipeline(script)
    audio = pipeline.audio
    asyncio.run(pipeline.run())

    assert len(pipeline.receipts) == 2
    assert pipeline.receipts[0].barge_in is True
    assert pipeline.receipts[1].barge_in is False
    assert audio.stopped_playbacks >= 1


def test_scripted_stt_prefinal_reuse_and_invalidation():
    async def scenario() -> tuple[bool, bool]:
        stt = ScriptedStt("hola mundo", finalize_latency_s=0.03)
        await stt.start("es")
        stt.feed(np.zeros(1600, dtype=np.int16))
        stt.prefinalize()
        await asyncio.sleep(0.06)
        await stt.finalize()
        reused = stt.prefinal_used
        await stt.start("es")
        stt.feed(np.zeros(1600, dtype=np.int16))
        stt.prefinalize()
        stt.feed(np.zeros(1600, dtype=np.int16))
        await stt.finalize()
        return reused, stt.prefinal_used

    reused, invalidated = asyncio.run(scenario())
    assert reused is True and invalidated is False


def test_pipeline_v2_prefetch_and_prefinal_collapse_ttfa():
    script = [("silence", 400), ("speech", 1400), ("silence", 2400)]
    v2 = _build_pipeline(script)
    asyncio.run(v2.run())
    r2 = v2.receipts[0]
    assert v2.stt.prefinal_used is True
    first_chunk = v2.tts.synthesized[0]
    assert v2.tts.synthesized.count(first_chunk) == 2  # 1 por draft especulativo; _respond NO re-sintetiza

    cfg_v1 = VoiceAgentConfig(
        endpoint=EndpointConfig(prefinal_silence_ms=None),
        speculative=SpeculativeConfig(prefetch_tts=False),
    )
    v1 = _build_pipeline(script, cfg=cfg_v1)
    asyncio.run(v1.run())
    r1 = v1.receipts[0]
    assert v1.tts.synthesized.count(first_chunk) == 1  # sin prefetch: solo la síntesis de _respond
    assert r2.ttfa_ms is not None and r1.ttfa_ms is not None
    assert r2.ttfa_ms < r1.ttfa_ms
    assert r2.stt_final_ms is not None and r1.stt_final_ms is not None
    assert r2.stt_final_ms < r1.stt_final_ms


def test_voice_agent_facade_e2e_with_injected_backends():
    agent = VoiceAgent(
        cfg=VoiceAgentConfig(),
        stt=ScriptedStt(_UTTERANCE, [(700.0, "cuál es el estado"), (1500.0, _UTTERANCE)], 0.02),
        brain=EchoBrain(),
        tts=NullTts(),
        audio=SimulatedAudio(_AUDIO, [("silence", 400), ("speech", 1400), ("silence", 2400)], time_scale=0.25),
        ledger=None,
    )
    asyncio.run(agent.run())
    assert len(agent.receipts) == 1
    assert agent.receipts[0].user_text == _UTTERANCE
    assert [m["role"] for m in agent.history] == ["user", "assistant"]


def test_benchmark_speculative_beats_fixed_baseline():
    from cortex.agents.voice.benchmark import run_full_benchmark

    reports = asyncio.run(run_full_benchmark(turns=2, time_scale=0.1))
    full, _, baseline = reports
    assert full.spec_hit_rate == 1.0
    assert full.ttfa_p50_ms < baseline.ttfa_p50_ms
