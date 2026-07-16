# █ SYS_ID: BABYLON-60 VOICE TRANSDUCER — BENCHMARK SOTA (C5-REAL)
# █ Mide TTFA (fin de habla → primer audio del agente) sobre el pipeline REAL con
# █ backends sintéticos de latencia inyectada conservadora. Aísla la ganancia de
# █ arquitectura (endpointing semántico + especulación) del coste de los modelos.
# █ AUTHOR: Borja Moskv (borjamoskv)
from __future__ import annotations

import asyncio
import dataclasses
import statistics

from .audio_io import SimulatedAudio
from .brain import EchoBrain
from .config import AudioConfig, EndpointConfig, SpeculativeConfig, VoiceAgentConfig
from .pipeline import VoiceAgentPipeline
from .stt import ScriptedStt
from .tts import NullTts

_UTTERANCE = "cuál es el estado del ledger."
_STT_FINAL_LATENCY_S = 0.080
_BRAIN_FIRST_TOKEN_S = 0.150
_BRAIN_INTER_TOKEN_S = 0.012
_TTS_CHUNK_LATENCY_S = 0.110

_SOTA_REFERENCES: list[tuple[str, float]] = [
    ("Humano (gap medio de turno)", 230.0),
    ("S2S comercial (voice-to-voice, ref. pública)", 500.0),
    ("Cascada half-duplex típica (endpoint fijo)", 1100.0),
]


@dataclasses.dataclass(frozen=True)
class BenchmarkReport:
    label: str
    turns: int
    ttfa_p50_ms: float
    ttfa_p95_ms: float
    hang_p50_ms: float
    stt_final_p50_ms: float
    spec_hit_rate: float

    def row(self) -> str:
        return (
            f"| {self.label:<38} | {self.ttfa_p50_ms:8.1f} | {self.ttfa_p95_ms:8.1f} "
            f"| {self.hang_p50_ms:7.1f} | {self.spec_hit_rate * 100:5.1f}% |"
        )


def _percentile(values: list[float], q: float) -> float:
    ordered = sorted(values)
    idx = min(len(ordered) - 1, max(0, round(q * (len(ordered) - 1))))
    return ordered[idx]


async def _run_turn(
    speculative: bool,
    semantic_endpoint: bool,
    time_scale: float,
    prefetch: bool = True,
    prefinal: bool = True,
) -> VoiceAgentPipeline:
    if semantic_endpoint:
        endpoint = EndpointConfig(prefinal_silence_ms=60.0 if prefinal else None)
    else:
        endpoint = EndpointConfig(
            base_hang_ms=700.0, fast_hang_ms=700.0, slow_hang_ms=700.0, prefinal_silence_ms=None
        )
    cfg = VoiceAgentConfig(
        endpoint=endpoint,
        speculative=SpeculativeConfig(enabled=speculative, prefetch_tts=prefetch),
    )
    audio = SimulatedAudio(
        AudioConfig(),
        script=[("silence", 400), ("speech", 1400), ("silence", 1300)],
        time_scale=time_scale,
    )
    stt = ScriptedStt(
        final_text=_UTTERANCE,
        partial_script=[(700.0, "cuál es el estado"), (1300.0, _UTTERANCE)],
        finalize_latency_s=_STT_FINAL_LATENCY_S * time_scale,
    )
    brain = EchoBrain(
        first_token_latency_s=_BRAIN_FIRST_TOKEN_S * time_scale,
        inter_token_s=_BRAIN_INTER_TOKEN_S * time_scale,
    )
    tts = NullTts(latency_s=_TTS_CHUNK_LATENCY_S * time_scale, seconds_per_char=0.008)
    pipeline = VoiceAgentPipeline(cfg, audio, stt, brain, tts)
    await pipeline.run()
    return pipeline

async def run_benchmark(
    label: str,
    turns: int = 8,
    speculative: bool = True,
    semantic_endpoint: bool = True,
    time_scale: float = 1.0,
    prefetch: bool = True,
    prefinal: bool = True,
) -> BenchmarkReport:
    """Latencias en tiempo real. time_scale != 1.0 solo para smoke-tests: mezcla
    reloj de audio y reloj de pared, así que las magnitudes dejan de ser físicas
    (el orden relativo entre configuraciones se preserva)."""
    ttfas: list[float] = []
    hangs: list[float] = []
    stt_finals: list[float] = []
    hits = 0
    for _ in range(turns):
        pipeline = await _run_turn(speculative, semantic_endpoint, time_scale, prefetch, prefinal)
        if not pipeline.receipts:
            raise RuntimeError("Benchmark sin recibo: el turno no colapsó")
        receipt = pipeline.receipts[0]
        if receipt.ttfa_ms is None or receipt.endpoint_hang_ms is None or receipt.stt_final_ms is None:
            raise RuntimeError(f"Recibo incompleto: {receipt}")
        ttfas.append(receipt.ttfa_ms)
        hangs.append(receipt.endpoint_hang_ms)
        stt_finals.append(receipt.stt_final_ms)
        hits += int(receipt.speculative_hit)
    return BenchmarkReport(
        label=label,
        turns=turns,
        ttfa_p50_ms=statistics.median(ttfas),
        ttfa_p95_ms=_percentile(ttfas, 0.95),
        hang_p50_ms=statistics.median(hangs),
        stt_final_p50_ms=statistics.median(stt_finals),
        spec_hit_rate=hits / turns,
    )


async def run_full_benchmark(turns: int = 8, time_scale: float = 1.0) -> list[BenchmarkReport]:
    v2 = await run_benchmark("BABYLON-60 v2 (prefinal + prefetch TTS)", turns, True, True, time_scale)
    v1 = await run_benchmark(
        "BABYLON-60 v1 (especulación básica)", turns, True, True, time_scale, prefetch=False, prefinal=False
    )
    baseline = await run_benchmark(
        "Baseline: endpoint fijo 700ms, sin espec.", turns, False, False, time_scale, prefetch=False, prefinal=False
    )
    return [v2, v1, baseline]


def render(reports: list[BenchmarkReport]) -> str:
    lines = [
        "█▄ BABYLON-60 VOICE TRANSDUCER — BENCHMARK TTFA (fin de habla → primer audio)",
        f"█▄ Latencias inyectadas: STT_final={_STT_FINAL_LATENCY_S * 1000:.0f}ms · "
        f"LLM_tok1={_BRAIN_FIRST_TOKEN_S * 1000:.0f}ms · TTS_chunk={_TTS_CHUNK_LATENCY_S * 1000:.0f}ms · "
        "medición en tiempo real",
        "",
        "| Configuración                          | p50 (ms) | p95 (ms) | hang    | spec  |",
        "|----------------------------------------|----------|----------|---------|-------|",
        *[r.row() for r in reports],
        "",
        "Referencias voice-to-voice:",
        *[f"  · {name}: ~{ms:.0f}ms" for name, ms in _SOTA_REFERENCES],
    ]
    best = reports[0]
    for name, ms in _SOTA_REFERENCES:
        delta = ms - best.ttfa_p50_ms
        verdict = "SUPERADO" if delta > 0 else "no superado"
        lines.append(f"  ⚡ vs {name}: {delta:+.0f}ms → {verdict}")
    return "\n".join(lines)


def main(turns: int = 8, time_scale: float = 1.0) -> str:
    reports = asyncio.run(run_full_benchmark(turns, time_scale))
    output = render(reports)
    print(output)
    return output


if __name__ == "__main__":
    main()
