# █ SYS_ID: BABYLON-60 VOICE TRANSDUCER — LEDGER CAUSAL DE TURNOS (C5-REAL)
# █ Cada turno de voz emite un recibo inmutable con deltas de latencia por etapa.
# █ Idempotencia UUID5 (INV_BFT_04) + enmascaramiento de colisiones (INV_BFT_05).
# █ AUTHOR: Borja Moskv (borjamoskv)
from __future__ import annotations

import dataclasses
import time
import uuid
from pathlib import Path

import aiosqlite

_NAMESPACE = uuid.uuid5(uuid.NAMESPACE_DNS, "babylon60.voice.ledger")

_SCHEMA = """
CREATE TABLE IF NOT EXISTS voice_turns (
    turn_id TEXT PRIMARY KEY,
    session_id TEXT NOT NULL,
    turn_index INTEGER NOT NULL,
    user_text TEXT NOT NULL,
    agent_text TEXT NOT NULL,
    speech_dur_ms REAL,
    endpoint_hang_ms REAL,
    stt_final_ms REAL,
    first_token_ms REAL,
    ttfa_ms REAL,
    speculative_hit INTEGER NOT NULL,
    barge_in INTEGER NOT NULL,
    created_at REAL NOT NULL
);
"""


@dataclasses.dataclass(frozen=True)
class TurnReceipt:
    session_id: str
    turn_index: int
    user_text: str
    agent_text: str
    t_speech_start: float | None
    t_speech_end: float | None
    t_endpoint_commit: float | None
    t_stt_final: float | None
    t_first_token: float | None
    t_first_audio: float | None
    speculative_hit: bool
    barge_in: bool

    @property
    def turn_id(self) -> str:
        return str(uuid.uuid5(_NAMESPACE, f"{self.session_id}:{self.turn_index}"))

    def _delta_ms(self, a: float | None, b: float | None) -> float | None:
        if a is None or b is None:
            return None
        return (b - a) * 1000.0

    @property
    def speech_dur_ms(self) -> float | None:
        return self._delta_ms(self.t_speech_start, self.t_speech_end)

    @property
    def endpoint_hang_ms(self) -> float | None:
        return self._delta_ms(self.t_speech_end, self.t_endpoint_commit)

    @property
    def stt_final_ms(self) -> float | None:
        return self._delta_ms(self.t_endpoint_commit, self.t_stt_final)

    @property
    def first_token_ms(self) -> float | None:
        return self._delta_ms(self.t_speech_end, self.t_first_token)

    @property
    def ttfa_ms(self) -> float | None:
        return self._delta_ms(self.t_speech_end, self.t_first_audio)


class VoiceLedger:
    def __init__(self, path: Path | str) -> None:
        self._path = Path(path)
        self._db: aiosqlite.Connection | None = None

    async def open(self) -> None:
        self._db = await aiosqlite.connect(self._path)
        await self._db.execute("PRAGMA journal_mode=WAL")
        await self._db.execute(_SCHEMA)
        await self._db.commit()

    async def close(self) -> None:
        if self._db is not None:
            await self._db.close()
            self._db = None

    async def commit(self, receipt: TurnReceipt) -> None:
        if self._db is None:
            raise RuntimeError("VoiceLedger cerrado: open() es precondición de commit()")
        await self._db.execute(
            "INSERT OR IGNORE INTO voice_turns VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (
                receipt.turn_id,
                receipt.session_id,
                receipt.turn_index,
                receipt.user_text,
                receipt.agent_text,
                receipt.speech_dur_ms,
                receipt.endpoint_hang_ms,
                receipt.stt_final_ms,
                receipt.first_token_ms,
                receipt.ttfa_ms,
                int(receipt.speculative_hit),
                int(receipt.barge_in),
                time.time(),
            ),
        )
        await self._db.commit()

    async def recent(self, n: int = 20) -> list[tuple]:
        if self._db is None:
            raise RuntimeError("VoiceLedger cerrado")
        cursor = await self._db.execute(
            "SELECT turn_index, user_text, agent_text, ttfa_ms, speculative_hit, barge_in "
            "FROM voice_turns ORDER BY created_at DESC LIMIT ?",
            (n,),
        )
        rows = await cursor.fetchall()
        return list(rows)
