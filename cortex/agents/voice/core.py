import os
import asyncio
from .stt import SpeechToText
from .tts import TextToSpeech
from .pipeline import VoicePipeline

class VoiceAgent:
    """High‑performance, speculative full‑duplex voice agent.
    
    - **Speculative generation**: Starts LLM inference on partial transcript.
    - **Full‑duplex**: Barge‑in detection (<120 ms) aborts playback.
    - **Ledger**: Persists per‑turn metrics in `cortex_voice_ledger.db` (WAL).
    """

    def __init__(self, model_path: str, tts_engine: str = "coqui"):
        self.stt = SpeechToText(model_path)
        self.tts = TextToSpeech(tts_engine)
        self.pipeline = VoicePipeline(self.stt, self.tts)
        self.db_path = os.path.join(os.path.dirname(__file__), "cortex_voice_ledger.db")
        self._init_ledger()

    def _init_ledger(self):
        import sqlite3
        conn = sqlite3.connect(self.db_path, isolation_level=None)
        conn.execute("PRAGMA journal_mode=WAL;")
        conn.execute(
            """CREATE TABLE IF NOT EXISTS turn (
                id TEXT PRIMARY KEY,
                start_ts REAL,
                end_ts REAL,
                first_token_ms REAL,
                speculative BOOL,
                latency_ms REAL
            )"""
        )
        conn.close()

    async def run(self):
        await self.pipeline.start()
