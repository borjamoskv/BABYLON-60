#!/usr/bin/env python3
# ============================================================================
# BABYLON-60 v4.0 Sovereign Hardened
# █ AUTOCOGNITION-Ω | STATE: C5-REAL | AESTHETIC: INDUSTRIAL_NOIR_2026
# ============================================================================
"""Create consistent SQLite snapshots and SHA-256 manifests.

The CLI records snapshot events in the ledger. The author field is descriptive
metadata; a file digest does not authenticate authorship.
"""

import hashlib
import json
import os
import sqlite3
import subprocess
import sys
import uuid
from contextlib import closing
from datetime import datetime, timezone
from pathlib import Path

from babylon60.bft.ledger_actor import BFTLedgerActor, LedgerEvent

REPO_ROOT = Path(__file__).absolute().parents[2]
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
    """Publish a complete DB/manifest pair from an existing SQLite source.

    Output names are allocated exclusively. A process crash may leave an
    unpublished DB or staging file, which is not a completed manifest.
    """
    if not DB_PATH.is_file():
        raise FileNotFoundError(f"Source database not found: {DB_PATH}")

    # The read-only open is essential: is_file() alone races with removal and
    # SQLite's normal connect would then recreate an absent source database.
    source_uri = DB_PATH.absolute().as_uri() + "?mode=ro"
    with closing(sqlite3.connect(source_uri, uri=True)) as conn:
        conn.execute("PRAGMA schema_version").fetchone()
        SNAPSHOT_DIR.mkdir(mode=0o700, parents=True, exist_ok=True)
        created_at = datetime.now(timezone.utc)
        token = f"{created_at.strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex}"
        dest_db = SNAPSHOT_DIR / f"cortex_snapshot_{token}.db"
        manifest_path = SNAPSHOT_DIR / f"manifest_{token}.json"
        temp_path = SNAPSHOT_DIR / f".tmp_{token}.json"
        flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_NOFOLLOW", 0)
        # SQLite permits VACUUM INTO an existing empty file. Reserving it with
        # O_EXCL protects a preexisting DB, including a zero-byte file.
        dest_fd = os.open(dest_db, flags, 0o600)
        dest_identity = os.fstat(dest_fd)
        temp_identity = None
        published = False
        try:
            conn.execute("VACUUM INTO ?", (str(dest_db),))
            os.fsync(dest_fd)
            manifest = {
                "snapshot_file": dest_db.name,
                "sha256": compute_sha256(dest_db),
                "commit_sha": get_latest_commit(),
                "author": AUTHOR,
                "created_at": created_at.isoformat(),
            }
            manifest_bytes = (json.dumps(manifest, indent=2) + "\n").encode("utf-8")
            temp_identity = _write_exclusive(temp_path, manifest_bytes)
            # Atomic exclusive publication; an exists() check plus replace()
            # would overwrite a manifest created concurrently after the check.
            os.link(temp_path, manifest_path, follow_symlinks=False)
            published = True
            _unlink_owned(temp_path, temp_identity)
            _sync_directory(SNAPSHOT_DIR)
            return manifest_path
        except BaseException as error:
            owned = [(dest_db, dest_identity)]
            if temp_identity is not None:
                owned.append((temp_path, temp_identity))
                if published:
                    owned.append((manifest_path, temp_identity))
            for path, identity in owned:
                try:
                    _unlink_owned(path, identity)
                except OSError:
                    add_note = getattr(error, "add_note", None)
                    if callable(add_note):
                        add_note("Snapshot output cleanup failed; inspect unpublished files")
            raise
        finally:
            os.close(dest_fd)


def _write_exclusive(path: Path, data: bytes) -> os.stat_result:
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_NOFOLLOW", 0), 0o600)
    identity = os.fstat(fd)
    try:
        offset = 0
        while offset < len(data):
            written = os.write(fd, data[offset:])
            if written <= 0:
                raise OSError("Snapshot manifest write made no progress")
            offset += written
        os.fsync(fd)
        return identity
    except BaseException:
        _unlink_owned(path, identity)
        raise
    finally:
        os.close(fd)


def _unlink_owned(path: Path, identity: os.stat_result) -> None:
    try:
        current = path.stat(follow_symlinks=False)
    except FileNotFoundError:
        return
    if os.path.samestat(identity, current):
        path.unlink()


def _sync_directory(path: Path) -> None:
    fd = os.open(path, os.O_RDONLY | getattr(os, "O_DIRECTORY", 0) | getattr(os, "O_NOFOLLOW", 0))
    try:
        os.fsync(fd)
    finally:
        os.close(fd)


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
