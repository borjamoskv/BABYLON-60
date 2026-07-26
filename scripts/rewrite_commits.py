#!/usr/bin/env python3
"""Rewrite commit history to enforce Conventional Commits and BFT metadata.

The script performs:
1. Ensure we are on main and up‑to‑date.
2. Preserve original history in a backup branch (already created).
3. Run `git filter-repo` with a custom message‑callback that:
   - Infers a Conventional type (feat/fix/refactor/chore) from the original message.
   - Prepends the type to the subject.
   - Appends `Causal‑Taint: borjamoskv` and `Lamport‑T: <timestamp>`.
4. After rewriting, iterate over the new commits and record a `commit_rewrite` event in the Cortex Ledger.
5. Run the exergy optimizer; abort if score < 950.
6. Force‑push the cleaned history to `origin/main`.
"""

import os, subprocess, sys, uuid
from datetime import datetime
from babylon60.database.core import connect
from babylon60.bft.ledger_actor import BFTLedgerActor, LedgerEvent
from babylon60.utils.hygiene import run_exergy_optimizer

def _ensure_main():
    subprocess.run(["git", "checkout", "main"], check=True)
    subprocess.run(["git", "reset", "--hard", "origin/main"], check=True)

def _create_callback():
    callback = """
def message_callback(message, metadata):
    lower = message.lower()
    if lower.startswith('add') or lower.startswith('implement'):
        typ = 'feat'
    elif lower.startswith('fix') or 'bug' in lower:
        typ = 'fix'
    elif lower.startswith('refactor'):
        typ = 'refactor'
    else:
        typ = 'chore'
    subject = message.split('\n')[0].strip()
    new_msg = f"{typ}: {subject}\n\nCausal‑Taint: borjamoskv\nLamport‑T: {metadata['commit_timestamp']}"
    return new_msg
"""
    with open('msg_callback.py', 'w') as f:
        f.write(callback)

def _run_filter_repo():
    subprocess.run([
        "git", "filter-repo",
        "--force",
        "--message-callback", "msg_callback.message_callback",
    ], check=True)

async def _record_events():
    async with connect('cortex.db') as conn:
        actor = BFTLedgerActor(conn)
        out = subprocess.check_output(["git", "log", "--pretty=%H %P"], text=True)
        for line in out.splitlines():
            new_sha, parents = line.split(' ', 1)
            payload = {"new_sha": new_sha, "parents": parents}
            event = LedgerEvent(
                stream="audit",
                entity_id=str(uuid.uuid5(uuid.NAMESPACE_URL, f"commit:{new_sha}")),
                event_type="commit_rewrite",
                payload=payload,
                cortex_taint="commit_rewrite",
                source_db="cortex.db",
                source_table="events",
                source_pk=str(uuid.uuid4()),
            )
            await actor.append(event)

def main():
    _ensure_main()
    _create_callback()
    _run_filter_repo()
    import asyncio
    asyncio.run(_record_events())
    if not run_exergy_optimizer():
        sys.exit("Exergy score too low – aborting rewrite")
    subprocess.run(["git", "push", "origin", "main", "--force"], check=True)

if __name__ == "__main__":
    main()
