import os
import hashlib
import sqlite3
from datetime import datetime, timezone


# [C5-REAL] BFT LEDGER HELPER — EAFP pattern, zero DDL in hot path
# SQLite is the sole source of truth. No process-local cache, no locks.

_DDL_ANCHORS = """
    CREATE TABLE IF NOT EXISTS anchors
    (hash TEXT PRIMARY KEY,
     prev_hash TEXT UNIQUE,
     content TEXT,
     timestamp TEXT,
     agent_id TEXT)
"""

_INSERT_SQL = (
    "INSERT INTO anchors (hash, prev_hash, content, timestamp, agent_id) "
    "VALUES (?, ?, ?, ?, ?)"
)


def resolve_db_path(raw_path: str) -> str:
    """Expands environment variables like $CORTEX_ROOT and creates parent folders."""
    expanded = os.path.expandvars(raw_path)
    dir_name = os.path.dirname(expanded)
    if dir_name:
        os.makedirs(dir_name, exist_ok=True)
    return expanded


def ensure_bft_table(conn: sqlite3.Connection) -> None:
    """Boot path only. Pure CREATE — never DROP, never destructive migration."""
    conn.execute(_DDL_ANCHORS)


def append_anchor(db_file_raw: str, content: str, agent_id: str) -> str:
    """Centralized method for writing to the daemons' anchors hash chain.
    
    EAFP: INSERT first (hot path, zero DDL). On 'no such table',
    create schema and retry (cold path, first call only).
    """
    db_file = resolve_db_path(db_file_raw)
    conn = sqlite3.connect(db_file, timeout=5.0)
    try:
        conn.execute("PRAGMA journal_mode=WAL;")
        conn.execute("PRAGMA synchronous=NORMAL;")
        conn.execute("PRAGMA busy_timeout=5000;")

        # Resolve prev_hash (EAFP: table might not exist yet)
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT hash FROM anchors ORDER BY timestamp DESC LIMIT 1")
            row = cursor.fetchone()
            prev_hash = row[0] if row else "GENESIS_V2"
        except sqlite3.OperationalError:
            prev_hash = "GENESIS_V2"

        ts = datetime.now(timezone.utc).isoformat()
        new_hash = hashlib.sha3_256((content + prev_hash).encode('utf-8')).hexdigest()
        params = (new_hash, prev_hash, content, ts, agent_id)

        # Hot path: pure INSERT, zero DDL
        try:
            conn.execute(_INSERT_SQL, params)
        except sqlite3.OperationalError as e:
            if "no such table" not in str(e).lower():
                raise  # schema drift, lock, corruption → propagate
            conn.execute(_DDL_ANCHORS)  # cold branch: table absent
            conn.execute(_INSERT_SQL, params)

        conn.commit()
    finally:
        conn.close()
    return new_hash
