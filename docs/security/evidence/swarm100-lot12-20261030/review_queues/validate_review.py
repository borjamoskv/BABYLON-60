"""Repeat independent S3 checks and bind the verdict to current source bytes."""
from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).absolute().parents[5]
HERE = Path(__file__).absolute().parent
EVIDENCE = HERE.parent
SOURCES = [
    "01_KISH_ENGINE/babylon60/bft/master_ledger_queue.py",
    "01_KISH_ENGINE/babylon60/bft/bounty_pipeline_orchestrator.py",
    "01_KISH_ENGINE/babylon60/core/moskv_kernel.py",
    "02_EDIN_SWARMS/agents_archi/orchestrator/kda_dag_swarm.py",
    "01_KISH_ENGINE/services/email_inbound/worker.js",
]
TESTS = [
    "tests/test_swarm100_lot12_s3_regressions.py",
    "tests/test_swarm100_lot12_s3_worker.mjs",
    "tests/test_itera2_invariants.py",
]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    source_hashes = {path: sha(ROOT / path) for path in SOURCES}
    test_hashes = {path: sha(ROOT / path) for path in TESTS}
    author = json.loads((EVIDENCE / "s3/result.json").read_text())
    for row in author["ids"]:
        assert source_hashes[row["path"]] == row["source_sha256_after"], row["candidate_id"]
    relative = str(HERE.relative_to(ROOT))
    checks = {
        "python": [
            "uv", "run", "--locked", "--no-sync", "python",
            str((EVIDENCE / "run_confined_tests.py").relative_to(ROOT)),
            f"{relative}/test_independent_queues.py", TESTS[0], "-q", "-o", "addopts=--tb=short",
        ],
        "node-independent": ["node", "--experimental-vm-modules", f"{relative}/independent_worker.mjs"],
        "node-regressions": ["node", "--experimental-vm-modules", TESTS[1]],
        "ruff": [
            "uv", "run", "--locked", "--no-sync", "ruff", "check", *SOURCES[:4],
            TESTS[0], TESTS[2], f"{relative}/test_independent_queues.py", f"{relative}/validate_review.py",
        ],
        "mypy": [
            "uv", "run", "--locked", "--no-sync", "mypy", "--check-untyped-defs",
            "--follow-imports=silent", *SOURCES[:4],
        ],
    }
    results = {}
    for label, command in checks.items():
        process = subprocess.run(command, cwd=ROOT, capture_output=True, timeout=120)
        log = HERE / f"final-{label}.log"
        log.write_bytes(process.stdout + process.stderr)
        results[label] = {
            "command": command, "exit_code": process.returncode,
            "log": str(log.relative_to(ROOT)), "log_sha256": sha(log),
        }
        print(label, process.returncode, (process.stdout + process.stderr).decode(errors="replace")[-450:])
    assert all(sha(ROOT / path) == digest for path, digest in source_hashes.items())
    assert all(sha(ROOT / path) == digest for path, digest in test_hashes.items())
    assert all(check["exit_code"] == 0 for check in results.values()), results
    review = {
        "date": "2026-10-30",
        "reviewer": "/root/lot12_review_queues",
        "decision": "APPROVED_WITH_EXPLICIT_SCOPE",
        "open_actionable_findings": [],
        "source_sha256": source_hashes,
        "test_source_sha256": test_hashes,
        "independent_test_sha256": {
            str(path.relative_to(ROOT)): sha(path)
            for path in [HERE / "test_independent_queues.py", HERE / "independent_worker.mjs"]
        },
        "checks": results,
        "observations": {
            "python": "32 passed: 22 author regressions plus 10 independent controls.",
            "node": "6 independent Worker fixtures and 4 author fixtures passed.",
            "independent_counts": {
                "auxiliary_queue_public_admissions": "5 rounds x 900 accepted rows, exact IDs and BLOB bytes; two rounds warmup",
                "auxiliary_queue_failure": "700 exact accepted payloads retained after atomic first-batch rollback, no rows committed",
                "kernel_concurrency": "120 accepted IDs from four stale-snapshot instances, concurrent real SQLite transactions, every SHA3-256 chain link recomputed",
                "pipeline": "3 partial-cycle rejections at distinct domains plus successful 3-domain admission-only report",
                "dag": "5 rounds with actual competing scheduler blocked during sibling cleanup; lock released only after task termination",
                "cancellation": "Both independent red cases now green: cancelled active claim processing propagates, concurrent initialize/close cannot reopen admission",
            },
        },
        "independent_findings_resolved": [
            {
                "candidate_id": "SW100-C0208",
                "before_log": f"{relative}/cancel-before.log",
                "regression": "test_kernel_cancelled_processing_is_not_reported_as_normal_completion",
                "resolution": "CancelledError is re-raised; an interrupted claim is not represented as a normally completed state-loop.",
            },
            {
                "candidate_id": "SW100-C0434",
                "before_log": f"{relative}/initialize-close-before.log",
                "regression": "test_auxiliary_close_during_initialize_cannot_reopen_admission",
                "resolution": "Queue owns a shielded initialization task; closure waits for it and closes its connection without reopening admission.",
            },
        ],
        "ids": {
            "SW100-C0434": "FIXED: successful shutdown drains accepted auxiliary transactions; failure is raised and uncommitted batch/backlog retained in RAM. Lifecycle interleaving revalidated.",
            "SW100-C0358": "FIXED: all three domain branches reject false enqueue and propagate writer failure; successful report says QUEUED_NOT_CONFIRMED.",
            "SW100-C0208": "FIXED: committed tip/logical tick selected inside BEGIN IMMEDIATE; no absent-ID replay success; cancellation is observable.",
            "SW100-C0509": "FIXED: failed/cancelled execution cancels and awaits siblings under exclusion, including repeated caller cancellation.",
            "SW100-C0422": "FIXED: exhausted HTTP/transport attempts reject; valid 2xx delivery resolves without extra attempts.",
        },
        "limits": [
            "No operator database, HOME, hardware, attestation, real network/mail or Git mutation was used. SQLite and lock files belong to temporary fixtures.",
            "Auxiliary queue admission and bounty enqueue are not durability acknowledgements. Failed transaction retention is in RAM; ambiguous COMMIT requires inspection before retry, not assumed rollback.",
            "Kernel tracking is admission only. Stop drains; forced cancellation propagates but does not provide durable job recovery or per-claim acknowledgement. Caller must observe the loop and reconcile tracking IDs.",
            "Tests exercise cooperative local SQLite/async tasks, not physical power failure, hostile writers or cross-event-loop/thread sharing.",
            "DAG cleanup can retain the lock indefinitely for cancellation-resistant tasks; no forced termination or redesign of the inherited lock identity policy is claimed.",
            "Node VM executes real Worker control flow with injected MIME/platform boundaries. It demonstrates rejection/resolution, not SMTP redelivery, deployment or platform retry guarantees.",
        ],
    }
    (HERE / "independent-review.json").write_text(json.dumps(review, indent=2) + "\n")
    print("Independent S3 review approved against unchanged final source/test hashes.")


if __name__ == "__main__":
    main()
