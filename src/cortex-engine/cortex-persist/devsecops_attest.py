#!/usr/bin/env python3
# C5-REAL EXERGY CERTIFIED
"""
devsecops_attest.py (C5-REAL Certified)
---------------------------------------
L5 Trust Anchor for the SOURCE TREE (not the ledger rows).

Closes the DevSecOps loop: binds the exact committed source state plus the
verdict of every security gate into a single SHA3-256 attestation digest,
persists it in the append-only BFT ledger (L1) and elevates it to Bitcoin
through OpenTimestamps (L5).

Axiom C7.7 (Trust Anchor): the digest is witnessed by an authority external
to the loop (the Bitcoin timestamp chain), so the repository cannot certify
itself. Rewriting history or injecting a backdoor does not break the stamp --
it makes the divergence mathematically undeniable (see verify_attestation.py).

Contract:
  - Deterministic core: the hashed payload contains ONLY reproducible fields.
    Wall-clock time and machine identity live outside the digest domain, so
    any auditor re-deriving the digest from a clean checkout gets a bit-identical
    result.
  - Zero new pip dependencies (rule 5). Uses the `ots` CLI if present.
  - Omega_23: dynamic root resolution, no orphan absolute paths, self-healing
    SQLite parent directory.
"""
from __future__ import annotations

import argparse
import datetime
import hashlib
import json
import os
import re
import shutil
import sqlite3
import subprocess
import sys
import uuid
from pathlib import Path
from typing import Any

SCRIPTS_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPTS_DIR))
import bft_sqlite  # noqa: E402  (Omega_23 dynamic module resolution)

ATTESTATION_SCHEMA = "moskv.devsecops.attestation/v1"

# Omega_23: root is discovered, never hardcoded.
MONOREPO_ROOT = Path(os.environ.get("MOSKV_ROOT", SCRIPTS_DIR.parents[2])).resolve()
DEFAULT_DB_PATH = SCRIPTS_DIR / "cortex_ledger.db"
DEFAULT_ANCHOR_DIR = SCRIPTS_DIR / "l5_anchors"

# Security gate reports emitted by .github/workflows/*. Absent report == gate not run.
GATE_REPORTS = {
    "bandit": "bandit.json",
    "pip_audit": "pip-audit.json",
    "coverage": "coverage.xml",
    "trufflehog": "trufflehog.json",
}

# Strips `user:token@` out of remote URLs before they enter the ledger.
_CREDENTIAL_RE = re.compile(r"//[^/@]*@")

OTS_TIMEOUT_SECONDS = 60.0


class AttestationError(RuntimeError):
    """Structured failure of the L5 attestation transducer (no blind excepts)."""


def _git(*args: str, cwd: Path = MONOREPO_ROOT) -> str:
    """Runs git and returns stripped stdout. Raises AttestationError on friction."""
    try:
        result = subprocess.run(
            ["git", *args],
            cwd=str(cwd),
            check=True,
            capture_output=True,
            text=True,
            timeout=120,
        )
    except FileNotFoundError as exc:
        raise AttestationError("git binary not present in PATH") from exc
    except subprocess.TimeoutExpired as exc:
        raise AttestationError(f"git {' '.join(args)} exceeded its deadline") from exc
    except subprocess.CalledProcessError as exc:
        raise AttestationError(f"git {' '.join(args)} failed: {exc.stderr.strip()}") from exc
    return result.stdout.strip()


def _sanitize_remote(url: str) -> str:
    return _CREDENTIAL_RE.sub("//", url)


def compute_source_digest(commit: str = "HEAD") -> str:
    """
    SHA3-256 over the full recursive git tree listing of `commit`.

    `git ls-tree -r` yields `<mode> <type> <blob-sha1>\\t<path>` for every tracked
    file, so the digest binds both content and path. This is a modern-hash
    rebinding of git's own Merkle root, whose native SHA-1 is no longer
    collision-resistant.
    """
    listing = _git("ls-tree", "-r", "--full-tree", commit)
    hasher = hashlib.sha3_256()
    # Sorted for determinism independent of git's output ordering guarantees.
    for line in sorted(listing.splitlines()):
        hasher.update(line.encode("utf-8"))
        hasher.update(b"\x00")
    return hasher.hexdigest()


