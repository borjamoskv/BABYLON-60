import sqlite3
import os
import json
from datetime import datetime, timezone

DB_PATH = "/Users/borjafernandezangulo/10_PROJECTS/paralife/engine/paralife_ledger.db"

class ParalifeLedger:
    """
    Sovereign Persistence Layer for Paralife Platform.
    Ensures O(1) state retrieval and data integrity.
    """
    def __init__(self):
        self._init_db()

    def _init_db(self):
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Sessions Table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sessions (
                id TEXT PRIMARY KEY,
                profile TEXT,
                spawned_at TEXT,
                status TEXT,
                path TEXT
            )
        """)
        
        # Audit Table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS audit_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT,
                data_summary TEXT,
                decision TEXT,
                reason TEXT,
                timestamp TEXT,
                FOREIGN KEY(session_id) REFERENCES sessions(id)
            )
        """)
        
        conn.commit()
        conn.close()

    def register_session(self, sid, profile, path):
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("INSERT OR REPLACE INTO sessions VALUES (?, ?, ?, 'OPERATIONAL', ?)", 
                       (sid, profile, datetime.now(timezone.utc).isoformat(), path))
        conn.commit()
        conn.close()

    def update_session_status(self, sid, status):
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("UPDATE sessions SET status = ? WHERE id = ?", (status, sid))
        conn.commit()
        conn.close()

    def log_audit(self, sid, decision, reason, data_summary):
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO audit_logs (session_id, data_summary, decision, reason, timestamp)
            VALUES (?, ?, ?, ?, ?)
        """, (sid, data_summary[:100], decision, reason, datetime.now(timezone.utc).isoformat()))
        conn.commit()
        conn.close()

    def get_active_sessions(self):
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM sessions WHERE status = 'OPERATIONAL'")
        rows = cursor.fetchall()
        conn.close()
        return rows

if __name__ == "__main__":
    ledger = ParalifeLedger()
    print("[+] Ledger INITIALIZED.")
