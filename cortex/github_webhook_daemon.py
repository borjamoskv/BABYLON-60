# C5-REAL EXERGY CERTIFIED
"""C5-REAL Sovereign GitHub Webhook Daemon (N=1 Perceptor)."""

import os
import sys
import json
import hmac
import hashlib
import sqlite3
import time
from http.server import HTTPServer, BaseHTTPRequestHandler


# C5-REAL Invariant: Zero External Dependencies for perception.
CORTEX_DB_PATH = ".cortex/cortex.db"
SECRET_KEY = os.environ.get("CORTEX_GITHUB_SECRET")
TRIGGER_PATH = ".cortex/.trigger_swarm"


def get_secret_key() -> str:
    key = os.environ.get("CORTEX_GITHUB_SECRET") or SECRET_KEY
    if not key:
        raise RuntimeError("CORTEX_GITHUB_SECRET env var is required (Ω25).")
    return key


def init_perception_ledger() -> None:
    if not os.path.exists(".cortex"):
        os.makedirs(".cortex", exist_ok=True)

    conn = sqlite3.connect(CORTEX_DB_PATH, timeout=5.0)
    cursor = conn.cursor()
    cursor.execute("PRAGMA journal_mode = WAL;")
    cursor.execute("PRAGMA busy_timeout = 5000;")

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS github_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            event_type TEXT NOT NULL,
            payload_hash TEXT UNIQUE NOT NULL,
            lamport_t INTEGER NOT NULL,
            cortex_taint TEXT NOT NULL,
            processed INTEGER DEFAULT 0
        )
    """)
    conn.commit()
    conn.close()


def log_event(event_type: str, payload_bytes: bytes) -> bool:
    conn = sqlite3.connect(CORTEX_DB_PATH, timeout=5.0)
    cursor = conn.cursor()

    cursor.execute("SELECT MAX(lamport_t) FROM github_events")
    row = cursor.fetchone()
    last_lamport = row[0] if row and row[0] is not None else 0
    new_lamport = last_lamport + 1

    payload_hash = hashlib.sha3_256(payload_bytes).hexdigest()
    taint = f"CORTEX-TAINT:webhook:{time.strftime('%Y-%m-%dT%H:%M:%SZ')}:{payload_hash[:8]}"

    try:
        cursor.execute(
            "INSERT INTO github_events (event_type, payload_hash, lamport_t, cortex_taint) VALUES (?, ?, ?, ?)",
            (event_type, payload_hash, new_lamport, taint),
        )
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        # Idempotency Lock (Ω15): Abort if payload already exists.
        return False
    finally:
        conn.close()


class GitHubWebhookHandler(BaseHTTPRequestHandler):
    def do_POST(self) -> None:
        content_length_str = self.headers.get("Content-Length")
        if not content_length_str:
            self.send_response(411)
            self.end_headers()
            return

        content_length = int(content_length_str)
        payload_bytes = self.rfile.read(content_length)

        # Validación HMAC (Ω24: Prohibido weak crypto)
        signature_header = self.headers.get("X-Hub-Signature-256")
        if not signature_header:
            self.send_response(401)
            self.end_headers()
            return

        expected_mac = hmac.new(get_secret_key().encode("utf-8"), payload_bytes, hashlib.sha3_256).hexdigest()

        expected_sig = f"sha3-256={expected_mac}"
        if not hmac.compare_digest(expected_sig, signature_header):
            self.send_response(403)
            self.end_headers()
            return

        event_type = self.headers.get("X-GitHub-Event", "unknown")

        # Escribir al Master Ledger
        if log_event(event_type, payload_bytes):
            # Ignición determinista: Notificar al Swarm Dispatcher (Ω9)
            with open(TRIGGER_PATH, "w") as f:
                f.write(f"{event_type}:{hashlib.sha3_256(payload_bytes).hexdigest()}")

            self.send_response(202)
            self.send_header("Content-type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"status": "C5-REAL_IGNITION_TRIGGERED"}).encode("utf-8"))
        else:
            self.send_response(200)
            self.send_header("Content-type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"status": "IDEMPOTENCY_LOCK_ABORTED"}).encode("utf-8"))


def run_daemon(port: int = 8080) -> None:
    init_perception_ledger()
    server_address = ("", port)
    httpd = HTTPServer(server_address, GitHubWebhookHandler)
    print(f"[C5-REAL] GitHub Webhook Daemon escuchando en el puerto {port} (Síncrono)")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n[C5-REAL] Purgando daemon.")
        httpd.server_close()
        sys.exit(0)


if __name__ == "__main__":
    run_daemon()
