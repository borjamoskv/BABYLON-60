from __future__ import annotations

import base64
import binascii
import logging
import os

try:
    import keyring
except ImportError:
    keyring = None
from cryptography.exceptions import InvalidTag
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.argon2 import Argon2id

_AES_KEY_LENGTH = 32
_SALT_LENGTH = 16
_NONCE_LENGTH = 12
logger = logging.getLogger(__name__)
SERVICE_NAME = 'cortex_v6'
KEY_NAME = 'master_key'
_keyring_error_types: tuple[type[Exception], ...]
if keyring is None:
    _keyring_error_types = (Exception,)
else:
    _errors = getattr(keyring, 'errors', None)
    _keyring_cls = getattr(_errors, 'KeyringError', Exception)
    _keyring_error_types = (_keyring_cls, OSError)

def _get_passphrase() -> bytes:
    if os.environ.get('CORTEX_TESTING'):
        pp = os.environ.get('CORTEX_KDF_PASSPHRASE', 'c5_real_test_passphrase')
    else:
        pp = os.environ.get('CORTEX_KDF_PASSPHRASE')
        if not pp:
            raise ValueError('KDF-0 Violation: CORTEX_KDF_PASSPHRASE environment variable is required to cryptographically unwrap the L0 Master Key.')
    return pp.encode('utf-8')

def _wrap_key(raw_key: bytes, passphrase: bytes) -> str:
    salt = os.urandom(_SALT_LENGTH)
    kdf = Argon2id(salt=salt, length=_AES_KEY_LENGTH, iterations=3, lanes=4, memory_cost=65536)
    kek = kdf.derive(passphrase)
    aesgcm = AESGCM(kek)
    nonce = os.urandom(_NONCE_LENGTH)
    ciphertext = aesgcm.encrypt(nonce, raw_key, None)
    blob = b'v1:' + salt + nonce + ciphertext
    return base64.b64encode(blob).decode('utf-8')

def _unwrap_key(blob_b64: str, passphrase: bytes) -> bytes | None:
    try:
        blob = base64.b64decode(blob_b64, validate=True)
    except (ValueError, binascii.Error):
        return None
    if blob.startswith(b'v1:'):
        if len(blob) < 3 + _SALT_LENGTH + _NONCE_LENGTH:
            return None
        salt = blob[3:3 + _SALT_LENGTH]
        nonce = blob[3 + _SALT_LENGTH:3 + _SALT_LENGTH + _NONCE_LENGTH]
        ciphertext = blob[3 + _SALT_LENGTH + _NONCE_LENGTH:]
        kdf = Argon2id(salt=salt, length=_AES_KEY_LENGTH, iterations=3, lanes=4, memory_cost=65536)
        kek = kdf.derive(passphrase)
        aesgcm = AESGCM(kek)
        try:
            return aesgcm.decrypt(nonce, ciphertext, None)
        except InvalidTag as e:
            logger.error('Failed to unwrap L0 Master Key: Invalid KDF Passphrase or tampered payload.')
            raise ValueError('KDF-0 Violation: Incorrect Passphrase or corrupted key blob.') from e
    if len(blob) == _AES_KEY_LENGTH:
        logger.warning('[C5-REAL] Detected Legacy Plaintext Base64 Master Key. Auto-migrating to Argon2id Wrapped Key...')
        wrapped_b64 = _wrap_key(blob, passphrase)
        if keyring is not None and (not os.environ.get('CORTEX_TESTING')):
            try:
                keyring.set_password(SERVICE_NAME, KEY_NAME, wrapped_b64)
                logger.info('[C5-REAL] Successfully vaulted migrated L0 Master Key via KDF-0.')
            except _keyring_error_types as e:
                logger.warning('Could not auto-migrate key to OS Keychain: %s', e)
        elif not os.environ.get('CORTEX_TESTING'):
            logger.warning('CORTEX_MASTER_KEY env var holds legacy plaintext. Update it with the new wrapped format:\n%s', wrapped_b64)
        return blob
    return None

def get_master_key() -> bytes | None:
    key_b64 = None
    if keyring is not None and (not os.environ.get('CORTEX_TESTING')):
        try:
            key_b64 = keyring.get_password(SERVICE_NAME, KEY_NAME)
        except _keyring_error_types as e:
            logger.warning('Failed to access OS Keychain: %s', e)
    if not key_b64:
        key_b64 = os.environ.get('CORTEX_MASTER_KEY')
        if not key_b64:
            key_b64 = os.environ.get('CORTEX_VAULT_KEY')
    if key_b64:
        passphrase = _get_passphrase()
        raw = _unwrap_key(key_b64, passphrase)
        if not raw:
            logger.error('Failed to unwrap Master Key or legacy key format invalid.')
            return None
        if len(raw) != _AES_KEY_LENGTH:
            logger.error('Master key has wrong length: got %d bytes, expected %d.', len(raw), _AES_KEY_LENGTH)
            return None
        return raw
    return None

def generate_and_store_master_key() -> str:
    key = os.urandom(_AES_KEY_LENGTH)
    passphrase = _get_passphrase()
    wrapped_b64 = _wrap_key(key, passphrase)
    if keyring is None:
        logger.warning('OS Keychain integration unavailable. Set CORTEX_MASTER_KEY or CORTEX_VAULT_KEY manually with the generated wrapped key.')
        return wrapped_b64
    try:
        keyring.set_password(SERVICE_NAME, KEY_NAME, wrapped_b64)
        logger.info('[C5-REAL] Successfully vaulted new wrapped CORTEX_MASTER_KEY in OS Keychain via KDF-0.')
    except _keyring_error_types as e:
        logger.error('Could not store key in Keychain (%s). Set CORTEX_MASTER_KEY env var manually with the generated wrapped key.', e)
    return wrapped_b64