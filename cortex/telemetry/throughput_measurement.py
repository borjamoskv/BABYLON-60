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
        CREATE TABLE IF NOT EXISTS throughput_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            model TEXT NOT NULL,
            prompt TEXT NOT NULL,
            total_tokens INTEGER NOT NULL,
            total_time_ms REAL NOT NULL,
            tokens_per_sec REAL NOT NULL,
            status TEXT NOT NULL,
            error_msg TEXT
        );
    """)
    conn.commit()
    return conn

def measure_throughput(model="qwen2.5:0.5b"):
    prompt = "Count from 1 to 30 using words (one, two, three...), separated by commas. Do not include any other text."
    payload = json.dumps({
        "model": model,
        "prompt": prompt,
        "stream": True,
        "options": {
            "temperature": 0.0  # Max determinism
        }
    }).encode("utf-8")

    req = urllib.request.Request(
        OLLAMA_URL, 
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST"
    )
    
    start_time = time.perf_counter()
    first_token_time = None
    token_count = 0
    
    try:
        with urllib.request.urlopen(req, timeout=30.0) as response:
            for line in response:
                if line:
                    data = json.loads(line.decode("utf-8"))
                    token_count += 1
                    if first_token_time is None:
                        first_token_time = time.perf_counter()
                    if data.get("done", False):
                        break
            
            end_time = time.perf_counter()
            
            if token_count > 1 and first_token_time is not None:
                total_time_ms = (end_time - start_time) * 1000.0
                gen_time = end_time - first_token_time
                tps = (token_count - 1) / gen_time if gen_time > 0 else 0.0
                return prompt, token_count, total_time_ms, tps, "SUCCESS", None
            else:
                return prompt, 0, 0.0, 0.0, "ERROR", "Insufficient tokens generated"
    except Exception as e:
        return prompt, 0, 0.0, 0.0, "ERROR", str(e)

def main():
    conn = init_db()
    model = sys.argv[1] if len(sys.argv) > 1 else "qwen2.5:0.5b"
    
    print(f"🔍 [DEBUG / TRACE / PARSING] Measuring throughput for {model}...")
    prompt, token_count, total_time_ms, tps, status, err = measure_throughput(model)
    
    conn.execute(
        """
        INSERT INTO throughput_log 
        (timestamp, model, prompt, total_tokens, total_time_ms, tokens_per_sec, status, error_msg) 
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (datetime.now(timezone.utc).isoformat(), model, prompt, token_count, total_time_ms, tps, status, err)
    )
    conn.commit()
    conn.close()

    if status == "SUCCESS":
        print(f"🟢 [STATUS_OK / EXERGY] Generated {token_count} tokens in {total_time_ms:.2f}ms.")
        print(f"🟢 [STATUS_OK / EXERGY] Throughput: {tps:.2f} tokens/second")
    else:
        print(f"🔴 [FATAL / SIGKILL / DESTRUCTION] Throughput Measurement Failed: {err}")
        sys.exit(1)

if __name__ == "__main__":
    main()
