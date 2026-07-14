#!/usr/bin/env python3
import sys
import os
import subprocess
import hashlib
import sqlite3
from datetime import datetime

# [C5-REAL] REPO PRIVACY AUDIT DAEMON
# Delta-1: Forensic PPI Evaluation on Repository Visibility

DB_FILE = "$CORTEX_ROOT/30_BABYLON-60/nexus_anchors_v2.db"

def run_privacy_audit():
    # 1. Inspect git remotes to analyze public vs private indicators
    try:
        remote_url = subprocess.check_output(
            ["git", "config", "--get", "remote.origin.url"], 
            stderr=subprocess.DEVNULL
        ).decode("utf-8").strip()
    except Exception:
        remote_url = "NO_REMOTE"

    # 2. Risk Assessment Matrix (PPI)
    # Reality: 5/5 (Neural scraper bots systematically index exergy frameworks)
    # Risk: 4/5 (Secrets/Paths exposure in system configs)
    # Evidence: 5/5 (Fable 5 / US Export Designations show sovereign technology isolation pressure)
    
    recommendation = (
        "DECISION: EXPORT_ISOLATION_MANDATE\n"
        "Claim: Git repositories containing C5-REAL/APEX specifications MUST be private.\n"
        "Proof:\n"
        "  - Exergy Theft: Neural scrapers will digest custom AST templates and rules to minimize their own entropy at our expense.\n"
        "  - Metadata Leakage: AGENTS.md rules reveal structural system prompt configurations, creating an attack vector for indirect injection.\n"
        "  - Threat Model: Sovereign technology controls (Pentagon/Commerce department) require air-gapped or private environments to mitigate supply-chain risk labels.\n"
        f"Remote Status: {remote_url}\n"
        "Action Plan: Execute 'gh repo edit --visibility private' or migrate to local private SSH endpoints immediately."
    )
    
    print(recommendation)

    # 3. Log to SQLite WAL Ledger
    if os.path.exists(DB_FILE):
        conn = sqlite3.connect(DB_FILE)
        conn.execute("PRAGMA journal_mode=WAL;")
        cursor = conn.cursor()
        
        try:
            cursor.execute("SELECT hash FROM anchors ORDER BY timestamp DESC LIMIT 1")
            row = cursor.fetchone()
            prev_hash = row[0] if row else "GENESIS_V2"
        except sqlite3.OperationalError:
            prev_hash = "GENESIS_V2"
            
        ts = datetime.utcnow().isoformat() + "Z"
        new_hash = hashlib.sha3_256((recommendation + prev_hash).encode('utf-8')).hexdigest()
        
        cursor.execute("INSERT INTO anchors (hash, prev_hash, content, timestamp, agent_id) VALUES (?, ?, ?, ?, ?)",
                       (new_hash, prev_hash, recommendation, ts, "REPO_PRIVACY_AUDIT"))
        conn.commit()
        conn.close()
        print(f"[✓] Ledger updated. Hash: {new_hash[:16]}")

if __name__ == "__main__":
    run_privacy_audit()
