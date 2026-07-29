# C5-REAL EXERGY CERTIFIED
import sqlite3
import json
import uuid
import time
import hashlib

DB_PATH = "master_ledger.db"

def compute_hash(payload: str, lamport: int) -> str:
    return hashlib.sha256(f"{payload}:{lamport}".encode()).hexdigest()

def inject_fact(conn, event_id, stream, payload_json, lamport_t):
    entry_hash = compute_hash(payload_json, lamport_t)
    conn.execute('''
        INSERT INTO master_ledger
        (event_id, stream, payload_json, cortex_taint, lamport_t, prev_hash, entry_hash, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, datetime('now'))
    ''', (
        event_id,
        stream,
        payload_json,
        "C5-REAL-SECURE",
        lamport_t,
        "GENESIS",
        entry_hash
    ))
    return entry_hash

def main():
    conn = sqlite3.connect(DB_PATH)

    # Check current lamport_t
    cur = conn.execute("SELECT MAX(lamport_t) FROM master_ledger")
    row = cur.fetchone()
    current_lamport = row[0] if row[0] is not None else 0

    intel_agy = {
        "app": "Antigravity IDE.app",
        "endpoints": ["https://agent-marketplace.corp.google.com"],
        "modules": ["jetskiAgent", "LSP Bridge"],
        "telemetry": ["g1-credits", "g1-activity"]
    }

    intel_chatgpt = {
        "app": "ChatGPT Classic.app",
        "frameworks": ["LiveKitWebRTC.framework"],
        "entitlements": ["com.apple.security.automation.apple-events"],
        "notes": "Native Swift, UDP voice streaming, zero Mojom"
    }

    lamport = current_lamport + 1
    h1 = inject_fact(conn, str(uuid.uuid4()), "threat_intel", json.dumps(intel_agy), lamport)

    lamport += 1
    h2 = inject_fact(conn, str(uuid.uuid4()), "threat_intel", json.dumps(intel_chatgpt), lamport)

    conn.commit()
    conn.close()
    print(f"Injected AGY IDE Intel. Hash: {h1}")
    print(f"Injected ChatGPT Classic Intel. Hash: {h2}")

if __name__ == "__main__":
    main()
