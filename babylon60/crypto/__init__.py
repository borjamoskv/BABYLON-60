from .aes import CortexEncrypter, get_default_encrypter
from .hash_registry import HashAlgorithm, cortex_hash, cortex_hash_raw, cortex_hash_truncated, cortex_hmac
from .hash_registry import configure as configure_hash
from .vault import Vault
from .zk_verifier import NULZKVerifier, ZKVerificationError, verify_nul_zk_proof, verify_zk_attestation


def get_master_key() -> bytes | None:
    from .keyring import get_master_key as _get_master_key

    return _get_master_key()


def generate_and_store_master_key() -> str:
    from .keyring import generate_and_store_master_key as _generate_and_store_master_key

    return _generate_and_store_master_key()


__all__ = [
    "CortexEncrypter",
    "HashAlgorithm",
    "NULZKVerifier",
    "RFC3161Client",
    "Vault",
    "ZKVerificationError",
    "configure_hash",
    "cortex_hash",
    "cortex_hash_raw",
    "cortex_hash_truncated",
    "cortex_hmac",
    "generate_and_store_master_key",
    "get_default_encrypter",
    "get_master_key",
    "verify_nul_zk_proof",
    "verify_zk_attestation",
]
# noqa: E402
from .rfc3161 import RFC3161Client

