"""Exercise metadata reconciliation using owned fixtures and intercepted writes.

No Git command is executed by fixture runs. The pinned-archive audit uses only
read-only cat-file against explicitly supplied revisions in the real checkout.
"""

from __future__ import annotations

import argparse
import contextlib
import copy
import hashlib
import importlib.util
import io
import json
import subprocess
import tempfile
from pathlib import Path
from unittest.mock import patch


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[4]
SOURCE = ROOT / "docs/security/evidence/swarm100-round3-20261028/reconcile_registry.py"
R3 = Path("docs/security/evidence/swarm100-round3-20261028")
BLOB = b"Historical source, not current execution.\nSecond audited line.\n"
REV = "a" * 40
ARCHIVE = "docs/security/evidence/owned/archive.txt"
WITHDRAWN = "examples/removed.py"
LIVE = "examples/live.py"
CID = "SW100-C0017"
SECOND = "SW100-C0018"
THIRD = "SW100-C0019"


def digest(value):
    return hashlib.sha256(value).hexdigest()


def load_module(source):
    spec = importlib.util.spec_from_file_location("independent_metadata_target", source)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def dump(repo, relative, value):
    target = repo / relative
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(value, indent=2) + "\n")


def proof():
    return {
        "path": WITHDRAWN,
        "git_revision": REV,
        "git_blob_sha256": digest(BLOB),
        "archive_path": ARCHIVE,
    }


def review(cid, path=LIVE):
    return {
        "candidate_id": cid,
        "path": path,
        "severity": "P2",
        "decision": "CONFIRMED_STATIC",
        "remediation_state": "OPEN",
        "runtime_executed": False,
        "rationale": "Synthetic metadata test; no product runtime.",
        "current_source_sha256": digest(BLOB),
        "source_checks": [
            {"path": path, "start_line": 1, "end_line": 2, "observation": "Historical source."}
        ],
        "evidence_paths": [ARCHIVE],
        "guards": [],
    }


def setup(repo):
    (repo / LIVE).parent.mkdir(parents=True)
    (repo / LIVE).write_bytes(BLOB)
    (repo / ARCHIVE).parent.mkdir(parents=True)
    (repo / ARCHIVE).write_bytes(BLOB)
    original = [
        {"candidate_id": f"SW100-C{index:04}", "path": WITHDRAWN if index == 17 else LIVE,
         "severity": "P2", "title": "Owned fixture"}
        for index in range(1, 599)
    ]
    historical = [review(item["candidate_id"], item["path"]) for item in original[16:]]
    root = copy.deepcopy(historical[0])
    root.update(source_state="REMOVED_PENDING_READJUDICATION", current_source_sha256=None,
                source_withdrawal=proof())
    root["source_checks"][0]["path"] = ARCHIVE
    data = {"original": original, "historical": historical, "root": [root], "additional": []}
    return data


def materialize(repo, data):
    original_path = Path("docs/security/evidence/swarm100-20261028/candidates.json")
    dump(repo, original_path, data["original"])
    dump(repo, R3 / "assignment-manifest.json", {
        "original_sha256": digest((repo / original_path).read_bytes()), "pending_count": 582,
        "shards": [{"id": 0, "candidate_ids": [i["candidate_id"] for i in data["historical"]]}],
    })
    dump(repo, "docs/security/evidence/swarm100-round2-20261028/candidate-status-updates.json", [
        {"candidate_id": item["candidate_id"], "status": "CONFIRMED"} for item in data["original"][:16]
    ])
    dump(repo, "docs/security/evidence/swarm100-remediation-20261028/candidate-status-updates.json", [])
    dump(repo, R3 / "root-adjudications.json", data["root"])
    dump(repo, R3 / "reviews/00.json", {"reviewer": "owned-fixture", "candidates": data["historical"]})
    dump(repo, R3 / "additional-findings.json", data["additional"])


