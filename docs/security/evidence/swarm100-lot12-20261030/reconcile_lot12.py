"""Apply reviewed Lote12 outcomes while preserving collateral states/history."""
from __future__ import annotations
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


def main():
    reviewed = read(HERE / "independent-review.json")
    assert reviewed["decision"] == "APPROVED_WITH_EXPLICIT_SCOPE"
    assert reviewed["open_actionable_findings"] == []
    for path, digest in reviewed["source_sha256"].items():
        assert sha(ROOT / path) == digest, path
    validation = read(HERE / "validation.json")
    assert all(v["exit_code"] == 0 for v in validation["checks"].values())
    assert read(HERE / "scope-check.json")["result"] == "PASS"
    selection = read(HERE / "execution-contract.json")["selection"]
    selected = {r["candidate_id"]: r for r in selection}
    assert set(reviewed["per_id"]) == set(selected) and len(selected) == 30
    records = {r["original"]["candidate_id"]: r for r in read(ROUND3 / "registry.json")["records"]}
    old = read(ROUND3 / "root-adjudications.json")
    for name in ("root-adjudications.json", "registry-summary.json"):
        snapshot = HERE / (name.removesuffix(".json") + "-before-lot12.json")
        if not snapshot.exists():
            write(snapshot, read(ROUND3 / name))
    updates = []
    common = [str((HERE / name).relative_to(ROOT)) for name in (
        "before-source-manifest.json", "execution-contract.json", "independent-review.json",
        "related-tests.log", "validation.json", "scope-check.json")]
    for cid, row in selected.items():
        decision = reviewed["per_id"][cid]
        item = copy.deepcopy(records[cid]["current"])
        item.update(candidate_id=cid, path=row["path"], severity=row["severity"], decision="ALREADY_FIXED",
            remediation_state=decision["state"], current_source_sha256=sha(ROOT / row["path"]),
            rationale=decision["rationale"], source_checks=decision["source_checks"],
            guards=decision["guards"] + ["Only this selected finding is resolved; neighbouring IDs retain their own dispositions.",
                "All observations use owned temporary fixtures and software keys; no operator data, protected hardware, external service or publication certified."],
            runtime_executed=True,
            runtime_scope="Confined Python/Node/SQLite/filesystem/concurrency or Lean-model fixtures as delimited by the independent per-ID review; no hardware or deployed effect.",
            evidence_paths=common + [decision["independent_review"]],
            resolution_type="CODE_AND_CONFINED_REGRESSIONS_VERIFIED" if decision["state"] == "FIXED" else "FAIL_CLOSED_CAPABILITY_MITIGATION")
        updates.append(item)
    write(HERE / "candidate-status-updates.json", updates)
    collateral = read(HERE / "collateral-source-refresh.json")["updates"]
    outside = read(HERE / "outside-scope-source-refresh.json")["updates"]
    duplicate = read(HERE / "duplicate-surface-refresh.json")["updates"]
    assert len(collateral) == 23 and len(outside) >= 6
    assert all(item["remediation_state"] == "OPEN" for item in outside)
    assert len(duplicate) == 1 and duplicate[0]["candidate_id"] == "SW100-C0461"
    assert duplicate[0]["remediation_state"] == duplicate[0]["independent_surface_state"] == "OPEN"
    all_updates = updates + collateral + outside + duplicate
    ids = [r["candidate_id"] for r in all_updates]
    assert len(ids) == len(set(ids)) == 30 + 23 + len(outside) + 1
    for item in collateral + outside:
        previous = records[item["candidate_id"]]["current"]
        original = records[item["candidate_id"]]["original"]
        for key in ("decision", "remediation_state"):
            assert item[key] == previous[key], (item["candidate_id"], key)
        assert item["severity"] == previous.get("severity", original["severity"])
        if item.get("source_state") == "REMOVED_PENDING_READJUDICATION":
            proof = item["source_withdrawal"]
            assert item["remediation_state"] == "OPEN" and item["runtime_executed"] is False
            assert proof["path"] == item["path"] and item["current_source_sha256"] is None
            assert not (ROOT / item["path"]).exists() and not (ROOT / item["path"]).is_symlink()
            assert sha(ROOT / proof["archive_path"]) == proof["git_blob_sha256"]
        else:
            assert sha(ROOT / item["path"]) == item["current_source_sha256"], item["candidate_id"]
    write(ROUND3 / "root-adjudications.json", [r for r in old if r["candidate_id"] not in set(ids)] + all_updates)
    write(HERE / "reconciliation-input.json", {"selected": len(updates), "collateral_state_preserved": len(collateral),
        "outside_prior_drift_state_preserved": len(outside), "root_updates": len(all_updates),
        "separate_duplicate_surface_retained_open": [r["candidate_id"] for r in duplicate],
        "historical_round2_hash_rule": "Historical hash is not compared with current bytes only when a later fully validated root override exists; historical record remains in history."})
    print(f"30 reviewed outcomes applied; {23 + len(outside)} collateral/prior-drift states preserved; run canonical reconciler next.")


if __name__ == "__main__":
    main()
