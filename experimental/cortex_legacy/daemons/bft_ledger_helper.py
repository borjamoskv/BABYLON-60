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





def append_anchor(db_file_raw: str, content: str, agent_id: str) -> str:
    """Centralized method for writing to the daemons' anchors hash chain."""
    db_file = resolve_db_path(db_file_raw)
    conn = sqlite3.connect(db_file, timeout=5.0)
    conn.isolation_level = None  # Autocommit disabled, manual transaction control
    
    try:
        conn.execute("PRAGMA journal_mode=WAL;")
        conn.execute("PRAGMA synchronous=NORMAL;")
        conn.execute("PRAGMA busy_timeout=5000;")

        try:
            # 1. Acquire exclusive write lock upfront (Anti-TOCTOU)
            conn.execute("BEGIN IMMEDIATE")
            try:
                cursor = conn.cursor()
                # [Fable 5 Fix] True Chain-Leaf topology + Tiebreaker to prevent clock-skew stuck ledgers
                cursor.execute("SELECT hash FROM anchors WHERE hash NOT IN (SELECT prev_hash FROM anchors WHERE prev_hash IS NOT NULL) ORDER BY timestamp DESC, rowid DESC LIMIT 1")
                row = cursor.fetchone()
                prev_hash = row[0] if row else "GENESIS_V2"
                
                # 2. Fixed-length timestamp (Anti-Truncation P1)
                ts = datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%S.%f') + 'Z'
                
                # [Fable 5 Fix] Byte-length framing to prevent multi-byte char boundary attacks
                c_bytes, p_bytes, t_bytes, a_bytes = content.encode('utf-8'), prev_hash.encode('utf-8'), ts.encode('utf-8'), agent_id.encode('utf-8')
                sealed_payload = f"{len(c_bytes)}:{content}:{len(p_bytes)}:{prev_hash}:{len(t_bytes)}:{ts}:{len(a_bytes)}:{agent_id}".encode('utf-8')
                
                # [Fable 5 Fix] HMAC-SHA3 with local key for adversarial rewrite prevention
                hmac_key = os.environ.get("CORTEX_BFT_HMAC_KEY", "C5-REAL-LOCAL-ANCHOR-KEY").encode('utf-8')
                import hmac
                new_hash = hmac.new(hmac_key, sealed_payload, hashlib.sha3_256).hexdigest()
                
                # 4. Insert (Hot Path)
                params = (new_hash, prev_hash, content, ts, agent_id)
                conn.execute(_INSERT_SQL, params)
                
                conn.execute("COMMIT")
            
            except Exception as inner_e:
                try:
                    conn.execute("ROLLBACK")
                except sqlite3.OperationalError:
                    pass
                raise RuntimeError("[C5-REAL] Transaction Failed") from inner_e
                
        except sqlite3.OperationalError as e:
            err_msg = str(e).lower()
            if "no such table" in err_msg:
                raise RuntimeError("[C5-REAL] LedgerAbsentError: BFT Ledger table missing. Explicit initialization required.") from e
            else:
                raise
    finally:
        conn.close()
        
    return new_hash
