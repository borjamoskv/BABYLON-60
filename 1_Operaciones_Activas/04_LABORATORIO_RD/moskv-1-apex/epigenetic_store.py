#!/usr/bin/env python3
import sqlite3
import hashlib
import json
import os

DB_PATH = "swarm_os.sqlite"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS epigenetic_memory (
            hash_key TEXT PRIMARY KEY,
            payload TEXT,
            methylated INTEGER DEFAULT 1
        )
    ''')
    conn.commit()
    conn.close()

def inject_context(raw_payload: dict):
    """
    Silences the context by default (methylated = 1) and returns the Transcription Factor (Hash Key).
    """
    payload_str = json.dumps(raw_payload, sort_keys=True)
    hash_key = hashlib.sha256(payload_str.encode('utf-8')).hexdigest()
    
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('INSERT OR IGNORE INTO epigenetic_memory (hash_key, payload, methylated) VALUES (?, ?, 1)', (hash_key, payload_str))
    conn.commit()
    conn.close()
    
    print(f"[EpigeneticStore] Context injected and silenced. TF: {hash_key[:8]}...")
    return hash_key

def invoke_demethylation(tf_hash: str):
    """
    Retrieves the payload only if the specific Transcription Factor (Hash) is requested.
    """
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('SELECT payload FROM epigenetic_memory WHERE hash_key = ?', (tf_hash,))
    row = c.fetchone()
    conn.close()
    
    if row:
        print(f"[EpigeneticStore] Memory demethylated for TF: {tf_hash[:8]}...")
        return json.loads(row[0])
    print(f"[EpigeneticStore] Critical Error: Transcription Factor {tf_hash[:8]}... invalid or missing.")
    return None

if __name__ == "__main__":
    print("=== C5-REAL EPIGENETIC STORE ===")
    init_db()
    # Test
    test_payload = {"directive": "Execute NMPC", "target": "Local DOM"}
    tf = inject_context(test_payload)
    retrieved = invoke_demethylation(tf)
    assert retrieved == test_payload
    print("Self-Test: PASSED")
