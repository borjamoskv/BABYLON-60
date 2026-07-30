# [C5-REAL] Exergy-Maximized
"""Graph Crypto module for tenant-isolated deterministic encryption."""

import hashlib
import json
import os

from babylon60.crypto.vault import Vault
from babylon60.utils.base60 import bytes_to_base60


def get_blind_name(name: str, tenant_id: str) -> str:
    """Generate a deterministic blind index for graph nodes."""
    if tenant_id == "default":
        return name
    vault_key = os.environ.get("CORTEX_VAULT_KEY", "")
    salt = f"{tenant_id}:{vault_key}".encode()
    return "hmac:" + bytes_to_base60(hashlib.sha256(salt + name.encode("utf-8")).digest())


def encrypt_node_meta(name: str, tenant_id: str) -> str:
    """Encrypt the node's real name using AES-GCM."""
    if tenant_id == "default":
        return "{}"
    vault = Vault()
    if not vault.is_available:
        raise RuntimeError(f"Vault unavailable but tenant {tenant_id} requires encryption")
    return json.dumps({"_enc_name": vault.encrypt(name, context_hash=tenant_id)})


def decrypt_node_name(meta_str: str, fallback_name: str, tenant_id: str = "default") -> str:
    """Decrypt the node's real name from its metadata."""
    if not meta_str or meta_str == "{}" or meta_str == '{"_enc_name": null}':
        return fallback_name
    try:
        meta = json.loads(meta_str)
        if "_enc_name" in meta and meta["_enc_name"]:
            vault = Vault()
            if not vault.is_available:
                raise RuntimeError("Vault required to decrypt graph node")
            return vault.decrypt(meta["_enc_name"], context_hash=tenant_id)
    except Exception:  # noqa: BLE001
        pass
    return fallback_name
