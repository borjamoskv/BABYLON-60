#!/usr/bin/env python3
# ============================================================================
# BABYLON-60 v4.0 Sovereign Hardened
# █ AUTOCOGNITION-Ω | STATE: C5-REAL | AESTHETIC: INDUSTRIAL_NOIR_2026
# ============================================================================
"""
MOSKV-1 APEX SINGULARITY — Causal-Determinist STATE MONITOR (EXERGY_OPTIMIZER)
------------------------------------------------------------
Transductor autónomo de estado. Audita entropía de disco, BFT Ledger,
linter, test suite y cristaliza el resultado en STATUS.md + Git Sentinel.
"""

import hashlib
import os
import re
import sqlite3
import stat
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import NamedTuple

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
STATUS_FILE = ROOT_DIR / "STATUS.md"

DB_TARGETS = [
    "master_ledger.db",
    "apex_cortex.db",
    "cortex.db",
    "cortex_memory.db",
    "cortex_ontology.db",
    "cortex_voice_ledger.db",
    "telemetry.db",
    "ultrathink_ledger.db",
]

LEDGER_TABLES = [
    "master_ledger",
    "ledger_entries",
    "state_log",
    "ledger",
    "jetsam_async_ledger",
    "ontology",
    "L1_primitive_nodes",
    "L2_isomorphism_edges",
    "L3_inference_cache",
    "voice_turns",
    "audit_ledger",
    "ttft_log",
    "throughput_log",
    "autonomic_daemon_log",
    "ttft_metrics",
]


def _git_bytes(args: list[str]) -> bytes:
    """Normal Git configuration/hooks apply; failures never become empty output."""
    selectors = {"GIT_DIR", "GIT_WORK_TREE", "GIT_INDEX_FILE", "GIT_COMMON_DIR", "GIT_NAMESPACE",
                 "GIT_OBJECT_DIRECTORY", "GIT_ALTERNATE_OBJECT_DIRECTORIES", "GIT_CONFIG_COUNT", "GIT_CONFIG_PARAMETERS"}
    if any(key in selectors or key.startswith(("GIT_CONFIG_KEY_", "GIT_CONFIG_VALUE_")) for key in os.environ):
        raise RuntimeError("Monitor rejects ambient repository/index/config selectors")
    return subprocess.run(["git", "--literal-pathspecs", *args], cwd=ROOT_DIR,
                          env={**os.environ, "GIT_OPTIONAL_LOCKS": "0"},
                          capture_output=True, text=False, check=True).stdout


def _git(args: list[str]) -> str:
    """Decode metadata for presentation; binary path/diff checks use _git_bytes."""
    return os.fsdecode(_git_bytes(args)).strip()


class _GitBaseline(NamedTuple):
    head: str
    branch: str
    index_file: Path
    index_bytes: bytes


def _index_image(path: Path) -> bytes:
    descriptor = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    with os.fdopen(descriptor, "rb") as stream:
        if not stat.S_ISREG(os.fstat(stream.fileno()).st_mode):
            raise RuntimeError("Monitor requires a regular Git index")
        return stream.read()


