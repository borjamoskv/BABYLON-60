"""Validate reviewer 18 records and frozen excerpts; no product runtime imports."""
import hashlib
import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).absolute().parents[4]
BASE = ROOT / "docs/security/evidence/swarm100-round3-20261028"
assignment = json.loads((BASE / "assignments/18.json").read_text())
review = json.loads((BASE / "reviews/18.json").read_text())
evidence = json.loads((BASE / "18-source-evidence.json").read_text())
assert review["reviewer"] == "18"
rows = review["candidates"]
assert len(rows) == len(assignment) == 29
assert len({r["candidate_id"] for r in rows}) == 29
assert {r["candidate_id"] for r in rows} == {r["candidate_id"] for r in assignment}
required = {"candidate_id", "decision", "severity", "remediation_state", "path", "current_source_sha256", "rationale", "source_checks", "guards", "runtime_executed", "evidence_paths"}
allowed_decisions = {"CONFIRMED_STATIC", "REPRODUCED", "REJECTED", "DUPLICATE", "ALREADY_FIXED", "NEEDS_VALIDATION"}
allowed_states = {"OPEN", "FIXED", "MITIGATED", "NOT_APPLICABLE", "UNKNOWN"}
expected = {r["candidate_id"]: r for r in assignment}
for row in rows:
    assert required <= set(row), row["candidate_id"]
    assert row["path"] == expected[row["candidate_id"]]["path"]
    assert row["decision"] in allowed_decisions
    assert row["severity"] in {"P0", "P1", "P2", "P3"}
    assert row["remediation_state"] in allowed_states
    assert isinstance(row["runtime_executed"], bool)
    assert row["rationale"] and row["guards"] and row["source_checks"]
    assert row["current_source_sha256"] == hashlib.sha256((ROOT / row["path"]).read_bytes()).hexdigest()
    for check in row["source_checks"]:
        lines = (ROOT / check["path"]).read_text().splitlines()
        assert 1 <= check["start_line"] <= check["end_line"] <= len(lines), check
        assert check["observation"]
    assert row["evidence_paths"]
    for path in row["evidence_paths"]:
        assert (ROOT / path).is_file(), path
    if row["decision"] == "DUPLICATE":
        assert row.get("canonical_id")
for snapshot in evidence["source_snapshots"]:
    content = (ROOT / snapshot["path"]).read_bytes()
    assert snapshot["sha256"] == hashlib.sha256(content).hexdigest(), snapshot["path"]
    lines = content.decode("utf-8").splitlines()
    assert snapshot["excerpt"] == "\n".join(lines[snapshot["start_line"] - 1:snapshot["end_line"]])
result = {
    "reviewer": "18",
    "validation": "PASS",
    "records": len(rows),
    "source_snapshots": len(evidence["source_snapshots"]),
    "decisions": dict(Counter(r["decision"] for r in rows)),
    "remediation_states": dict(Counter(r["remediation_state"] for r in rows)),
    "severity_counts": dict(Counter(r["severity"] for r in rows)),
    "product_runtime_executed": False,
    "scope": "Assignment/schema/current hashes/line ranges/frozen excerpts; no product behavior certification. Workspace-wide gates are delegated to parent."
}
(BASE / "18-validation.json").write_text(json.dumps(result, indent=2) + "\n")
print(json.dumps(result, indent=2))
