"""Reconcile immutable SW100 evidence with individually reviewed current sources."""

import argparse
import hashlib
import json
import re
import subprocess
from collections import Counter
from pathlib import Path


def read(path):
    return json.loads(path.read_text())


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def reconcile(repo):
    evidence = repo / "docs/security/evidence"
    here = evidence / "swarm100-round3-20261028"
    original = read(evidence / "swarm100-20261028/candidates.json")
    originals = {item["candidate_id"]: item for item in original}
    assert len(originals) == len(original) == 598, "Original ID inventory changed"
    manifest = read(here / "assignment-manifest.json")
    assert sha(evidence / "swarm100-20261028/candidates.json") == manifest["original_sha256"]
    previous = read(evidence / "swarm100-round2-20261028/candidate-status-updates.json")
    previous_ids = {item["candidate_id"] for item in previous}
    expected = set(originals) - previous_ids
    assert len(expected) == manifest["pending_count"] == 582
    root_updates = read(here / "root-adjudications.json")
    overrides = {item["candidate_id"]: item for item in root_updates}
    assert len(overrides) == len(root_updates), "Duplicate root adjudication"
    withdrawn_sources = {}
    for item in root_updates:
        primary = item.get("source_withdrawal")
        references = item.get("source_reference_withdrawals", [])
        assert isinstance(references, list), item["candidate_id"]
        if item.get("source_state") == "REMOVED_PENDING_READJUDICATION":
            assert primary is not None, item["candidate_id"]
        if primary is not None:
            assert item.get("source_state") == "REMOVED_PENDING_READJUDICATION", item["candidate_id"]
            assert item.get("current_source_sha256") is None, item["candidate_id"]
            assert primary["path"] == item["path"], item["candidate_id"]
        if primary is not None or references:
            cid = item["candidate_id"]
            assert cid in originals and item["path"] == originals[cid]["path"], cid
            assert item["remediation_state"] == "OPEN" and item["runtime_executed"] is False, cid
            assert item["decision"] != "DUPLICATE", cid
        for proof in ([primary] if primary is not None else []) + references:
            path = Path(proof["path"])
            archive = Path(proof["archive_path"])
            assert not path.is_absolute() and ".." not in path.parts, item["candidate_id"]
            assert not archive.is_absolute() and ".." not in archive.parts, item["candidate_id"]
            assert archive.parts[:3] == ("docs", "security", "evidence"), item["candidate_id"]
            assert proof["archive_path"] in item["evidence_paths"], item["candidate_id"]
            assert not (repo / path).exists() and not (repo / path).is_symlink(), item["candidate_id"]
            assert (repo / archive).is_file() and not (repo / archive).is_symlink(), item["candidate_id"]
            assert re.fullmatch(r"[0-9a-f]{40}", proof["git_revision"]), item["candidate_id"]
            assert re.fullmatch(r"[0-9a-f]{64}", proof["git_blob_sha256"]), item["candidate_id"]
            blob = subprocess.check_output([
                "git", "--no-replace-objects", "-C", str(repo), "cat-file", "blob",
                f"{proof['git_revision']}:{proof['path']}",
            ], stdin=subprocess.DEVNULL, stderr=subprocess.PIPE)
            assert hashlib.sha256(blob).hexdigest() == proof["git_blob_sha256"], item["candidate_id"]
            assert sha(repo / archive) == proof["git_blob_sha256"], item["candidate_id"]
            if proof["path"] in withdrawn_sources:
                assert withdrawn_sources[proof["path"]] == proof, item["candidate_id"]
            withdrawn_sources[proof["path"]] = proof
    reviews = {}
    decisions = {"CONFIRMED_STATIC", "REPRODUCED", "REJECTED", "DUPLICATE", "ALREADY_FIXED", "NEEDS_VALIDATION"}
    states = {"OPEN", "FIXED", "MITIGATED", "NOT_APPLICABLE", "UNKNOWN"}

    def validate(item, current=True, original=True):
        cid = item["candidate_id"]
        if original:
            assert cid in originals, f"Unknown ID: {cid}"
            assert item["path"] == originals[cid]["path"], cid
        else:
            assert cid not in originals, f"Additional issue reuses original ID: {cid}"
        assert item["decision"] in decisions, cid
        assert item["remediation_state"] in states, cid
        assert item["severity"] in {"P1", "P2", "P3"}, cid
        assert isinstance(item["runtime_executed"], bool), cid
        assert item["rationale"] and item["source_checks"], cid
        if any(key in item for key in ("source_state", "source_withdrawal", "source_reference_withdrawals")):
            assert current and cid in overrides and item is overrides[cid], cid
            assert item["remediation_state"] == "OPEN" and item["runtime_executed"] is False, cid
            assert item["decision"] != "DUPLICATE", cid
            if item.get("source_state") == "REMOVED_PENDING_READJUDICATION":
                assert item.get("source_withdrawal") is not None, cid
        if item["decision"] == "REJECTED":
            assert item["remediation_state"] == "NOT_APPLICABLE", cid
        if item["decision"] == "ALREADY_FIXED":
            assert item["remediation_state"] in {"FIXED", "MITIGATED"}, cid
        if current and item.get("source_state") != "REMOVED_PENDING_READJUDICATION":
            assert sha(repo / item["path"]) == item["current_source_sha256"], f"Stale review: {cid}"
        for check in item["source_checks"]:
            path = repo / check["path"]
            if not current and check["path"] in withdrawn_sources:
                # History remains readable against the pinned Git archive;
                # current reviews must explicitly cite existing evidence.
                path = repo / withdrawn_sources[check["path"]]["archive_path"]
            assert path.is_file(), f"Missing checked source: {cid} {path}"
            assert 1 <= check["start_line"] <= check["end_line"], cid
            # Superseded ranges refer to the reviewed historical source. A valid
            # remediation may shorten a file; only current checks use its bounds.
            if current:
                assert check["end_line"] <= len(path.read_text().splitlines()), f"Invalid source range: {cid}"
            assert check["observation"], cid
        for path in item["evidence_paths"]:
            assert not Path(path).is_absolute() and ".." not in Path(path).parts, cid
            assert (repo / path).is_file(), f"Missing evidence: {cid} {path}"
        if item["decision"] == "DUPLICATE":
            assert item["canonical_id"] in originals and item["canonical_id"] != cid, cid
            if "independent_surface_state" in item:
                assert cid in overrides, cid
                assert item["independent_surface_state"] in {"OPEN", "MITIGATED"}, cid
                assert item["remediation_state"] == item["independent_surface_state"], cid
                assert item["path"] != originals[item["canonical_id"]]["path"], cid
                assert not (repo / item["path"]).samefile(repo / originals[item["canonical_id"]]["path"]), cid
                assert item["evidence_paths"] and item["source_checks"], cid

    for shard in manifest["shards"]:
        path = here / "reviews" / f"{shard['id']:02}.json"
        report = read(path)
        items = report["candidates"]
        ids = [item["candidate_id"] for item in items]
        assert len(ids) == len(set(ids)) and set(ids) == set(shard["candidate_ids"]), str(path)
        for item in items:
            cid = item["candidate_id"]
            assert cid not in reviews, cid
            validate(item, current=cid not in overrides)
            reviews[cid] = {**item, "review_file": str(path.relative_to(repo))}
    assert set(reviews) == expected, "Missing or unexpected candidate coverage"
    for item in root_updates:
        validate(item)
    additional = read(here / "additional-findings.json")
    assert len({item["candidate_id"] for item in additional}) == len(additional)
    for item in additional:
        validate(item, original=False)

    records = {cid: {"original": item, "history": []} for cid, item in originals.items()}
    for item in previous:
        cid = item["candidate_id"]
        if item["status"] == "DUPLICATE":
            review = {"candidate_id": cid, "decision": "DUPLICATE", "canonical_id": item["duplicate_of"],
                      "remediation_state": "UNKNOWN", "basis": "round2_duplicate_adjudication"}
        else:
            review = {"candidate_id": cid, "decision": "REPRODUCED", "remediation_state": "OPEN",
                      "basis": "round2_reproduction"}
        records[cid]["history"].append(item)
        records[cid]["current"] = review
    for item in read(evidence / "swarm100-remediation-20261028/candidate-status-updates.json"):
        cid = item["candidate_id"]
        # Historical remediation hashes describe their original source. A later
        # validated override supplies the current hash, ranges and evidence.
        if cid not in overrides:
            assert sha(repo / originals[cid]["path"]) == item["source_sha256"], f"Stale prior remediation: {cid}"
        records[cid]["history"].append(item)
        records[cid]["current"] = {
            "candidate_id": cid, "decision": "ALREADY_FIXED",
            "remediation_state": "MITIGATED" if cid == "SW100-C0364" else "FIXED",
            "basis": "round2_remediation", "evidence": "docs/security/evidence/swarm100-remediation-20261028/validation.json",
        }
    for cid, review in reviews.items():
        records[cid]["history"].append(review)
        records[cid]["current"] = review
    for cid, item in overrides.items():
        records[cid]["history"].append(item)
        records[cid]["current"] = item
    for cid, record in records.items():
        assert "current" in record, cid
        if record["current"]["decision"] == "DUPLICATE":
            target = record["current"]["canonical_id"]
            seen = {cid}
            while records[target]["current"]["decision"] == "DUPLICATE":
                assert target not in seen, "Duplicate cycle"
                seen.add(target)
                target = records[target]["current"]["canonical_id"]
            record["current"]["canonical_id"] = target
            # Equal findings in separate copies do not prove equal remediation.
            record["current"]["remediation_state"] = record["current"].get(
                "independent_surface_state", records[target]["current"]["remediation_state"]
            )
    current = [records[cid]["current"] for cid in sorted(expected)]
    unique_open = [record for record in records.values()
                   if record["current"]["remediation_state"] == "OPEN"
                   and record["current"]["decision"] != "DUPLICATE"]
    summary = {
        "original_candidates": len(records), "round3_assigned": len(expected), "round3_reviewed": len(reviews),
        "round3_decisions": dict(Counter(item["decision"] for item in current)),
        "round3_remediation_states": dict(Counter(item["remediation_state"] for item in current)),
        "all_decisions": dict(Counter(record["current"]["decision"] for record in records.values())),
        "all_remediation_states": dict(Counter(record["current"]["remediation_state"] for record in records.values())),
        "needs_validation_ids": sorted(cid for cid in records if records[cid]["current"]["decision"] == "NEEDS_VALIDATION"),
        "unique_open_findings": len(unique_open),
        "removed_sources_pending_readjudication": sorted(
            cid for cid, record in records.items()
            if record["current"].get("source_state") == "REMOVED_PENDING_READJUDICATION"
        ),
        "separately_unremediated_duplicate_surfaces": [
            cid for cid, record in records.items()
            if record["current"].get("independent_surface_state") in {"OPEN", "MITIGATED"}
        ],
        "unique_open_severity": dict(Counter(record["current"].get("severity", record["original"]["severity"])
                                             for record in unique_open)),
        "additional_findings_outside_original_inventory": len(additional),
        "additional_decisions": dict(Counter(item["decision"] for item in additional)),
        "scope": "Every assigned candidate reviewed; static confirmation is not correction or runtime certification.",
    }
    (here / "registry.json").write_text(json.dumps({"summary": summary, "records": list(records.values())}, ensure_ascii=False, indent=2) + "\n")
    (here / "registry-summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n")
    queue = []
    for record in records.values():
        item = record["current"]
        if (item["decision"] != "DUPLICATE" or "independent_surface_state" in item) and item["remediation_state"] in {"OPEN", "MITIGATED", "UNKNOWN"}:
            queue.append({"candidate_id": record["original"]["candidate_id"],
                          "severity": item.get("severity", record["original"]["severity"]),
                          "title": record["original"]["title"], "path": record["original"]["path"],
                          "decision": item["decision"], "remediation_state": item["remediation_state"],
                          "registry": "registry.json"})
            if item["decision"] == "DUPLICATE":
                queue[-1].update(canonical_id=item["canonical_id"], counting_unit="SEPARATE_DUPLICATE_SURFACE")
            if item.get("source_state") == "REMOVED_PENDING_READJUDICATION":
                queue[-1].update(source_state=item["source_state"], source_archive=item["source_withdrawal"]["archive_path"])
    for item in additional:
        if item["remediation_state"] in {"OPEN", "MITIGATED", "UNKNOWN"}:
            queue.append({key: item[key] for key in
                          ("candidate_id", "severity", "title", "path", "decision", "remediation_state")}
                         | {"registry": "additional-findings.json"})
    queue.sort(key=lambda item: (item["severity"], item["candidate_id"]))
    (here / "remediation-queue.json").write_text(json.dumps(queue, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", type=Path, default=Path(__file__).absolute().parents[4])
    reconcile(parser.parse_args().repo)
