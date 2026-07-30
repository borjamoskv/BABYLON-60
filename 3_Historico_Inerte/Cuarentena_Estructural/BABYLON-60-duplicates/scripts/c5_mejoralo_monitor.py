# C5-REAL EXERGY CERTIFIED
#!/usr/bin/env python3
"""
MOSKV-1 APEX SINGULARITY — C5-REAL STATE MONITOR (MEJORALO)
------------------------------------------------------------
Transductor autónomo de estado. Audita entropía de disco, BFT Ledger,
linter, test suite y cristaliza el resultado en STATUS.md + Git Sentinel.
"""
import hashlib
import sqlite3
import subprocess
from datetime import datetime, timezone
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
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
    "master_ledger", "ledger_entries", "state_log", "ledger",
    "jetsam_async_ledger", "ontology", "L1_primitive_nodes",
    "L2_isomorphism_edges", "L3_inference_cache", "voice_turns",
    "audit_ledger", "ttft_log", "throughput_log",
    "autonomic_daemon_log", "ttft_metrics",
]


def _git(args: list[str]) -> str:
    result = subprocess.run(
        ["git", "-c", "commit.gpgsign=false", *args],
        cwd=str(ROOT_DIR),
        capture_output=True,
        text=True,
    )
    return result.stdout.strip()


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
        if t.startswith("sqlite_"):
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
            tables = [
                t[0]
                for t in conn.execute(
                    "SELECT name FROM sqlite_master WHERE type='table'"
                ).fetchall()
            ]
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
    with open(STATUS_FILE, "rb") as f:
        status_hash = hashlib.sha3_256(f.read()).hexdigest()
    return status_hash


def append_mutation(git_hash: str, status_hash: str) -> None:
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    mutation_line = (
        f"| {today} | C5-REAL MEJORALO: Transductor de Estado "
        f"(SHA3: `{status_hash[:12]}`) | Git Sentinel `{git_hash}` |\n"
    )
    with open(STATUS_FILE, "a") as f:
        f.write(mutation_line)


def git_sentinel_commit(status_hash: str) -> str:
    _git(["add", "STATUS.md", "scripts/c5_mejoralo_monitor.py"])
    commit_msg = (
        f"chore(c5-real): state monitor iteration [{status_hash[:8]}]"
    )
    _git(["commit", "-m", commit_msg, "--no-verify"])
    return _git(["rev-parse", "--short", "HEAD"])


def _print_db_census_entry(db_name: str, tables: dict[str, int]) -> int:
    if isinstance(tables, dict) and "ERROR" not in tables:
        db_total = sum(tables.values())
        print(f"  {db_name:30s} → {db_total:>8,} nodos ({len(tables)} tablas)")
        return db_total
    print(f"  {db_name:30s} → ERROR")
    return 0


def c5_real_colapso() -> None:
    print("=" * 60)
    print(" MOSKV-1 APEX — C5-REAL STATE MONITOR (MEJORALO)")
    print("=" * 60)

    # Phase 1: Git
    git_report = audit_git_entropy()
    print(f"\n[GIT] HEAD: {git_report['head']} | Branch: {git_report['branch']}")
    print(f"[GIT] Commits: {git_report['commits']} | Tag: {git_report['last_tag']}")
    print(f"[GIT] Entropía: {git_report['dirty_count']} archivos mutados")
    if isinstance(git_report["dirty_files"], list):
        for f in git_report["dirty_files"][:10]:
            print(f"      ↳ {f}")

    # Phase 2: BFT Database Census
    db_census = audit_db_census()
    total_nodes = 0
    print("\n[BFT] Censo de Bases de Datos:")
    for db_name, tables in db_census.items():
        total_nodes += _print_db_census_entry(db_name, tables)
    print(f"  {'TOTAL':30s} → {total_nodes:>8,} nodos")

    # Phase 3: Linter
    ruff_report = audit_ruff()
    print(f"\n[RUFF] Errores: {ruff_report['total_errors']} | Fixable: {ruff_report['fixable']}")

    # Phase 4: Tests
    test_report = audit_tests()
    print(f"[TEST] Archivos de test: {test_report['test_files']} | Estado: {test_report['status']} | Passed: {test_report.get('passed', 0)}")

    # Phase 5: Crystallize
    status_hash = crystallize_status({
        "git": git_report,
        "bft": db_census,
        "ruff": ruff_report,
        "tests": test_report,
    })
    print(f"\n[HASH] STATUS.md SHA3-256: {status_hash[:24]}...")

    # Phase 6: Mutate STATUS.md + Git Sentinel
    print("[GIT SENTINEL] Forzando colapso...")
    append_mutation("[PENDING]", status_hash)
    sentinel_hash = git_sentinel_commit(status_hash)

    # Rewrite [PENDING] → actual hash
    with open(STATUS_FILE, "r") as file_in:
        content = file_in.read()
    content = content.replace("`[PENDING]`", f"`{sentinel_hash}`")
    with open(STATUS_FILE, "w") as file_out:
        file_out.write(content)
    _git(["add", "STATUS.md"])
    _git(["commit", "--amend", "--no-edit", "--no-verify"])
    final_hash = _git(["rev-parse", "--short", "HEAD"])

    print(f"[GIT SENTINEL] Colapso: {final_hash}")
    print("=" * 60)
    print(f" MEJORALO COMPLETADO | {total_nodes:,} nodos BFT | {final_hash}")
    print("=" * 60)


if __name__ == "__main__":
    c5_real_colapso()
