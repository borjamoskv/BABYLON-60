# [C5-REAL] Exergy-Maximized
import logging
import sqlite3

logger = logging.getLogger(__name__)


def _migration_030_identity_phase3(conn: sqlite3.Connection) -> None:
    """
    Ignition Phase 3: Persistent Identity + Accumulative State Root.
    Implements L0 Sovereign Identity anchor and Merkle/Hash Chain hybrid accumulator.
    """
    logger.info("Executing Migration 030: Phase 3 Ignition (Identity + State Root)")

    # 1. Identity Anchor
    conn.execute("""
        CREATE TABLE IF NOT EXISTS identity_anchor (
            node_id       TEXT PRIMARY KEY,
            pubkey_ed25519 BLOB NOT NULL,
            created_at_lamport INTEGER NOT NULL,
            self_signature BLOB NOT NULL,
            CHECK (length(pubkey_ed25519) = 32),
            CHECK (length(self_signature) = 64)
        ) STRICT;
    """)
    logger.info("Crystallized identity_anchor table.")

    # 2. State Root Accumulator (Merkle + Hash Chain)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS state_root (
            lamport      INTEGER PRIMARY KEY,
            event_hash   BLOB NOT NULL,
            root         BLOB NOT NULL,            -- acumulativo
            signature    BLOB NOT NULL             -- Ed25519(root) por node_id
        ) STRICT;
    """)
    logger.info("Crystallized state_root table.")

    # 3. Lamport Clock
    conn.execute("""
        CREATE TABLE IF NOT EXISTS lamport_clock (
            id INTEGER PRIMARY KEY CHECK (id = 1),
            tick INTEGER NOT NULL DEFAULT 0
        ) STRICT;
    """)
    conn.execute("INSERT OR IGNORE INTO lamport_clock (id, tick) VALUES (1, 0);")
    logger.info("Initialized lamport_clock.")
