"""
BABYLON60 IDE — Git Sentinel routes.
Read-only repo identity + lineage warnings.

Causal contract (STATUS.md · P0):
- Canonical lineage = LOCAL repo `Teorema-Robinson-Moskv`, branch `main`.
- The public fork `github.com/borjamoskv/BABYLON-60` is a DEAD publication
  fork (unrelated history, leaked keys). Any remote pointing at it — or any
  remote at all while P0 is open — is a lineage violation and must be flagged.
- This module NEVER mutates the repo. Delegated mutations (commit/push/merge/
  deploy) are queued by the frontend for the agent (Git Sentinel protocol).
"""

from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Any

from fastapi import APIRouter

router = APIRouter(prefix="/api/sentinel", tags=["sentinel"])

CANONICAL_REPO_NAME = "Teorema-Robinson-Moskv"
CANONICAL_BRANCH = "main"
DEAD_FORK_MARKER = "BABYLON-60"


def _get_project_root() -> Path:
    return Path(__file__).resolve().parent.parent.parent.parent


async def _git_async(root: Path, *args: str) -> str | None:
    """Run a read-only git command concurrently. Returns stdout or None on failure."""
    try:
        proc = await asyncio.create_subprocess_exec(
            "git", *args,
            cwd=str(root),
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, _ = await asyncio.wait_for(proc.communicate(), timeout=5.0)
    except (OSError, asyncio.TimeoutError):
        return None
    if proc.returncode != 0:
        return None
    return stdout.decode("utf-8").strip()


@router.get("/status")
async def sentinel_status() -> dict[str, Any]:
    """Repo identity, dirty state, remotes and lineage warnings (read-only)."""
    root = _get_project_root()
    repo_name = root.name
    is_git = (root / ".git").is_dir() or (root / ".git").is_file()

    branch = head = head_subject = head_time = commit_count_raw = porcelain = remotes_raw = None

    if is_git:
        results = await asyncio.gather(
            _git_async(root, "rev-parse", "--abbrev-ref", "HEAD"),
            _git_async(root, "log", "-1", "--format=%h%x00%cI%x00%s"),
            _git_async(root, "rev-list", "--count", "HEAD"),
            _git_async(root, "status", "--porcelain"),
            _git_async(root, "remote", "-v"),
        )
        branch, log_out, commit_count_raw, porcelain, remotes_raw = results
        
        if log_out:
            parts = log_out.split('\x00', 2)
            if len(parts) == 3:
                head, head_time, head_subject = parts

    dirty_files = len([ln for ln in porcelain.splitlines() if ln.strip()]) if porcelain else 0

    remotes: list[dict[str, str]] = []
    if remotes_raw:
        seen: set[str] = set()
        for line in remotes_raw.splitlines():
            parts = line.split()
            if len(parts) >= 2 and parts[0] not in seen:
                seen.add(parts[0])
                remotes.append({"name": parts[0], "url": parts[1]})

    # ── Lineage warnings (RECALCAR repo actual + intuir repo incorrecto) ──
    warnings: list[dict[str, str]] = []
    if not is_git:
        warnings.append({
            "level": "red",
            "msg": f"'{repo_name}' no es un repo git — sin Git Sentinel no hay ledger de mutaciones.",
        })
    if repo_name != CANONICAL_REPO_NAME:
        warnings.append({
            "level": "red",
            "msg": f"REPO INCORRECTO: estás en '{repo_name}', el linaje canónico es '{CANONICAL_REPO_NAME}'.",
        })
    if branch and branch != CANONICAL_BRANCH:
        warnings.append({
            "level": "amber",
            "msg": f"Rama '{branch}' ≠ '{CANONICAL_BRANCH}' (canónica). Verifica antes de mutar.",
        })
    for r in remotes:
        if DEAD_FORK_MARKER in r["url"]:
            warnings.append({
                "level": "red",
                "msg": f"Remoto '{r['name']}' apunta al fork muerto {DEAD_FORK_MARKER} (historia no relacionada, claves expuestas). Linaje NO canónico.",
            })
    if remotes and not any(DEAD_FORK_MARKER in r["url"] for r in remotes):
        warnings.append({
            "level": "amber",
            "msg": "Hay remoto configurado. P0 (STATUS.md) exige linaje local sin remoto hasta rotar claves.",
        })

    return {
        "repo_root": str(root),
        "repo_name": repo_name,
        "is_git": is_git,
        "branch": branch,
        "head": head,
        "head_subject": head_subject,
        "head_time": head_time,
        "commit_count": int(commit_count_raw) if commit_count_raw and commit_count_raw.isdigit() else None,
        "dirty_files": dirty_files,
        "remotes": remotes,
        "canonical": {
            "repo_name": CANONICAL_REPO_NAME,
            "branch": CANONICAL_BRANCH,
            "remote_policy": "none-until-P0-resolved",
        },
        "warnings": warnings,
    }


@router.get("/exergy")
def get_exergy_history() -> dict[str, Any]:
    """Retrieve exergy audit history from the SQLite ledger."""
    import sqlite3
    db_path = Path.home() / ".babylon60" / "exergy_agent_ledger.db"
    if not db_path.exists():
        return {"history": []}
    try:
        conn = sqlite3.connect(str(db_path), timeout=5.0)
        conn.execute("PRAGMA journal_mode=WAL;")
        cursor = conn.cursor()
        cursor.execute("SELECT timestamp, commit_hash, exergy_score, gradient, entropy, leverage, autoloop, bottleneck, verdict_yaml FROM ledger ORDER BY id DESC")
        rows = cursor.fetchall()
        conn.close()
        
        history = []
        for r in rows:
            history.append({
                "timestamp": r[0],
                "commit_hash": r[1],
                "exergy_score": r[2],
                "gradient": r[3],
                "entropy": r[4],
                "leverage": r[5],
                "autoloop": r[6],
                "bottleneck": r[7],
                "verdict_yaml": r[8]
            })
        return {"history": history}
    except sqlite3.Error as e:
        return {"error": str(e), "history": []}
