"""Read-only metadata review, including actual reconciler rejection controls.

All canonical writes from the reconciler are intercepted in memory. Negative
controls additionally fail if it even attempts a canonical write.
"""

from __future__ import annotations

import ast
import contextlib
import copy
import hashlib
import importlib.util
import io
import json
from collections import Counter
from pathlib import Path
from unittest.mock import patch

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
ROUND3 = HERE.parent / "swarm100-round3-20261028"
PLAN13 = HERE.parent / "swarm100-lot13-plan-20261030"
RECONCILER = ROUND3 / "reconcile_registry.py"
LOG = HERE / "metadata-independent-review.log"
OUT = HERE / "metadata-independent-review.json"


def read(path):
    return json.loads(path.read_text())


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def checked_ranges(item):
    assert item["source_checks"], item["candidate_id"]
    result = []
    for check in item["source_checks"]:
        path = ROOT / check["path"]
        lines = path.read_text().splitlines(keepends=True)
        assert 1 <= check["start_line"] <= check["end_line"] <= len(lines), item["candidate_id"]
        assert check["observation"]
        excerpt = "".join(lines[check["start_line"] - 1:check["end_line"]])
        assert excerpt.strip(), item["candidate_id"]
        result.append({**check, "excerpt_sha256": hashlib.sha256(excerpt.encode()).hexdigest()})
    for path in item["evidence_paths"]:
        assert not Path(path).is_absolute() and ".." not in Path(path).parts
        assert (ROOT / path).is_file(), path
    assert sha(ROOT / item["path"]) == item["current_source_sha256"], item["candidate_id"]
    return result


def control_reconciler():
    spec = importlib.util.spec_from_file_location("lot12_metadata_reconciler", RECONCILER)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    actual_read = module.read
    expected_outputs = {ROUND3 / x for x in ("registry.json", "registry-summary.json", "remediation-queue.json")}
    original_roots = actual_read(ROUND3 / "root-adjudications.json")
    nodes = list(ast.walk(ast.parse(RECONCILER.read_text())))

    def subscript_key(node):
        return node.slice.value if isinstance(node, ast.Subscript) and isinstance(node.slice, ast.Constant) else None

    state_line = next(n.lineno for n in nodes if isinstance(n, ast.Assert)
                      and isinstance(n.test, ast.Compare)
                      and subscript_key(n.test.left) == "independent_surface_state"
                      and isinstance(n.test.ops[0], ast.In))
    evidence_line = next(n.lineno for n in nodes if isinstance(n, ast.Assert)
                         and isinstance(n.test, ast.BoolOp)
                         and [subscript_key(v) for v in n.test.values] == ["evidence_paths", "source_checks"])
    hash_line = next(n.lineno for n in nodes if isinstance(n, ast.Assert)
                     and isinstance(n.test, ast.Compare)
                     and subscript_key(n.test.comparators[0]) == "current_source_sha256")
    results = []

    def run(name, mutate=None, rejected_at=None):
        roots = copy.deepcopy(original_roots)
        if mutate:
            mutate(roots)
        attempted = []
        captured = {}

        def read_with_override(path):
            return copy.deepcopy(roots) if path == ROUND3 / "root-adjudications.json" else actual_read(path)

        def guarded_write(path, text, *args, **kwargs):
            attempted.append(str(path.relative_to(ROOT)))
            assert rejected_at is None, (name, "canonical write attempted")
            assert path in expected_outputs, path
            captured[path.name] = json.loads(text)
            return len(text)

        output = io.StringIO()
        error_line = None
        error_function = None
        with patch.object(module, "read", side_effect=read_with_override):
            with patch.object(Path, "write_text", autospec=True, side_effect=guarded_write):
                with contextlib.redirect_stdout(output):
                    try:
                        module.reconcile(ROOT)
                    except AssertionError as exc:
                        if rejected_at is None:
                            raise
                        trace = exc.__traceback__
                        while trace.tb_next is not None:
                            trace = trace.tb_next
                        error_line = trace.tb_lineno
                        error_function = trace.tb_frame.f_code.co_name
        if rejected_at is not None:
            assert error_line == rejected_at and error_function == "validate", (name, error_line, error_function)
            assert attempted == [], (name, attempted)
        else:
            assert set(captured) == {p.name for p in expected_outputs}
        result = {"case": name, "passed": True, "canonical_write_attempts": attempted,
                  "writes_reached_filesystem": 0, "rejected_at_line": error_line,
                  "rejected_in_function": error_function}
        results.append(result)
        return captured

    positive = run("actual_current_metadata_reconciles_in_memory")
    for filename, payload in positive.items():
        assert payload == actual_read(ROUND3 / filename), filename
    assert positive["registry-summary.json"]["separately_unremediated_duplicate_surfaces"] == ["SW100-C0461"]

    def change_surface(roots, **changes):
        next(x for x in roots if x["candidate_id"] == "SW100-C0461").update(changes)

    run("duplicate_fixed_independent_state_rejects_before_any_write",
        lambda roots: change_surface(roots, remediation_state="FIXED", independent_surface_state="FIXED"), state_line)
    run("duplicate_empty_evidence_rejects_before_any_write",
        lambda roots: change_surface(roots, evidence_paths=[]), evidence_line)
    run("duplicate_stale_source_hash_rejects_before_any_write",
        lambda roots: change_surface(roots, current_source_sha256="0" * 64), hash_line)

    def stale_prior_fix(roots):
        next(x for x in roots if x["candidate_id"] == "SW100-C0177")["current_source_sha256"] = "0" * 64

    run("historical_fix_override_still_requires_current_valid_hash", stale_prior_fix, hash_line)

    def remove_surface_field(roots):
        next(x for x in roots if x["candidate_id"] == "SW100-C0461").pop("independent_surface_state")

    ordinary = run("ordinary_duplicate_inheritance_remains_unchanged", remove_surface_field)
    record = next(x for x in ordinary["registry.json"]["records"] if x["original"]["candidate_id"] == "SW100-C0461")
    assert record["current"]["remediation_state"] == "FIXED"
    assert ordinary["registry-summary.json"]["unique_open_findings"] == 503
    assert ordinary["registry-summary.json"]["separately_unremediated_duplicate_surfaces"] == []
    return results


