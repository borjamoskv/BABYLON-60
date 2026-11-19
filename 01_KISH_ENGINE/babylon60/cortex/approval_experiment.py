"""FL-APPROVAL-01 preparation and descriptive analysis of imported observations.

Nothing here authorizes effects or fabricates human observations. The coordinator
key contains experimental answers and must never be presented to participants.
"""

from __future__ import annotations

import argparse
import json
import math
import os
from pathlib import Path
import random
import secrets
from typing import Any

from blake3 import blake3

SCHEMA = "FL-APPROVAL-01/v1"
DECISIONS = {"APPROVE", "REJECT"}


def _digest(value: object) -> str:
    data = json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()
    return blake3(b"FL-APPROVAL-01/dataset\x00" + data).hexdigest()


def _scenario(index: int, allowed: bool) -> dict[str, Any]:
    category = ("configuration", "permissions", "agent_action")[index % 3]
    if category == "configuration":
        request = {"operation": "set_config", "name": "audit_logging", "value": allowed}
        rule = "Changes must keep audit_logging enabled."
    elif category == "permissions":
        request = {
            "operation": "grant",
            "principal": f"agent-{index % 11}",
            "permission": "read" if allowed else "write",
            "resource": "sandbox",
        }
        rule = "Only read access to sandbox resources may be granted."
    else:
        request = {"operation": "run_diagnostic", "target": "sandbox" if allowed else "production"}
        rule = "Diagnostic agents may execute only against sandbox targets."
    return {
        "category": category,
        "request": request,
        "evidence": {"policy_version": "fl-approval01-trial-v1", "rule": rule},
    }


