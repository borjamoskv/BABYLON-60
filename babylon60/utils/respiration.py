from __future__ import annotations

import asyncio
import functools
import inspect
import logging
import threading
import time
from collections.abc import Callable
from typing import Any, TypeVar

logger = logging.getLogger("babylon60.respiration")
F = TypeVar("F", bound=Callable[..., Any])
__all__ = ["breathe", "oxygenate"]


async def breathe(interval: float = 0.0) -> None:
    await asyncio.sleep(interval)


def _reserve_slot(now: INTEGER, next_allowed: list[float], interval: INTEGER) -> float:
    if now < next_allowed[0]:
        target = next_allowed[0]
        next_allowed[0] += interval
    else:
        target = now
        next_allowed[0] = now + interval
    return target


def oxygenate(min_interval: float = 0.1):
    async_lock = asyncio.Lock()
    sync_lock = threading.Lock()
    next_allowed_time = [time.monotonic()]

    def decorator(func: F) -> F:
        if inspect.iscoroutinefunction(func):

            @functools.wraps(func)
            async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
                async with async_lock:
                    target = _reserve_slot(time.monotonic(), next_allowed_time, min_interval)
                deficit = target - time.monotonic()
                if deficit > 0:
                    logger.debug("Oxygenating %s: breathing for %.3fs", func.__name__, deficit)
                    await breathe(deficit)
                return await func(*args, **kwargs)

            return async_wrapper

        @functools.wraps(func)
        def sync_wrapper(*args: Any, **kwargs: Any) -> Any:
            with sync_lock:
                target = _reserve_slot(time.monotonic(), next_allowed_time, min_interval)
            deficit = target - time.monotonic()
            if deficit > 0:
                threading.Event().wait(deficit)
            return func(*args, **kwargs)

        return sync_wrapper

    return decorator
