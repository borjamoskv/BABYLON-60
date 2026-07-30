# [C5-REAL] Exergy-Maximized
"""
Tests for KDF-0 Invariant in OS Keychain (Argon2id Key Wrapping).
"""

import os
import pytest
import base64
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.argon2 import Argon2id

from babylon60.crypto.keyring import (
    _wrap_key,
    _unwrap_key,
    get_master_key,
    generate_and_store_master_key,
    _AES_KEY_LENGTH,
    _SALT_LENGTH,
    _NONCE_LENGTH,
)


def test_wrap_and_unwrap_deterministic():
    """Ensure Argon2id wrapped key can be successfully unwrapped with correct passphrase."""
    raw_key = os.urandom(_AES_KEY_LENGTH)
    passphrase = b"super_secure_cortex_passphrase_for_testing"

    wrapped_b64 = _wrap_key(raw_key, passphrase)
    assert isinstance(wrapped_b64, str)
    assert wrapped_b64.startswith("dj") or "v1" in base64.b64decode(wrapped_b64).decode(
        "utf-8", errors="ignore"
    )

    unwrapped = _unwrap_key(wrapped_b64, passphrase)
    assert unwrapped == raw_key


def test_unwrap_fails_with_wrong_passphrase():
    """Ensure Argon2id wrapped key fails to unwrap with wrong passphrase."""
    raw_key = os.urandom(_AES_KEY_LENGTH)
    passphrase = b"correct_passphrase"
    wrong_passphrase = b"incorrect_passphrase"

    wrapped_b64 = _wrap_key(raw_key, passphrase)

    with pytest.raises(ValueError, match="KDF-0 Violation"):
        _unwrap_key(wrapped_b64, wrong_passphrase)


def test_legacy_migration_on_the_fly():
    """Ensure legacy plaintext base64 keys are automatically migrated to wrapped format."""
    raw_key = os.urandom(_AES_KEY_LENGTH)
    legacy_b64 = base64.b64encode(raw_key).decode("utf-8")
    passphrase = b"migration_passphrase"

    # Should detect 32-byte raw length, wrap it, and return the raw key
    unwrapped = _unwrap_key(legacy_b64, passphrase)
    assert unwrapped == raw_key


def test_unwrap_corrupted_payload():
    """Ensure corrupted payloads are rejected."""
    raw_key = os.urandom(_AES_KEY_LENGTH)
    passphrase = b"correct_passphrase"
    wrapped_b64 = _wrap_key(raw_key, passphrase)

    blob = base64.b64decode(wrapped_b64)
    # Corrupt the ciphertext by flipping a bit
    corrupted_blob = blob[:-1] + bytes([blob[-1] ^ 0x01])
    corrupted_b64 = base64.b64encode(corrupted_blob).decode("utf-8")

    with pytest.raises(ValueError, match="KDF-0 Violation"):
        _unwrap_key(corrupted_b64, passphrase)


@pytest.fixture
def mock_env(monkeypatch):
    monkeypatch.setenv("CORTEX_TESTING", "1")
    monkeypatch.setenv("CORTEX_KDF_PASSPHRASE", "test_passphrase")


def test_generate_and_store_master_key(mock_env):
    """Test generating and storing creates a wrapped key."""
    wrapped_b64 = generate_and_store_master_key()
    assert wrapped_b64 is not None

    # Try unwrapping the generated key
    unwrapped = _unwrap_key(wrapped_b64, b"test_passphrase")
    assert unwrapped is not None
    assert len(unwrapped) == _AES_KEY_LENGTH
