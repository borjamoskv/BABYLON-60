"""
BABYLON-60 Ergonomic API — Batch Merkle Accumulator (Sprints 2 & 4).
RFC-B60-2026-01-ADOPTION-ARCHITECTURE (Iceberg Pattern).

Accumulates event hashes in memory buffers and lazily computes balanced Merkle roots,
eliminating cryptographic bottlenecks on the critical execution path.
"""

from __future__ import annotations

import hashlib
import json
import threading
from typing import Any, List, Optional, Sequence, Tuple


def _canonical_json(data: Any) -> str:
    """Deterministic JSON serialization matching BABYLON-60 canonicalization."""
    return json.dumps(data, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False)


class BatchMerkleAccumulator:
    """
    High-performance in-memory accumulator for Merkle tree generation.

    Buffering strategy:
    - append operations (`add_leaf`, `add_event`) execute in sub-microsecond time (<0.01ms).
    - When `len(buffer) >= batch_size`, a batch Merkle root is computed and appended to batch roots.
    - On session close (`finalize`), all remaining buffer leaves are folded into the global root.
    """

    def __init__(self, batch_size: int = 100, algorithm: str = "sha256") -> None:
        if batch_size <= 0:
            batch_size = 100
        self.batch_size: int = batch_size
        self.algorithm: str = algorithm.lower()

        self._buffer: List[str] = []
        self._all_leaves: List[str] = []
        self._batch_roots: List[str] = []
        self._current_merkle_root: Optional[str] = None
        self._lock = threading.Lock()

    def _hash_bytes(self, data: bytes) -> str:
        if self.algorithm == "sha3_256":
            return hashlib.sha3_256(data).hexdigest()
        return hashlib.sha256(data).hexdigest()

    def add_leaf(self, leaf_hash: str) -> Optional[str]:
        """
        Appends a precomputed hash (64 hex characters) to the accumulator.
        If the buffer reaches `batch_size`, it flushes and returns the batch Merkle root.
        Otherwise, returns None.
        """
        cleaned_hash = str(leaf_hash).strip().lower()
        if not cleaned_hash:
            raise ValueError("Leaf hash cannot be empty.")

        with self._lock:
            self._buffer.append(cleaned_hash)
            self._all_leaves.append(cleaned_hash)

            if len(self._buffer) >= self.batch_size:
                return self._flush_locked()
            return None

    def add_event(self, data: Any) -> str:
        """
        Serializes and computes the SHA-256/SHA3-256 hash of arbitrary event data,
        adds it to the accumulator, and returns the computed leaf hash.
        """
        if isinstance(data, (dict, list)):
            serialized = _canonical_json(data).encode("utf-8")
        elif isinstance(data, bytes):
            serialized = data
        else:
            serialized = str(data).encode("utf-8")

        leaf_hash = self._hash_bytes(serialized)
        self.add_leaf(leaf_hash)
        return leaf_hash

    def _flush_locked(self) -> Optional[str]:
        if not self._buffer:
            return self._current_merkle_root

        batch_root = self.compute_merkle_root(self._buffer, algorithm=self.algorithm)
        self._batch_roots.append(batch_root)
        self._buffer.clear()
        self._current_merkle_root = batch_root
        return batch_root

    def flush(self) -> Optional[str]:
        """
        Flushes the current pending buffer, computes its batch Merkle root,
        and returns it.
        """
        with self._lock:
            return self._flush_locked()

    def finalize(self) -> str:
        """
        Closes the accumulator, flushing any pending buffer items and computing
        the final global Merkle root over all accumulated leaves.
        """
        with self._lock:
            if self._buffer:
                self._flush_locked()

            if not self._all_leaves:
                empty_root = self._hash_bytes(b"")
                self._current_merkle_root = empty_root
                return empty_root

            global_root = self.compute_merkle_root(self._all_leaves, algorithm=self.algorithm)
            self._current_merkle_root = global_root
            return global_root

    @classmethod
    def compute_merkle_root(cls, leaves: Sequence[str], algorithm: str = "sha256") -> str:
        """
        Deterministic, balanced binary Merkle root computation over a sequence of leaf hashes.
        Odd nodes are duplicated to the right to preserve tree balance.
        """
        algo = algorithm.lower()

        def _h(b: bytes) -> str:
            if algo == "sha3_256":
                return hashlib.sha3_256(b).hexdigest()
            return hashlib.sha256(b).hexdigest()

        if not leaves:
            return _h(b"")

        current = list(leaves)
        if len(current) == 1:
            return current[0]

        while len(current) > 1:
            next_level: List[str] = []
            for i in range(0, len(current), 2):
                left = current[i]
                right = current[i + 1] if i + 1 < len(current) else left
                combined = f"{left}:{right}".encode("utf-8")
                parent = _h(combined)
                next_level.append(parent)
            current = next_level

        return current[0]

    def get_inclusion_proof(self, index: int) -> List[Tuple[str, str]]:
        """
        Generates an O(log N) inclusion proof for the leaf at `index` across all accumulated leaves.
        Returns a list of tuples: (position: 'LEFT' | 'RIGHT', sibling_hash: str).
        """
        with self._lock:
            leaves = list(self._all_leaves)

        if index < 0 or index >= len(leaves):
            raise IndexError(f"Leaf index {index} out of range (total leaves: {len(leaves)})")

        proof: List[Tuple[str, str]] = []
        current = leaves
        curr_idx = index

        while len(current) > 1:
            is_odd = len(current) % 2 != 0
            if is_odd:
                current.append(current[-1])

            is_right_child = curr_idx % 2 == 1
            sibling_idx = curr_idx - 1 if is_right_child else curr_idx + 1
            sibling_pos = "LEFT" if is_right_child else "RIGHT"
            proof.append((sibling_pos, current[sibling_idx]))

            next_level: List[str] = []
            for i in range(0, len(current), 2):
                left = current[i]
                right = current[i + 1]
                combined = f"{left}:{right}".encode("utf-8")
                next_level.append(self._hash_bytes(combined))

            current = next_level
            curr_idx = curr_idx // 2

        return proof

    @classmethod
    def verify_inclusion_proof(
        cls,
        leaf: str,
        proof: Sequence[Tuple[str, str]],
        expected_root: str,
        algorithm: str = "sha256",
    ) -> bool:
        """
        Verifies that `leaf` is contained in the Merkle tree with `expected_root`
        using the provided `proof`.
        """
        algo = algorithm.lower()

        def _h(b: bytes) -> str:
            if algo == "sha3_256":
                return hashlib.sha3_256(b).hexdigest()
            return hashlib.sha256(b).hexdigest()

        curr = leaf
        for pos, sibling in proof:
            if pos == "LEFT":
                combined = f"{sibling}:{curr}".encode("utf-8")
            else:
                combined = f"{curr}:{sibling}".encode("utf-8")
            curr = _h(combined)

        return curr == expected_root

    @property
    def count(self) -> int:
        """Total number of leaves accumulated across all batches."""
        with self._lock:
            return len(self._all_leaves)

    @property
    def pending_count(self) -> int:
        """Number of leaves waiting in the current unflushed buffer."""
        with self._lock:
            return len(self._buffer)

    @property
    def batch_count(self) -> int:
        """Number of completed batch flushes."""
        with self._lock:
            return len(self._batch_roots)

    @property
    def current_root(self) -> str:
        """The most recently computed Merkle root or current global root."""
        with self._lock:
            if self._current_merkle_root is not None:
                return self._current_merkle_root
            if not self._all_leaves:
                return self._hash_bytes(b"")
            return self.compute_merkle_root(self._all_leaves, algorithm=self.algorithm)

    @property
    def leaves(self) -> List[str]:
        """Snapshot of all accumulated leaves."""
        with self._lock:
            return list(self._all_leaves)
