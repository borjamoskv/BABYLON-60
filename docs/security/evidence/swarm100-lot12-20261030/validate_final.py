"""Validate inventory deltas, frozen sources, document links and local gates."""
from __future__ import annotations
import hashlib
import json
import re
import subprocess
from collections import Counter
from pathlib import Path
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).absolute().parents[4]
HERE = Path(__file__).absolute().parent
ROUND3 = HERE.parent / "swarm100-round3-20261028"


def read(path):
    return json.loads(path.read_text())


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n")


def main():
    validation = read(HERE / "validation.json")
    review = read(HERE / "independent-review.json")
    assert all(sha(ROOT / p) == h for p, h in review["source_sha256"].items())
    assert all(sha(ROOT / p) == h for p, h in review["test_source_sha256"].items())
    run = read(HERE / "related-tests-result.json")
    assert run["exit_code"] == 0 and run["source_sha256_before"] == run["source_sha256_after"] == review["source_sha256"]
    counts = re.search(r"(\d+) passed, (\d+) skipped", (HERE / "related-tests.log").read_text())
    assert counts and tuple(map(int, counts.groups())) == (1387, 2)
    records = read(ROUND3 / "registry.json")["records"]
    current = {r["original"]["candidate_id"]: r["current"] for r in records}
    summary = read(ROUND3 / "registry-summary.json")
    assert len(current) == 598 and dict(Counter(r["remediation_state"] for r in current.values())) == summary["all_remediation_states"]
    selected = {r["candidate_id"] for r in read(HERE / "execution-contract.json")["selection"]}
    assert {cid for cid in selected if current[cid]["remediation_state"] == "MITIGATED"} == {"SW100-C0294", "SW100-C0378"}
    assert sum(current[cid]["remediation_state"] == "FIXED" for cid in selected) == 28
    assert current["SW100-C0461"]["remediation_state"] == "OPEN" and current["SW100-C0461"]["canonical_id"] == "SW100-C0103"
    baseline = read(HERE / "before-source-manifest.json")
    old = json.loads(subprocess.check_output(["git", "show", baseline["git_head"] + ":docs/security/evidence/swarm100-round3-20261028/registry.json"]))
    before = {r["original"]["candidate_id"]: r["current"] for r in old["records"]}
    transitions = [{"candidate_id": cid, "before": before[cid]["remediation_state"], "after": item["remediation_state"]}
                   for cid, item in current.items() if item["remediation_state"] != before[cid]["remediation_state"]]
    assert {r["candidate_id"] for r in transitions} == selected
    if not (HERE / "state-transitions-initial.json").exists():
        (HERE / "state-transitions-initial.json").write_bytes((HERE / "state-transitions.json").read_bytes())
    write(HERE / "state-transitions.json", transitions)
    next_plan = read(HERE.parent / "swarm100-lot13-plan-20261030/selection-30.json")
    next_ids = {r["candidate_id"] for r in next_plan}
    assert len(next_ids) == 30 and not (next_ids & selected)
    assert all(current[cid]["remediation_state"] == "OPEN" and current[cid]["decision"] != "DUPLICATE" for cid in next_ids)
    assert all(sha(ROOT / r["path"]) == r["source_sha256"] for r in next_plan)
    surface = read(HERE.parent / "swarm100-lot13-plan-20261030/duplicate-surface-obligations.json")
    assert len(surface) == 1 and surface[0]["candidate_id"] == "SW100-C0461" and sha(ROOT / surface[0]["path"]) == surface[0]["source_sha256"]
    paths = [ROOT / "docs/security" / name for name in ("REMEDIATION_SWARM100_LOTE12_2026-10-30.md", "PLAN_SWARM100_LOTE12_2026-10-29.md", "PLAN_SWARM100_LOTE13_2026-10-30.md", "AUDIT_SWARM100_ROUND3_2026-10-28.md")]
    links = 0
    for path in paths:
        for target in re.findall(r"(?<!!)\[[^\]]*\]\(([^)]+)\)", path.read_text()):
            parsed = urlsplit(target.strip().split(' "')[0].strip("<>"))
            if parsed.scheme or not parsed.path:
                continue
            assert (path.parent / unquote(parsed.path)).exists(), (path, target)
            links += 1
    commands = {
        "semantic-gate": ["python3", "scripts/c5_quality_gates/audit_semantic_contracts.py", "--workspace-only"],
        "budget-gate": ["python3", "scripts/c5_quality_gates/audit_token_budget.py", "--workspace-only", "--skip-ghost-listeners"],
        "topology-gate": ["python3", "scripts/guards/verify_active_topology.py"],
        "diff-check": ["git", "diff", "--check", "--", *review["source_sha256"], "tests/test_bounty_aeon_sealer.py", "tests/test_compliance_and_attestation.py", "tests/test_itera2_invariants.py", *[str(p.relative_to(ROOT)) for p in paths], "docs/security/evidence/swarm100-round3-20261028/reconcile_registry.py"],
    }
    for name, command in commands.items():
        result = subprocess.run(command, cwd=ROOT, capture_output=True)
        log = HERE / (name + ".log")
        log.write_bytes(result.stdout + result.stderr)
        validation["checks"][name] = {"command": command, "exit_code": result.returncode, "log": str(log.relative_to(ROOT)), "log_sha256": sha(log)}
        assert result.returncode == 0, (name, (result.stdout + result.stderr).decode(errors="replace"))
    validation["local_links_checked"] = links
    validation["inventory"] = {"state_changes": len(transitions), "original_ids": 598, "unique_open": summary["unique_open_findings"], "separate_duplicate_open": ["SW100-C0461"]}
    write(HERE / "validation.json", validation)
    metadata_path = HERE / "metadata-independent-review.json"
    metadata_approved = metadata_path.exists() and read(metadata_path).get("decision") == "APPROVED_WITH_EXPLICIT_SCOPE"
    write(HERE / "final-state.json", {"status": "VALIDATED" if metadata_approved else "CHECKS_VALIDATED_METADATA_REVIEW_PENDING", "reviewed": 30, "fixed": 28, "mitigated": 2,
        "tests_passed": 1387, "tests_skipped": 2, "source_sha256": review["source_sha256"],
        "registry_summary_sha256": sha(ROUND3 / "registry-summary.json"), "next_plan_unique": 30,
        "next_plan_sources": 24, "next_plan_applied": False, "local_links_checked": links,
        "metadata_review": "metadata-independent-review.json", "telemetry": "NOT_CHECKED workspace-only"})
    print(json.dumps({"validated": 30, "fixed": 28, "mitigated": 2, "state_transitions": len(transitions), "unique_open": summary["unique_open_findings"], "next_unique": 30, "next_applied": False, "local_links": links}))


if __name__ == "__main__":
    main()
