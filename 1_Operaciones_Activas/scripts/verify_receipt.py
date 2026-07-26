# C5-REAL EXERGY CERTIFIED
"""Zero-Trust Independent Verifier (verify_receipt.py)

Validates receipt integrity (self_hash), file hashes against live disk,
and absence of undeclared mutations.
"""

import argparse
import hashlib
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

def sha256_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()

def sha256_file(path: Path) -> str | None:
    if not path.exists():
        return None
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()

def git_toplevel() -> Path:
    r = subprocess.run(
        ["git", "rev-parse", "--show-toplevel"],
        capture_output=True,
        text=True,
    )
    if r.returncode != 0:
        raise RuntimeError("Not inside a git repository.")
    return Path(r.stdout.strip()).resolve()

def safe_resolve(repo_root: Path, rel: str) -> Path:
    target = (repo_root / rel).resolve()
    if repo_root not in target.parents and target != repo_root:
        raise ValueError(f"Path escapes repo: {rel!r}")
    return target

def main():
    ap = argparse.ArgumentParser(description="Verify receipt JSON integrity vs disk")
    ap.add_argument("receipt_path", help="Path to receipt JSON file")
    args = ap.parse_args()

    repo_root = git_toplevel()
    rp = Path(args.receipt_path).resolve()

    if not rp.exists():
        print(json.dumps({"PASS": False, "errors": ["RECEIPT_NOT_FOUND"]}))
        sys.exit(1)

    receipt = json.loads(rp.read_text(encoding="utf-8"))
    errors: list[str] = []
    checks: list[dict] = []

    # 1. Self-hash integrity
    stored_self_hash = receipt.get("self_hash")
    receipt_copy = {k: v for k, v in receipt.items() if k != "self_hash"}
    recomputed = sha256_bytes(json.dumps(receipt_copy, sort_keys=True).encode("utf-8"))
    ok_self = recomputed == stored_self_hash
    checks.append(
        {
            "check": "self_hash_integrity",
            "pass": ok_self,
            "stored": stored_self_hash,
            "recomputed": recomputed,
        }
    )
    if not ok_self:
        errors.append("SELF_HASH_MISMATCH: receipt tampered or corrupted")

    # 2. File hashes against live disk
    file_hashes = receipt.get("file_hashes", {})
    for rel, expected_hash in file_hashes.items():
        try:
            fp = safe_resolve(repo_root, rel)
        except ValueError as e:
            errors.append(str(e))
            checks.append({"check": f"file_hash:{rel}", "pass": False, "error": str(e)})
            continue

        actual_hash = sha256_file(fp)
        ok_file = actual_hash == expected_hash

        checks.append(
            {
                "check": f"file_hash:{rel}",
                "pass": ok_file,
                "expected": expected_hash,
                "actual": actual_hash,
            }
        )

        if not ok_file:
            if actual_hash is None:
                errors.append(f"MISSING_FILE: {rel}")
            else:
                errors.append(f"HASH_MISMATCH: {rel}")

    # 3. Undeclared mutations check
    undeclared = receipt.get("undeclared_mutations", [])
    ok_undeclared = len(undeclared) == 0
    checks.append(
        {
            "check": "undeclared_mutations",
            "pass": ok_undeclared,
            "undeclared": undeclared,
        }
    )
    if not ok_undeclared:
        errors.append(f"UNDECLARED_MUTATIONS: {undeclared}")

    result = {
        "receipt": (str(rp.relative_to(repo_root)) if repo_root in rp.parents else str(rp)),
        "PASS": len(errors) == 0,
        "errors": errors,
        "checks": checks,
        "verified_at_utc": datetime.now(timezone.utc).isoformat(),
    }

    print(json.dumps(result, indent=2, ensure_ascii=False))
    sys.exit(0 if result["PASS"] else 1)

if __name__ == "__main__":
    main()
