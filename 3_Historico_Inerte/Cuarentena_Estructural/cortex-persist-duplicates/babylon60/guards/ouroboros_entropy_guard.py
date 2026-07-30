# [C5-REAL] Exergy-Maximized
"""
CORTEX - Ouroboros Entropy Guard (Axiom Ω₁₄: Infinite Loop Prevention).

Detects loop structures, abnormally high repetition, and task leaks/death spirals
in the active asyncio tasks running in the event loop.
"""

from __future__ import annotations

import asyncio
import logging
import math
import threading
import time
from typing import Any

import aiosqlite

logger = logging.getLogger("babylon60.guards.ouroboros_entropy")


class OuroborosEntropyGuard:
    """Detects loop/entropy decay in the active asyncio tasks."""

    def __init__(
        self,
        max_tasks: int = 150,
        repetition_threshold: float = 0.8,
        latency_threshold: float | None = None,
    ):
        import os

        self.max_tasks = max_tasks
        self.repetition_threshold = repetition_threshold
        if latency_threshold is None:
            latency_threshold = float(os.getenv("CORTEX_OEG_LATENCY", "0.1"))
        self.latency_threshold = latency_threshold
        self._monitor_thread: threading.Thread | None = None
        self._stop_event = threading.Event()
        self._last_tick_time = time.time()
        self._active_loop: asyncio.AbstractEventLoop | None = None

    def start(self, loop: asyncio.AbstractEventLoop | None = None) -> None:
        if loop is None:
            try:
                loop = asyncio.get_running_loop()
            except RuntimeError:
                return
        if self._monitor_thread is not None and self._monitor_thread.is_alive():
            return
        self._active_loop = loop
        self._last_tick_time = time.time()
        self._stop_event.clear()
        self._monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self._monitor_thread.start()
        # Schedule the first tick update
        loop.call_soon(self._update_tick)

    def stop(self) -> None:
        self._stop_event.set()
        if self._monitor_thread:
            self._monitor_thread.join(timeout=1.0)
            self._monitor_thread = None

    def _update_tick(self) -> None:
        if self._stop_event.is_set():
            return
        self._last_tick_time = time.time()
        if self._active_loop and self._active_loop.is_running():
            self._active_loop.call_soon(self._update_tick)

    def _monitor_loop(self) -> None:
        while not self._stop_event.is_set():
            if self._stop_event.wait(0.01):
                break
            now = time.time()
            elapsed = now - self._last_tick_time
            if elapsed > self.latency_threshold:
                logger.warning(
                    "[P0] Ouroboros Entropy Guard: Event loop latency exceeded threshold (%fs > %fs)",
                    elapsed,
                    self.latency_threshold,
                )
                # Force cancellation of other tasks
                if self._active_loop and self._active_loop.is_running():
                    self._active_loop.call_soon_threadsafe(self._cancel_all_tasks)

    def _cancel_all_tasks(self) -> None:
        if not self._active_loop:
            return
        current = asyncio.current_task(self._active_loop)
        for task in asyncio.all_tasks(self._active_loop):
            if task is not current and not task.done():
                task.cancel()

    async def check(
        self,
        content: str,
        project: str,
        fact_type: str,
        meta: dict[str, Any],
        conn: aiosqlite.Connection,
        *,
        tenant_id: str = "default",
    ) -> None:
        # Start monitoring automatically if in an active event loop
        try:
            loop = asyncio.get_running_loop()
            import os

            if os.environ.get("CORTEX_TESTING") != "1":
                self.start(loop)
            all_tasks = asyncio.all_tasks(loop)
        except RuntimeError:
            all_tasks = set()

        if len(all_tasks) > self.max_tasks:
            raise ValueError(
                f"[P0] Ouroboros Entropy Guard: Async task limit exceeded ({len(all_tasks)} > {self.max_tasks}). "
                "Potential event loop death spiral / leak detected."
            )

        # 2. Loop detection in task names/coros (repetition)
        task_names = []
        for task in all_tasks:
            name = task.get_name().lower()
            try:
                coro_name = task.get_coro().__name__.lower()  # type: ignore
            except AttributeError:
                coro_name = ""
            task_names.append(f"{name}:{coro_name}")

        # Calculate Jaccard similarity/repetition ratio of task names
        if len(task_names) >= 5:
            # Group identical/near-identical task signatures
            unique_tasks = set(task_names)
            repetition_ratio = 1.0 - (len(unique_tasks) / len(task_names))
            if repetition_ratio > self.repetition_threshold:
                # Find the most repeated task name
                from collections import Counter

                most_common = Counter(task_names).most_common(1)[0]
                raise ValueError(
                    f"[P0] Ouroboros Entropy Guard: Infinite loop detected in async tasks. "
                    f"Task signature '{most_common[0]}' repeated {most_common[1]} times "
                    f"(repetition ratio {repetition_ratio:.2f} > {self.repetition_threshold})."
                )

        # 3. Content Shannon Entropy Check for incoming task payload
        if len(content) > 100:
            entropy = self._calculate_shannon_entropy(content)
            # Rejects abnormally low entropy (potential loop or repetitive garbage)
            if entropy < 1.5:
                raise ValueError(
                    f"[P0] Ouroboros Entropy Guard: Content has abnormally low Shannon entropy ({entropy:.4f}). "
                    "Potential repetitive loop content."
                )

    def _calculate_shannon_entropy(self, s: str) -> float:
        if not s:
            return 0.0
        probabilities = [float(s.count(c)) / len(s) for c in dict.fromkeys(s)]
        return -sum(p * math.log(p, 2) for p in probabilities)
