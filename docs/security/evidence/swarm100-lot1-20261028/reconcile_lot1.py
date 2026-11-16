"""Apply verified Lot1 dispositions without closing unrelated source findings."""

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


def main():
    records = {r["original"]["candidate_id"]: r for r in read(ROUND3 / "registry.json")["records"]}
    previous = read(ROUND3 / "root-adjudications.json")
    snapshot = ROUND3 / "root-adjudications-before-lot1.json"
    if not snapshot.exists():
        write(snapshot, previous)
    review = read(HERE / "independent-review.json")
    for path, digest in review["source_sha256"].items():
        assert sha(ROOT / path) == digest, path

    def check(path, function, observation):
        def functions(body, prefix=""):
            found = {}
            for node in body:
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                    name = prefix + node.name
                    found[name] = node
                    if isinstance(node, ast.ClassDef):
                        found.update(functions(node.body, name + "."))
            return found
        node = functions(ast.parse((ROOT / path).read_text()).body)[function]
        return dict(path=path, start_line=node.lineno, end_line=node.end_lineno, observation=observation)

    fixed = {
        "SW100-C0373": (
            "Errors return stable codes/static messages and numeric transport status, without command, stderr, exception or arbitrary provider error body. Successful IDs redact the credential. Synthetic failure and normal-result regressions pass.",
            [("C5MailTransducer.dispatch", "Allowlisted failure data; command-bearing exception details discarded.")]),
        "SW100-C0420": (
            "Signed v2 verifies an external raw Ed25519 trust key over the complete header/payload and recomputes named current artifacts, manifest root, commit and canonical topology. Missing/changed state rejects. Authorized signed fixtures pass API and actual CLI, so this is not an always-reject mitigation. Legacy unsigned JSON does not authenticate. No hardware/SCITT registration/claim truth is certified.",
            [("verify_attestation", "External trust and complete signature precede current-state comparison."),
             ("_read_evidence", "Named explicit files read once; bytes hashed and declared manifest root compared."),
             ("generate_attestation_statement", "Explicitly UNSIGNED producer without fabricated audits.")]),
        "SW100-C0421": (
            "Rejected verification returns 1 through SystemExit(main()). Real CLI checks return 0 for the authorized coherent fixture, 1 for changed evidence/missing trust, and 2 for absent/conflicting operation options before emission.",
            [("main", "Verification result controls process status; no implicit emission or ignored verify-only emit flags.")]),
        "SW100-C0501": (
            "SOCINT v2 binds each name and recursively typed JSON value with leaf/node/empty domains, rejects unsupported/nonfinite values and seals after final analysis fields. Both identical copies pass swap/rename/type/nested and producer tests. This verifies body integrity, not authorship; timestamp metadata is outside the commitment.",
            [("compute_merkle_root", "Name/type/value commitments in deterministic key order."),
             ("seal_evidence", "Version and exact final body coverage."),
             ("verify_evidence_seal", "Recomputes every body field; legacy/extra/missing coverage rejects.")]),
    }
    updates = []
    for cid, (rationale, checks) in fixed.items():
        item = copy.deepcopy(records[cid]["current"])
        path = records[cid]["original"]["path"]
        item.update(decision="ALREADY_FIXED", remediation_state="FIXED", current_source_sha256=sha(ROOT / path),
                    rationale=rationale, source_checks=[check(path, f, obs) for f, obs in checks],
                    runtime_executed=True, runtime_scope="Real Python modules, synthetic credentials/keys and temporary files; no network or operator data.",
                    guards=["Trust and coverage are limited to the explicit module contract; no hardware or claim-truth certification."],
                    evidence_paths=[str((HERE / name).relative_to(ROOT)) for name in
                                    ["before-tests.log", "related-tests.log", "independent-review.json", "cli-smoke.json"]],
                    resolution_type="CODE_AND_REGRESSIONS_VERIFIED")
        updates.append(item)
    cid = "SW100-C0264"
    item = copy.deepcopy(records[cid]["current"])
    path = records[cid]["original"]["path"]
    item.update(decision="DUPLICATE", canonical_id="SW100-C0501", remediation_state="FIXED",
                current_source_sha256=sha(ROOT / path), rationale="Same omission as C0501 in a distinct identical bundled copy. Both implementations now use v2 and pass the shared parameterized regressions; preserve this affected path and inherit FIXED.",
                source_checks=[check(path, "compute_merkle_root", "Bundled v2 name/type/value commitment.")],
                runtime_executed=True, runtime_scope="Both full Python source modules exercised with synthetic evidence; no extraction network or operator data.",
                guards=["Same v2 implementation in both paths; scope is body integrity, not author authentication."],
                evidence_paths=[str((HERE / n).relative_to(ROOT)) for n in
                                                     ["related-tests.log", "independent-review.json"]])
    updates.append(item)

    remaining, snapshots = [], []
    literals = {
        "SW100-C0265": [("rec_id = str(data.get", "Local ID remains the vault key."),
                         ("INSERT OR REPLACE", "ID collisions still replace captures.")],
        "SW100-C0268": [(".join(all_reports)", "Batch JSON retains the unrelated Markdown-separator defect.")],
        "SW100-C0269": [("transcript_text = body", "Watch-page body remains transcript data."),
                         ("Transcripción de Audio", "The unrelated audio-transcript label remains.")],
        "SW100-C0270": [('"hechos_verificados"', "Regex hits remain a verified-fact count."),
                         ("Hechos Verificados", "Consumer keeps the unrelated verified-fact label.")],
    }
    for cid, terms in literals.items():
        item = copy.deepcopy(records[cid]["current"])
        path = records[cid]["original"]["path"]
        lines = (ROOT / path).read_text().splitlines()
        checks = []
        for literal, observation in terms:
            index = next(i for i, line in enumerate(lines, 1) if literal in line)
            c = dict(path=path, start_line=max(1, index - 2), end_line=min(len(lines), index + 2), observation=observation)
            checks.append(c)
            snapshots.append({**c, "source_sha256": sha(ROOT / path), "lines": lines[c["start_line"] - 1:c["end_line"]]})
        item.update(current_source_sha256=sha(ROOT / path), source_checks=checks,
                    rationale=item["rationale"].split(" Re-reviewed after Lot1:")[0] + " Re-reviewed after Lot1: this separate behavior is unchanged and remains OPEN; sharing a modified source file does not close it.")
        item["evidence_paths"] = list(dict.fromkeys(item.get("evidence_paths", []) + [
            str((HERE / "remaining-socint-source-checks.json").relative_to(ROOT)),
            str((HERE / "independent-review.json").relative_to(ROOT)),
        ]))
        remaining.append(item)
    write(HERE / "remaining-socint-source-checks.json", snapshots)
    write(HERE / "candidate-status-updates.json", updates)
    write(HERE / "remaining-open-source-refresh.json", remaining)
    ids = {item["candidate_id"] for item in updates + remaining}
    write(ROUND3 / "root-adjudications.json", [item for item in previous if item["candidate_id"] not in ids] + updates + remaining)
    print("Four fixes, one fixed duplicate; four separate SOCINT findings remain OPEN with fresh source evidence.")


if __name__ == "__main__":
    main()