def _git_preflight() -> _GitBaseline:
    """Read-only preconditions for this monitor's single tracked output."""
    root = ROOT_DIR.absolute()
    if STATUS_FILE.absolute() != root/"STATUS.md" or any(ord(char) < 32 for char in str(root)):
        raise ValueError("Monitor output must be the workspace STATUS.md")
    top = Path(os.fsdecode(_git_bytes(["rev-parse", "--show-toplevel"]).rstrip(b"\n")))
    if not root.samefile(top):
        raise RuntimeError("Monitor must run at its exact repository root")
    head = _git(["rev-parse", "--verify", "HEAD^{commit}"])
    branch = _git(["symbolic-ref", "--quiet", "HEAD"])
    if not re.fullmatch(r"(?:[0-9a-f]{40}|[0-9a-f]{64})", head):
        raise RuntimeError("Monitor requires a valid existing commit")
    for marker in ("MERGE_HEAD", "CHERRY_PICK_HEAD", "REVERT_HEAD", "rebase-merge", "rebase-apply", "sequencer"):
        path = Path(os.fsdecode(_git_bytes(["rev-parse", "--git-path", marker]).rstrip(b"\n")))
        if os.path.lexists(path if path.is_absolute() else root/path):
            raise RuntimeError("Finish the current Git operation before monitoring")
    if _git(["config", "--get", "--default=false", "--bool", "core.sparseCheckout"]) != "false":
        raise RuntimeError("Monitor does not support sparse checkout")
    if _git_bytes(["rev-parse", "--shared-index-path"]).strip():
        raise RuntimeError("Monitor does not support split indexes")
    path = Path(os.fsdecode(_git_bytes(["rev-parse", "--git-path", "index"]).rstrip(b"\n")))
    index = path if path.is_absolute() else root/path
    image = _index_image(index)
    if any(row and not row.startswith(b"H ") for row in _git_bytes(["ls-files", "-v", "-z"]).split(b"\0")):
        raise RuntimeError("Monitor rejects special or unresolved index entries")
    if _git_bytes(["diff", "--cached", "--name-only", "--no-ext-diff", "--no-textconv",
                   "--ita-visible-in-index", "-z", head, "--"]):
        raise RuntimeError("Monitor requires an index with no prepared changes")
    entry = _git_bytes(["ls-files", "--stage", "-z", "--", "STATUS.md"]).rstrip(b"\0").split(b"\t")
    if (len(entry) != 2 or entry[1] != b"STATUS.md" or len(entry[0].split()) != 3
            or entry[0].split()[0] not in (b"100644", b"100755") or entry[0].split()[2] != b"0"):
        raise RuntimeError("STATUS.md must already be a tracked regular file")
    directory = os.open(root, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    try:
        descriptor = os.open("STATUS.md", os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=directory)
        try:
            if not stat.S_ISREG(os.fstat(descriptor).st_mode):
                raise RuntimeError("STATUS.md must be a regular file")
        finally:
            os.close(descriptor)
    finally:
        os.close(directory)
    if (image != _index_image(index) or head != _git(["rev-parse", "--verify", "HEAD"])
            or branch != _git(["symbolic-ref", "--quiet", "HEAD"])):
        raise RuntimeError("Git state changed during monitor preflight")
    return _GitBaseline(head, branch, index, image)


def audit_git_entropy() -> dict[str, str | int | list[str]]:
    porcelain = _git(["status", "--porcelain"])
    dirty_files = [line.strip() for line in porcelain.splitlines() if line.strip()]
    head = _git(["rev-parse", "--short", "HEAD"])
    branch = _git(["branch", "--show-current"])
    commit_count = int(_git(["rev-list", "--count", "HEAD"]) or "0")
    last_tag = _git(["tag", "--sort=-creatordate"]).splitlines()
    return {
        "head": head,
        "branch": branch,
        "commits": commit_count,
        "last_tag": last_tag[0] if last_tag else "NONE",
        "dirty_count": len(dirty_files),
        "dirty_files": dirty_files,
    }


def _get_table_counts(conn: sqlite3.Connection, tables: list[str]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for t in tables:
        if t.startswith("sqlite_") or not re.match(r"^[a-zA-Z0-9_]+$", t):
            continue
        try:
            counts[t] = int(conn.execute(f"SELECT count(*) FROM [{t}]").fetchone()[0])  # nosec B608
        except sqlite3.OperationalError:
            pass
    return counts


def audit_db_census() -> dict[str, dict[str, int]]:
    db_paths = [
        p
        for p in ROOT_DIR.rglob("*.db")
        if not any(part in ("venv", ".venv", ".git", "__pycache__") for part in p.parts)
    ]
    census: dict[str, dict[str, int]] = {}
    for db_path in sorted(db_paths):
        rel_name = str(db_path.relative_to(ROOT_DIR))
        try:
            conn = sqlite3.connect(str(db_path), timeout=2.0)
            conn.execute("PRAGMA journal_mode=WAL;")
            conn.execute("PRAGMA busy_timeout=5000;")
            tables = [t[0] for t in conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()]
            census[rel_name] = _get_table_counts(conn, tables)
            conn.close()
        except sqlite3.DatabaseError:
            census[rel_name] = {"ERROR": -1}
    return census


def _parse_int_token(parts: list[str], idx: int = 1) -> int | None:
    try:
        return int(parts[idx])
    except (IndexError, ValueError):
        return None


def audit_ruff() -> dict[str, int]:
    ruff_bin = ROOT_DIR / ".venv" / "bin" / "ruff"
    cmd = [str(ruff_bin) if ruff_bin.exists() else "ruff", "check", ".", "--statistics", "-q"]
    result = subprocess.run(
        cmd,
        cwd=str(ROOT_DIR),
        capture_output=True,
        text=True,
    )
    error_count = 0
    fixable_count = 0
    for line in result.stdout.splitlines():
        parts = line.strip().split()
        if parts and parts[0].isdigit():
            error_count += int(parts[0])
        if "fixable" in line.lower():
            val = _parse_int_token(parts, 0)
            if val is not None:
                fixable_count += val
    for line in result.stderr.splitlines():
        parts = line.split()
        if "Found" in line and "error" in line:
            val = _parse_int_token(parts, 1)
            if val is not None:
                error_count = val
        if "fixable" in line:
            val = _parse_int_token(parts, 1)
            if val is not None:
                fixable_count = val
    return {"total_errors": error_count, "fixable": fixable_count}


def _parse_passed_count_from_line(line: str) -> int | None:
    if "passed" not in line:
        return None
    parts = line.split()
    for i, p in enumerate(parts):
        if p.startswith("passed") or (i + 1 < len(parts) and parts[i + 1].startswith("passed")):
            try:
                return int(parts[i])
            except ValueError:
                return None
    return None


def audit_tests() -> dict[str, int | str]:
    tests_dir = ROOT_DIR / "tests"
    if not tests_dir.exists():
        return {"test_files": 0, "status": "NO_TESTS_DIR", "passed": 0}
    test_files = list(tests_dir.rglob("test_*.py"))
    pytest_bin = ROOT_DIR / ".venv" / "bin" / "pytest"
    cmd = [str(pytest_bin) if pytest_bin.exists() else "pytest", "-q", "--tb=no", "--disable-warnings"]
    result = subprocess.run(cmd, cwd=str(ROOT_DIR), capture_output=True, text=True)
    passed_count = 0
    for line in result.stdout.splitlines():
        cnt = _parse_passed_count_from_line(line)
        if cnt is not None:
            passed_count = cnt
    return {"test_files": len(test_files), "status": "PRESENT", "passed": passed_count}


def crystallize_status(report: dict[str, object]) -> str:
    if not STATUS_FILE.exists():
        STATUS_FILE.write_text("# BABYLON-60 Status Ledger\n\n| Date | Action | Git Sentinel |\n| --- | --- | --- |\n", encoding="utf-8")
    with open(STATUS_FILE, "rb") as f:
        status_hash = hashlib.sha3_256(f.read()).hexdigest()
    return status_hash


def append_mutation(git_hash: str, status_hash: str) -> None:
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    mutation_line = (
        f"| {today} | Causal-Determinist EXERGY_OPTIMIZER: Transductor de Estado "
        f"(SHA3: `{status_hash[:12]}`) | Git Sentinel `{git_hash}` |\n"
    )
    with open(STATUS_FILE, "a") as f:
        f.write(mutation_line)


def git_sentinel_commit(status_hash: str, *, baseline: _GitBaseline | None = None) -> str | None:
    """One STATUS commit, or explicit no-op; Git/config/hooks remain trusted.

    Whole-file selection is not a transaction against concurrent writers of
    STATUS.md. Postvalidation detects hook-created effects without undoing them.
    """
    if not isinstance(status_hash, str) or not re.fullmatch(r"[0-9a-f]{64}", status_hash):
        raise ValueError("A hexadecimal status digest is required")
    current = _git_preflight()
    if baseline is not None and baseline != current:
        raise RuntimeError("Git state changed during the monitor audit")
    dirty = _git_bytes(["diff", "--name-only", "--no-ext-diff", "--no-textconv", "-z", current.head, "--", "STATUS.md"])
    if _git_preflight() != current:
        raise RuntimeError("Git state changed before monitor commit")
    if not dirty:
        return None
    commit_msg = f"chore(Causal-Determinist): state monitor iteration [{status_hash[:8]}]"
    try:
        _git_bytes(["commit", "--only", "--message", commit_msg, "--", "STATUS.md"])
    except subprocess.CalledProcessError as error:
        if _git(["rev-parse", "--verify", "HEAD"]) != current.head or _index_image(current.index_file) != current.index_bytes:
            raise RuntimeError("Commit rejected and Git state changed; inspect it without automatic rollback") from error
        raise
    after = _git(["rev-parse", "--verify", "HEAD"])
    parents = _git(["rev-list", "--parents", "-n", "1", after]).split()
    changed = set(filter(None, _git_bytes(["diff-tree", "--no-commit-id", "--name-only", "-r", "-z",
                                           current.head, after, "--"]).split(b"\0")))
    if parents != [after, current.head] or changed != {b"STATUS.md"} or _git(["symbolic-ref", "--quiet", "HEAD"]) != current.branch:
        raise RuntimeError("Unexpected committed state; inspect history without automatic rollback")
    return after


def _print_db_census_entry(db_name: str, tables: dict[str, int]) -> int:
    if isinstance(tables, dict) and "ERROR" not in tables:
        db_total = sum(tables.values())
        print(f"  {db_name:30s} → {db_total:>8,} nodes ({len(tables)} tables)")
        return db_total
    print(f"  {db_name:30s} → ERROR")
    return 0


def c5_real_colapso() -> None:
    baseline = _git_preflight()
    print("=" * 60)
    print(" MOSKV-1 APEX — Causal-Determinist STATE MONITOR (EXERGY_OPTIMIZER)")
    print("=" * 60)

    # Phase 1: Git
    git_report = audit_git_entropy()
    print(f"\n[GIT] HEAD: {git_report['head']} | Branch: {git_report['branch']}")
    print(f"[GIT] Commits: {git_report['commits']} | Tag: {git_report['last_tag']}")
    print(f"[GIT] Entropy: {git_report['dirty_count']} mutated files")
    if isinstance(git_report["dirty_files"], list):
        for f in git_report["dirty_files"][:10]:
            print(f"      ↳ {f}")

    # Phase 2: BFT Database Census
    db_census = audit_db_census()
    total_nodes = 0
    print("\n[BFT] Database Census:")
    for db_name, tables in db_census.items():
        total_nodes += _print_db_census_entry(db_name, tables)
    print(f"  {'TOTAL':30s} → {total_nodes:>8,} nodes")

    # Phase 3: Linter
    ruff_report = audit_ruff()
    print(f"\n[RUFF] Errors: {ruff_report['total_errors']} | Fixable: {ruff_report['fixable']}")

    # Phase 4: Tests
    test_report = audit_tests()
    print(
        f"[TEST] Test Files: {test_report['test_files']} | State: {test_report['status']} | Passed: {test_report.get('passed', 0)}"
    )

    # Phase 5: Crystallize
    status_hash = crystallize_status(
        {
            "git": git_report,
            "bft": db_census,
            "ruff": ruff_report,
            "tests": test_report,
        }
    )
    print(f"\n[HASH] STATUS.md SHA3-256: {status_hash[:24]}...")

    # Phase 6: Mutate STATUS.md + Git Sentinel
    print("[GIT SENTINEL] Enforcing state collapse...")
    append_mutation("COMMIT_REFERENCE_IN_STDOUT", status_hash)
    final_hash = git_sentinel_commit(status_hash, baseline=baseline)
    if final_hash is None:
        print("[GIT SENTINEL] NO_CHANGE: no new commit was created")
        return

    print(f"[GIT SENTINEL] Collapse: {final_hash}")
    print("=" * 60)
    print(f" EXERGY_OPTIMIZER COMPLETE | {total_nodes:,} BFT nodes | {final_hash}")
    print("=" * 60)


if __name__ == "__main__":
    c5_real_colapso()
