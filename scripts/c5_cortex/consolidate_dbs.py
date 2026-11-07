#!/usr/bin/env python3
"""Create SQLite snapshots in the central directory without deleting source data.

Existing destinations and unrecognized databases require separate reconciliation.
An online backup cannot prove that the source has no remaining writers.
"""

import os
import sqlite3
import tempfile
import time
from contextlib import closing
from pathlib import Path

REPO_ROOT = Path(__file__).absolute().parent.parent.parent
CENTRAL_DIR = Path.home() / ".babylon60" / "dbs"
MASTER_LEDGERS = {"cortex.db", "master_ledger.db", "cortex_memory.db", "ultrathink_ledger.db", "telemetry.db"}


def _process_master_db(db_path: Path, name: str) -> bool:
    dest = CENTRAL_DIR / name
    if db_path.is_symlink() or dest.exists() or dest.is_symlink():
        print(f"Preserved source and existing destination: {db_path}")
        return False
    deadline = time.monotonic() + 10.0

    def progress(status: int, remaining: int, total: int) -> None:
        if time.monotonic() > deadline:
            raise TimeoutError("SQLite snapshot timed out; source preserved")

    with tempfile.TemporaryDirectory(prefix=".sqlite-backup-", dir=CENTRAL_DIR) as staging:
        snapshot = Path(staging) / "snapshot.sqlite"
        with closing(sqlite3.connect(db_path.absolute().as_uri() + "?mode=ro", uri=True)) as source:
            with closing(sqlite3.connect(snapshot)) as target:
                target.execute("PRAGMA synchronous=FULL")
                source.backup(target, pages=256, progress=progress, sleep=0.01)
                target.execute("PRAGMA journal_mode=DELETE")
                if target.execute("PRAGMA integrity_check").fetchall() != [("ok",)]:
                    raise ValueError(f"Invalid SQLite snapshot: {db_path}")
        with snapshot.open("rb") as stream:
            os.fsync(stream.fileno())
        # Same-filesystem exclusive publication: a racing destination is never overwritten.
        try:
            os.link(snapshot, dest)
        except FileExistsError:
            print(f"Destination appeared during backup, preserved both: {db_path}")
            return False
        directory_fd = os.open(CENTRAL_DIR, os.O_RDONLY | os.O_DIRECTORY)
        try:
            os.fsync(directory_fd)
        finally:
            os.close(directory_fd)
    print(f"Snapshot created: {db_path} -> {dest}; source retained")
    return True


def consolidate_dbs() -> None:
    CENTRAL_DIR.mkdir(parents=True, exist_ok=True)
    copied = 0
    # Materialize before creating snapshots; never sweep or purge arbitrary *.db files.
    db_paths = [
        p
        for p in REPO_ROOT.rglob("*.db")
        if not any(part in ("venv", ".venv", ".git", "__pycache__") for part in p.parts)
    ]
    for db_path in db_paths:
        if db_path.name in MASTER_LEDGERS and "archive" not in db_path.parts:
            copied += int(_process_master_db(db_path, db_path.name))
    print(f"Consolidation finished: {copied} snapshots created; all source databases retained")


if __name__ == "__main__":
    consolidate_dbs()
