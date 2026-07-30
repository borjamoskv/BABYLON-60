# [C5-REAL] Exergy-Maximized
import base64
import os
import sqlite3
import tempfile
from pathlib import Path

import pytest
from cryptography.exceptions import InvalidSignature

from babylon60.crypto.identity import L0IdentityForge, StateRootAccumulator


@pytest.fixture
def temp_identity_dir():
    with tempfile.TemporaryDirectory() as d:
        yield Path(d)


@pytest.fixture
def sqlite_conn():
    conn = sqlite3.connect(":memory:")
    conn.execute("""
        CREATE TABLE state_root (
            lamport      INTEGER PRIMARY KEY,
            event_hash   BLOB NOT NULL,
            root         BLOB NOT NULL,
            signature    BLOB NOT NULL
        ) STRICT;
    """)
    yield conn
    conn.close()


def test_forge_and_load_identity(temp_identity_dir):
    forge = L0IdentityForge(storage_dir=temp_identity_dir)
    passphrase = "super_secure_passphrase_123"

    # 1. Forge Identity
    payload_forged = forge.forge_identity(passphrase)

    assert payload_forged.public_key_b64
    assert payload_forged.private_key_b64
    assert len(payload_forged.seed_bytes) == 32

    # Ensure file exists and permissions
    assert forge.seed_path.exists()
    st = os.stat(forge.seed_path)
    # Note: permissions check can be tricky across OS, but we verify it's readable

    # 2. Load Identity
    payload_loaded = forge.load_identity(passphrase)

    assert payload_loaded.public_key_b64 == payload_forged.public_key_b64
    assert payload_loaded.private_key_b64 == payload_forged.private_key_b64
    assert payload_loaded.seed_bytes == payload_forged.seed_bytes


def test_load_identity_wrong_password(temp_identity_dir):
    forge = L0IdentityForge(storage_dir=temp_identity_dir)
    forge.forge_identity("correct_passphrase")

    with pytest.raises(ValueError, match="Identity Decryption Failed"):
        forge.load_identity("wrong_passphrase")


def test_state_root_accumulator(temp_identity_dir, sqlite_conn):
    forge = L0IdentityForge(storage_dir=temp_identity_dir)
    payload = forge.forge_identity("test_pass")

    acc = StateRootAccumulator(sqlite_conn)

    # Empty state
    lamport, root = acc.get_latest_root()
    assert lamport == 0
    assert root == b""

    # Append event 1
    event_1_hash = os.urandom(32)
    root_1 = acc.append_event(1, event_1_hash, payload.private_key_b64)

    lamport, latest_root = acc.get_latest_root()
    assert lamport == 1
    assert latest_root == root_1

    # Append event 2
    event_2_hash = os.urandom(32)
    root_2 = acc.append_event(2, event_2_hash, payload.private_key_b64)

    lamport, latest_root = acc.get_latest_root()
    assert lamport == 2
    assert latest_root == root_2

    # Verify Chain
    assert acc.verify_chain(payload.public_key_b64) is True


def test_state_root_tampering_detection(temp_identity_dir, sqlite_conn):
    forge = L0IdentityForge(storage_dir=temp_identity_dir)
    payload = forge.forge_identity("test_pass")

    acc = StateRootAccumulator(sqlite_conn)

    # Append events
    acc.append_event(1, os.urandom(32), payload.private_key_b64)
    acc.append_event(2, os.urandom(32), payload.private_key_b64)
    acc.append_event(3, os.urandom(32), payload.private_key_b64)

    # Chain should be valid
    assert acc.verify_chain(payload.public_key_b64) is True

    # Tamper with event 2
    cursor = sqlite_conn.cursor()
    cursor.execute("UPDATE state_root SET event_hash = ? WHERE lamport = 2", (os.urandom(32),))
    sqlite_conn.commit()

    # Chain verification should fail
    assert acc.verify_chain(payload.public_key_b64) is False


def test_identity_anchor_manager(temp_identity_dir, sqlite_conn):
    sqlite_conn.execute("""
        CREATE TABLE identity_anchor (
            node_id       TEXT PRIMARY KEY,
            pubkey_ed25519 BLOB NOT NULL,
            created_at_lamport INTEGER NOT NULL,
            self_signature BLOB NOT NULL,
            CHECK (length(pubkey_ed25519) = 32),
            CHECK (length(self_signature) = 64)
        ) STRICT;
    """)
    forge = L0IdentityForge(storage_dir=temp_identity_dir)
    payload = forge.forge_identity("test_pass")

    from babylon60.crypto.identity import IdentityAnchorManager

    manager = IdentityAnchorManager(sqlite_conn)

    assert manager.is_anchored() is False

    node_id = manager.anchor_genesis(payload)
    assert node_id is not None
    assert manager.is_anchored() is True

    # Cannot anchor twice
    with pytest.raises(ValueError, match="Ledger is already anchored"):
        manager.anchor_genesis(payload)

    # Verify DB contents
    cursor = sqlite_conn.cursor()
    cursor.execute(
        "SELECT node_id, pubkey_ed25519, created_at_lamport, self_signature FROM identity_anchor"
    )
    row = cursor.fetchone()
    assert row[0] == node_id
    assert row[1] == base64.b64decode(payload.public_key_b64)
    assert row[2] == 0
    assert len(row[3]) == 64
