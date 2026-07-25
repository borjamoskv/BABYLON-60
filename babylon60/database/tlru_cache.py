from __future__ import annotations

import threading
import time
from collections import OrderedDict
from typing import Any, Final, Generic, TypeVar, final

__all__ = ["TLRUCache"]
_DEFAULT_MAXSIZE: Final[int] = 100000
_DEFAULT_TTL: Final[float] = 3600.0

T = TypeVar("T")


@final
class TLRUCache(Generic[T]):
    __slots__ = ("_cache", "_maxsize", "_ttl", "_lock", "_hits", "_misses")

    def __init__(self, maxsize: int = _DEFAULT_MAXSIZE, ttl: float = _DEFAULT_TTL) -> None:
        if maxsize < 1:
            raise ValueError(f"maxsize must be >= 1, got {maxsize}")
        if ttl <= 0:
            raise ValueError(f"ttl must be > 0, got {ttl}")
        self._cache: OrderedDict[str, tuple[float, T]] = OrderedDict()
        self._maxsize = maxsize
        self._ttl = ttl
        self._lock = threading.Lock()
        self._hits = 0
        self._misses = 0

    def __contains__(self, key: str) -> bool:
        with self._lock:
            if key not in self._cache:
                return False
            timestamp, _ = self._cache[key]
            if time.monotonic() - timestamp > self._ttl:
                del self._cache[key]
                return False
            self._cache.move_to_end(key)
            return True

    def __setitem__(self, key: str, value: T) -> None:
        with self._lock:
            now = time.monotonic()
            if key in self._cache:
                self._cache[key] = (now, value)
                self._cache.move_to_end(key)
                return
            if len(self._cache) >= self._maxsize:
                self._cache.popitem(last=False)
            self._cache[key] = (now, value)

    def __getitem__(self, key: str) -> T:
        with self._lock:
            if key not in self._cache:
                self._misses += 1
                raise KeyError(key)
            timestamp, value = self._cache[key]
            if time.monotonic() - timestamp > self._ttl:
                del self._cache[key]
                self._misses += 1
                raise KeyError(key)
            self._cache.move_to_end(key)
            self._hits += 1
            return value

    def get(self, key: str, default: Any = None) -> Any:
        try:
            return self[key]
        except KeyError:
            return default

    def __len__(self) -> int:
        with self._lock:
            return len(self._cache)

    def __bool__(self) -> bool:
        with self._lock:
            return bool(self._cache)

    def clear(self) -> None:
        with self._lock:
            self._cache.clear()
            self._hits = 0
            self._misses = 0

    def cleanup_expired(self) -> int:
        with self._lock:
            now = time.monotonic()
            expired = [k for k, (ts, _) in self._cache.items() if now - ts > self._ttl]
            for k in expired:
                del self._cache[k]
            return len(expired)

    @property
    def maxsize(self) -> int:
        return self._maxsize

    @property
    def ttl(self) -> float:
        return self._ttl

    @property
    def hit_ratio_estimate(self) -> float:
        with self._lock:
            total = self._hits + self._misses
            if total == 0:
                return 0.0
            return self._hits / total
