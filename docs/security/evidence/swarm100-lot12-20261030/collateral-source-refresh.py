"""Regenerate collateral range maintenance without adjudicating additional IDs.

Recipes below record the explicitly inspected post-patch code. Unchanged
fragments are located by exact lines; changed fragments use named functions
and reviewed observations. No production module is imported or executed.
"""

from __future__ import annotations

import ast
import copy
import hashlib
import json
import subprocess
import sys
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
ROUND3 = HERE.parent / "swarm100-round3-20261028"
VALIDATION = HERE / "collateral-source-refresh-validation.json"
OUTPUT = HERE / "collateral-source-refresh.json"


def read(path):
    return json.loads(path.read_text())


def write(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n")


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def functions(path):
    result = {}

    def walk(nodes, prefix=""):
        for node in nodes:
            if isinstance(node, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
                name = prefix + node.name
                result[name] = (node.lineno, node.end_lineno)
                walk(node.body, name + ".")

    walk(ast.parse((ROOT / path).read_text()).body)
    return result


def function_check(path, name, observation):
    start, end = functions(path)[name]
    return dict(path=path, start_line=start, end_line=end, observation=observation)


def anchor_check(path, anchor, observation, size=1):
    lines = (ROOT / path).read_text().splitlines()
    found = [i + 1 for i, line in enumerate(lines) if anchor in line]
    assert len(found) == 1, (path, anchor, found)
    return dict(path=path, start_line=found[0], end_line=found[0] + size - 1,
                observation=observation)


NOTES = {
    "SW100-C0032": "The FIFO test still imports the configured production QUEUE_FILE and unlinks it without a temporary-path fixture. The production default has moved from shared /tmp to a private per-user queue, so the old absolute-/tmp wording is historical; the test still targets the configured queue. No destructive test was run.",
    "SW100-C0073": "The compiler's rejection of a false ledger verdict and the verifier's ordering/hash rejection branches remain byte-identical. Concurrent work outside Lote12 added nine lines of regulatory-catalogue metadata earlier in the compiler source, moving its rejection fragment from623-637 to632-646 without changing it. The current V01 temporary-fixture regression also passes without promoting unobserved campaigns. This preserves the previously FIXED ignored-verdict issue, not another selected closure or a legal/regulatory conformity guarantee.",
    "SW100-C0176": "The current verifier still guards trace cardinality/hash comparisons with if trace_lines. Mandatory digest coverage added for C0175 does not make a legitimately signed empty trace consistent with a nonempty ledger. This is current source inspection, not a new signed-pack reproduction.",
    "SW100-C0177": "The JSON ledger verifier still recomputes event-content digests and rejects altered payloads through both offline and certificate verification. Eight confined V04 cases passed against the current source, including both event envelope shapes, malformed shapes and explicit hash-commitment-only scope. This preserves the prior FIXED state and is not an additional Lote12 closure.",
    "SW100-C0272": "The public claim-leaf helper still joins unrestricted fields with colons, and manifest recomputation still calls it. The complete-manifest signature/trust-anchor change does not change that leaf encoding. The historic delimiter-collision reproduction was not rerun; no new producer reachability claim is made.",
    "SW100-C0277": "generate_notary_checkpoint remains byte-identical: its default branch returns CHECKPOINT_SEALED and 3f+1_QUORUM_VERIFIED from a hash/time calculation without validator interaction. Hardware-quote changes are separate. No network or consensus runtime was executed.",
    "SW100-C0295": "PENDING_SEPARATE_READJUDICATION: the old in-process catch tuple has been removed. safe_exec now launches a bounded worker; the worker catches ordinary Exception, while this host rejects unsupported resource enforcement before user code. The historical escaping-error trigger is not asserted to remain in current code. OPEN and its inherited REPRODUCED decision are retained only pending a separate, platform-scoped adjudication; no new error reproduction or closure is claimed.",
    "SW100-C0323": "The primary conversation auditor is unchanged and retains its unconditional/unsupported cohort verdict branches. The secondary reporter no longer derives an exergy score from PASS counts and now distinguishes observed/unexecuted results. This narrows the old rationale: no current claim is made that the reporter still fabricates that score. The unchanged auditor issue remains OPEN without a new runtime audit.",
    "SW100-C0334": "The archived sitrep JSON is unchanged and still contains its historical certification/health literals. The current reporter now emits NOT_ATTESTED, null health/exergy values and explicit unexecuted controls; it cannot retroactively authenticate the archive. OPEN is preserved for the archived provenance issue, not as a claim that the repaired generator still emits the old literals.",
    "SW100-C0353": "Receipt generation/verification in the primary attester is unchanged. The pipeline still generates receipts from risk findings and attempts enqueue; it now checks enqueue rejection. That queue fix does not bind omitted finding metadata into receipt verification. No new attestation or ledger effect was executed.",
    "SW100-C0356": "The public code generator and its schema remain unchanged, including its metadata promotion without compiler evidence. The repaired demonstration stops before Rust generation, so the old E2E reachability statement is historical. The generator issue stays OPEN; no claim of current demo activation or runtime deployment is made.",
    "SW100-C0361": "The previous rejection remains valid: EOF namespace termination is legal Lean syntax. The current generator additionally emits an explicit end Babylon60.Oncology. The historical omission is now absent, but neither version establishes the claimed compilation defect. NOT_APPLICABLE is preserved without inferring any other formal guarantee.",
    "SW100-C0375": "The primary bounded-deque dispatcher is unchanged, and the pipeline still dispatches all frames before draining domain queues. Checking a later cold-ledger enqueue return does not remove bounded-deque eviction at dispatch. OPEN is preserved on source inspection; no new concurrent dispatch run was performed.",
    "SW100-C0376": "The primary extractor/ingestor still have their recorded first-trace/cluster-validation limitations. The repaired proof emitter now refuses certification and no longer independently promotes a selected trace to PROVED. The extractor issue remains OPEN, with downstream proof amplification explicitly no longer asserted for this path.",
    "SW100-C0386": "PENDING_SEPARATE_READJUDICATION: the old timed-compiler/literal-speedup report has been removed. The current synthetic demo declares benchmark and native compilation NOT_EXECUTED and exits unsuccessfully while correspondence is unverified. The old benchmark defect is not claimed to persist in current code. OPEN and the inherited CONFIRMED_STATIC decision are retained pending separate adjudication; no benchmark or closure was performed here.",
    "SW100-C0405": "The primary EVM decoder is unchanged, including the recorded TLOAD constant. The pipeline still uses risk findings to select receipts, now with observable enqueue rejection. That delivery change does not repair opcode decoding. OPEN is preserved without a new EVM runtime or standards assertion.",
    "SW100-C0406": "The primary hook-permission address decoding is unchanged. The pipeline still uses its risk findings when selecting receipts, although enqueue rejection is now observed. OPEN is preserved; no new EVM/contract execution was performed.",
    "SW100-C0426": "The unchanged commit polisher still names scripts/rewrite_commits.py, which is absent. The implementation continues to exist under scripts/c5_git_utils/rewrite_commits.py; its backup-safety repair does not fix that caller path. No rewrite or Git mutation was executed for this review.",
    "SW100-C0436": "PENDING_SEPARATE_READJUDICATION: the old unlocked read/modify/truncate operations were replaced by a shared flock, descriptor-relative reads and atomic replacement. The historic lost-update/truncated-JSON trigger is not asserted to persist. OPEN and its inherited CONFIRMED_STATIC decision are retained pending explicit separate concurrency adjudication; this source refresh performs no new race reproduction or closure.",
    "SW100-C0485": "The token-bucket refill/debt code is unchanged, and query still sleeps separately after a reservation. The sensitive-explicit-destination repair is outside those branches. OPEN is preserved for the recorded reservation defect, without a new timing or provider run.",
    "SW100-C0491": "The installer acquisition loop still removes an existing lock after its retry count, and release still removes the path without ownership validation. Instruction-preservation changes do not repair that lock protocol. OPEN is preserved without running installation or lock contenders.",
    "SW100-C0492": "Uninstall still removes any symlink at the instruction paths without testing its target. Installation now backs up replaced instructions; this does not add an ownership check to uninstall. OPEN is preserved; no uninstall or user instruction mutation was executed.",
    "SW100-C0534": "The sealer still chooses AUTHENTICATED_RFC3161_TSA solely from tsr_b64 field presence and persists that status/token. Its complete-manifest software signature authenticates the chosen bytes, not a TSA signature/imprint/trust chain. The RFC3161 client is unchanged; OPEN is preserved without a TSA request.",
}


def replacements(cid, path):
    name = path.rsplit("/", 1)[-1]

    def fn(symbol, observation):
        return function_check(path, symbol, observation)

    if cid == "SW100-C0032" and name == "moskv_native_host.py":
        return [anchor_check(path, "QUEUE_FILE =", "Configured production queue remains the test's imported target; default is now private per-user storage."),
                fn("_queue_store", "Current queue accesses are serialized in a private descriptor-anchored store; test isolation is a separate obligation.")]
    if cid == "SW100-C0295":
        return [fn("ASTSandbox.safe_exec", "Current API returns worker outcomes; old in-process exception path is removed and awaits separate adjudication."),
                fn("_execute_bounded", "Worker rejects unsupported limits and catches ordinary runtime exceptions; no current escaping-error defect is asserted by this refresh.")]
    if cid == "SW100-C0323" and name == "sharur_100_conversation_reporters.py":
        return [fn("compile_swarm_sitrep", "Reporter now separates execution statuses and emits no derived exergy score; original primary auditor issue remains separately recorded.")]
    if cid == "SW100-C0334" and name == "sharur_100_conversation_reporters.py":
        return [fn("run_cohort_4", "Current cohort reports counts/unexecuted controls instead of the historical fixed sync/isolation verdicts."),
                fn("run_cohort_5", "Current certification is NOT_ATTESTED and health is null; this does not validate the unchanged archived report."),
                fn("emit_sitrep_reports", "Serializes current result fields, not independent proof of historical archived values.")]
    if cid in {"SW100-C0353", "SW100-C0405", "SW100-C0406"} and name == "bounty_pipeline_orchestrator.py":
        return [fn("BountyPipelineOrchestrator.execute_cycle", "Risk findings still select generated receipts; enqueue rejection is now explicit and does not repair the separate upstream metadata/decoder issue.")]
    if cid in {"SW100-C0356", "SW100-C0386"} and name == "test_destiladora_e2e.py":
        return [fn("_run_isolated_demo", "Synthetic report stops before Rust and marks benchmark/native compilation NOT_EXECUTED; former demo behavior is not claimed current."),
                fn("run_end_to_end_test", "Disposable demo returns failure until verified correspondence exists; no measured fast-path speedup is emitted.")]
    if cid == "SW100-C0361":
        return [fn("export_lean4", "Current generated module has explicit namespace/end; historical EOF termination was legal and the rejected defect stays NOT_APPLICABLE.")]
    if cid == "SW100-C0376" and name == "proof_emitter_lean4.py":
        return [fn("Lean4ProofEmitter.prove_extracted_clusters", "Current emitter withdraws PROVED eligibility; the unchanged extractor's cluster-validation issue is not repaired by that rejection.")]
    if cid == "SW100-C0426" and name == "rewrite_commits.py":
        return [dict(path=path, start_line=1, end_line=18, observation="Rewrite implementation remains in scripts/c5_git_utils; the polisher's obsolete scripts/rewrite_commits.py path is still absent.")]
    if cid == "SW100-C0436":
        return [fn("_queue_store", "Shared flock covers current cooperative operations; old unlocked protocol is removed and awaits separate adjudication."),
                fn("_write_queue", "Current writes use an exclusive temporary, fsync and descriptor-relative atomic replace."),
                fn("enqueue_prompt", "Whole read/append/write now executes inside the common queue-store context."),
                fn("get_next_prompt", "Whole read/pop/write now executes inside the common queue-store context.")]
    if cid == "SW100-C0492":
        return [anchor_check(path, 'preserve_rule() {', "Installation preserves replaced instructions; uninstall target ownership remains unchecked.", 22)]
    if cid == "SW100-C0534" and name == "seal_bounty_aeon.py":
        return [anchor_check(path, 'tsa_status = ', "TSA authenticated label is still selected solely from tsr_b64 presence.", 2),
                anchor_check(path, '"rfc3161_tsa": {', "Artifact stores the label and token; software manifest signing is not TSA verification.", 5)]
    raise AssertionError((cid, path, "Changed fragment needs an explicit reviewed recipe"))


def main():
    snapshots = read(HERE / "before-source-snapshots.json")
    impact = read(HERE / "registry-impact.json")
    ids = {x["candidate_id"] for x in impact["affected_records"] if not x["selected"]}
    if VALIDATION.exists():
        validation = read(VALIDATION)
        baseline = validation["baseline_records"]
    else:
        records = read(ROUND3 / "registry.json")["records"]
        baseline = {r["original"]["candidate_id"]: r for r in records if r["original"]["candidate_id"] in ids}
        validation = {"baseline_records": baseline}
    for path, source in validation.get("additional_baseline_git_sources", {}).items():
        original_bytes = subprocess.check_output(["git", "show", source["revision"] + ":" + path])
        assert hashlib.sha256(original_bytes).hexdigest() == source["sha256"]
        snapshots[path] = original_bytes.decode("utf-8")
    assert set(baseline) == ids and len(ids) == 23
    mapped = []
    updates = []
    inputs = set()
    for cid in sorted(ids):
        record = baseline[cid]
        prior = record["current"]
        primary = prior.get("path", record["original"]["path"])
        inputs.add(primary)
        item = copy.deepcopy(prior)
        checks = []
        remapped_paths = set()
        for check in prior.get("source_checks", []):
            path = check["path"]
            inputs.add(path)
            if path not in snapshots:
                checks.append(copy.deepcopy(check))
                continue
            old_lines = snapshots[path].splitlines()
            lines = (ROOT / path).read_text().splitlines()
            fragment = old_lines[check["start_line"] - 1:check["end_line"]]
            matches = [i + 1 for i in range(len(lines) - len(fragment) + 1)
                       if lines[i:i + len(fragment)] == fragment]
            if len(matches) == 1:
                moved = copy.deepcopy(check)
                moved.update(start_line=matches[0], end_line=matches[0] + len(fragment) - 1)
                checks.append(moved)
                mapped.append(dict(candidate_id=cid, path=path, mode="EXACT_FRAGMENT", old_range=[check["start_line"], check["end_line"]], new_range=[moved["start_line"], moved["end_line"]]))
            elif path not in remapped_paths:
                checks.extend(replacements(cid, path))
                remapped_paths.add(path)
                mapped.append(dict(candidate_id=cid, path=path, mode="EXPLICIT_CURRENT_SOURCE_REVIEW", old_range=[check["start_line"], check["end_line"]]))
        if cid == "SW100-C0177":
            checks = [function_check(primary, "_verify_json_ledger", "Recomputes content-bearing event digests; rejects changed payloads while delimiting hash-only commitments."),
                      function_check(primary, "verify_compliance_certificate", "Certificate verification propagates ledger-integrity failure; V04 current regressions preserve rejection.")]
        unique = {(c["path"], c["start_line"], c["end_line"], c["observation"]): c for c in checks}
        checks = list(unique.values())
        assert checks, cid
        for check in checks:
            assert 1 <= check["start_line"] <= check["end_line"] <= len((ROOT / check["path"]).read_text().splitlines()), (cid, check)
        item.update(candidate_id=cid, path=primary, severity=prior.get("severity", record["original"]["severity"]),
                    current_source_sha256=sha(ROOT / primary), source_checks=checks,
                    rationale=NOTES[cid], runtime_executed=cid in {"SW100-C0073", "SW100-C0177"},
                    resolution_type="COLLATERAL_SOURCE_REFRESH_NO_NEW_CLOSURE")
        item["guards"] = list(prior.get("guards", [])) + [
            "Only Lote12 selected IDs receive new remediation outcomes. This collateral record retains its inherited decision/severity/remediation state.",
            ("Range/source refresh is explicit static maintenance; C0073 has current V01 temporary-fixture compatibility revalidation, not a new closure or regulatory conformity guarantee."
             if cid == "SW100-C0073" else
             "Range/source refresh is explicit static maintenance. Except C0177 V04 revalidation, no historical reproduction is rerun or new runtime guarantee claimed."),
        ]
        item["source_refresh"] = {"inherited_decision": prior["decision"], "inherited_remediation_state": prior["remediation_state"],
                                  "previous_current_source_sha256": prior.get("current_source_sha256"),
                                  "previous_rationale": prior.get("rationale"),
                                  "pending_separate_readjudication": cid in {"SW100-C0295", "SW100-C0386", "SW100-C0436"}}
        item["evidence_paths"] = sorted(set(prior.get("evidence_paths", [])) | {
            str(OUTPUT.relative_to(ROOT)), str(VALIDATION.relative_to(ROOT)),
            str((HERE / "before-source-snapshots.json").relative_to(ROOT)),
        })
        assert all(item[k] == prior[k] for k in ("decision", "remediation_state")), cid
        assert item["severity"] == prior.get("severity", record["original"]["severity"]), cid
        updates.append(item)
    assert not (ROOT / "scripts/rewrite_commits.py").exists()
    states = Counter(x["remediation_state"] for x in updates)
    assert states == {"OPEN": 20, "FIXED": 2, "NOT_APPLICABLE": 1}
    current_hashes = {p: sha(ROOT / p) for p in sorted(inputs)}
    previous_hashes = validation.get("checked_source_sha256", {})
    changed_since_review = [p for p, h in current_hashes.items()
                            if p in previous_hashes and previous_hashes[p] != h]
    if changed_since_review and "--accept-reviewed" not in sys.argv[1:]:
        raise AssertionError(("Sources changed since explicit inspection; inspect their diff before --accept-reviewed", changed_since_review))
    write(OUTPUT, {"scope": "23 collateral source refreshes; zero new closures; original decisions/severities/states retained",
                   "updates": updates, "source_sha256": current_hashes})
    validation.update(result="PASS_STATIC_REFRESH_WITH_EXPLICIT_PENDING_READJUDICATION", count=23,
                      states=dict(states), mapping=mapped,
                      checked_source_sha256=current_hashes,
                      last_explicitly_accepted_source_changes=changed_since_review,
                      limits="Not a fresh runtime adjudication of the 20 OPEN issues; semantic recipes were read against these source hashes. Regenerate and inspect if source changes.")
    write(VALIDATION, validation)
    print(json.dumps({"count": len(updates), "states": dict(states), "mapped_checks": len(mapped)}, indent=2))


if __name__ == "__main__":
    main()
