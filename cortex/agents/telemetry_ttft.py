import sqlite3
import time
import json
import urllib.request
import urllib.error

TELEMETRY_DB = "telemetry.db"

def init_db():
    conn = sqlite3.connect(TELEMETRY_DB, timeout=5.0)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("""
        CREATE TABLE IF NOT EXISTS ttft_metrics (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            model TEXT,
            ttft_ms REAL,
            status TEXT
        )
    """)
    conn.commit()
    return conn

def measure_ttft():
    url = "http://localhost:11434/api/generate"
    data = json.dumps({
        "model": "llama3",
        "prompt": "Hello",
        "stream": True
    }).encode("utf-8")
    
    req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
    
    start_time = time.perf_counter()
    try:
        with urllib.request.urlopen(req, timeout=5.0) as response:
            # Leer el primer chunk para contar como TTFT
            _ = response.read(1)
            end_time = time.perf_counter()
            ttft_ms = (end_time - start_time) * 1000
            return "llama3", ttft_ms, "SUCCESS"
    except urllib.error.URLError as e:
        return "llama3", 0.0, f"FAILED: {e.reason}"
    except Exception as e:
        return "llama3", 0.0, f"ERROR: {str(e)}"

def main():
    print("[*] Iniciando sonda TTFT C5-REAL...")
    conn = init_db()
    model, ttft, status = measure_ttft()
    
    conn.execute(
        "INSERT INTO ttft_metrics (model, ttft_ms, status) VALUES (?, ?, ?)",
        (model, ttft, status)
    )
    conn.commit()
    
    if status == "SUCCESS":
        print(f"🟢 [TTFT] Modelo: {model} | Latencia: {ttft:.2f} ms")
    else:
        print(f"🔴 [TTFT] Fallo en sonda: {status}")

if __name__ == "__main__":
    main()