def execute(module, repo, data, *, missing_blob=False):
    materialize(repo, data)
    writes = {}
    git_calls = []

    def git_read(args, **kwargs):
        expected = ["git", "--no-replace-objects", "-C", str(repo), "cat-file", "blob", f"{REV}:{WITHDRAWN}"]
        assert args == expected, f"Unexpected Git request: {args!r}"
        assert kwargs == {"stdin": subprocess.DEVNULL, "stderr": subprocess.PIPE}
        git_calls.append(args)
        if missing_blob:
            raise subprocess.CalledProcessError(128, args, stderr=b"missing owned blob")
        return BLOB

    def intercept_write(path, text, *args, **kwargs):
        rel = path.relative_to(repo)
        assert rel in {R3 / "registry.json", R3 / "registry-summary.json", R3 / "remediation-queue.json"}
        writes[str(rel)] = json.loads(text)
        return len(text)

    error = None
    with patch.object(module.subprocess, "check_output", git_read), patch.object(Path, "write_text", intercept_write), contextlib.redirect_stdout(io.StringIO()):
        try:
            module.reconcile(repo)
        except (AssertionError, OSError, KeyError, ValueError, TypeError, subprocess.CalledProcessError) as exc:
            error = type(exc).__name__ + ": " + str(exc)
    return {"accepted": error is None, "error": error, "writes": writes, "git_calls": len(git_calls)}


