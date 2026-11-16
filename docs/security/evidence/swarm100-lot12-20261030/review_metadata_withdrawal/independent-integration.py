"""Validate proposed real metadata in memory; intercept every canonical write."""

from __future__ import annotations

import contextlib
import copy
import hashlib
import importlib.util
import io
import json
import subprocess
from pathlib import Path
from unittest.mock import patch

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[4]
LOT = HERE.parent
R3 = LOT.parent / "swarm100-round3-20261028"


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    canonical_path = R3 / "reconcile_registry.py"
    driver_path = LOT / "reconcile_lot12.py"
    canonical = load(canonical_path, "independent_canonical_reconciler")
    driver = load(driver_path, "independent_lot12_driver")
    approved_writes = {
        R3 / "root-adjudications.json", R3 / "registry.json", R3 / "registry-summary.json",
        R3 / "remediation-queue.json", LOT / "candidate-status-updates.json",
        LOT / "root-adjudications-before-lot12.json", LOT / "registry-summary-before-lot12.json",
        LOT / "reconciliation-input.json",
    }
    before = {str(p.relative_to(ROOT)): sha(p) for p in approved_writes if p.is_file()}
    source_before = {str(p.relative_to(ROOT)): sha(p) for p in (canonical_path, driver_path)}
    writes = {}
    saved_read = canonical.read
    saved_git = subprocess.check_output
    git_calls = []

    def intercept_write(path, text, *args, **kwargs):
        assert path in approved_writes, f"Unexpected metadata write: {path}"
        writes[path] = json.loads(text)
        return len(text)

    def overlay_read(path):
        return copy.deepcopy(writes[path]) if path in writes else saved_read(path)

    def readonly_git(args, **kwargs):
        assert args[:6] == ["git", "--no-replace-objects", "-C", str(ROOT), "cat-file", "blob"]
        assert len(args) == 7
        git_calls.append(args[6])
        return saved_git(args, **kwargs)

    with patch.object(Path, "write_text", intercept_write), patch.object(canonical, "read", overlay_read), patch.object(canonical.subprocess, "check_output", readonly_git), contextlib.redirect_stdout(io.StringIO()):
        driver.main()
        canonical.reconcile(ROOT)

    registry = writes[R3 / "registry.json"]
    records = {r["original"]["candidate_id"]: r for r in registry["records"]}
    queue = {r["candidate_id"]: r for r in writes[R3 / "remediation-queue.json"]}
    inspected = {}
    for cid in ("SW100-C0516", "SW100-C0517", "SW100-C0445"):
        item = records[cid]["current"]
        assert item["remediation_state"] == "OPEN" and item["runtime_executed"] is False
        assert queue[cid]["remediation_state"] == "OPEN"
        if cid != "SW100-C0445":
            assert item["source_state"] == "REMOVED_PENDING_READJUDICATION"
            assert item["current_source_sha256"] is None
        else:
            assert sha(ROOT / item["path"]) == item["current_source_sha256"]
            assert len(item["source_reference_withdrawals"]) == 1
        inspected[cid] = {
            "path": item["path"], "state": item["remediation_state"], "decision": item["decision"],
            "runtime_executed": item["runtime_executed"], "current_source_sha256": item["current_source_sha256"],
            "source_state": item.get("source_state"), "source_checks": item["source_checks"],
        }
    assert before == {str(p.relative_to(ROOT)): sha(p) for p in approved_writes if p.is_file()}
    assert source_before == {str(p.relative_to(ROOT)): sha(p) for p in (canonical_path, driver_path)}
    print(json.dumps({"result": "PASS", "source_sha256": source_before, "canonical_writes": 0,
                      "intercepted_writes": sorted(str(p.relative_to(ROOT)) for p in writes),
                      "readonly_git_blobs": git_calls, "per_id": inspected,
                      "summary": registry["summary"]}, indent=2))


if __name__ == "__main__":
    main()
