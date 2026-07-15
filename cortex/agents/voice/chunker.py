# █ SYS_ID: BABYLON-60 VOICE TRANSDUCER — CLAUSE CHUNKER (C5-REAL)
# █ Segmenta el stream del LLM en cláusulas prosódicas para TTS incremental.
# █ Primer chunk agresivo (TTFA mínimo), siguientes más largos (prosodia estable).
# █ AUTHOR: Borja Moskv (borjamoskv)
from __future__ import annotations

from .config import ChunkerConfig

_STRONG_BOUNDARIES = ".?!…:;\n"


class ClauseChunker:
    def __init__(self, cfg: ChunkerConfig) -> None:
        self._cfg = cfg
        self._buffer = ""
        self._emitted = 0

    def _min_chars(self) -> int:
        return self._cfg.first_chunk_min_chars if self._emitted == 0 else self._cfg.next_chunk_min_chars

    def _cut(self, index: int) -> str:
        chunk = self._buffer[: index + 1].strip()
        self._buffer = self._buffer[index + 1 :]
        self._emitted += 1
        return chunk

    def feed(self, delta: str) -> list[str]:
        self._buffer += delta
        out: list[str] = []
        chunk = self._scan()
        while chunk is not None:
            out.append(chunk)
            chunk = self._scan()
        return out

    def _scan(self) -> str | None:
        buf = self._buffer
        for i, ch in enumerate(buf):
            if ch in _STRONG_BOUNDARIES and i + 1 >= 3:
                return self._cut(i)
            if ch == "," and i + 1 >= self._min_chars():
                return self._cut(i)
        if len(buf) >= self._cfg.max_chunk_chars:
            space = buf.rfind(" ", 0, self._cfg.max_chunk_chars)
            if space > 0:
                return self._cut(space)
            return self._cut(self._cfg.max_chunk_chars - 1)
        return None

    def flush(self) -> str | None:
        rest = self._buffer.strip()
        self._buffer = ""
        if rest:
            self._emitted += 1
            return rest
        return None

    def reset(self) -> None:
        self._buffer = ""
        self._emitted = 0
