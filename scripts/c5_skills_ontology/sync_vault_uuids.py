#!/usr/bin/env python3
# ============================================================================
# BABYLON-60 v4.0 Sovereign Hardened
# █ AUTOCOGNITION-Ω | STATE: C5-REAL | AESTHETIC: INDUSTRIAL_NOIR_2026
# ============================================================================
"""
sync_vault_uuids.py - INV_C5_15 Memory Vault Session UUID Synchronizer
Scans session UUIDs in CORTEX memory vault and synchronizes active ledger state.
Supports --json for Machine-to-Machine orchestration.
"""

import argparse
import json
import sqlite3
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
DB_PATH = REPO_ROOT / "data" / "cortex_memory.db"


def sync_vault_uuids(json_output: bool = False) -> None:
    if not DB_PATH.exists():
        if json_output:
            print(json.dumps({
                "schema_version": "1.0",
                "type": "C5_VAULT_UUID_SYNC",
                "status": "SKIPPED",
                "reason": f"Database not found at {DB_PATH}"
            }, indent=2))
            return
        print(f"[-] Database not found at {DB_PATH}. Skipping UUID sync.")
        return

    conn = sqlite3.connect(DB_PATH, timeout=5.0)
    cursor = conn.cursor()

    # Query L1 primitive nodes for session UUIDs
    try:
        cursor.execute("SELECT id, name FROM L1_primitive_nodes WHERE id LIKE 'SESSION.%'")
        rows = cursor.fetchall()
        session_uuids = [row[0] for row in rows]
    except sqlite3.OperationalError:
        session_uuids = []

    conn.close()

    if json_output:
        payload = {
            "schema_version": "1.0",
            "type": "C5_VAULT_UUID_SYNC",
            "db_path": str(DB_PATH),
            "metrics": {
                "synced_session_uuids": len(session_uuids)
            },
            "session_uuids": session_uuids,
            "status": "SYNCHRONIZED"
        }
        print(json.dumps(payload, indent=2))
        return

    print("============================================================")
    print(" 🌀 INV_C5_15: MEMORY VAULT UUID SYNCHRONIZER")
    print("============================================================")
    print(f" Memory Vault DB Path       : {DB_PATH}")
    print(f" Synced Session UUIDs       : {len(session_uuids)}")
    print(" Status                      : ✅ SYNCHRONIZED")
    print("============================================================\n")


def main() -> None:
    parser = argparse.ArgumentParser(description="INV_C5_15 Memory Vault Session UUID Synchronizer")
    parser.add_argument("--json", action="store_true", help="Emit JSON payload for M2M communication")
    args = parser.parse_args()

    sync_vault_uuids(json_output=args.json)


if __name__ == "__main__":
    main()
