# █ SYS_ID: BABYLON-60 VOICE TRANSDUCER — BRAIN LOCAL (C5-REAL)
# █ Inferencia MLX en Apple Silicon, puenteada a asyncio vía cola thread-safe.
# █ AUTHOR: Borja Moskv (borjamoskv)
from __future__ import annotations

import asyncio
import threading
from collections.abc import AsyncIterator

from .speculative import BrainBackend, Message

__all__ = ["BrainBackend", "EchoBrain", "MlxBrain"]

_DONE = object()


class EchoBrain:
    """Cerebro determinista para tests y benchmark, con latencias inyectables."""

    def __init__(
        self,
        template: str = "Recibido. Has dicho: {text}. Ledger íntegro, cero anergía.",
        first_token_latency_s: float = 0.0,
        inter_token_s: float = 0.0,
    ) -> None:
        self._template = template
        self._first = first_token_latency_s
        self._inter = inter_token_s
        self.calls: list[str] = []

    async def stream(self, messages: list[Message], system: str) -> AsyncIterator[str]:
        user = messages[-1]["content"]
        self.calls.append(user)
        text = self._template.format(text=user)
        await asyncio.sleep(self._first)
        words = text.split(" ")
        for i, word in enumerate(words):
            if i:
                await asyncio.sleep(self._inter)
                yield " " + word
            else:
                yield word


class MlxBrain:
    """LLM local vía mlx-lm (Apple Silicon). Streaming token a token."""

    def __init__(
        self,
        model_id: str = "mlx-community/Llama-3.2-3B-Instruct-4bit",
        max_tokens: int = 220,
        temperature: float = 0.6,
    ) -> None:
        self._model_id = model_id
        self._max_tokens = max_tokens
        self._temperature = temperature
        self._model = None
        self._tokenizer = None

    def _ensure_loaded(self):
        if self._model is None:
            try:
                from mlx_lm import load
            except ImportError as exc:
                raise ImportError("mlx-lm ausente. Instalar: pip install -e '.[voice-full]'") from exc
            self._model, self._tokenizer = load(self._model_id)
        return self._model, self._tokenizer

    async def stream(self, messages: list[Message], system: str) -> AsyncIterator[str]:
        model, tokenizer = await asyncio.to_thread(self._ensure_loaded)
        prompt = tokenizer.apply_chat_template(
            [{"role": "system", "content": system}, *messages],
            add_generation_prompt=True,
            tokenize=False,
        )
        loop = asyncio.get_running_loop()
        queue: asyncio.Queue = asyncio.Queue()
        stop = threading.Event()

        def worker() -> None:
            from mlx_lm import stream_generate
            from mlx_lm.sample_utils import make_sampler

            try:
                sampler = make_sampler(temp=self._temperature)
                for response in stream_generate(
                    model, tokenizer, prompt, max_tokens=self._max_tokens, sampler=sampler
                ):
                    if stop.is_set():
                        break
                    loop.call_soon_threadsafe(queue.put_nowait, response.text)
                loop.call_soon_threadsafe(queue.put_nowait, _DONE)
            except BaseException as exc:
                loop.call_soon_threadsafe(queue.put_nowait, exc)

        thread = threading.Thread(target=worker, daemon=True, name="mlx-brain")
        thread.start()
        try:
            while True:
                item = await queue.get()
                if item is _DONE:
                    return
                if isinstance(item, BaseException):
                    raise item
                yield item
        finally:
            stop.set()
