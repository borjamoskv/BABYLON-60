# C5-REAL EXERGY CERTIFIED
#!/usr/bin/env python3
"""Continuous Commit Polisher Daemon.

Monitors the Git repository, rewrites commits to meet Conventional‑Commit
format, adds BFT metadata, validates exergy, and pushes the clean history.
"""

import sys
import subprocess
import time
import uuid
from datetime import datetime
from pathlib import Path

from babylon60.utils.hygiene import run_exergy_optimizer
from babylon60.database.core import connect
from babylon60.bft.ledger_actor import BFTLedgerActor, LedgerEvent

REPO_ROOT = Path(__file__).parents[1]
POLL_INTERVAL = 5  # seconds
DEBOUNCE_TIME = 10  # seconds after last commit before processing

def _latest_commit_hash() -> str:
    result = subprocess.run(["git", "rev-parse", "HEAD"], cwd=REPO_ROOT, capture_output=True, text=True, check=True)
    return result.stdout.strip()

def _record_event(event_type: str, payload: dict) -> None:
    async def _inner():
        async with connect("cortex.db") as conn:
            actor = BFTLedgerActor(conn)
            event = LedgerEvent(
                stream="audit",
                entity_id=str(uuid.uuid5(uuid.NAMESPACE_URL, f"{event_type}:{datetime.utcnow().isoformat()}")),
                event_type=event_type,
                payload=payload,
                cortex_taint="commit_polisher",
                source_db="cortex.db",
                source_table="events",
                source_pk=str(uuid.uuid4()),
            )
            await actor.append(event)
    import asyncio
    asyncio.run(_inner())

def _run_strict_reviewer() -> int:
    proc = subprocess.run([sys.executable, "-m", "babylon60.commands.strict_reviewer"], cwd=REPO_ROOT)
    return proc.returncode

def _rewrite_commits() -> None:
    subprocess.run([sys.executable, "scripts/rewrite_commits.py"], cwd=REPO_ROOT, check=True)

def main() -> None:
    if not (REPO_ROOT / ".git").exists():
        print("⚠️  Not a git repository", file=sys.stderr)
        sys.exit(1)

    last_seen = _latest_commit_hash()
    last_change = time.time()
    while True:
        time.sleep(POLL_INTERVAL)
        current = _latest_commit_hash()
        if current != last_seen:
            last_seen = current
            last_change = time.time()
            continue
        if time.time() - last_change >= DEBOUNCE_TIME:
            # Ensure on main and create backup
            subprocess.run(["git", "checkout", "main"], cwd=REPO_ROOT, check=True)
            subprocess.run(["git", "branch", "-f", "backup_main_before_polisher"], cwd=REPO_ROOT, check=True)
            if _run_strict_reviewer() != 0:
                _record_event("polisher_failure", {"stage": "strict_reviewer"})
                continue
            if not run_exergy_optimizer():
                _record_event("polisher_failure", {"stage": "exergy"})
                continue
            try:
                _rewrite_commits()
            except subprocess.CalledProcessError as e:
                _record_event("polisher_failure", {"stage": "rewrite", "error": str(e)})
                continue
            _record_event("polisher_success", {"commit": _latest_commit_hash()})
            last_change = time.time()

if __name__ == "__main__":
    main()
