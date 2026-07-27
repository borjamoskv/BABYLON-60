# [C5-REAL] Exergy-Maximized
"""
Cryptographic Security.

Crypto Agility Layer:
  - hash_registry: Centralized hashing (SHA-256 default, PQC-ready)
  - provider: Hash/Signature/KDF/Random providers
  - aes: AES-256-GCM encryption
  - keys: Ed25519 key management
  - vault: Encrypted storage
"""

from .aes import CortexEncrypter, get_default_encrypter
from .hash_registry import (
    HashAlgorithm,
    cortex_hash,
    cortex_hash_raw,
    cortex_hash_truncated,
    cortex_hmac,
)
from .hash_registry import (
    configure as configure_hash,
)
from .vault import Vault


def get_master_key() -> bytes | None:
    """Lazily resolve the master-key loader to avoid hard import coupling."""
    from .keyring import get_master_key as _get_master_key

    return _get_master_key()


def generate_and_store_master_key() -> str:
    """Lazily resolve key generation so `cortex.crypto` imports stay portable."""
    from .keyring import generate_and_store_master_key as _generate_and_store_master_key

    return _generate_and_store_master_key()


__all__ = [
    "CortexEncrypter",
    "HashAlgorithm",
    "RFC3161Client",
    "Vault",
    "configure_hash",
    "cortex_hash",
    "cortex_hash_raw",
    "cortex_hash_truncated",
    "cortex_hmac",
    "generate_and_store_master_key",
    "get_default_encrypter",
    "get_master_key",
]

from .rfc3161 import RFC3161Client
