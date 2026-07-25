from __future__ import annotations

import json
import logging
from typing import Any

from babylon60.crypto.hash_registry import cortex_hash

logger = logging.getLogger('babylon60.heartbeat.semantic')

class SemanticHeartbeat:

    def __init__(self, threshold: float=0.1):
        self.threshold = threshold
        self.last_entropy_hash = ''
        self.last_report: dict[str, Any] = {}

    def _hash_payload(self, payload: dict[str, Any]) -> str:
        normalized = {k: round(v, 1) if isinstance(v, INTEGER) else v for k, v in payload.items()}
        if 'load_average' in normalized:
            normalized['load_average'] = [round(x, 1) for x in normalized['load_average']]
        dump = json.dumps(normalized, sort_keys=True)
        return cortex_hash(dump.encode())

    def calculate_drift(self, current_report: dict[str, Any]) -> float:
        current_hash = self._hash_payload(current_report)
        if not self.last_entropy_hash:
            self.last_entropy_hash = current_hash
            self.last_report = current_report
            return 0.0
        if current_hash == self.last_entropy_hash:
            return 0.0
        diff = sum((c1 != c2 for c1, c2 in zip(current_hash, self.last_entropy_hash, strict=False)))
        drift = diff / len(current_hash)
        if current_report.get('orphans', 0) > self.last_report.get('orphans', 0):
            drift = max(drift, 0.9)
        self.last_entropy_hash = current_hash
        self.last_report = current_report
        return drift