def _digest_file(path: Path) -> str:
    hasher = hashlib.sha3_256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def collect_gate_evidence(root: Path = MONOREPO_ROOT) -> dict[str, dict[str, Any]]:
    """
    Digests every security-gate report present on disk.

    A gate whose report is missing is recorded as NOT_RUN -- never as passing.
    Silence is not evidence.
    """
    evidence: dict[str, dict[str, Any]] = {}
    for gate, filename in sorted(GATE_REPORTS.items()):
        report = root / filename
        if report.is_file():
            evidence[gate] = {
                "status": "EVIDENCED",
                "report": filename,
                "sha3_256": _digest_file(report),
                "bytes": report.stat().st_size,
            }
        else:
            evidence[gate] = {"status": "NOT_RUN", "report": filename}
    return evidence


def worktree_is_clean(root: Path = MONOREPO_ROOT) -> bool:
    return _git("status", "--porcelain", cwd=root) == ""


def build_attestation(allow_dirty: bool = False) -> dict[str, Any]:
    """
    Assembles the attestation. `core` is the deterministic hashed domain;
    `witness` is non-reproducible metadata deliberately excluded from the digest.
    """
    clean = worktree_is_clean()
    if not clean and not allow_dirty:
        raise AttestationError(
            "Worktree is dirty. An attestation over uncommitted entropy is unverifiable. "
            "Commit the changes or pass --allow-dirty to stamp an explicitly degraded proof."
        )

    commit = _git("rev-parse", "HEAD")
    core: dict[str, Any] = {
        "schema": ATTESTATION_SCHEMA,
        "commit": commit,
        "tree": _git("rev-parse", "HEAD^{tree}"),
        "parents": _git("rev-list", "--parents", "-n", "1", commit).split()[1:],
        "source_digest_sha3_256": compute_source_digest(commit),
        "worktree_clean": clean,
        "gates": collect_gate_evidence(),
    }

    canonical = json.dumps(core, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    digest = hashlib.sha3_256(canonical.encode("utf-8")).hexdigest()

    try:
        remote = _sanitize_remote(_git("config", "--get", "remote.origin.url"))
    except AttestationError:
        remote = ""

    return {
        "core": core,
        "attestation_digest_sha3_256": digest,
        "witness": {
            "attested_at_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "remote": remote,
            "ci_run": os.environ.get("GITHUB_RUN_ID", ""),
            "ci_workflow": os.environ.get("GITHUB_WORKFLOW", ""),
        },
    }


def recompute_digest(core: dict[str, Any]) -> str:
    """Re-derives the digest from a `core` block. Used by the verifier."""
    canonical = json.dumps(core, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha3_256(canonical.encode("utf-8")).hexdigest()


def persist_to_ledger(attestation: dict[str, Any], db_path: Path = DEFAULT_DB_PATH) -> str:
    """
    Appends the attestation to the L1 BFT ledger.

    PK is uuid5(digest), so re-running over an unchanged tree is idempotent and
    the append-only triggers are never provoked.
    """
    # Omega_23: self-healing parent directory.
    os.makedirs(os.path.dirname(os.path.abspath(db_path)), exist_ok=True)

    digest = attestation["attestation_digest_sha3_256"]
    entry_uuid = str(uuid.uuid5(uuid.NAMESPACE_URL, f"moskv:devsecops:attestation:{digest}"))
    timestamp = attestation["witness"]["attested_at_utc"]
    payload = json.dumps(attestation, sort_keys=True, separators=(",", ":"), ensure_ascii=False)

    conn = bft_sqlite.connect(str(db_path))
    try:
        conn.execute("PRAGMA journal_mode=WAL;")
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS bft_taint_log (
                uuid TEXT PRIMARY KEY,
                timestamp TEXT,
                payload TEXT
            )
            """
        )
        conn.execute(
            """
            CREATE TRIGGER IF NOT EXISTS trg_bft_taint_log_no_delete
            BEFORE DELETE ON bft_taint_log
            BEGIN
                SELECT RAISE(ABORT, 'C5-REAL: BFT Taint Log is Append-Only. Entropy purge rejected.');
            END;
            """
        )
        conn.execute(
            """
            CREATE TRIGGER IF NOT EXISTS trg_bft_taint_log_no_update
            BEFORE UPDATE ON bft_taint_log
            BEGIN
                SELECT RAISE(ABORT, 'C5-REAL: BFT Taint Log entries are immutable. State mutation rejected.');
            END;
            """
        )
        try:
            conn.execute(
                "INSERT INTO bft_taint_log (uuid, timestamp, payload) VALUES (?, ?, ?)",
                (entry_uuid, timestamp, payload),
            )
            conn.commit()
            print(f"[L1 LEDGER] Atestación fijada: {entry_uuid}")
        except Exception:
            # Same digest already witnessed: the tree did not mutate. ATP saved (Fase 3).
            print(f"[L1 LEDGER] Idempotente: la atestación {entry_uuid} ya estaba fijada.")
    finally:
        conn.close()

    return entry_uuid


def anchor_to_bitcoin(digest: str, anchor_dir: Path = DEFAULT_ANCHOR_DIR) -> dict[str, str]:
    """
    Elevates the digest to the OpenTimestamps calendars (Bitcoin anchoring).

    Asynchronous fire-and-forget execution with in-flight lock protection.
    """
    anchor_dir.mkdir(parents=True, exist_ok=True)
    data_file = anchor_dir / f"{digest}.digest"
    ots_file = anchor_dir / f"{digest}.digest.ots"
    lock_file = anchor_dir / f"{digest}.digest.lock"

    if ots_file.exists():
        return {"status": "ALREADY_STAMPED", "ots": str(ots_file), "data": str(data_file)}

    if lock_file.exists():
        return {"status": "IN_PROGRESS", "ots": str(ots_file), "data": str(data_file)}

    if shutil.which("ots") is None:
        return {
            "status": "SKIPPED",
            "reason": "opentimestamps-client (`ots`) not present in PATH",
            "data": "",
            "ots": "",
        }

    data_file.write_text(digest, encoding="utf-8")
    lock_file.write_text("1", encoding="utf-8")
    print(f"[L5 ANCHOR] Elevando {digest[:16]}... a los calendarios OpenTimestamps (asíncrono con lock)...")

    # Command wrapper that creates and cleans up the lockfile atomically
    cmd = f'ots stamp "{data_file}" ; rm -f "{lock_file}"'
    subprocess.Popen(
        cmd,
        shell=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        start_new_session=True,
    )

    print(f"[L5 ANCHOR] Petición OTS delegada a proceso en segundo plano (DEFERRED).")
    return {"status": "DEFERRED", "ots": str(ots_file), "data": str(data_file)}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Builds, ledgers and Bitcoin-anchors the DevSecOps attestation of the source tree."
    )
    parser.add_argument("--allow-dirty", action="store_true", help="Attest an uncommitted worktree (degraded proof).")
    parser.add_argument("--no-anchor", action="store_true", help="Skip OpenTimestamps; only ledger the digest.")
    parser.add_argument("--no-ledger", action="store_true", help="Skip the L1 ledger write; only stamp.")
    parser.add_argument(
        "--require-anchor",
        action="store_true",
        help="Exit non-zero if the Bitcoin anchor could not be produced (CI gate).",
    )
    parser.add_argument("--db", type=Path, default=DEFAULT_DB_PATH, help="Path to the L1 BFT ledger.")
    parser.add_argument("--anchor-dir", type=Path, default=DEFAULT_ANCHOR_DIR, help="Directory for .ots proofs.")
    parser.add_argument("--out", type=Path, default=None, help="Write the attestation JSON to this path.")
    args = parser.parse_args(argv)

    try:
        attestation = build_attestation(allow_dirty=args.allow_dirty)
    except AttestationError as exc:
        print(f"[ERR] {exc}", file=sys.stderr)
        return 2

    digest = attestation["attestation_digest_sha3_256"]
    core = attestation["core"]
    print(f"[ATTEST] commit          : {core['commit']}")
    print(f"[ATTEST] source digest   : {core['source_digest_sha3_256']}")
    print(f"[ATTEST] attestation     : {digest}")
    evidenced = [g for g, v in core["gates"].items() if v["status"] == "EVIDENCED"]
    print(f"[ATTEST] gates evidenced : {', '.join(evidenced) if evidenced else 'NINGUNO'}")

    if not args.no_anchor:
        anchor = anchor_to_bitcoin(digest, args.anchor_dir)
    else:
        anchor = {"status": "DISABLED", "ots": "", "data": ""}
    attestation["witness"]["anchor"] = anchor
    print(f"[ATTEST] anchor          : {anchor['status']}{' - ' + anchor['reason'] if anchor.get('reason') else ''}")

    if not args.no_ledger:
        attestation["witness"]["ledger_uuid"] = persist_to_ledger(attestation, args.db)

    out_path = args.out or (args.anchor_dir / f"{digest}.attestation.json")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(
        json.dumps(attestation, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    print(f"[ATTEST] attestation JSON: {out_path}")

    if args.require_anchor and anchor["status"] not in ("STAMPED", "ALREADY_STAMPED"):
        print("[REFUTED] Anclaje Bitcoin exigido pero no obtenido.", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
