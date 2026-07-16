import os
import hashlib
import sqlite3
from datetime import datetime, timezone

# [C5-REAL] BFT LEDGER HELPER — STRICT ATOMICITY & DOMAIN SEPARATION
# P0: BEGIN IMMEDIATE explicit transactions prevent TOCTOU on read-head/insert.
# P0: Length-framing and full metadata inclusion in SHA3 prevents collisions and metadata tampering.
# P0: Strict Environment Variable expansion prevents phantom ledgers.
# P0: No blind OperationalError catching (prevents SQLITE_BUSY from resetting chain).
# P1: Fixed-length ISO timestamps guarantee lexicographic sort.

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
    """Expands environment variables. Fails hard if unresolved or relative."""
    expanded = os.path.expandvars(raw_path)
    if "$" in expanded or not os.path.isabs(expanded):
        raise RuntimeError(f"[C5-REAL] FATAL: Unresolved variable or relative path -> {expanded}")
    return expanded

def init_ledger(db_file_raw: str) -> None:
    """Explicitly provisions the ledger directory and schema. Never auto-creates in runtime."""
    db_file = resolve_db_path(db_file_raw)
    dir_name = os.path.dirname(db_file)
    if dir_name:
        os.makedirs(dir_name, exist_ok=True)
    
    conn = sqlite3.connect(db_file, timeout=5.0)
    try:
        conn.execute(_DDL_ANCHORS)
    finally:
        conn.close()


def ensure_bft_table(conn: sqlite3.Connection) -> None:
    """Boot path only. Pure CREATE — never DROP, never destructive migration."""
    conn.execute(_DDL_ANCHORS)


def append_anchor(db_file_raw: str, content: str, agent_id: str) -> str:
    """Centralized method for writing to the daemons' anchors hash chain."""
    db_file = resolve_db_path(db_file_raw)
    conn = sqlite3.connect(db_file, timeout=5.0)
    conn.isolation_level = None  # Autocommit disabled, manual transaction control
    
    try:
        conn.execute("PRAGMA journal_mode=WAL;")
        conn.execute("PRAGMA synchronous=NORMAL;")
        conn.execute("PRAGMA busy_timeout=5000;")

        while True:
            try:
                # 1. Acquire exclusive write lock upfront (Anti-TOCTOU)
                conn.execute("BEGIN IMMEDIATE")
                try:
                    cursor = conn.cursor()
                    # We rely on timestamp DESC, but strictly formatted, and protected by BEGIN IMMEDIATE
                    cursor.execute("SELECT hash FROM anchors ORDER BY timestamp DESC LIMIT 1")
                    row = cursor.fetchone()
                    prev_hash = row[0] if row else "GENESIS_V2"
                    
                    # 2. Fixed-length timestamp (Anti-Truncation P1)
                    ts = datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%S.%f') + 'Z'
                    
                    # 3. Domain Separation & Full Metadata Seal (Anti-Tampering P0)
                    sealed_payload = f"{len(content)}:{content}:{len(prev_hash)}:{prev_hash}:{len(ts)}:{ts}:{len(agent_id)}:{agent_id}"
                    new_hash = hashlib.sha3_256(sealed_payload.encode('utf-8')).hexdigest()
                    
                    # 4. Insert (Hot Path)
                    params = (new_hash, prev_hash, content, ts, agent_id)
                    conn.execute(_INSERT_SQL, params)
                    
                    conn.execute("COMMIT")
                    break  # Success, exit loop
                
                except Exception as inner_e:
                    conn.execute("ROLLBACK")
                    raise inner_e
                    
            except sqlite3.OperationalError as e:
                err_msg = str(e).lower()
                if "no such table" in err_msg:
                    raise RuntimeError("[C5-REAL] LedgerAbsentError: BFT Ledger table missing. Explicit initialization required.") from e
                else:
                    raise
    finally:
        conn.close()
        
    return new_hash