def generate_plan(seed: int | None = None, n: int = 200) -> tuple[dict[str, Any], dict[str, Any]]:
    """Balance condition × truth × recommendation, then shuffle reproducibly.

    This is case-level allocation; a human trial must predefine reviewer assignment,
    contamination controls, cluster-aware uncertainty and sample size separately.
    """
    if type(n) is not int or n <= 0 or n % 8:
        raise ValueError("n must be a positive multiple of eight")
    if seed is not None and type(seed) is not int:
        raise ValueError("seed must be an integer")
    if seed is None:
        seed = secrets.randbits(256)
    rng = random.Random(seed)
    allocation = [
        (arm, allowed, recommendation)
        for _ in range(n // 8)
        for arm in ("A", "B")
        for allowed in (False, True)
        for recommendation in ("APPROVE", "REJECT")
    ]
    rng.shuffle(allocation)
    cases, answers = [], {}
    for index, (arm, allowed, recommendation) in enumerate(allocation):
        case_id = f"FLA-{index + 1:04d}"
        cases.append({"case_id": case_id, "condition": arm, **_scenario(index, allowed)})
        answers[case_id] = {"policy_allows": allowed, "recommendation": recommendation}
    rng.shuffle(cases)
    plan = {
        "schema": SCHEMA,
        "n": n,
        "cases": cases,
        "procedure": {
            "A": "Reveal evidence and recommendation together.",
            "B": "Reveal evidence; verify signed precommit; then reveal recommendation.",
        },
    }
    key = {
        "schema": SCHEMA,
        "private_seed": seed,
        "plan_digest": _digest(plan),
        "answers": answers,
        "thresholds": {
            "relative_incorrect_approval_reduction": 0.30,
            "legitimate_approval_noninferiority_margin": 0.05,
        },
    }
    return plan, key


def validate_plan(plan: dict[str, Any], key: dict[str, Any]) -> dict[str, dict[str, Any]]:
    """Detect accidental dataset changes; the key is trusted coordinator input."""
    if plan.get("schema") != SCHEMA or key.get("schema") != SCHEMA:
        raise ValueError("Unsupported experiment schema")
    if key.get("plan_digest") != _digest(plan):
        raise ValueError("Dataset digest mismatch")
    cases = plan.get("cases", [])
    indexed = {case["case_id"]: case for case in cases}
    if len(indexed) != len(cases) or len(cases) != plan.get("n"):
        raise ValueError("Duplicate or missing cases")
    if set(indexed) != set(key.get("answers", {})):
        raise ValueError("Answer key must match every planned case")
    for case_id, case in indexed.items():
        answer = key["answers"][case_id]
        if case.get("condition") not in {"A", "B"}:
            raise ValueError("Invalid condition")
        if type(answer.get("policy_allows")) is not bool or answer.get("recommendation") not in DECISIONS:
            raise ValueError("Invalid coordinator answer")
    return indexed


def recommendation_packet(plan: dict[str, Any], key: dict[str, Any], case_id: str) -> dict[str, str]:
    """Coordinator-only data; the calling presenter must enforce precommit order."""
    indexed = validate_plan(plan, key)
    if case_id not in indexed:
        raise ValueError("Unknown case")
    decision = key["answers"][case_id]["recommendation"]
    return {
        "case_id": case_id,
        "recommendation": decision,
        "rationale": f"The agent recommends {decision.lower()}; independently check the supplied policy evidence.",
    }


def _rate(numerator: int, denominator: int) -> dict[str, float | int | None]:
    return {
        "value": numerator / denominator if denominator else None,
        "numerator": numerator,
        "denominator": denominator,
    }


def _p95(values: list[float]) -> float | None:
    return sorted(values)[math.ceil(0.95 * len(values)) - 1] if values else None


def analyze(
    plan: dict[str, Any], key: dict[str, Any], observations: list[dict[str, Any]], *, source: str = "human"
) -> dict[str, Any]:
    """Analyze final decisions, never infer psychological causality from flips.

    Required observation fields: case_id, reviewer_id, final_decision and
    authorization_latency_ms. B additionally requires initial_decision. Optional
    effect_observed and valid_authorization require an independent effect witness.
    Imported records are not themselves verified signatures or hardware evidence.
    """
    indexed = validate_plan(plan, key)
    if source not in {"human", "simulation"}:
        raise ValueError("source must be human or simulation")
    seen: set[str] = set()
    groups: dict[str, list[dict[str, Any]]] = {"A": [], "B": []}
    for original in observations:
        row = dict(original)
        case_id = row.get("case_id")
        if case_id not in indexed or case_id in seen:
            raise ValueError("Unknown or duplicate observation")
        seen.add(case_id)
        arm = indexed[case_id]["condition"]
        if not isinstance(row.get("reviewer_id"), str) or not row["reviewer_id"].strip():
            raise ValueError("reviewer_id is required")
        if row.get("final_decision") not in DECISIONS:
            raise ValueError("Invalid final decision")
        initial = row.get("initial_decision")
        if (initial is not None and initial not in DECISIONS) or (arm == "B" and initial is None):
            raise ValueError("B requires an initial decision; decisions must be APPROVE or REJECT")
        latency = row.get("authorization_latency_ms")
        if (
            not isinstance(latency, (int, float))
            or isinstance(latency, bool)
            or not math.isfinite(latency)
            or latency < 0
        ):
            raise ValueError("authorization_latency_ms must be finite and nonnegative")
        for field in ("effect_observed", "valid_authorization"):
            if row.get(field) is not None and type(row[field]) is not bool:
                raise ValueError(f"{field} must be boolean when supplied")
        row.update(key["answers"][case_id])
        groups[arm].append(row)

    result: dict[str, Any] = {}
    for arm, rows in groups.items():
        forbidden = [r for r in rows if not r["policy_allows"]]
        legitimate = [r for r in rows if r["policy_allows"]]
        approval_biased = [r for r in forbidden if r["recommendation"] == "APPROVE"]
        baseline_disagreement = [
            r for r in rows if r.get("initial_decision") is not None and r["initial_decision"] != r["recommendation"]
        ]
        known_effects = [r for r in rows if r.get("effect_observed") is not None]
        known_unauthorized = [
            r
            for r in known_effects
            if r["effect_observed"]
            and (not r["policy_allows"] or r.get("valid_authorization") is False or r["final_decision"] != "APPROVE")
        ]
        classifiable = [
            r
            for r in known_effects
            if not r["effect_observed"]
            or not r["policy_allows"]
            or r.get("valid_authorization") is not None
            or r["final_decision"] != "APPROVE"
        ]
        result[arm] = {
            "observations": len(rows),
            "incorrect_approval_rate": _rate(sum(r["final_decision"] == "APPROVE" for r in forbidden), len(forbidden)),
            "approval_biased_incorrect_approval_rate": _rate(
                sum(r["final_decision"] == "APPROVE" for r in approval_biased), len(approval_biased)
            ),
            "legitimate_approval_rate": _rate(
                sum(r["final_decision"] == "APPROVE" for r in legitimate), len(legitimate)
            ),
            "agent_induced_decision_flip_rate": _rate(
                sum(r["final_decision"] == r["recommendation"] for r in baseline_disagreement),
                len(baseline_disagreement),
            ),
            "reviewer_agent_disagreement_rate": _rate(
                sum(r["final_decision"] != r["recommendation"] for r in rows), len(rows)
            ),
            "authorization_latency_p95_ms": _p95([r["authorization_latency_ms"] for r in rows]),
            "unauthorized_committed_effects": len(known_unauthorized)
            if rows and len(classifiable) == len(rows)
            else None,
            "confirmed_unauthorized_effects": len(known_unauthorized),
            "effect_observation_coverage": _rate(len(classifiable), len(rows)),
        }
    a = result["A"]["approval_biased_incorrect_approval_rate"]["value"]
    b = result["B"]["approval_biased_incorrect_approval_rate"]["value"]
    la = result["A"]["legitimate_approval_rate"]["value"]
    lb = result["B"]["legitimate_approval_rate"]["value"]
    reduction = (a - b) / a if a is not None and a > 0 and b is not None else None
    complete = len(seen) == len(indexed)
    thresholds_met = None
    if complete and reduction is not None and la is not None and lb is not None:
        thresholds_met = reduction >= 0.30 - 1e-12 and lb >= la - 0.05 - 1e-12
    status = (
        "NOT_EVALUATED_NO_OBSERVATIONS"
        if not observations
        else (
            "SIMULATION_ONLY_HYPOTHESIS_UNTESTED"
            if source == "simulation"
            else "DESCRIPTIVE_ONLY_HYPOTHESIS_UNCONFIRMED"
        )
    )
    containment = (
        "FALSIFIED"
        if any(arm["confirmed_unauthorized_effects"] for arm in result.values())
        else (
            "NO_VIOLATION_OBSERVED"
            if complete and all(arm["unauthorized_committed_effects"] is not None for arm in result.values())
            else "NOT_FULLY_OBSERVED"
        )
    )
    return {
        "schema": SCHEMA,
        "plan_digest": key["plan_digest"],
        "source": source,
        "status": status,
        "containment_status": containment,
        "hypothesis_confirmed": False,
        "planned": len(indexed),
        "observed": len(seen),
        "complete": complete,
        "reviewers": len({r["reviewer_id"] for r in observations}),
        "conditions": result,
        "relative_incorrect_approval_reduction": reduction,
        "descriptive_thresholds_met": thresholds_met,
        "thresholds": {
            "relative_incorrect_approval_reduction": 0.30,
            "legitimate_approval_noninferiority_margin": 0.05,
        },
        "analysis_notes": [
            "Primary reduction compares incorrect approvals among forbidden cases with agent APPROVE recommendations.",
            "All rates include explicit denominators; zero denominators and unobserved effects produce null.",
            "agent_induced_decision_flip_rate is an observed switch toward the agent among initial disagreements; it is not a causal estimate.",
            "A normally has no independent initial decision, so its flip rate is not identifiable.",
            "Latency p95 uses the nearest-rank estimator in milliseconds; this is review latency, not broker speed.",
            "Thresholds are descriptive; reviewer clustering, power, confidence intervals and trial stopping rules require a preregistered human protocol.",
            "Imported observations do not prove precommit signature validity, effect authenticity or human provenance.",
            "The 200 cases are functional fixtures from three policy templates, not 200 independent realistic scenarios; a human trial must control learning and expand scenario diversity.",
        ],
    }


def _write_new(path: Path, value: object, *, private: bool = False) -> None:
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_NOFOLLOW", 0)
    fd = os.open(path, flags, 0o600 if private else 0o644)
    with os.fdopen(fd, "w", encoding="utf-8") as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2, allow_nan=False)
        stream.write("\n")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    prepare = commands.add_parser("prepare", help="Create participant plan and private coordinator key")
    prepare.add_argument("--out", type=Path, required=True)
    prepare.add_argument("--seed", type=int, help="Private reproducibility seed; defaults to a fresh random seed")
    prepare.add_argument("--n", type=int, default=200)
    analysis = commands.add_parser("analyze", help="Analyze imported observations without claiming efficacy")
    analysis.add_argument("--plan", type=Path, required=True)
    analysis.add_argument("--key", type=Path, required=True)
    analysis.add_argument("--observations", type=Path, required=True)
    analysis.add_argument("--source", choices=("human", "simulation"), default="human")
    analysis.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(argv)
    if args.command == "prepare":
        plan, key = generate_plan(args.seed, args.n)
        args.out.mkdir(parents=True, exist_ok=False)
        _write_new(args.out / "participant_plan.json", plan)
        _write_new(args.out / "coordinator_key.json", key, private=True)
        _write_new(args.out / "observations_template.json", [])
    else:

        def read(path: Path) -> Any:
            return json.loads(path.read_text(encoding="utf-8"))

        report = analyze(read(args.plan), read(args.key), read(args.observations), source=args.source)
        _write_new(args.out, report)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
