# -*- coding: utf-8 -*-
"""Exergy Dashboard Server (Causal-Determinist).

A sovereign, zero-dependency HTTP server that serves the Exergy Dashboard UI
and exposes a read-only telemetry API from the BFT Ledger.
Complies with INV_C5_17 (100% free, zero external dependencies).
"""

import json
import os
import sqlite3
from http.server import HTTPServer, BaseHTTPRequestHandler
from pathlib import Path
from urllib.parse import urlparse

from .kda_buffer import kda_buffer

DEFAULT_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>BABYLON-60 · Exergy Dashboard</title>
  <style>
    body { font-family: monospace; background: #0d1117; color: #58a6ff; padding: 2rem; }
    h1 { color: #f0883e; }
    pre { background: #161b22; padding: 1rem; border-radius: 6px; border: 1px solid #30363d; color: #c9d1d9; }
  </style>
</head>
<body>
  <h1>BABYLON-60 Exergy Telemetry</h1>
  <p>Status: <strong>ONLINE (Read-Only BFT Channel)</strong></p>
  <p>Telemetry API: <a href="/api/metrics" style="color: #79c0ff;">/api/metrics</a></p>
  <div id="events">Loading latest events...</div>
  <script>
    fetch('/api/metrics').then(r => r.json()).then(data => {
      document.getElementById('events').innerHTML = '<pre>' + JSON.stringify(data, null, 2) + '</pre>';
    }).catch(err => {
      document.getElementById('events').innerHTML = '<pre>Error loading metrics: ' + err + '</pre>';
    });
  </script>
</body>
</html>
"""


def _get_db_path() -> Path:
    babylon_home = os.environ.get("BABYLON_HOME")
    if not babylon_home:
        babylon_home = str(Path.home() / ".babylon60")
    home_path = Path(babylon_home)
    if home_path.name == ".babylon60":
        return home_path / "exergy_agent_ledger.db"
    return home_path / ".babylon60" / "exergy_agent_ledger.db"


class ExergyDashboardHandler(BaseHTTPRequestHandler):
    def end_headers(self) -> None:
        self.send_header("Content-Security-Policy", "default-src 'self' 'unsafe-inline'")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("X-Frame-Options", "DENY")
        self.send_header("Referrer-Policy", "no-referrer")
        super().end_headers()

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path == "/api/metrics":
            self.serve_metrics()
        elif parsed.path in ("/", "/index.html"):
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(DEFAULT_HTML.encode("utf-8"))
        else:
            asset = kda_buffer.get_asset(parsed.path)
            if asset:
                self.send_response(200)
                self.send_header("Content-Type", asset["content_type"])
                self.end_headers()
                self.wfile.write(asset["content"])
            else:
                self.send_error(404, "Asset not found")

    def serve_metrics(self) -> None:
        db_path = _get_db_path()
        try:
            if not db_path.exists():
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps([]).encode("utf-8"))
                return

            conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM ledger ORDER BY timestamp DESC LIMIT 50")
            rows = cursor.fetchall()
            data = [dict(row) for row in rows]
            conn.close()

            kda_buffer.write_telemetry(data)
            payload = kda_buffer.read_telemetry()

            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(payload)
        except Exception:
            self.send_response(500)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"error": "Telemetry query failed", "code": 500}).encode("utf-8"))


def main() -> None:
    port = int(os.environ.get("BABYLON_DASHBOARD_PORT", "8080"))
    host = os.environ.get("BABYLON_DASHBOARD_HOST", "127.0.0.1")
    server_address = (host, port)
    httpd = HTTPServer(server_address, ExergyDashboardHandler)
    print(f"🔋 Exergy Dashboard Server ignited on http://localhost:{port}", flush=True)
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nServer shutting down.")
    finally:
        httpd.server_close()


if __name__ == "__main__":
    main()
