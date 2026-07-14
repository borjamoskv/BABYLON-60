# █ SYS_ID: BABYLON-60 VOICE TRANSDUCER — FACHADA VoiceAgent (C5-REAL)
# █ Punto de entrada de alto nivel sobre VoiceAgentPipeline. Backends inyectables;
# █ por defecto: faster-whisper + MLX + Kokoro, 100% local.
# █ AUTHOR: Borja Moskv (borjamoskv)
from __future__ import annotations

from .audio_io import AudioTransport, SoundDeviceAudio
from .brain import MlxBrain
from .config import VoiceAgentConfig
from .ledger import TurnReceipt, VoiceLedger
from .pipeline import EventSink, VoiceAgentPipeline
from .speculative import BrainBackend, Message
from .stt import FasterWhisperStt, StreamingStt
from .tts import KokoroTts, TtsBackend

_UNSET: object = object()


class VoiceAgent:
    """Agente de voz full-duplex especulativo (fachada).

    - Especulación: LLM sobre el parcial STT + prefetch TTS de la primera cláusula.
    - Prefinal STT: el decode final corre dentro de la ventana de hang.
    - Full-duplex: barge-in <120ms purga playback y abre turno.
    - Ledger causal por turno en `cortex_voice_ledger.db` (aiosqlite, WAL, UUID5).
    """

    def __init__(
        self,
        cfg: VoiceAgentConfig | None = None,
        stt: StreamingStt | None = None,
        brain: BrainBackend | None = None,
        tts: TtsBackend | None = None,
        audio: AudioTransport | None = None,
        ledger: VoiceLedger | None | object = _UNSET,
        on_event: EventSink | None = None,
    ) -> None:
        self.cfg = cfg or VoiceAgentConfig()
        resolved_ledger = VoiceLedger(self.cfg.ledger_path) if ledger is _UNSET else ledger
        assert resolved_ledger is None or isinstance(resolved_ledger, VoiceLedger)
        self.pipeline = VoiceAgentPipeline(
            self.cfg,
            audio if audio is not None else SoundDeviceAudio(self.cfg.audio),
            stt if stt is not None else FasterWhisperStt(),
            brain if brain is not None else MlxBrain(),
            tts if tts is not None else KokoroTts(),
            ledger=resolved_ledger,
            on_event=on_event,
        )

    @property
    def session_id(self) -> str:
        return self.pipeline.session_id

    @property
    def receipts(self) -> list[TurnReceipt]:
        return self.pipeline.receipts

    @property
    def history(self) -> list[Message]:
        return self.pipeline.history

    async def run(self) -> None:
        await self.pipeline.run()
