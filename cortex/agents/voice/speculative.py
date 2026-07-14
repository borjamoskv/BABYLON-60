# █ SYS_ID: BABYLON-60 VOICE TRANSDUCER — GENERACIÓN ESPECULATIVA (C5-REAL)
# █ Lanza el LLM sobre el parcial STT durante la ventana de hang. Si el transcript
# █ final coincide (similitud >= τ), los tokens ya generados se sirven a coste cero:
# █ la latencia de primer token colapsa a ~0 (o negativa respecto al fin de habla).
# █ Con prefetch_tts, la primera cláusula del draft se pre-sintetiza también: en un
# █ hit, el primer audio del agente ya existe al cerrar el endpoint.
# █ AUTHOR: Borja Moskv (borjamoskv)
from __future__ import annotations

import asyncio
import dataclasses
import difflib
import time
from collections.abc import AsyncIterator
from typing import Protocol

from .chunker import ClauseChunker
from .config import ChunkerConfig, SpeculativeConfig
from .tts import TtsBackend

Message = dict[str, str]
_DONE = object()


class BrainBackend(Protocol):
    def stream(self, messages: list[Message], system: str) -> AsyncIterator[str]: ...


def normalize_transcript(text: str) -> str:
    kept = [ch.lower() if ch.isalnum() else " " for ch in text]
    return " ".join("".join(kept).split())


def transcript_similarity(a: str, b: str) -> float:
    return difflib.SequenceMatcher(None, normalize_transcript(a), normalize_transcript(b)).ratio()


@dataclasses.dataclass
class _Draft:
    partial: str
    queue: asyncio.Queue
    pump: asyncio.Task | None = None
    first_token_at: float | None = None
    chunker: ClauseChunker | None = None
    prefetch_text: str | None = None
    prefetch_task: asyncio.Task | None = None


@dataclasses.dataclass(frozen=True)
class SpecOutcome:
    stream: AsyncIterator[str]
    hit: bool
    draft_first_token_at: float | None
    prefetch_text: str | None = None
    prefetch_task: asyncio.Task | None = None


class SpeculativeExecutor:
    def __init__(
        self,
        brain: BrainBackend,
        cfg: SpeculativeConfig,
        tts: TtsBackend | None = None,
        chunker_cfg: ChunkerConfig | None = None,
    ) -> None:
        self._brain = brain
        self._cfg = cfg
        self._tts = tts
        self._chunker_cfg = chunker_cfg
        self._draft: _Draft | None = None

    def launch(self, partial: str, messages: list[Message], system: str) -> None:
        if not self._cfg.enabled or len(partial.strip()) < self._cfg.min_partial_chars:
            return
        if self._draft and normalize_transcript(self._draft.partial) == normalize_transcript(partial):
            return
        self._cancel_draft_nowait()
        gen = self._brain.stream([*messages, {"role": "user", "content": partial}], system)
        draft = _Draft(partial=partial, queue=asyncio.Queue())
        if self._tts is not None and self._cfg.prefetch_tts and self._chunker_cfg is not None:
            draft.chunker = ClauseChunker(self._chunker_cfg)
        draft.pump = asyncio.create_task(self._pump(gen, draft))
        self._draft = draft

    async def _pump(self, gen: AsyncIterator[str], draft: _Draft) -> None:
        try:
            async for token in gen:
                if draft.first_token_at is None:
                    draft.first_token_at = time.monotonic()
                draft.queue.put_nowait(token)
                self._maybe_prefetch(draft, token)
            draft.queue.put_nowait(_DONE)
        except asyncio.CancelledError:
            raise
        except BaseException as exc:
            draft.queue.put_nowait(exc)

    def _maybe_prefetch(self, draft: _Draft, token: str) -> None:
        if draft.chunker is None or draft.prefetch_task is not None:
            return
        chunks = draft.chunker.feed(token)
        if chunks:
            assert self._tts is not None
            draft.prefetch_text = chunks[0]
            draft.prefetch_task = asyncio.create_task(self._tts.synthesize(chunks[0]))
            draft.chunker = None

    async def resolve(self, final: str, messages: list[Message], system: str) -> SpecOutcome:
        draft = self._draft
        self._draft = None
        if (
            self._cfg.enabled
            and draft is not None
            and transcript_similarity(draft.partial, final) >= self._cfg.commit_similarity
        ):
            return SpecOutcome(
                stream=self._drain(draft),
                hit=True,
                draft_first_token_at=draft.first_token_at,
                prefetch_text=draft.prefetch_text,
                prefetch_task=draft.prefetch_task,
            )
        if draft is not None:
            if draft.pump is not None:
                draft.pump.cancel()
            if draft.prefetch_task is not None:
                draft.prefetch_task.cancel()
        fresh = self._brain.stream([*messages, {"role": "user", "content": final}], system)
        return SpecOutcome(stream=fresh, hit=False, draft_first_token_at=None)

    async def _drain(self, draft: _Draft) -> AsyncIterator[str]:
        while True:
            item = await draft.queue.get()
            if item is _DONE:
                return
            if isinstance(item, BaseException):
                raise item
            yield item

    def _cancel_draft_nowait(self) -> None:
        if self._draft is not None:
            if self._draft.pump is not None:
                self._draft.pump.cancel()
            if self._draft.prefetch_task is not None:
                self._draft.prefetch_task.cancel()
            self._draft = None

    async def cancel(self) -> None:
        self._cancel_draft_nowait()
