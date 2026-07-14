import os
import hashlib
import sqlite3
from datetime import datetime

def resolve_db_path(raw_path: str) -> str:
    """Expands environment variables like $CORTEX_ROOT and creates parent folders."""
    expanded = os.path.expandvars(raw_path)
    dir_name = os.path.dirname(expanded)
    if dir_name:
        os.makedirs(dir_name, exist_ok=True)
    return expanded

def append_anchor(db_file_raw: str, content: str, agent_id: str) -> str:
    """Centralized method for writing to the daemons' anchors hash chain."""
    db_file = resolve_db_path(db_file_raw)
    conn = sqlite3.connect(db_file, timeout=5.0)
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA synchronous=NORMAL;")
    conn.execute("PRAGMA busy_timeout=5000;")
    cursor = conn.cursor()
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS anchors
        (hash TEXT PRIMARY KEY,
         prev_hash TEXT UNIQUE,
         content TEXT,
         timestamp TEXT,
         agent_id TEXT)
    """)
    
    try:
        cursor.execute("SELECT hash FROM anchors ORDER BY timestamp DESC LIMIT 1")
        row = cursor.fetchone()
        prev_hash = row[0] if row else "GENESIS_V2"
    except sqlite3.OperationalError:
        prev_hash = "GENESIS_V2"
        
    # Standard format: datetime.utcnow().isoformat() + "Z" (or datetime.now(timezone.utc).isoformat() in timezone terms)
    ts = datetime.utcnow().isoformat() + "Z"
    new_hash = hashlib.sha3_256((content + prev_hash).encode('utf-8')).hexdigest()
    
    cursor.execute("INSERT INTO anchors (hash, prev_hash, content, timestamp, agent_id) VALUES (?, ?, ?, ?, ?)",
                   (new_hash, prev_hash, content, ts, agent_id))
    conn.commit()
    conn.close()
    return new_hash
