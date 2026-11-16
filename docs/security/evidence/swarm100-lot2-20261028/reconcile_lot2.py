"""Reconcile Lot2 code fixes and preserve the unsupported-consolidation limit."""

import ast
import copy
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).absolute().parents[4]
HERE = Path(__file__).absolute().parent
ROUND3 = HERE.parent / "swarm100-round3-20261028"


def read(path):
    return json.loads(path.read_text())


def write(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n")


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def source_check(path, name, observation):
    node = next(n for n in ast.parse((ROOT / path).read_text()).body
                if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)) and n.name == name)
    return dict(path=path, start_line=node.lineno, end_line=node.end_lineno, observation=observation)


def main():
    records = {r["original"]["candidate_id"]: r for r in read(ROUND3 / "registry.json")["records"]}
    previous = read(ROUND3 / "root-adjudications.json")
    snapshot = ROUND3 / "root-adjudications-before-lot2.json"
    if not snapshot.exists():
        write(snapshot, previous)
    review = read(HERE / "independent-review.json")
    for path, digest in review["source_sha256"].items():
        assert sha(ROOT / path) == digest, path
    evidence = [str((HERE / name).relative_to(ROOT)) for name in
                ["before-tests-confined.log", "consolidation-before.json", "related-tests.log", "independent-review.json"]]
    descriptions = {
        "SW100-C0018": ("ALREADY_FIXED", "FIXED", "run_auto_purge",
                        "Legacy find deletion of WAL/SHM and recursive cache removal are gone. Descriptor-relative cleanup removes only current-interpreter bytecode under cwd, preserves directories/SQLite and rejects symlink or replaced/uninspectable files. Temporary SQLite and cache regressions pass; legacy find was modeled strictly within the fixture, not invoked on the operator workspace."),
        "SW100-C0219": ("ALREADY_FIXED", "FIXED", "run_cohort_1",
                        "Cohort1 no longer scans WORKSPACE/CORTEX roots or deletes SQLite state. It selects cwd or an explicit workspace and removes only identified bytecode, using descriptor-relative O_NOFOLLOW operations and identity checks. Existing cohorts2-5/main are outside this correction and were not executed. Dry-run records zero actual removals."),
        "SW100-C0387": ("ALREADY_FIXED", "FIXED", "purge_anergy",
                        "Both purge copies preserve SQLite names/known headers and never classify or delete WAL/SHM as orphan caches. Files are processed individually under opened directory descriptors; no recursive directory removal. Live WAL, unusual locations, protected artifacts, symlinks and inspection failures pass controlled fixtures. This is not an atomic sandbox against hostile post-stat rename or arbitrary encrypted formats disguised as artifacts."),
        "SW100-C0563": ("ALREADY_FIXED", "FIXED", "purge_anergy",
                        "Global conversation maintenance and Path.home/sqlite3 access were removed from both workspace purge copies. Dry-run and ordinary mode leave two synthetic sessions active without resolving/opening the global path. The output reports global sessions NOT_CHECKED, with zero reset count."),
        "SW100-C0460": ("REPRODUCED", "MITIGATED", "autoconsolidate",
                        "Original code deleted three real temporary journal rows without a replacement. No durable load/merge/save contract or schema consumer was found in the scoped search. Consolidation and the legacy JournalEntry operations now raise CONSOLIDATION_UNSUPPORTED before path resolution or database access, preserving exact rows and unrelated writes. This is rejection-based mitigation, not implemented consolidation; functional durability/transaction guarantees remain unavailable."),
    }
    updates = []
    for cid, (decision, state, name, rationale) in descriptions.items():
        item = copy.deepcopy(records[cid]["current"])
        path = records[cid]["original"]["path"]
        item.update(decision=decision, remediation_state=state, current_source_sha256=sha(ROOT / path),
                    rationale=rationale, source_checks=[source_check(path, name, rationale)],
                    guards=["Temporary in-memory/filesystem fixtures only; no operator data or global purge executed.",
                            "Sizes are logical unlinked-file bytes, not measured physical space or energy."],
                    runtime_executed=True, runtime_scope="Real Python helpers and temporary SQLite; isolated legacy find interpreter for ITERA only.",
                    evidence_paths=evidence, resolution_type="CODE_AND_REGRESSIONS_VERIFIED")
        updates.append(item)
    for cid, canonical in [("SW100-C0562", "SW100-C0387"), ("SW100-C0388", "SW100-C0563")]:
        item = copy.deepcopy(records[cid]["current"])
        path = records[cid]["original"]["path"]
        rationale = f"Same defect as {canonical} in a separate byte-identical purge copy. Both implementations are patched and exercised by the shared regression suite; preserve this affected path and inherit FIXED."
        item.update(decision="DUPLICATE", canonical_id=canonical, remediation_state="FIXED",
                    current_source_sha256=sha(ROOT / path), rationale=rationale,
                    source_checks=[source_check(path, "purge_anergy", rationale)], runtime_executed=True,
                    runtime_scope="Both Python purge implementations; only temporary workspace/session fixtures.",
                    guards=["Separate physical copy retained; no operator global data read."], evidence_paths=evidence)
        updates.append(item)
    cid = "SW100-C0223"
    item = copy.deepcopy(records[cid]["current"])
    path = records[cid]["original"]["path"]
    item.update(current_source_sha256=sha(ROOT / path),
                rationale=item["rationale"].split(" Re-reviewed after Lot2:")[0] +
                " Re-reviewed after Lot2: cohort2 still deletes unprotected .lake directories across WORKSPACE; cohort1's change does not fix this separate behavior. No cohort2/main execution was performed.",
                source_checks=[source_check(path, "run_cohort_2", "The separate .lake traversal/removal remains unchanged and OPEN.")])
    item["evidence_paths"] = list(dict.fromkeys(item.get("evidence_paths", []) +
                                             [str((HERE / "independent-review.json").relative_to(ROOT))]))
    assert item["remediation_state"] == "OPEN"
    updates.append(item)
    write(HERE / "candidate-status-updates.json", updates)
    ids = {item["candidate_id"] for item in updates}
    write(ROUND3 / "root-adjudications.json", [item for item in previous if item["candidate_id"] not in ids] + updates)
    print("Four direct fixes, two fixed copies, one consolidation mitigation; unrelated cohort2 finding remains OPEN.")


if __name__ == "__main__":
    main()
