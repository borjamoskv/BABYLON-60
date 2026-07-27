# [C5-REAL] Exergy-Maximized — Stress Test Shared Fixtures
# Author: borjamoskv
"""Shared pytest fixtures for the BABYLON-60 stress test suite."""

from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT))

os.environ.setdefault("CORTEX_DB_PATH", str(ROOT / ".cortex_test"))


@pytest.fixture
def stress_db(tmp_path: Path):
    """Creates a temporary WAL-mode SQLite database via CortexConnection factory."""
    from babylon60.database.core import causal_write, connect

    db_path = str(tmp_path / "stress_fixture.db")
    conn = connect(db_path)
    with causal_write(conn):
        conn.execute("CREATE TABLE fixture_data (id INTEGER PRIMARY KEY, val TEXT)")
        for i in range(100):
            conn.execute("INSERT INTO fixture_data (val) VALUES (?)", (f"seed-{i}",))
        conn.commit()
    yield db_path, conn
    conn.close()


@pytest.fixture
def ed25519_key():
    """Generates an ephemeral Ed25519 key pair for taint token testing."""
    import base64

    from cryptography.hazmat.primitives import serialization
    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

    private_key = Ed25519PrivateKey.generate()
    private_key_b64 = base64.b64encode(
        private_key.private_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PrivateFormat.Raw,
            encryption_algorithm=serialization.NoEncryption(),
        )
    ).decode()
    public_key = private_key.public_key()
    public_key_b64 = base64.b64encode(
        public_key.public_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PublicFormat.Raw,
        )
    ).decode()
    return private_key_b64, public_key_b64


@pytest.fixture
def runtime_db_path():
    """Returns the runtime.db path, skipping if not found."""
    db_path = os.path.expanduser("~/.cortex/runtime.db")
    if not Path(db_path).exists():
        pytest.skip("runtime.db not found")
    return db_path
