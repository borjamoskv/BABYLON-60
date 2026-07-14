import sys
import time
import json
import sqlite3
import urllib.request
from pathlib import Path
from datetime import datetime, timezone

DB_PATH = Path("/Users/borjafernandezangulo/30_BABYLON-60/telemetry.db")
OLLAMA_URL = "http://127.0.0.1:11434/api/generate"

def init_db():
    conn = sqlite3.connect(DB_PATH, timeout=5.0)
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA synchronous=NORMAL;")
    conn.execute("""
        CREATE TABLE IF NOT EXISTS ttft_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            model TEXT NOT NULL,
            ttft_ms REAL NOT NULL,
            status TEXT NOT NULL,
            error_msg TEXT
        );
    """)
    conn.commit()
    return conn

def measure_ttft(model="llama3"):
    payload = json.dumps({
        "model": model,
        "prompt": "Say 'OK' strictly without preambles.",
        "stream": True
    }).encode("utf-8")

    req = urllib.request.Request(
        OLLAMA_URL, 
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST"
    )
    
    start_time = time.perf_counter()
    
    try:
        with urllib.request.urlopen(req, timeout=10.0) as response:
            # Await first chunk
            chunk = response.readline()
            if chunk:
                first_token_time = time.perf_counter()
                ttft_ms = (first_token_time - start_time) * 1000.0
                return ttft_ms, "SUCCESS", None
            else:
                return 0.0, "ERROR", "Empty response"
    except Exception as e:
        return 0.0, "ERROR", str(e)

def main():
    conn = init_db()
    
    # Try with a common local model alias. 
    # Can fallback if needed but we test base connection and inference.
    model = "llama3"
    
    print(f"🔍 [DEBUG / TRACE / PARSING] Pinging {OLLAMA_URL} for TTFT measurement...")
    ttft_ms, status, err = measure_ttft(model)
    
    conn.execute(
        "INSERT INTO ttft_log (timestamp, model, ttft_ms, status, error_msg) VALUES (?, ?, ?, ?, ?)",
        (datetime.now(timezone.utc).isoformat(), model, ttft_ms, status, err)
    )
    conn.commit()
    conn.close()

    if status == "SUCCESS":
        print(f"🟢 [STATUS_OK / EXERGY] TTFT: {ttft_ms:.2f}ms")
        if ttft_ms > 500:
            print(f"🟡 [WARNING / ANERGY RISK] TTFT > 500ms ({ttft_ms:.2f}ms). Execution not optimal.")
        else:
            print("🟢 [STATUS_OK / EXERGY] TTFT under threshold (< 500ms).")
    else:
        print(f"🔴 [FATAL / SIGKILL / DESTRUCTION] TTFT Measurement Failed: {err}")
        sys.exit(1)

if __name__ == "__main__":
    main()
