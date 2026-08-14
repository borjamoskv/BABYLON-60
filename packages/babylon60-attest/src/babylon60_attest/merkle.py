# C5-REAL EXERGY CERTIFIED
"""
Merkle Tree primitives using SHA3-256.

Provides the foundational hash function and binary Merkle tree used by all
attestation and receipt modules. Zero external dependencies.

Invariant: identical input bytes ALWAYS produce identical Merkle roots
(deterministic, reproducible, auditable).
"""
from __future__ import annotations

import hashlib
from typing import List, Sequence

BLOCK_SIZE = 4096  # 4 KB per Merkle leaf


def sha3_256(data: bytes) -> str:
    """Compute SHA3-256 hex digest of raw bytes."""
    return hashlib.sha3_256(data).hexdigest()


def sha3_256_str(text: str) -> str:
    """Compute SHA3-256 hex digest of a UTF-8 string."""
    return sha3_256(text.encode("utf-8"))


class MerkleTree:
    """
    Binary Merkle tree over SHA3-256 leaf digests.

    Construction is eager: the tree is fully built on instantiation.
    The root is available as `self.root` immediately after creation.

    Example:
        >>> tree = MerkleTree.from_bytes(b"hello world", block_size=4096)
        >>> tree.root  # SHA3-256 Merkle root hex string
        '...'
    """

    __slots__ = ("leaves", "root", "depth")

    def __init__(self, leaves: Sequence[str]) -> None:
        if not leaves:
            self.leaves: List[str] = [sha3_256(b"")]
        else:
            self.leaves = list(leaves)
        self.root, self.depth = self._build(self.leaves)

    @classmethod
    def from_bytes(cls, data: bytes, block_size: int = BLOCK_SIZE) -> "MerkleTree":
        """Partition raw bytes into fixed-size blocks and build the tree."""
        if not data:
            return cls([sha3_256(b"")])
        blocks = [data[i : i + block_size] for i in range(0, len(data), block_size)]
        leaves = [sha3_256(block) for block in blocks]
        return cls(leaves)

    @classmethod
    def from_strings(cls, items: Sequence[str]) -> "MerkleTree":
        """Build tree from a sequence of UTF-8 strings (each becomes a leaf)."""
        leaves = [sha3_256_str(item) for item in items]
        return cls(leaves)

    @staticmethod
    def _build(nodes: List[str]) -> tuple[str, int]:
        depth = 0
        current = list(nodes)
        while len(current) > 1:
            next_level: List[str] = []
            for i in range(0, len(current), 2):
                left = current[i]
                right = current[i + 1] if i + 1 < len(current) else left
                combined = sha3_256((left + right).encode("ascii"))
                next_level.append(combined)
            current = next_level
            depth += 1
        return current[0], depth

    @property
    def leaf_count(self) -> int:
        return len(self.leaves)

    def __repr__(self) -> str:
        return f"MerkleTree(leaves={self.leaf_count}, depth={self.depth}, root={self.root[:16]}...)"
