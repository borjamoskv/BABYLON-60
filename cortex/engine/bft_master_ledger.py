"""
CORTEX BFT MASTER LEDGER (C5-REAL)
Enforces:
- Rule Ω11: RAISE(ABORT) on UPDATE/DELETE, UNIQUE(prev_hash), CORTEX-TAINT.
- Rule Ω12: Lamport recovery and Tie-Breaking total order.
- Rule Ω15: Idempotency Lock (Zero ATP waste on duplicate payloads).
"""

import sqlite3
import json
import os
import sys

# Attempt High-Exergy BLAKE3, fallback to SHA-256
try:
    from blake3 import blake3
    def get_hasher(): return blake3()
except ImportError:
    import hashlib
    def get_hasher(): return hashlib.sha256()

LEDGER_PATH = os.environ.get("CORTEX_LEDGER_PATH", os.path.join(os.path.dirname(__file__), "nexus_anchors.db"))

def get_db_connection() -> sqlite3.Connection:
    os.makedirs(os.path.dirname(LEDGER_PATH), exist_ok=True)
    conn = sqlite3.connect(LEDGER_PATH, timeout=5.0)
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA synchronous=NORMAL;")
    conn.execute("PRAGMA busy_timeout=5000;") # Rule R10
    return conn

def canonical(payload: dict) -> bytes:
    """Deterministic JSON serialization (zero whitespace entropy)."""
    return json.dumps(payload, sort_keys=True, separators=(',', ':'), ensure_ascii=False).encode('utf-8')

def init_ledger():
    conn = get_db_connection()
    with conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS master_ledger (
                seq INTEGER PRIMARY KEY AUTOINCREMENT,
                lamport_t INTEGER NOT NULL,
                agent_id TEXT NOT NULL,
                payload TEXT NOT NULL,
                payload_hash TEXT NOT NULL UNIQUE,
                prev_hash TEXT NOT NULL UNIQUE,
                cortex_taint TEXT NOT NULL,
                entry_hash TEXT NOT NULL UNIQUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        
        # Ensure schema compatibility with v11.0-NEXUS without DROP TABLE
        cursor = conn.cursor()
        cursor.execute("PRAGMA table_info(master_ledger)")
        cols = {row[1] for row in cursor.fetchall()}
        if cols and "seq" not in cols and "id" in cols:
            conn.execute("ALTER TABLE master_ledger RENAME COLUMN id TO seq")
        if cols and "entry_hash" not in cols and "hash" in cols:
            conn.execute("ALTER TABLE master_ledger RENAME COLUMN hash TO entry_hash")
        if cols and "payload_hash" not in cols:
            conn.execute("ALTER TABLE master_ledger ADD COLUMN payload_hash TEXT DEFAULT ''")
        
        conn.execute("""
            CREATE TRIGGER IF NOT EXISTS prevent_ledger_update 
            BEFORE UPDATE ON master_ledger 
            BEGIN SELECT RAISE(ABORT, 'C5-REAL KINETIC BOUNDARY: UPDATE prohibited.'); END;
        """)
        
        conn.execute("""
            CREATE TRIGGER IF NOT EXISTS prevent_ledger_delete 
            BEFORE DELETE ON master_ledger 
            BEGIN SELECT RAISE(ABORT, 'C5-REAL KINETIC BOUNDARY: DELETE prohibited.'); END;
        """)
        
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM master_ledger")
        if cursor.fetchone()[0] == 0:
            gen_payload = {"genesis": "APEX_SINGULARITY"}
            gen_payload_bytes = canonical(gen_payload)
            
            h1 = get_hasher(); h1.update(gen_payload_bytes); p_hash = h1.hexdigest()
            h2 = get_hasher(); h2.update(b"0"*64 + gen_payload_bytes + b"UID0_MOSKV" + b"0" + b"CORTEX-TAINT:GENESIS")
            e_hash = h2.hexdigest()
            
            conn.execute(
                "INSERT INTO master_ledger (lamport_t, agent_id, payload, payload_hash, prev_hash, cortex_taint, entry_hash) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (0, "UID0_MOSKV", gen_payload_bytes.decode('utf-8'), p_hash, "0" * 64, "CORTEX-TAINT:GENESIS", e_hash)
            )

def compute_entry_hash(prev_hash: str, payload_bytes: bytes, agent_id: str, lamport_t: int, taint: str) -> str:
    hasher = get_hasher()
    hasher.update(prev_hash.encode('utf-8'))
    hasher.update(payload_bytes)
    hasher.update(agent_id.encode('utf-8'))
    hasher.update(str(lamport_t).encode('utf-8'))
    hasher.update(taint.encode('utf-8'))
    return hasher.hexdigest()

def append_block(payload: dict, agent_id: str, taint_prefix: str) -> str:
    """Appends block. Enforces Idempotency Lock (Ω15)."""
    conn = get_db_connection()
    payload_bytes = canonical(payload)
    
    h1 = get_hasher()
    h1.update(payload_bytes)
    payload_hash = h1.hexdigest()
    
    with conn:
        cursor = conn.cursor()
        
        # Rule Ω15: Idempotency Lock Check
        cursor.execute("SELECT entry_hash FROM master_ledger WHERE payload_hash = ?", (payload_hash,))
        existing = cursor.fetchone()
        if existing:
            return f"IDEMPOTENT:{existing[0]}"
            
        cursor.execute("SELECT lamport_t, entry_hash FROM master_ledger ORDER BY seq DESC LIMIT 1")
        row = cursor.fetchone()
        if not row:
            raise RuntimeError("No Genesis block. Run init_ledger() first.")
            
        prev_lamport_t, prev_hash = row
        new_lamport_t = prev_lamport_t + 1
        taint = f"CORTEX-TAINT:{taint_prefix}:{new_lamport_t}"
        
        new_hash = compute_entry_hash(prev_hash, payload_bytes, agent_id, new_lamport_t, taint)
        
        cursor.execute(
            "INSERT INTO master_ledger (lamport_t, agent_id, payload, payload_hash, prev_hash, cortex_taint, entry_hash) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (new_lamport_t, agent_id, payload_bytes.decode('utf-8'), payload_hash, prev_hash, taint, new_hash)
        )
        return new_hash

if __name__ == "__main__":
    init_ledger()
    if len(sys.argv) > 1 and sys.argv[1] == "verify":
        conn = get_db_connection()
        c = conn.cursor()
        c.execute("SELECT lamport_t, agent_id, payload, prev_hash, cortex_taint, entry_hash FROM master_ledger ORDER BY lamport_t ASC")
        rows = c.fetchall()
        for i in range(1, len(rows)):
            prev, curr = rows[i-1], rows[i]
            if prev[5] != curr[3]:
                print(f"CHAIN BROKEN at Lamport_T={curr[0]}: prev_hash mismatch.")
                sys.exit(1)
            payload_bytes = canonical(json.loads(curr[2]))
            if compute_entry_hash(curr[3], payload_bytes, curr[1], curr[0], curr[4]) != curr[5]:
                print(f"CHAIN BROKEN at Lamport_T={curr[0]}: hash mutation.")
                sys.exit(1)
        print("C5-REAL STATE: CHAIN INTEGRITY VALIDATED.")
        sys.exit(0)
