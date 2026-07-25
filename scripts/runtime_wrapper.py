# C5-REAL EXERGY CERTIFIED
"""Zero-Trust Runtime Wrapper (runtime_wrapper.py)

Executes declared agent plans, captures stdout/stderr, measures pre/post git state,
detects undeclared file mutations, and emits an atomically self-hashed receipt JSON.
"""

import argparse
import hashlib
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

MAX_TIMEOUT = 300


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


def git_head() -> str:
    r = subprocess.run(
        ["git", "rev-parse", "HEAD"], capture_output=True, text=True
    )
    return r.stdout.strip() if r.returncode == 0 else "no-commits"


def git_diff_name_only() -> list[str]:
    r = subprocess.run(
        ["git", "diff", "--name-only"], capture_output=True, text=True
    )
    return sorted(set(x.strip() for x in r.stdout.splitlines() if x.strip()))


def safe_resolve(repo_root: Path, rel: str) -> Path:
    target = (repo_root / rel).resolve()
    if repo_root not in target.parents and target != repo_root:
        raise ValueError(f"Path escapes repo root: {rel!r}")
    return target


def action_write_file(repo_root: Path, a: dict) -> dict:
    rel = a["path"]
    mode = a.get("mode", "write")
    content = a.get("content", "")

    target = safe_resolve(repo_root, rel)
    target.parent.mkdir(parents=True, exist_ok=True)

    pre_hash = sha256_file(target)

    if mode == "append":
        with target.open("a", encoding="utf-8") as f:
            f.write(content)
    elif mode == "write":
        with target.open("w", encoding="utf-8") as f:
            f.write(content)
    else:
        raise ValueError(f"Unknown write mode: {mode!r}")

    post_hash = sha256_file(target)

    return {
        "type": "write_file",
        "path": rel,
        "mode": mode,
        "pre_hash": pre_hash,
        "post_hash": post_hash,
        "changed": pre_hash != post_hash,
    }


def action_run_python(repo_root: Path, a: dict) -> dict:
    script_rel = a["script"]
    script = safe_resolve(repo_root, script_rel)

    if not script.exists():
        raise FileNotFoundError(f"Script not found: {script_rel!r}")

    timeout = min(int(a.get("timeout", 60)), MAX_TIMEOUT)
    cmd = ["python3", str(script)]

    env = os.environ.copy()
    env["PYTHONPATH"] = str(repo_root)

    proc = subprocess.run(
        cmd,
        cwd=str(repo_root),
        env=env,
        capture_output=True,
        text=True,
        timeout=timeout,
    )

    result = {
        "type": "run_python_script",
        "script": script_rel,
        "returncode": proc.returncode,
        "stdout_sha256": sha256_bytes(proc.stdout.encode("utf-8", "replace")),
        "stderr_sha256": sha256_bytes(proc.stderr.encode("utf-8", "replace")),
        "stdout_preview": proc.stdout[:2000],
        "stderr_preview": proc.stderr[:2000],
    }

    if proc.returncode != 0:
        raise RuntimeError(
            f"Script failed rc={proc.returncode}: {script_rel}\nstderr: {proc.stderr[:500]}"
        )

    return result


def main():
    ap = argparse.ArgumentParser(description="Zero-Trust Runtime Wrapper")
    ap.add_argument("plan_path", help="Path to agent plan JSON")
    ap.add_argument("--outdir", default=".audit/receipts")
    args = ap.parse_args()

    repo_root = git_toplevel()
    plan_path = Path(args.plan_path).resolve()

    if not plan_path.exists():
        print(f"[ERROR] plan not found: {plan_path}", file=sys.stderr)
        sys.exit(1)

    plan = json.loads(plan_path.read_text(encoding="utf-8"))

    declared_targets = set(plan.get("declared_targets", []))
    actions = plan.get("actions", [])

    run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    receipts_dir = repo_root / args.outdir
    receipts_dir.mkdir(parents=True, exist_ok=True)

    head_before = git_head()
    diff_before = set(git_diff_name_only())

    dispatch = {
        "write_file": action_write_file,
        "run_python_script": action_run_python,
    }

    executed = []
    error = None

    for i, a in enumerate(actions):
        atype = a.get("type", "")
        handler = dispatch.get(atype)
        if handler is None:
            error = f"Unknown action type: {atype!r} at index {i}"
            break
        try:
            result = handler(repo_root, a)
            executed.append(result)
        except Exception as e:
            error = f"Action {i} ({atype!r}) failed: {e}"
            break

    head_after = git_head()
    diff_after = set(git_diff_name_only())

    new_worktree_changes = sorted(diff_after - diff_before)
    undeclared = sorted(set(new_worktree_changes) - declared_targets)

    file_hashes = {}
    for rel in new_worktree_changes:
        fp = safe_resolve(repo_root, rel)
        h = sha256_file(fp)
        if h:
            file_hashes[rel] = h

    try:
        rel_plan_path = str(plan_path.relative_to(repo_root))
    except ValueError:
        rel_plan_path = str(plan_path)

    receipt = {
        "version": "1.0",
        "run_id": run_id,
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "plan_path": rel_plan_path,
        "plan_sha256": sha256_file(plan_path),
        "git_head_before": head_before,
        "git_head_after": head_after,
        "declared_targets": sorted(declared_targets),
        "touched_files": new_worktree_changes,
        "undeclared_mutations": undeclared,
        "file_hashes": file_hashes,
        "actions": executed,
        "error": error,
        "PASS": error is None and len(undeclared) == 0,
    }

    receipt_bytes = json.dumps(receipt, sort_keys=True).encode("utf-8")
    receipt["self_hash"] = sha256_bytes(receipt_bytes)

    out_path = receipts_dir / f"run-{run_id}.json"
    out_path.write_text(
        json.dumps(receipt, indent=2, sort_keys=True), encoding="utf-8"
    )

    try:
        rel_out_path = str(out_path.relative_to(repo_root))
    except ValueError:
        rel_out_path = str(out_path)

    summary = {
        "receipt": rel_out_path,
        "PASS": receipt["PASS"],
        "undeclared": undeclared,
        "error": error,
        "self_hash": receipt["self_hash"],
    }

    print(json.dumps(summary, ensure_ascii=False))

    if error:
        sys.exit(1)
    if undeclared:
        sys.exit(2)
    sys.exit(0)


if __name__ == "__main__":
    main()
