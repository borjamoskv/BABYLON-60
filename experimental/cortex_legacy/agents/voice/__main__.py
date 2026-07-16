# █ SYS_ID: BABYLON-60 VOICE TRANSDUCER — CLI (C5-REAL)
# █ Uso:  python -m cortex.agents.voice            (micrófono, 100% local)
# █        python -m cortex.agents.voice --benchmark
# █ AUTHOR: Borja Moskv (borjamoskv)
from __future__ import annotations

import argparse
import asyncio
from typing import Any

from . import benchmark as bench
from .audio_io import SoundDeviceAudio
from .brain import EchoBrain, MlxBrain
from .config import SpeculativeConfig, VoiceAgentConfig
from .ledger import TurnReceipt, VoiceLedger
from .pipeline import VoiceAgentPipeline
from .stt import FasterWhisperStt
from .tts import KokoroTts, NullTts, SayTts, TtsBackend

_GLYPHS = {"listening": "👁️", "thinking": "🧠", "speaking": "⚡"}


def _printer(name: str, payload: Any) -> None:
    if name == "state":
        print(f"\n{_GLYPHS.get(payload.value, '·')} [{payload.value.upper()}]", flush=True)
    elif name == "partial":
        print(f"  ── {payload}", flush=True)
    elif name == "final":
        print(f"  ►► {payload}", flush=True)
    elif name == "chunk":
        print(f"  ♪ {payload}", flush=True)
    elif name == "barge_in":
        print("  🩸 BARGE-IN: playback purgado", flush=True)
    elif name == "receipt" and isinstance(payload, TurnReceipt):
        ttfa = f"{payload.ttfa_ms:.0f}ms" if payload.ttfa_ms is not None else "—"
        spec = "HIT" if payload.speculative_hit else "miss"
        print(f"  ▣ recibo #{payload.turn_index} · TTFA={ttfa} · spec={spec} · barge={int(payload.barge_in)}")


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="cortex.agents.voice", description="BABYLON-60 Voice Transducer (100% local)")
    parser.add_argument("--benchmark", action="store_true", help="benchmark TTFA sintético, sin hardware")
    parser.add_argument("--turns", type=int, default=8)
    parser.add_argument("--time-scale", type=float, default=1.0)
    parser.add_argument("--brain", choices=("mlx", "echo"), default="mlx")
    parser.add_argument("--tts", choices=("kokoro", "say", "null"), default="kokoro")
    parser.add_argument("--whisper-model", default="small")
    parser.add_argument("--brain-model", default="mlx-community/Llama-3.2-3B-Instruct-4bit")
    parser.add_argument("--voice", default=None, help="voz TTS (kokoro: ef_dora · say: Mónica)")
    parser.add_argument("--language", default="es")
    parser.add_argument("--db", default="cortex_voice_ledger.db")
    parser.add_argument("--no-spec", action="store_true", help="desactiva generación especulativa")
    parser.add_argument("--list-devices", action="store_true")
    return parser


def _build_pipeline(args: argparse.Namespace) -> VoiceAgentPipeline:
    cfg = VoiceAgentConfig(
        language=args.language,
        speculative=SpeculativeConfig(enabled=not args.no_spec),
    )
    stt = FasterWhisperStt(model_size=args.whisper_model)
    brain = MlxBrain(model_id=args.brain_model) if args.brain == "mlx" else EchoBrain()
    tts: TtsBackend
    if args.tts == "kokoro":
        tts = KokoroTts(voice=args.voice or "ef_dora")
    elif args.tts == "say":
        tts = SayTts(voice=args.voice or "Mónica")
    else:
        tts = NullTts()
    audio = SoundDeviceAudio(cfg.audio)
    ledger = VoiceLedger(args.db)
    return VoiceAgentPipeline(cfg, audio, stt, brain, tts, ledger=ledger, on_event=_printer)


def main() -> None:
    args = _build_parser().parse_args()
    if args.list_devices:
        import sounddevice as sd

        print(sd.query_devices())
        return
    if args.benchmark:
        bench.main(turns=args.turns, time_scale=args.time_scale)
        return
    pipeline = _build_pipeline(args)
    print("█▄ BABYLON-60 VOICE TRANSDUCER — full-duplex local. Ctrl-C para colapsar.")
    try:
        asyncio.run(pipeline.run())
    except KeyboardInterrupt:
        print(f"\n█▄ Sesión {pipeline.session_id[:8]} sellada · {len(pipeline.receipts)} turnos en ledger.")


if __name__ == "__main__":
    main()
