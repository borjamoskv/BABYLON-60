"""Validate current review hashes and normalize thirty independent verdicts."""
from __future__ import annotations
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).absolute().parents[4]
HERE = Path(__file__).absolute().parent
REVIEWS = ["review_identity_snapshots", "review_trust_m0", "review_queues", "review_files", "review_inputs", "review_reports_formal"]


def read(path):
    return json.loads(path.read_text())


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    selection = read(HERE / "execution-contract.json")["selection"]
    expected = {r["candidate_id"]: r for r in selection}
    fallback = {r["candidate_id"]: r for r in read(HERE / "s5/result.json")["results"]}
    sources, tests, verdicts, reviews = {}, {}, {}, []
    for folder in REVIEWS:
        path = HERE / folder / "independent-review.json"
        data = read(path)
        assert data["decision"] == "APPROVED_WITH_EXPLICIT_SCOPE", folder
        assert data.get("open_actionable_findings") == [], folder
        for key, target in [("source_sha256", sources), ("test_source_sha256", tests)]:
            for source, digest in data[key].items():
                assert sha(ROOT / source) == digest, (folder, source)
                if source in target:
                    assert target[source] == digest, source
                target[source] = digest
        per_id = data["per_id"]
        if isinstance(per_id, list):
            per_id = {r["candidate_id"]: r for r in per_id}
        for cid, item in per_id.items():
            assert cid in expected and cid not in verdicts, cid
            state = next((item.get(key) for key in ("state", "recommended_state", "proposed_state", "remediation_state") if item.get(key)), None)
            assert state in {"FIXED", "MITIGATED"}, (cid, item)
            checks = item.get("source_checks") or fallback.get(cid, {}).get("source_checks")
            assert checks, cid
            for check in checks:
                assert 1 <= check["start_line"] <= check["end_line"] <= len((ROOT / check["path"]).read_text().splitlines()), cid
                assert check["observation"], cid
            rationale = item.get("rationale") or item.get("observed") or item.get("change")
            assert rationale, cid
            limits = item.get("limits", data.get("limits", []))
            if isinstance(limits, str):
                limits = [limits]
            verdicts[cid] = {"state": state, "rationale": rationale, "source_checks": checks,
                "guards": limits, "independent_review": str(path.relative_to(ROOT)),
                "independent_review_sha256": sha(path)}
        reviews.append({"path": str(path.relative_to(ROOT)), "sha256": sha(path), "decision": data["decision"]})
    assert set(verdicts) == set(expected), set(expected) - set(verdicts)
    assert set(sources) == {r["path"] for r in selection}, set(sources) ^ {r["path"] for r in selection}
    states = {cid: v["state"] for cid, v in verdicts.items()}
    assert {cid for cid, state in states.items() if state == "MITIGATED"} == {"SW100-C0294", "SW100-C0378"}
    output = {"date": "2026-10-30", "decision": "APPROVED_WITH_EXPLICIT_SCOPE", "open_actionable_findings": [],
        "review_count": len(reviews), "candidate_count": len(verdicts), "source_sha256": sources,
        "test_source_sha256": tests, "per_id": verdicts, "reviews": reviews,
        "limits": ["Thirty selected findings only; no hardware, deployment, provider, physical power-cut or general safety certification.",
                   "C0294 and C0378 remain mitigated with unavailable or unverified capabilities, not fully implemented features."]}
    (HERE / "independent-review.json").write_text(json.dumps(output, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({"approved": len(verdicts), "fixed": sum(v == "FIXED" for v in states.values()), "mitigated": sum(v == "MITIGATED" for v in states.values()), "sources": len(sources)}))


if __name__ == "__main__":
    main()