def main():
    canonical_paths = [ROUND3 / n for n in ("registry.json", "registry-summary.json", "remediation-queue.json", "root-adjudications.json", "reconcile_registry.py")]
    before = {str(p.relative_to(ROOT)): sha(p) for p in canonical_paths}
    selection = read(HERE.parent / "swarm100-lot12-plan-20261029/selection-30.json")
    selected = {x["candidate_id"]: x for x in selection}
    updates = read(HERE / "candidate-status-updates.json")
    review = read(HERE / "independent-review.json")
    registry = read(ROUND3 / "registry.json")
    records = {r["original"]["candidate_id"]: r for r in registry["records"]}
    summary = read(ROUND3 / "registry-summary.json")
    queue = read(ROUND3 / "remediation-queue.json")
    originals = read(HERE.parent / "swarm100-20261028/candidates.json")
    assert len(records) == len(originals) == 598
    assert {x["candidate_id"]: x for x in originals} == {cid: r["original"] for cid, r in records.items()}
    assert len(updates) == len(selected) == 30 and {u["candidate_id"] for u in updates} == set(selected) == set(review["per_id"])
    assert review["decision"] == "APPROVED_WITH_EXPLICIT_SCOPE" and review["open_actionable_findings"] == []
    for group in review["reviews"]:
        assert sha(ROOT / group["path"]) == group["sha256"]
        document = read(ROOT / group["path"])
        assert document["decision"] == group["decision"] == "APPROVED_WITH_EXPLICIT_SCOPE"
        assert document["open_actionable_findings"] == []
    for path, digest in {**review["source_sha256"], **review["test_source_sha256"]}.items():
        assert sha(ROOT / path) == digest, path
    checked = {}
    for item in updates:
        cid = item["candidate_id"]
        per_id = review["per_id"][cid]
        assert item["path"] == selected[cid]["path"]
        assert item["severity"] == selected[cid]["severity"]
        assert item["remediation_state"] == per_id["state"]
        assert item["rationale"] == per_id["rationale"]
        assert item["source_checks"] == per_id["source_checks"]
        assert set(per_id["guards"]) <= set(item["guards"])
        assert item["current_source_sha256"] == review["source_sha256"][item["path"]]
        assert sha(ROOT / per_id["independent_review"]) == per_id["independent_review_sha256"]
        nested = read(ROOT / per_id["independent_review"])["per_id"][cid]
        state = nested.get("state", nested.get("recommended_state", nested.get("recommendation")))
        assert state == per_id["state"], cid
        assert nested.get("rationale", nested.get("observed")) == per_id["rationale"], cid
        if "source_checks" in nested:
            assert nested["source_checks"] == per_id["source_checks"], cid
        assert per_id["independent_review"] in item["evidence_paths"]
        assert records[cid]["current"] == item
        checked[cid] = checked_ranges(item)
    assert Counter(x["remediation_state"] for x in updates) == {"FIXED": 28, "MITIGATED": 2}
    assert {x["candidate_id"] for x in updates if x["remediation_state"] == "MITIGATED"} == {"SW100-C0294", "SW100-C0378"}
    inherited_count = 0
    for name in ("collateral-source-refresh.json", "outside-scope-source-refresh.json"):
        document = read(HERE / name)
        for item in document["updates"]:
            cid = item["candidate_id"]
            assert records[cid]["current"] == item, cid
            checked[cid] = checked_ranges(item)
            inherited_count += 1
    assert inherited_count == 34
    outside_inputs = read(HERE / "outside-scope-source-refresh.json")["updates"]
    assert len(outside_inputs) == 11
    assert all(item["remediation_state"] == "OPEN" and item["severity"] == "P2" for item in outside_inputs)
    baseline = read(HERE / "collateral-source-refresh-validation.json")["baseline_records"]
    for cid, record in baseline.items():
        current = records[cid]["current"]
        old = record["current"]
        assert current["decision"] == old["decision"] and current["remediation_state"] == old["remediation_state"]
        assert current["severity"] == old.get("severity", record["original"]["severity"])
    for old in read(HERE / "outside-scope-source-refresh-validation.json")["checks"]:
        current = records[old["candidate_id"]]["current"]
        assert (current["decision"], current["remediation_state"], current["severity"]) == (old["decision_preserved"], old["state_preserved"], old["severity_preserved"])
    duplicate = read(HERE / "duplicate-surface-refresh.json")["updates"][0]
    assert records["SW100-C0461"]["current"] == duplicate
    checked["SW100-C0461"] = checked_ranges(duplicate)
    assert duplicate["decision"] == "DUPLICATE" and duplicate["canonical_id"] == "SW100-C0103"
    assert duplicate["remediation_state"] == duplicate["independent_surface_state"] == "OPEN"
    assert not (ROOT / duplicate["path"]).samefile(ROOT / records["SW100-C0103"]["original"]["path"])
    assert sha(ROOT / duplicate["path"]) == records["SW100-C0461"]["original"]["source_sha256"]
    states = Counter(r["current"]["remediation_state"] for r in records.values())
    assert states == summary["all_remediation_states"] == {"OPEN": 509, "FIXED": 79, "MITIGATED": 6, "NOT_APPLICABLE": 4}
    assert dict(Counter(r["current"]["decision"] for r in records.values())) == summary["all_decisions"]
    unique_open = [r for r in records.values() if r["current"]["remediation_state"] == "OPEN" and r["current"]["decision"] != "DUPLICATE"]
    assert len(unique_open) == summary["unique_open_findings"] == 503
    assert dict(Counter(r["current"].get("severity", r["original"]["severity"]) for r in unique_open)) == summary["unique_open_severity"]
    assert registry["summary"] == summary
    assert summary["separately_unremediated_duplicate_surfaces"] == ["SW100-C0461"]
    assert summary["needs_validation_ids"] == []
    expected_queue_ids = {cid for cid, r in records.items() if r["current"]["remediation_state"] in {"OPEN", "MITIGATED", "UNKNOWN"} and (r["current"]["decision"] != "DUPLICATE" or "independent_surface_state" in r["current"])}
    assert len(queue) == len({x["candidate_id"] for x in queue}) == 510
    assert {x["candidate_id"] for x in queue} == expected_queue_ids
    assert next(x for x in queue if x["candidate_id"] == "SW100-C0461")["counting_unit"] == "SEPARATE_DUPLICATE_SURFACE"
    future = read(PLAN13 / "selection-30.json")
    obligations = read(PLAN13 / "duplicate-surface-obligations.json")
    plan = read(PLAN13 / "plan-validation.json")
    expected_future = [x for x in queue if x["remediation_state"] == "OPEN" and x["decision"] != "DUPLICATE"][:30]
    assert [x["candidate_id"] for x in future] == [x["candidate_id"] for x in expected_future]
    assert len(future) == len({x["candidate_id"] for x in future}) == 30
    assert Counter(x["severity"] for x in future) == {"P1": 25, "P2": 5}
    assert not set(selected).intersection(x["candidate_id"] for x in future)
    for row in future:
        current = records[row["candidate_id"]]["current"]
        assert row["decision"] == current["decision"] != "DUPLICATE" and row["remediation_state"] == current["remediation_state"] == "OPEN"
        assert row["source_sha256"] == sha(ROOT / row["path"])
        assert row["registry_review_sha256"] == current.get("current_source_sha256")
    assert len(obligations) == 1 and obligations[0]["candidate_id"] == "SW100-C0461"
    assert obligations[0]["decision"] == "DUPLICATE" and obligations[0]["remediation_state"] == "OPEN"
    assert obligations[0]["source_sha256"] == duplicate["current_source_sha256"]
    paths = {x["path"] for x in future} | {x["path"] for x in obligations}
    assert len({x["path"] for x in future}) == plan["primary_source_files"] == 23
    assert len(paths) == plan["source_files"] == 24 and plan["additional_duplicate_surfaces"] == 1
    assert set(plan["source_sha256"]) == paths
    assert all(sha(ROOT / p) == digest for p, digest in plan["source_sha256"].items())
    assert plan["registry_summary_sha256"] == sha(ROUND3 / "registry-summary.json")
    assert plan["status"] == "PLAN_ONLY" and plan["production_edits"] is False
    assert not paths.intersection(x["path"] for x in selection)
    controls = control_reconciler()
    after = {str(p.relative_to(ROOT)): sha(p) for p in canonical_paths}
    assert before == after, "Canonical files changed during metadata review"
    result = {"date": "2026-10-30", "reviewer": "lot12_registry_impact_independent_metadata_review",
              "command": ["python3", str(Path(__file__).relative_to(ROOT))],
              "review_script_sha256": sha(Path(__file__)),
              "decision": "APPROVED_WITH_EXPLICIT_SCOPE", "open_actionable_findings": [],
              "selected_findings": 30, "selected_states": {"FIXED": 28, "MITIGATED": 2},
              "collateral_states_preserved": 23, "outside_scope_states_preserved": 11,
              "pending_duplicate_surfaces": ["SW100-C0461"],
              "all_remediation_states": dict(states), "unique_open_findings": len(unique_open),
              "queue_entries": len(queue), "lot13_unique_findings": 30, "lot13_primary_sources": 23,
              "lot13_total_sources_with_duplicate_obligation": 24, "range_checks": checked,
              "actual_reconciler_controls": controls, "canonical_hashes_before": before,
              "canonical_hashes_after": after, "source_sha256": {p: sha(ROOT / p) for p in review["source_sha256"]},
              "evidence_sha256": {str(p.relative_to(ROOT)): sha(p) for p in [HERE / "candidate-status-updates.json", HERE / "independent-review.json", RECONCILER, PLAN13 / "selection-30.json", PLAN13 / "duplicate-surface-obligations.json", PLAN13 / "plan-validation.json"]},
              "limits": ["Metadata and static range/evidence consistency review; no additional product behavior or closure is certified.",
                         "Reconciler controls use current real inputs and intercepted in-memory writes. Four negative cases reject before any write attempt; no canonical filesystem writes occur in any control.",
                         "C0294 and C0378 remain MITIGATED; C0461 stays an OPEN duplicate surface without increasing unique counts. Lote13 remains planning only."]}
    log = "\n".join(["PASS selected30 match current per-ID independent reviews, hashes, ranges and evidence",
                      "PASS inherited34 decisions/severities/states preserved (23 collateral and11 outside-scope)",
                      "PASS C0461 independent OPEN duplicate surface remains current and unpatched",
                      "PASS original598 inventory, summary509/79/6/4, unique503, queue510",
                      "PASS Lote13:30unique,25P1+5P2,23primary+1duplicate surface; sources unchanged",
                      *[f"PASS {c['case']}: filesystem_writes={c['writes_reached_filesystem']}" for c in controls],
                      "PASS canonical hashes unchanged before/after all controls"]) + "\n"
    LOG.write_text(log)
    result["log"] = str(LOG.relative_to(ROOT))
    result["log_sha256"] = sha(LOG)
    OUT.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    print(log)


if __name__ == "__main__":
    main()
