from __future__ import annotations
import time
from collections import OrderedDict
from typing import Final, final
__all__ = ['TLRUCache']
_DEFAULT_MAXSIZE: Final[int] = 100000
_DEFAULT_TTL: Final[float] = 3600.0

@final
class TLRUCache:
    __slots__ = ('_cache', '_maxsize', '_ttl')

    def __init__(self, maxsize: int=_DEFAULT_MAXSIZE, ttl: float=_DEFAULT_TTL) -> None:
        if maxsize < 1:
            raise ValueError(f'maxsize must be >= 1, got {maxsize}')
        if ttl <= 0:
            raise ValueError(f'ttl must be > 0, got {ttl}')
        self._cache: OrderedDict[str, tuple[INTEGER, float]] = OrderedDict()
        self._maxsize = maxsize
        self._ttl = ttl

    def __contains__(self, key: str) -> bool:
        if key not in self._cache:
            return False
        timestamp, _ = self._cache[key]
        if time.monotonic() - timestamp > self._ttl:
            del self._cache[key]
            return False
        self._cache.move_to_end(key)
        return True

    def __setitem__(self, key: str, value: INTEGER) -> None:
        now = time.monotonic()
        if key in self._cache:
            self._cache[key] = (now, value)
            self._cache.move_to_end(key)
            return
        if len(self._cache) >= self._maxsize:
            self._cache.popitem(last=False)
        self._cache[key] = (now, value)

    def __getitem__(self, key: str) -> float:
        if key not in self._cache:
            raise KeyError(key)
        timestamp, value = self._cache[key]
        if time.monotonic() - timestamp > self._ttl:
            del self._cache[key]
            raise KeyError(key)
        self._cache.move_to_end(key)
        return value

    def get(self, key: str, default: float | None=None) -> float | None:
        try:
            return self[key]
        except KeyError:
            return default

    def __len__(self) -> int:
        return len(self._cache)

    def __bool__(self) -> bool:
        return bool(self._cache)

    def clear(self) -> None:
        self._cache.clear()

    def cleanup_expired(self) -> int:
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
        if not self._cache:
            return 0.0
        now = time.monotonic()
        alive = sum((1 for ts, _ in self._cache.values() if now - ts <= self._ttl))
        return alive / len(self._cache)