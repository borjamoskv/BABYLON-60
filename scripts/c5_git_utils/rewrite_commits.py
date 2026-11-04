#!/usr/bin/env python3
# ============================================================================
# BABYLON-60 v4.0 Sovereign Hardened
# █ AUTOCOGNITION-Ω | STATE: C5-REAL | AESTHETIC: INDUSTRIAL_NOIR_2026
# ============================================================================
"""Rewrite commit history to enforce Conventional Commits and BFT metadata.

The script performs:
1. Require main and a clean working tree; never reset to a remote ref.
2. Create and verify a private recovery bundle before any rewrite.
3. Run `git filter-repo` with a custom message‑callback that:
   - Infers a Conventional type (feat/fix/refactor/chore) from the original message.
   - Prepends the type to the subject.
   - Appends `Causal‑Taint: borjamoskv` and `Lamport‑T: <timestamp>`.
4. After rewriting, iterate over the new commits and record a `commit_rewrite` event in the Cortex Ledger.
5. Run the exergy optimizer; abort if score < 950.
6. Force‑push the cleaned history to `origin/main`.
"""

import subprocess
import sys
import uuid
import os
import stat
from pathlib import Path
from babylon60.bft.ledger_actor import BFTLedgerActor, LedgerEvent
from babylon60.utils.hygiene import run_exergy_optimizer


def _git_output(*arguments: str) -> str:
    return subprocess.check_output(["git", *arguments]).decode("utf-8").strip()


def _require_clean_main(*, allow_callback: bool = False) -> str:
    if _git_output("symbolic-ref", "--short", "HEAD") != "main":
        raise RuntimeError("History rewrite requires main; no checkout was attempted")
    # Keep raw bytes: porcelain paths may contain non-UTF-8 names.
    status = subprocess.check_output(["git", "status", "--porcelain=v1", "-z", "--untracked-files=all"])
    entries = [entry for entry in status.split(b"\0") if entry]
    if allow_callback:
        entries = [entry for entry in entries if entry != b"?? msg_callback.py"]
    if entries:
        raise RuntimeError("Uncommitted or untracked work must be preserved before rewriting")
    return _git_output("rev-parse", "HEAD")


def _verify_backup(backup: Path, expected_head: str) -> None:
    subprocess.run(["git", "bundle", "verify", str(backup)], check=True, capture_output=True)
    heads = _git_output("bundle", "list-heads", str(backup)).splitlines()
    if f"{expected_head} HEAD" not in heads:
        raise RuntimeError("Recovery bundle does not contain the original HEAD")


def _ensure_main() -> Path:
    """Preserve every ref and local commit before admitting a clean rewrite."""
    head = _require_clean_main()
    common = Path(_git_output("rev-parse", "--git-common-dir")).absolute()
    common_fd = os.open(common, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    try:
        try:
            os.mkdir("rewrite-backups", 0o700, dir_fd=common_fd)
            os.fsync(common_fd)
        except FileExistsError:
            pass
        backup_fd = os.open("rewrite-backups", os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW,
                            dir_fd=common_fd)
        try:
            info = os.fstat(backup_fd)
            if info.st_uid != os.getuid() or stat.S_IMODE(info.st_mode) & 0o077:
                raise PermissionError("Recovery directory must be private and user-owned")
            name = uuid.uuid4().hex
            os.mkdir(name, 0o700, dir_fd=backup_fd)
            os.fsync(backup_fd)
        finally:
            os.close(backup_fd)
    finally:
        os.close(common_fd)
    backup = common / "rewrite-backups" / name / "history.bundle"
    subprocess.run(["git", "bundle", "create", str(backup), "--all", "HEAD"], check=True)
    fd = os.open(backup, os.O_RDONLY | os.O_NOFOLLOW)
    try:
        os.fchmod(fd, 0o600)
        os.fsync(fd)
    finally:
        os.close(fd)
    parent_fd = os.open(backup.parent, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    try:
        os.fsync(parent_fd)
    finally:
        os.close(parent_fd)
    _verify_backup(backup, head)
    if _require_clean_main() != head:
        raise RuntimeError("HEAD changed during backup; rewrite rejected")
    print(f"Verified history recovery bundle: {backup}")
    return backup


def _create_callback() -> None:
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
    with open("msg_callback.py", "x") as f:
        f.write(callback)


def _run_filter_repo(backup: Path) -> None:
    # The callback is an exclusively created tool artifact. Recheck every
    # other tracked/staged/untracked change immediately before dispatch.
    _verify_backup(backup, _require_clean_main(allow_callback=True))
    subprocess.run(
        [
            "git",
            "filter-repo",
            "--force",
            "--message-callback",
            "msg_callback.message_callback",
        ],
        check=True,
    )


async def _record_events() -> None:
    actor = BFTLedgerActor(db_path=Path("cortex.db"))
    await actor.start()
    try:
        out = subprocess.check_output(["git", "log", "--pretty=%H %P"], text=True)
        for line in out.splitlines():
            new_sha, parents = line.split(" ", 1)
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
    finally:
        await actor.stop()


def main() -> None:
    backup = _ensure_main()
    _create_callback()
    _run_filter_repo(backup)
    import asyncio

    asyncio.run(_record_events())
    if not run_exergy_optimizer():
        sys.exit("Exergy score too low – aborting rewrite")
    subprocess.run(["git", "push", "origin", "main", "--force"], check=True)


if __name__ == "__main__":
    main()
