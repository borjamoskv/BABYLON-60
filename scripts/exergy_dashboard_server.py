#!/usr/bin/env python3
"""Exergy Dashboard Server (C5-REAL).

A sovereign, zero-dependency HTTP server that serves the Exergy Dashboard UI
and exposes a read-only telemetry API from the BFT Ledger.
Complies with INV_C5_17 (100% free, zero external dependencies).
"""

import json
import sqlite3
import sys
from http.server import HTTPServer, SimpleHTTPRequestHandler
from pathlib import Path
from urllib.parse import urlparse

# Add project root to sys.path to resolve local packages
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from babylon60.database.core import connect_sync

# We will read from exergy_agent_ledger.db which is created in ~/.babylon60/exergy_agent_ledger.db
DB_PATH = Path.home() / ".babylon60/exergy_agent_ledger.db"

class ExergyDashboardHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        # Serve static files from apps/ExergyDashboard/public
        public_dir = PROJECT_ROOT / "apps" / "ExergyDashboard" / "public"
        super().__init__(*args, directory=str(public_dir), **kwargs)

    def do_GET(self):
        parsed = urlparse(self.path)
        if parsed.path == "/api/metrics":
            self.serve_metrics()
        else:
            super().do_GET()

    def serve_metrics(self):
        try:
            # We connect strictly read-only to avoid any lock contention (INV_BFT_02 compliance)
            # uri=True allows us to specify mode=ro
            conn = sqlite3.connect(f"file:{DB_PATH}?mode=ro", uri=True)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            # Fetch last 50 events
            cursor.execute("SELECT * FROM ledger ORDER BY timestamp DESC LIMIT 50")
            rows = cursor.fetchall()
            
            data = [dict(row) for row in rows]
            
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(data).encode("utf-8"))
            
        except sqlite3.OperationalError as e:
            self.send_response(500)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"error": str(e), "db": str(DB_PATH)}).encode("utf-8"))
        finally:
            if 'conn' in locals():
                conn.close()

def main():
    port = 8080
    server_address = ('', port)
    
    # Ensure public directory exists
    public_dir = PROJECT_ROOT / "apps" / "ExergyDashboard" / "public"
    public_dir.mkdir(parents=True, exist_ok=True)
    
    httpd = HTTPServer(server_address, ExergyDashboardHandler)
    print(f"🔋 Exergy Dashboard Server (C5-REAL) ignited on http://localhost:{port}")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nServer shutting down.")
    finally:
        httpd.server_close()

if __name__ == '__main__':
    main()
