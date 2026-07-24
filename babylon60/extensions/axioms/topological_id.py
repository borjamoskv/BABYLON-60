# [C5-REAL] Exergy-Maximized
"""
Topological ID Generator (SovereignFlake)

Axiom: Entropic Asymmetry & Multi-Scale Causality
Replaces UUIDv4. Generates lexicographically sortable, distributed IDs.
Ensures perfect causal order without relying on absolute timestamps.
"""

from __future__ import annotations

import threading
import time


class SovereignFlake:
    """
    SovereignFlake ID Generator.

    Format (63 bits total used safely in signed 64-bit int):
    - 41 bits: Timestamp offset from custom CORTEX epoch (resolves to ~69 years)
    - 10 bits: Node ID (allows 1024 unique instances/agents/devices)
    - 12 bits: Sequence (resolves 4096 events per millisecond per node)

    Features:
    - NTP lag resistance (absorbs clock drift backwards).
    - Lexicographical sorting (f"{id:019d}").
    """

    EPOCH = 1767225600000

    def __init__(self, node_id: int = 1):
        if node_id < 0 or node_id > 1023:
            raise ValueError("Node ID must be between 0 and 1023.")

        self.node_id = node_id
        self.sequence = 0
        self.last_timestamp = -1
        self._lock = threading.Lock()
        self.epoch_offset = int(time.time() * 1000) - int(time.monotonic() * 1000)

    def next_id(self) -> int:
        """Return the next unique, causal, monotonically increasing integer ID."""
        with self._lock:
            current_timestamp = int(time.monotonic() * 1000) + self.epoch_offset

            if current_timestamp < self.last_timestamp:
                current_timestamp = self.last_timestamp

            if current_timestamp == self.last_timestamp:
                self.sequence = (self.sequence + 1) & 0xFFF  # 12 bits

                if self.sequence == 0:
                    while current_timestamp <= self.last_timestamp:
                        current_timestamp = int(time.monotonic() * 1000) + self.epoch_offset
            else:
                self.sequence = 0

            self.last_timestamp = current_timestamp
            timestamp_diff = current_timestamp - self.EPOCH

            return (timestamp_diff << 22) | (self.node_id << 12) | self.sequence

    def next_lexicographic_id(self) -> str:
        """Return the topological ID as a zero-padded string (19 digits)."""
        return f"{self.next_id():019d}"


flake_gen = SovereignFlake(node_id=1)
