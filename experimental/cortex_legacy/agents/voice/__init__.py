"""Entry point for the Babylon60 voice agent.

High-level API: `VoiceAgent` (fachada). CLI: `python -m cortex.agents.voice`.
"""
# █ SYS_ID: BABYLON-60 VOICE TRANSDUCER (C5-REAL)
# █ Full-duplex 100% local: VAD adaptativo, endpointing semántico, especulación
# █ LLM + prefetch TTS, prefinal STT, barge-in <120ms y ledger causal por turno.
# █ AUTHOR: Borja Moskv (borjamoskv)
from .audio_io import SimulatedAudio, SoundDeviceAudio, resample_linear
from .brain import EchoBrain, MlxBrain
from .chunker import ClauseChunker
from .config import (
    AudioConfig,
    ChunkerConfig,
    EndpointConfig,
    SpeculativeConfig,
    VadConfig,
    VoiceAgentConfig,
)
from .core import VoiceAgent
from .endpointing import EndpointDecision, SemanticEndpointer
from .fsm import DuplexTurnFSM, TurnEvent, TurnProtocolError, TurnState
from .ledger import TurnReceipt, VoiceLedger
from .pipeline import VoiceAgentPipeline
from .speculative import SpeculativeExecutor, transcript_similarity
from .stt import FasterWhisperStt, ScriptedStt
from .tts import KokoroTts, NullTts, SayTts
from .vad import VoiceActivityDetector

__all__ = [
    "AudioConfig",
    "ChunkerConfig",
    "ClauseChunker",
    "DuplexTurnFSM",
    "EchoBrain",
    "EndpointConfig",
    "EndpointDecision",
    "FasterWhisperStt",
    "KokoroTts",
    "MlxBrain",
    "NullTts",
    "SayTts",
    "ScriptedStt",
    "SemanticEndpointer",
    "SimulatedAudio",
    "SoundDeviceAudio",
    "SpeculativeConfig",
    "SpeculativeExecutor",
    "TurnEvent",
    "TurnProtocolError",
    "TurnReceipt",
    "TurnState",
    "VadConfig",
    "VoiceActivityDetector",
    "VoiceAgent",
    "VoiceAgentConfig",
    "VoiceAgentPipeline",
    "VoiceLedger",
    "resample_linear",
    "transcript_similarity",
]
