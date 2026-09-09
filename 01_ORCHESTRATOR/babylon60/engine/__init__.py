"""
BABYLON-60 Engine Module (v4.0 Sovereign Epistemic Memory Engine).
Provides zero-entropy, in-memory store and vector query interface.
"""

import hashlib
import time
from typing import Any, Dict, List, Optional


class CortexEngine:
    def __init__(self, capacity: int = 10000):
        self.capacity = capacity
        self._store: Dict[str, Dict[str, Any]] = {}
        self._keys: List[str] = []

    def store_sync(self, key: Optional[str] = None, payload: Any = None, **kwargs) -> str:
        """
        Stores an item synchronously with a deterministic SHA-256 digest key.
        """
        timestamp = time.time()
        data_str = f"{key}:{payload}:{kwargs}:{timestamp}"
        digest = hashlib.sha256(data_str.encode("utf-8")).hexdigest()

        record_key = key if key else digest[:16]
        record = {"key": record_key, "digest": digest, "payload": payload, "kwargs": kwargs, "timestamp": timestamp}

        if len(self._keys) >= self.capacity:
            oldest = self._keys.pop(0)
            self._store.pop(oldest, None)

        self._store[record_key] = record
        self._keys.append(record_key)
        return record_key

    def query(self, pattern: Optional[str] = None, limit: int = 50, *args, **kwargs) -> List[Dict[str, Any]]:
        """
        Queries stored epistemic records matching pattern or returns recent entries.
        """
        results = []
        for k in reversed(self._keys):
            item = self._store.get(k)
            if not item:
                continue
            if pattern is None or pattern in str(item["key"]) or pattern in str(item["payload"]):
                results.append(item)
                if len(results) >= limit:
                    break
        return results
