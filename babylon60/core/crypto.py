# [C5-REAL] Exergy-Maximized
from __future__ import annotations

import hashlib
from typing import Any, Dict

import cbor2
from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ed25519


def canonicalize_cbor(data: Dict[str, Any]) -> bytes:
    """
    Serialización canónica determinista usando CBOR.
    Las claves del diccionario se ordenan lexicográficamente para asegurar BFT.
    """
    return cbor2.dumps(data, canonical=True)


def hash_sha3_256(data: bytes) -> str:
    """
    Genera un hash SHA3-256 (no SHA-256) garantizando resistencia a ataques de extensión de longitud.
    """
    return hashlib.sha3_256(data).hexdigest()


class Ed25519Signer:
    """
    Firma criptográfica Ed25519 REAL.

    C5-REAL: cero firmas mock. Cada instancia posee material de clave verificable;
    `sign()` produce una firma Ed25519 auténtica y `verify()` cierra el ciclo de
    falsación contra la clave pública publicada en `key_id` / `public_key_hex`.
    """

    def __init__(self, private_key: ed25519.Ed25519PrivateKey | None = None) -> None:
        self._private_key = private_key or ed25519.Ed25519PrivateKey.generate()
        public_bytes = self._private_key.public_key().public_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PublicFormat.Raw,
        )
        self.public_key_hex: str = public_bytes.hex()
        self.key_id: str = f"did:key:ed25519:{self.public_key_hex[:16]}"

    def sign(self, payload_hash: str) -> str:
        signature = self._private_key.sign(payload_hash.encode("utf-8"))
        return f"ed25519:{signature.hex()}"

    def verify(self, payload_hash: str, signature: str) -> bool:
        if not signature.startswith("ed25519:"):
            return False
        try:
            raw = bytes.fromhex(signature.removeprefix("ed25519:"))
            public_key = ed25519.Ed25519PublicKey.from_public_bytes(
                bytes.fromhex(self.public_key_hex)
            )
            public_key.verify(raw, payload_hash.encode("utf-8"))
            return True
        except (InvalidSignature, ValueError):
            return False
