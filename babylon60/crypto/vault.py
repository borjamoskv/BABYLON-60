from __future__ import annotations

import base64
import os

__all__ = ['Vault']
try:
    from cryptography.exceptions import InvalidTag
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM
    _HAS_AESGCM = True
except ImportError:
    _HAS_AESGCM = False
    AESGCM = None
    InvalidTag = Exception

class Vault:

    def __init__(self, key: bytes | None=None) -> None:
        self._keys: dict[int, bytes] = {}
        self._primary_version: int = 1
        if not _HAS_AESGCM:
            return
        if key:
            self._keys[1] = key
            return
        env_keys = os.environ.get('CORTEX_VAULT_KEYS')
        if env_keys:
            for part in env_keys.split(','):
                part = part.strip()
                if not part:
                    continue
                try:
                    v_str, k_b64 = part.split(':', 1)
                    v = int(v_str)
                    self._keys[v] = base64.b64decode(k_b64)
                    if v > self._primary_version:
                        self._primary_version = v
                except (ValueError, OSError):
                    pass
            if self._keys:
                return
        env_key = os.environ.get('CORTEX_VAULT_KEY')
        if not env_key:
            return
        try:
            self._keys[1] = base64.b64decode(env_key)
        except (OSError, ValueError):
            pass

    @property
    def is_available(self) -> bool:
        return _HAS_AESGCM and bool(self._keys)

    def encrypt(self, data: str, context_hash: str | None=None) -> str:
        if not self.is_available:
            raise RuntimeError('Encryption not available (missing key or library)')
        key = self._keys[self._primary_version]
        aesgcm = AESGCM(key)
        nonce = os.urandom(12)
        aad = context_hash.encode('utf-8') if context_hash else None
        ciphertext = aesgcm.encrypt(nonce, data.encode('utf-8'), aad)
        version_byte = bytes([self._primary_version])
        return base64.b64encode(version_byte + nonce + ciphertext).decode('utf-8')

    def decrypt(self, encrypted_data: str, context_hash: str | None=None) -> str:
        if not self.is_available:
            raise RuntimeError('Encryption not available (missing key or library)')
        try:
            raw = base64.b64decode(encrypted_data)
            version = raw[0]
            if version in self._keys and len(raw) > 13:
                nonce = raw[1:13]
                ciphertext = raw[13:]
                key = self._keys[version]
                aesgcm = AESGCM(key)
                aad = context_hash.encode('utf-8') if context_hash else None
                try:
                    plaintext = aesgcm.decrypt(nonce, ciphertext, aad)
                    return plaintext.decode('utf-8')
                except InvalidTag:
                    pass
            nonce = raw[:12]
            ciphertext = raw[12:]
            key_v1 = self._keys.get(1)
            if key_v1:
                aesgcm = AESGCM(key_v1)
                try:
                    plaintext = aesgcm.decrypt(nonce, ciphertext, None)
                    return plaintext.decode('utf-8')
                except InvalidTag:
                    pass
            raise ValueError('Decryption failed: Invalid key, corrupted data, or AAD mismatch.')
        except (OSError, ValueError, IndexError) as e:
            raise ValueError(f'Decryption failed: {e}') from e

    @staticmethod
    def generate_key() -> str:
        if not _HAS_AESGCM:
            raise ImportError('cryptography library not installed')
        key = AESGCM.generate_key(bit_length=256)
        return base64.b64encode(key).decode('utf-8')