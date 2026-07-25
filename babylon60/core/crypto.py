from __future__ import annotations

import hashlib
from typing import Any

import cbor2
from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ed25519


def _check_no_floats(data: Any) -> None:
    if isinstance(data, float):
        raise ValueError('Flotantes (float) están estrictamente prohibidos en el payload BFT (IEEE 754 no-determinismo).')
    elif isinstance(data, dict):
        for k, v in data.items():
            _check_no_floats(k)
            _check_no_floats(v)
    elif isinstance(data, (list, tuple, set, frozenset)):
        for v in data:
            _check_no_floats(v)

def canonicalize_cbor(data: dict[str, Any]) -> bytes:
    _check_no_floats(data)
    return cbor2.dumps(data, canonical=True)

def hash_sha3_256(data: bytes) -> str:
    return hashlib.sha3_256(data).hexdigest()

class Ed25519Signer:

    def __init__(self, private_key: ed25519.Ed25519PrivateKey | None=None) -> None:
        self._private_key = private_key or ed25519.Ed25519PrivateKey.generate()
        public_bytes = self._private_key.public_key().public_bytes(encoding=serialization.Encoding.Raw, format=serialization.PublicFormat.Raw)
        self.public_key_hex: str = public_bytes.hex()
        self.key_id: str = f'did:key:ed25519:{self.public_key_hex[:16]}'

    def sign(self, payload_hash: str) -> str:
        signature = self._private_key.sign(payload_hash.encode('utf-8'))
        return f'ed25519:{signature.hex()}'

    def verify(self, payload_hash: str, signature: str) -> bool:
        return verify_ed25519(self.public_key_hex, payload_hash, signature)

def verify_ed25519(public_key_hex: str, message: str, signature: str) -> bool:
    if not signature.startswith('ed25519:'):
        return False
    try:
        raw = bytes.fromhex(signature.removeprefix('ed25519:'))
        public_key = ed25519.Ed25519PublicKey.from_public_bytes(bytes.fromhex(public_key_hex))
        public_key.verify(raw, message.encode('utf-8'))
        return True
    except (InvalidSignature, ValueError):
        return False