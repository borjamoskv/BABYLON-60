#!/usr/bin/env python3
import sqlite3
import os
import hashlib

# [C5-REAL] WEISMANN BARRIER (ONTOLOGICAL APOPTOSIS ENFORCER)
# L0.3 Invariant: Civilizations lack a reproductive bottleneck. 
# This script enforces a generational reset on the BFT Ledger to purge monotonically accumulating entropy (schema drift).

DB_SOURCE = "$CORTEX_ROOT/30_BABYLON-60/nexus_anchors.db"
DB_TARGET = "$CORTEX_ROOT/30_BABYLON-60/nexus_anchors_v2.db"

def enforce_weismann_barrier():
    if not os.path.exists(DB_SOURCE):
        print("[!] No source ledger found.")
        return

    # 1. Intercept Source WAL
    conn_in = sqlite3.connect(DB_SOURCE)
    conn_in.execute("PRAGMA journal_mode=WAL;")
    cursor_in = conn_in.cursor()

    try:
        cursor_in.execute("SELECT hash, prev_hash, content, timestamp, agent_id FROM anchors ORDER BY timestamp ASC")
        rows = cursor_in.fetchall()
    except sqlite3.OperationalError:
        print("[!] Error reading source ledger. Perhaps empty?")
        return
    
    # 2. State Distillation (Semantic Purge)
    # Filter out any payloads flagged as "C4-SIM" or "Semantic_Friction"
    distilled_rows = []
    for r in rows:
        content = r[2]
        if "C4-SIM" not in content and "Green Theater" not in content:
            distilled_rows.append(r)

    # 3. Clean Slate Spawn (Generational Reset)
    conn_out = sqlite3.connect(DB_TARGET)
    conn_out.execute("PRAGMA journal_mode=WAL;")
    conn_out.execute("PRAGMA busy_timeout=5000;")
    conn_out.execute('''CREATE TABLE IF NOT EXISTS anchors
                 (hash TEXT PRIMARY KEY,
                  prev_hash TEXT UNIQUE,
                  content TEXT,
                  timestamp TEXT,
                  agent_id TEXT)''')
    
    cursor_out = conn_out.cursor()
    cursor_out.execute("DELETE FROM anchors") # Hard reset

    # Re-chain the canonical subgraph
    canonical_hash_acc = hashlib.sha3_256(b"GENESIS_V2").hexdigest()
    
    for r in distilled_rows:
        orig_hash, _, content, ts, agent = r
        new_prev = canonical_hash_acc
        
        # CORTEX-TAINT injection
        tainted_content = f"{content} [WEISMANN_PURGED]"
        new_hash = hashlib.sha3_256((tainted_content + new_prev).encode('utf-8')).hexdigest()
        
        cursor_out.execute(
            "INSERT INTO anchors (hash, prev_hash, content, timestamp, agent_id) VALUES (?, ?, ?, ?, ?)",
            (new_hash, new_prev, tainted_content, ts, agent + "_APOPTOSIS")
        )
        canonical_hash_acc = new_hash

    conn_out.commit()
    conn_in.close()
    conn_out.close()

    print(f"WEISMANN_BARRIER_ENFORCED. Canonical Subgraph Taint Hash: {canonical_hash_acc[:16]}")

if __name__ == "__main__":
    enforce_weismann_barrier()
