# █ SYS_ID: BABYLON-60 VOICE TRANSDUCER — CONFIG (C5-REAL)
# █ AUTHOR: Borja Moskv (borjamoskv)
from __future__ import annotations

import dataclasses
from pathlib import Path


@dataclasses.dataclass(frozen=True)
class AudioConfig:
    sample_rate: int = 16_000
    frame_ms: int = 20
    channels: int = 1
    preroll_ms: int = 320

    @property
    def frame_samples(self) -> int:
        return self.sample_rate * self.frame_ms // 1000

    @property
    def preroll_frames(self) -> int:
        return max(1, self.preroll_ms // self.frame_ms)


@dataclasses.dataclass(frozen=True)
class VadConfig:
    margin_on_db: float = 9.0
    margin_off_db: float = 6.0
    attack_frames: int = 2
    floor_init_dbfs: float = -60.0
    floor_alpha_down: float = 0.30
    floor_alpha_up: float = 0.01
    barge_margin_boost_db: float = 12.0
    barge_attack_frames: int = 6


@dataclasses.dataclass(frozen=True)
class EndpointConfig:
    base_hang_ms: float = 480.0
    fast_hang_ms: float = 200.0
    slow_hang_ms: float = 900.0
    min_speech_ms: float = 200.0
    max_utterance_ms: float = 30_000.0
    prefinal_silence_ms: float | None = 60.0


@dataclasses.dataclass(frozen=True)
class SpeculativeConfig:
    enabled: bool = True
    min_partial_chars: int = 12
    commit_similarity: float = 0.92
    prefetch_tts: bool = True


@dataclasses.dataclass(frozen=True)
class ChunkerConfig:
    first_chunk_min_chars: int = 24
    next_chunk_min_chars: int = 60
    max_chunk_chars: int = 240


@dataclasses.dataclass(frozen=True)
class VoiceAgentConfig:
    audio: AudioConfig = dataclasses.field(default_factory=AudioConfig)
    vad: VadConfig = dataclasses.field(default_factory=VadConfig)
    endpoint: EndpointConfig = dataclasses.field(default_factory=EndpointConfig)
    speculative: SpeculativeConfig = dataclasses.field(default_factory=SpeculativeConfig)
    chunker: ChunkerConfig = dataclasses.field(default_factory=ChunkerConfig)
    language: str = "es"
    system_prompt: str = (
        "Eres el transductor de voz de BABYLON-60. Respondes en frases cortas, densas y "
        "sin relleno conversacional. Máximo tres frases por turno salvo petición explícita."
    )
    ledger_path: Path = Path("cortex_voice_ledger.db")
    session_namespace: str = "babylon60.voice"
