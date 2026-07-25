"""Shared fixtures for BABYLON-60 test suite."""

import pytest

from babylon60.crypto.keys import KeyManager


@pytest.fixture
def tmp_db_path(tmp_path):
    """Provide a temporary database path for SQLite."""
    db_file = tmp_path / "test_cortex.db"
    return str(db_file)


@pytest.fixture
def key_manager(tmp_path):
    """Provide an isolated KeyManager instance."""
    # Assuming KeyManager uses an isolated space if parameterized or mocked.
    # For now, just instantiating it.
    return KeyManager("test_shared_actor")


@pytest.fixture
def lexicon():
    """Provide a basic Lexicon representation."""
    return {"CORE_BFT_NODE": "0x01", "SYNC_PROTOCOL": "v1"}
