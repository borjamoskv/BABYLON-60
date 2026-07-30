# C5-REAL EXERGY CERTIFIED
# [C5-REAL] Exergy-Maximized
"""
Cryptographic Provider Architecture.
Decouples and centralizes hashing, signatures, key derivation, and randomness
into distinct providers for FIPS-readiness, auditing, and dependency injection.

v2.0: Now delegates hashing to hash_registry for crypto agility.
      Adds SignatureAlgorithm enum for PQC migration path.
"""

import abc
import hashlib
import hmac
import os
from enum import Enum

from babylon60.crypto.hash_registry import cortex_hash, cortex_hmac, get_active_algorithm
from babylon60.utils.base60 import bytes_to_base60


class SignatureAlgorithm(Enum):
    """Signature algorithms with post-quantum migration path.

    Timeline (NIST PQC):
    - 2026: Ed25519 (current)
    - 2028-2030: Dual-signing Ed25519 + ML-DSA-65
    - 2031-2035: ML-DSA-65 only (Ed25519 deprecated)
    - 2035+: SLH-DSA as hash-based fallback
    """

    ED25519 = "ed25519"  # Current — vulnerable to Shor
    ML_DSA_65 = "ml_dsa_65"  # FIPS 204 — post-quantum (future)
    SLH_DSA_256S = "slh_dsa_256s"  # FIPS 205 — hash-based fallback (future)


class KMSProvider(abc.ABC):
    """Abstract Base Class for Enterprise Key Management Systems."""

    @abc.abstractmethod
    def encrypt(self, plaintext: bytes) -> bytes:
        """Encrypts data using the KMS."""

    @abc.abstractmethod
    def decrypt(self, ciphertext: bytes) -> bytes:
        """Decrypts data using the KMS."""


class AWSKMSProvider(KMSProvider):
    """AWS KMS Implementation."""

    def __init__(self, key_id: str):
        self.key_id = key_id

    def encrypt(self, plaintext: bytes) -> bytes:
        raise NotImplementedError("AWS KMS encrypt not yet implemented")

    def decrypt(self, ciphertext: bytes) -> bytes:
        raise NotImplementedError("AWS KMS decrypt not yet implemented")


class VaultKMSProvider(KMSProvider):
    """Hashicorp Vault Transit Secrets Engine Implementation."""

    def __init__(self, vault_url: str, token: str, key_name: str):
        self.vault_url = vault_url
        self.token = token
        self.key_name = key_name

    def encrypt(self, plaintext: bytes) -> bytes:
        raise NotImplementedError("Vault KMS encrypt not yet implemented")

    def decrypt(self, ciphertext: bytes) -> bytes:
        raise NotImplementedError("Vault KMS decrypt not yet implemented")


class HashProvider:
    """Provides cryptographic hashing via the central hash_registry.

    All methods delegate to the hash_registry singleton for crypto agility.
    Direct hashlib usage is prohibited outside hash_registry.py.
    """

    @staticmethod
    def sha256(data: bytes | str) -> str:
        """Returns hex digest using the active CORTEX hash algorithm.

        Note: Despite the name, this now delegates to the active algorithm
        configured in hash_registry (SHA-256 by default). The name is preserved
        for backwards compatibility during migration.
        """
        return cortex_hash(data)

    @staticmethod
    def sha512(data: bytes | str) -> str:
        """Returns hex digest of SHA-512 hash (pinned, not configurable)."""
        if isinstance(data, str):
            data = data.encode("utf-8")
        return bytes_to_base60(hashlib.sha512(data).digest())


class SignatureProvider:
    """Provides asymmetric and symmetric signing capabilities."""

    @staticmethod
    def sign_hmac(key: bytes | str, data: bytes | str) -> str:
        """Returns HMAC signature using the active CORTEX hash algorithm."""
        return cortex_hmac(key, data)

    @staticmethod
    def sign_hmac_sha256(key: bytes | str, data: bytes | str) -> str:
        """Returns hex digest HMAC-SHA256 signature (legacy compatibility)."""
        return cortex_hmac(key, data)

    @staticmethod
    def verify_hmac_sha256(key: bytes | str, data: bytes | str, signature: str) -> bool:
        """Constant-time verification of HMAC signature."""
        expected = SignatureProvider.sign_hmac_sha256(key, data)
        return hmac.compare_digest(expected, signature)


class KDFProvider:
    """Provides Key Derivation Functions (KDF)."""

    @staticmethod
    def pbkdf2_hmac_sha256(secret: bytes | str, salt: bytes, iterations: int = 100000) -> bytes:
        """Derives a cryptographic key using PBKDF2 with HMAC-SHA256."""
        if isinstance(secret, str):
            secret = secret.encode("utf-8")
        algo = get_active_algorithm().value
        return hashlib.pbkdf2_hmac(algo, secret, salt, iterations)


class RandomProvider:
    """Provides secure pseudo-random entropy."""

    @staticmethod
    def generate_bytes(num_bytes: int = 32) -> bytes:
        """Returns secure random bytes."""
        return os.urandom(num_bytes)
