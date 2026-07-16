#!/usr/bin/env python3
import sqlite3
import os
import hashlib
from cortex.daemons.bft_ledger_helper import resolve_db_path, _ensure_table

# [C5-REAL] WEISMANN BARRIER (ONTOLOGICAL APOPTOSIS ENFORCER)
# L0.3 Invariant: Civilizations lack a reproductive bottleneck. 
# This script enforces a generational reset on the BFT Ledger to purge monotonically accumulating entropy (schema drift).

DB_SOURCE = "$CORTEX_ROOT/30_BABYLON-60/nexus_anchors.db"
DB_TARGET = "$CORTEX_ROOT/30_BABYLON-60/nexus_anchors_v2.db"

def enforce_weismann_barrier():
    resolved_source = resolve_db_path(DB_SOURCE)
    resolved_target = resolve_db_path(DB_TARGET)
    
    if not os.path.exists(resolved_source):
        print(f"[!] No source ledger found at {resolved_source}.")
        return

    # 1. Intercept Source WAL
    conn_in = sqlite3.connect(resolved_source)
    try:
        conn_in.execute("PRAGMA journal_mode=WAL;")
        cursor_in = conn_in.cursor()

        try:
            cursor_in.execute("SELECT hash, prev_hash, content, timestamp, agent_id FROM anchors ORDER BY timestamp ASC")
            rows = cursor_in.fetchall()
        except sqlite3.OperationalError:
            print("[!] Error reading source ledger. Perhaps empty?")
            return
    finally:
        conn_in.close()
    
    # 2. State Distillation (Semantic Purge)
    distilled_rows = [r for r in rows if "C4-SIM" not in r[2] and "Green Theater" not in r[2]]

    # 3. Clean Slate Spawn (Generational Reset)
    conn_out = sqlite3.connect(resolved_target)
    try:
        conn_out.execute("PRAGMA journal_mode=WAL;")
        conn_out.execute("PRAGMA busy_timeout=5000;")
        _ensure_table(conn_out, resolved_target)
        
        cursor_out = conn_out.cursor()
        cursor_out.execute("DELETE FROM anchors")  # Hard reset

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
    finally:
        conn_out.close()

    print(f"WEISMANN_BARRIER_ENFORCED. Canonical Subgraph Taint Hash: {canonical_hash_acc[:16]}")

if __name__ == "__main__":
    enforce_weismann_barrier()
