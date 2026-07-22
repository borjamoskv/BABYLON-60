import sqlite3
import os
from fastapi import FastAPI
import uvicorn

app = FastAPI()

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'cortex_bft_ledger.db')

def init_db():
    conn = sqlite3.connect(DB_PATH)
    conn.execute('PRAGMA journal_mode=WAL')
    conn.execute('PRAGMA busy_timeout=5000')
    conn.execute('CREATE TABLE IF NOT EXISTS stress_log (id INTEGER PRIMARY KEY AUTOINCREMENT, pulse TEXT, ts DATETIME DEFAULT CURRENT_TIMESTAMP)')
    conn.commit()
    conn.close()

init_db()

@app.get("/api/stress")
def stress():
    conn = sqlite3.connect(DB_PATH)
    conn.execute('PRAGMA busy_timeout=5000')
    conn.execute('INSERT INTO stress_log (pulse) VALUES ("C5-REAL-STRESS")')
    conn.commit()
    conn.close()
    return {"exergy": "max"}

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8080, log_level="warning")
