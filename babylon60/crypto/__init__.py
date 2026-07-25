from .aes import CortexEncrypter, get_default_encrypter
from .hash_registry import HashAlgorithm, cortex_hash, cortex_hash_raw, cortex_hash_truncated, cortex_hmac
from .hash_registry import configure as configure_hash
from .vault import Vault


def get_master_key() -> bytes | None:
    from .keyring import get_master_key as _get_master_key

    return _get_master_key()


def generate_and_store_master_key() -> str:
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
