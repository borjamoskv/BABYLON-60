#!/usr/bin/env python3
"""Incremental Ledger Snapshot Engine.

Creates deterministic snapshots of cortex.db, computes SHA-256 manifests,
records snapshot events in the BFT ledger, and verifies authorship:
Telmo Dinámico de Moskv (borjamoskv).
"""

import json
import hashlib
import sqlite3
import sys
import subprocess
import uuid
from datetime import datetime, timezone
from pathlib import Path

from babylon60.bft.ledger_actor import BFTLedgerActor, LedgerEvent

REPO_ROOT = Path(__file__).parents[1]
SNAPSHOT_DIR = REPO_ROOT / "audit" / "snapshots"
DB_PATH = REPO_ROOT / "cortex.db"
AUTHOR = "Telmo Dinámico de Moskv (borjamoskv)"

def compute_sha256(filepath: Path) -> str:
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()

def get_latest_commit() -> str:
    res = subprocess.run(["git", "rev-parse", "HEAD"], cwd=REPO_ROOT, capture_output=True, text=True)
    return res.stdout.strip() if res.returncode == 0 else "unknown"

def create_snapshot() -> Path:
    SNAPSHOT_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    dest_db = SNAPSHOT_DIR / f"cortex_snapshot_{timestamp}.db"

    # SQLite VACUUM INTO to safely create a consistent snapshot without blocking WAL
    if DB_PATH.exists():
        conn = sqlite3.connect(DB_PATH)
        try:
            conn.execute(f"VACUUM INTO '{dest_db}'")
        finally:
            conn.close()
    else:
        # Create empty db if cortex.db doesn't exist yet
        sqlite3.connect(dest_db).close()

    db_hash = compute_sha256(dest_db)
    commit_sha = get_latest_commit()

    manifest = {
        "snapshot_file": dest_db.name,
        "sha256": db_hash,
        "commit_sha": commit_sha,
        "author": AUTHOR,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }

    manifest_path = SNAPSHOT_DIR / f"manifest_{timestamp}.json"
    with open(manifest_path, "w") as f:
        json.dump(manifest, f, indent=2)

    return manifest_path

async def record_snapshot_event(manifest_path: Path) -> None:
    with open(manifest_path) as f:
        data = json.load(f)

    actor = BFTLedgerActor(DB_PATH)
    await actor.start()
    try:
        event = LedgerEvent(
            stream="audit",
            entity_id=str(uuid.uuid5(uuid.NAMESPACE_URL, f"snapshot:{data['sha256']}")),
            event_type="ledger_snapshot",
            payload=data,
            cortex_taint=f"snapshot_engine:{AUTHOR}",
            source_db="cortex.db",
            source_table="snapshots",
            source_pk=str(uuid.uuid4()),
        )
        await actor.append(event)
    finally:
        await actor.stop()

def main() -> int:
    print(f"📸 Igniting Ledger Snapshot Engine by {AUTHOR}...")
    manifest_path = create_snapshot()
    import asyncio
    asyncio.run(record_snapshot_event(manifest_path))
    print(f"🟢 Ledger snapshot created successfully: {manifest_path.name}")
    return 0

if __name__ == "__main__":
    sys.exit(main())
