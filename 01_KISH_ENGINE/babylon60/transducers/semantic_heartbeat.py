# ============================================================================
# BABYLON-60 v4.0 Sovereign Hardened
# █ AUTOCOGNITION-Ω | STATE: C5-REAL | AESTHETIC: INDUSTRIAL_NOIR_2026
# ============================================================================
# [Causal-Determinist] Exergy-Maximized
"""
Semantic Heartbeat - Metastatic Drift Analysis.

A true heartbeat monitor calculating the semantic asymmetry
between system health states.
"""

from __future__ import annotations

import json
import logging

from babylon60.crypto.hash_registry import cortex_hash

logger = logging.getLogger("babylon60.heartbeat.semantic")


class SemanticHeartbeat:
    """Calculates the metastate drift of system hygiene."""

    def __init__(self, threshold: float = 0.1) -> None:
        self.threshold = threshold
        self.last_entropy_hash = ""
        self.last_report: dict[str, object] = {}

    def _hash_payload(self, payload: dict[str, object]) -> str:
        """Serializes and hashes the health report."""
        normalized: dict[str, object] = {}
        for k, v in payload.items():
            if isinstance(v, float):
                normalized[k] = round(v, 1)
            elif k == "load_average" and isinstance(v, (list, tuple)):
                normalized[k] = [round(float(x), 1) for x in v]
            else:
                normalized[k] = v

        dump = json.dumps(normalized, sort_keys=True)
        return str(cortex_hash(dump.encode()))

    def calculate_drift(self, current_report: dict[str, object]) -> float:
        """
        Calculates the semantic drift (asymmetry) between states.

        Returns a float [0.0, 1.0].
        """
        current_hash = self._hash_payload(current_report)
        if not self.last_entropy_hash:
            self.last_entropy_hash = current_hash
            self.last_report = current_report
            return 0.0

        if current_hash == self.last_entropy_hash:
            return 0.0

        # Simple Hamming distance between hashes as proxy for asymmetry
        diff = sum(c1 != c2 for c1, c2 in zip(current_hash, self.last_entropy_hash, strict=False))
        drift = diff / len(current_hash)

        # High-weight semantic triggers: if orphans appeared, bypass hash and spike drift
        curr_orphans = current_report.get("orphans", 0)
        last_orphans = self.last_report.get("orphans", 0)
        c_orphans = int(curr_orphans) if isinstance(curr_orphans, (int, float)) else 0
        l_orphans = int(last_orphans) if isinstance(last_orphans, (int, float)) else 0
        if c_orphans > l_orphans:
            drift = max(drift, 0.9)  # CRITICAL DRIFT

        self.last_entropy_hash = current_hash
        self.last_report = current_report
        return drift
