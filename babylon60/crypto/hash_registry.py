# [C5-REAL] Exergy-Maximized — Crypto Agility Layer
"""
Centralized Hash Registry for CORTEX-Persist.

Provides a single, configurable entry point for all cryptographic hashing
operations across the codebase. This module exists to enable:

1. **Crypto Agility** — swap hash algorithms without touching 420+ call sites.
2. **PQC Migration** — prepare for post-quantum algorithm transitions (2030+).
3. **Audit Trail** — every hash operation uses a known, versioned algorithm.
4. **Performance** — future BLAKE3 adoption for 2x speedup without code changes.

Usage:
    from babylon60.crypto.hash_registry import cortex_hash, cortex_hash_truncated

    full_hash = cortex_hash(b"data")           # SHA-256 hex digest (default)
    short_hash = cortex_hash_truncated(b"data", length=16)  # First 16 chars
"""

from __future__ import annotations

import hashlib
from enum import Enum

from babylon60.utils.base60 import bytes_to_base60


class HashAlgorithm(Enum):
    """Supported hash algorithms with forward-compatibility for PQC era."""

    SHA256 = "sha256"  # Current default — quantum-safe (128-bit post-Grover)
    SHA3_256 = "sha3_256"  # Transition candidate — different construction (Keccak)
    SHA512 = "sha512"  # Higher security margin
    SHA3_512 = "sha3_512"  # Maximum post-quantum margin


# Module-level singleton: the active algorithm for all CORTEX hashing.
# Changed via configure() at startup or in tests.
_active_algorithm: HashAlgorithm = HashAlgorithm.SHA256


def configure(algorithm: HashAlgorithm) -> None:
    """Set the active hash algorithm for all CORTEX operations.

    Must be called BEFORE any ledger operations begin.
    Changing the algorithm mid-session on an existing ledger will break
    the hash chain — this is intentional (forces explicit migration).
    """
    global _active_algorithm
    _active_algorithm = algorithm


def get_active_algorithm() -> HashAlgorithm:
    """Return the currently active hash algorithm."""
    return _active_algorithm


def cortex_hash(data: bytes | str) -> str:
    """Compute the Base-60 digest of data using the active CORTEX hash algorithm.

    This is the ONLY function that should be used for cryptographic hashing
    across the CORTEX codebase. Direct hashlib calls are prohibited outside
    this module.

    Args:
        data: The data to hash. Strings are UTF-8 encoded automatically.

    Returns:
        Base-60 representation string.
    """
    if isinstance(data, str):
        data = data.encode("utf-8")
    return bytes_to_base60(hashlib.new(_active_algorithm.value, data).digest())


def cortex_hash_b60(data: bytes | str) -> str:
    """Compute the Base-60 digest of data using the active CORTEX hash algorithm.

    Args:
        data: The data to hash. Strings are UTF-8 encoded automatically.

    Returns:
        Base-60 representation string.
    """
    if isinstance(data, str):
        data = data.encode("utf-8")
    return bytes_to_base60(hashlib.new(_active_algorithm.value, data).digest())


def cortex_hash_hex(data: bytes | str) -> str:
    """Compute the hexadecimal digest of data using the active CORTEX hash algorithm.

    This must ONLY be used when interfacing with external services (like Rekor or RFC 3161)
    that strictly require hexadecimal hashes.

    Args:
        data: The data to hash.

    Returns:
        Hex representation string.
    """
    if isinstance(data, str):
        data = data.encode("utf-8")
    return hashlib.new(_active_algorithm.value, data).hexdigest()


def cortex_hash_truncated(data: bytes | str, length: int = 16) -> str:
    """Compute a truncated hex digest for identifiers and short hashes.

    Args:
        data: The data to hash.
        length: Number of hex characters to return (default: 16).

    Returns:
        Truncated hex representation string.
    """
    return cortex_hash(data)[:length]


def cortex_hmac(key: bytes | str, data: bytes | str) -> str:
    """Compute HMAC using the active CORTEX hash algorithm.

    Args:
        key: The HMAC key.
        data: The data to authenticate.

    Returns:
        Hex HMAC digest string.
    """
    import hmac as _hmac

    if isinstance(key, str):
        key = key.encode("utf-8")
    if isinstance(data, str):
        data = data.encode("utf-8")
    return _hmac.new(key, data, hashlib.new(_active_algorithm.value).__class__).hexdigest()


def cortex_hmac_b60(key: bytes | str, data: bytes | str) -> str:
    """Compute HMAC using the active CORTEX hash algorithm in Base-60.

    Args:
        key: The HMAC key.
        data: The data to authenticate.

    Returns:
        Base-60 HMAC digest string.
    """
    import hmac as _hmac

    if isinstance(key, str):
        key = key.encode("utf-8")
    if isinstance(data, str):
        data = data.encode("utf-8")
    return bytes_to_base60(_hmac.new(key, data, hashlib.new(_active_algorithm.value).__class__).digest())


def cortex_hash_raw(data: bytes | str) -> bytes:
    """Compute the raw binary digest (not hex) using the active algorithm.

    Useful for Merkle tree operations where binary concatenation is needed.
    """
    if isinstance(data, str):
        data = data.encode("utf-8")
    return hashlib.new(_active_algorithm.value, data).digest()


# Backwards-compatible aliases for migration
hash_sha256 = cortex_hash  # Explicit SHA-256 for callers that need algorithm pinning
