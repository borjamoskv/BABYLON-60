#!/usr/bin/env python3
import sqlite3
import sys
import os
from datetime import datetime

DB_PATH = os.path.expanduser("~/.cortex/cortex_sync.db")

def init_db():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS synchronicities (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            location TEXT NOT NULL,
            intent TEXT NOT NULL,
            observed_event TEXT NOT NULL,
            time_delta_seconds REAL,
            witnesses INTEGER DEFAULT 0,
            reality_level TEXT DEFAULT 'C5-REAL'
        )
    """)
    conn.commit()
    return conn

def seed_default_events(conn):
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM synchronicities")
    if cursor.fetchone()[0] == 0:
        events = [
            ("2023-08-01 23:00:00", "Chiclana", "Diego, voy a ver si veo un ovni a 30 segundos o menos", "ISS (en el jardín de la casa de Diego y Eneko. Testigos: Diego, Eneko, Hugo, Kapi, Patxi)", 30.0, 4, "C5-REAL"),
            ("2025-05-10 10:00:00", "Artxanda", "Voy a ver si pasa un Corzo", "Corzo (cabrito pasando de inmediato)", 1.0, 0, "C5-REAL")
        ]
        cursor.executemany("""
            INSERT INTO synchronicities (timestamp, location, intent, observed_event, time_delta_seconds, witnesses, reality_level)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, events)
        conn.commit()
        print("[✓] Seeded default synchronicity events into ledger.")

def log_event(location, intent, observed_event, time_delta_seconds, witnesses):
    conn = init_db()
    cursor = conn.cursor()
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute("""
        INSERT INTO synchronicities (timestamp, location, intent, observed_event, time_delta_seconds, witnesses)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (timestamp, location, intent, observed_event, time_delta_seconds, witnesses))
    conn.commit()
    print(f"[✓] Event logged at {timestamp} | Location: {location}")
    conn.close()

def list_events():
    conn = init_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM synchronicities ORDER BY timestamp DESC")
    rows = cursor.fetchall()
    print("\n=== CORTEX SYNCHRONICITY LEDGER ===")
    for row in rows:
        print(f"ID: {row[0]} | {row[1]} | Loc: {row[2]} | Reality: {row[7]}")
        print(f"  Intent:   \"{row[3]}\"")
        print(f"  Observed: \"{row[4]}\" (Delta: {row[5]}s | Witnesses: {row[6]})")
        print("-" * 50)
    conn.close()

if __name__ == "__main__":
    conn = init_db()
    seed_default_events(conn)
    conn.close()
    
    if len(sys.argv) > 1:
        if sys.argv[1] == "list":
            list_events()
        elif sys.argv[1] == "log" and len(sys.argv) >= 7:
            # log <location> <intent> <observed> <delta> <witnesses>
            log_event(sys.argv[2], sys.argv[3], sys.argv[4], float(sys.argv[5]), int(sys.argv[6]))
        else:
            print("Usage:")
            print("  python3 sync_logger.py list")
            print("  python3 sync_logger.py log <location> <intent> <observed> <delta_seconds> <witnesses>")
    else:
        list_events()