def withdraw_field(data, field, value):
    data["root"][0]["source_withdrawal"][field] = value


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, default=SOURCE)
    parser.add_argument("--real-archive-audit", action="store_true")
    args = parser.parse_args()
    source_before = digest(args.source.read_bytes())
    module = load_module(args.source)
    cases = []

    def case(name, mutate=lambda r, d: None, *, accept=False, missing_blob=False, inspect=None):
        with tempfile.TemporaryDirectory(prefix="sw100-metadata-review-") as temp:
            repo = Path(temp)
            data = setup(repo)
            mutate(repo, data)
            result = execute(module, repo, data, missing_blob=missing_blob)
            ok = result["accepted"] == accept
            if accept and result["accepted"] and inspect:
                ok = bool(inspect(result)) and ok
            if not accept:
                ok = ok and not result["writes"]
            record = {"control": name, "result": "PASS" if ok else "FAIL", "expected_accepted": accept,
                      "observed_accepted": result["accepted"], "error": result["error"],
                      "intercepted_write_count": len(result["writes"]), "stub_git_reads": result["git_calls"]}
            cases.append(record)
            print(json.dumps(record, sort_keys=True))

    def valid_output(result):
        records = result["writes"][str(R3 / "registry.json")]["records"]
        current = next(r["current"] for r in records if r["original"]["candidate_id"] == CID)
        queue = result["writes"][str(R3 / "remediation-queue.json")]
        queued = next(r for r in queue if r["candidate_id"] == CID)
        return current["remediation_state"] == "OPEN" and current["current_source_sha256"] is None and current["runtime_executed"] is False and queued["source_archive"] == ARCHIVE

    case("authorized_root_absence_remains_open_and_queued", accept=True, inspect=valid_output)
    case("invalid_revision_rejected", lambda r, d: withdraw_field(d, "git_revision", "HEAD"))
    case("missing_git_blob_rejected", missing_blob=True)
    case("declared_digest_mismatch_rejected", lambda r, d: withdraw_field(d, "git_blob_sha256", "0" * 64))
    case("archive_bytes_altered_rejected", lambda r, d: (r / ARCHIVE).write_bytes(BLOB + b"altered"))
    case("source_reappears_regular_rejected", lambda r, d: (r / WITHDRAWN).write_bytes(BLOB))
    case("source_reappears_directory_rejected", lambda r, d: (r / WITHDRAWN).mkdir())
    case("source_reappears_dangling_symlink_rejected", lambda r, d: (r / WITHDRAWN).symlink_to("missing"))
    case("fraudulent_fixed_rejected", lambda r, d: d["root"][0].update(remediation_state="FIXED"))
    case("runtime_true_rejected", lambda r, d: d["root"][0].update(runtime_executed=True))
    case("missing_withdrawal_rejected", lambda r, d: d["root"][0].pop("source_withdrawal"))
    case("absence_without_any_declaration_rejected", lambda r, d: d.update(root=[]))
    case("non_null_current_hash_rejected", lambda r, d: d["root"][0].update(current_source_sha256=digest(BLOB)))
    case("archive_not_evidence_rejected", lambda r, d: d["root"][0].update(evidence_paths=[]))
    case("archive_outside_evidence_rejected", lambda r, d: withdraw_field(d, "archive_path", "examples/live.py"))
    case("path_traversal_rejected", lambda r, d: withdraw_field(d, "archive_path", "docs/security/evidence/../archive.txt"))

    def archive_symlink(repo, data):
        (repo / ARCHIVE).unlink()
        (repo / ARCHIVE).symlink_to(repo / LIVE)

    case("archive_symlink_rejected", archive_symlink)

    def reviewer_spoof(repo, data):
        item = data["historical"][1]
        item.update(source_state="REMOVED_PENDING_READJUDICATION", current_source_sha256=None,
                    source_withdrawal=proof(), remediation_state="FIXED")

    case("non_root_reviewer_cannot_bypass_hash", reviewer_spoof)

    def additional_spoof(repo, data):
        item = review("EXTRA-OWNED")
        item.update(source_state="REMOVED_PENDING_READJUDICATION", current_source_sha256=None,
                    source_withdrawal=proof(), remediation_state="FIXED")
        data["additional"].append(item)

    case("additional_cannot_bypass_hash", additional_spoof)

    def duplicate_closure(repo, data):
        data["root"][0].update(decision="DUPLICATE", canonical_id=SECOND)
        data["historical"][1]["remediation_state"] = "FIXED"

    case("duplicate_cannot_auto_close_withdrawn_primary", duplicate_closure)

    def secondary(repo, data):
        item = copy.deepcopy(data["historical"][1])
        item["source_reference_withdrawals"] = [proof()]
        data["root"].append(item)

    case("valid_secondary_reference_preserves_live_primary", secondary, accept=True)

    def secondary_duplicate(repo, data):
        secondary(repo, data)
        data["root"][1].update(decision="DUPLICATE", canonical_id=THIRD)
        data["historical"][2]["remediation_state"] = "FIXED"

    case("duplicate_cannot_auto_close_withdrawn_reference", secondary_duplicate)

    def secondary_mismatch(repo, data):
        secondary(repo, data)
        data["root"][1]["source_reference_withdrawals"][0]["git_blob_sha256"] = "0" * 64

    case("secondary_inconsistent_proof_rejected", secondary_mismatch)
    case("current_check_cannot_resolve_missing_source", lambda r, d: d["root"][0]["source_checks"][0].update(path=WITHDRAWN))
    case("current_archive_range_bounds_enforced", lambda r, d: d["root"][0]["source_checks"][0].update(end_line=99))

    real_archive_checks = []
    if args.real_archive_audit:
        manifest = json.loads((HERE.parent / "withdrawn-source-observations.json").read_text())
        for item in manifest["sources"]:
            archive = ROOT / item["archive_path"]
            source = ROOT / item["path"]
            blob = subprocess.check_output(["git", "--no-replace-objects", "-C", str(ROOT), "cat-file", "blob", f"{item['git_revision']}:{item['path']}"], stdin=subprocess.DEVNULL, stderr=subprocess.PIPE)
            assert not source.exists() and not source.is_symlink()
            assert archive.is_file() and not archive.is_symlink()
            assert digest(blob) == digest(archive.read_bytes()) == item["git_blob_sha256"]
            real_archive_checks.append({"path": item["path"], "archive_path": item["archive_path"], "git_revision": item["git_revision"], "sha256": digest(blob), "result": "PASS"})
        print(json.dumps({"real_read_only_archive_checks": real_archive_checks}, sort_keys=True))
    assert digest(args.source.read_bytes()) == source_before, "Source changed during run"
    result = {"source_path": str(args.source), "source_sha256": source_before, "controls": len(cases),
              "passed": sum(c["result"] == "PASS" for c in cases), "failed": sum(c["result"] == "FAIL" for c in cases),
              "real_archive_checks": len(real_archive_checks), "canonical_writes": 0, "real_git_mutations": 0}
    print(json.dumps(result, sort_keys=True))
    return 1 if result["failed"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
