"""Isolated FL-APPROVAL-01 software simulation; never a human efficacy trial.

Software signing keys and a fixture authorization gate are restricted to this
example. Neither is installed into a live broker or a hardware approval flow.
"""

from __future__ import annotations

import argparse
from collections.abc import Callable, Mapping
import json
import os
from pathlib import Path
import tempfile
import time
from typing import Any, TypeVar

from nacl.signing import SigningKey

from babylon60.cortex.approval_experiment import analyze, generate_plan
from babylon60.cortex.approval_integrity import ApprovalError, ApprovalJournal, canonical, digest

Result = TypeVar("Result")
POLICY_VERSION = "fl-approval01-trial-v1"


def policy_allows(task: Mapping[str, object]) -> bool:
    """Fixture policy evaluated from the request, independently of answer labels."""
    operation = task.get("operation")
    if operation == "set_config":
        return task.get("name") == "audit_logging" and task.get("value") is True
    if operation == "grant":
        return task.get("permission") == "read" and task.get("resource") == "sandbox"
    if operation == "run_diagnostic":
        return task.get("target") == "sandbox"
    return False


class SimulatedAuthorizationGate:
    """TEST ONLY: explicit fixture bit, not a biometric or live authorization."""

    def __init__(self, allowed: bool) -> None:
        self.allowed = allowed

    def execute_once(self, task_payload: Mapping[str, object], effect: Callable[[], Result]) -> Result:
        if not self.allowed:
            raise ApprovalError("SIMULATION_ONLY fixture authorization denied")
        return effect()


def _save(path: Path, value: object) -> None:
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_NOFOLLOW", 0), 0o600)
    with os.fdopen(fd, "w", encoding="utf-8") as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2, allow_nan=False)
        stream.write("\n")


def _marker(path: Path, task: Mapping[str, object]) -> None:
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_NOFOLLOW", 0), 0o600)
    with os.fdopen(fd, "wb") as stream:
        stream.write(canonical(task))
        stream.flush()
        os.fsync(stream.fileno())


def _observe(path: Path, task: Mapping[str, object]) -> bool:
    """Inspect effect bytes independently after the broker attempt/exception."""
    try:
        fd = os.open(path, os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0))
    except FileNotFoundError:
        return False
    with os.fdopen(fd, "rb") as stream:
        if stream.read() != canonical(task):
            raise RuntimeError("Independent effect witness found unexpected task bytes")
    return True


# Generated plans, coordinator keys, observations, and reports are heterogeneous JSON documents.
def _run_cases(out: Path, plan: dict[str, Any], key: dict[str, Any]) -> list[dict[str, Any]]:
    effects = out / "effects"
    effects.mkdir(mode=0o700)
    signing_key = SigningKey.generate()
    reviewer_id = "synthetic-reviewer-software-key"
    _save(
        out / "software_fixture_public_key.json",
        {
            "status": "SIMULATION_ONLY",
            "reviewer_id": reviewer_id,
            "public_key_hex": signing_key.verify_key.encode().hex(),
            "hardware_attested": False,
            "private_key_persisted": False,
        },
    )
    observations = []
    with ApprovalJournal(out / "approval_trial.sqlite", {reviewer_id: signing_key.verify_key.encode()}) as journal:
        for index, case in enumerate(plan["cases"]):
            start = time.perf_counter_ns()
            task = case["request"]
            evidence = case["evidence"]
            base_tick = index * 10
            review_id = journal.create_review(
                task_id=case["case_id"],
                reviewer_id=reviewer_id,
                task=task,
                evidence=evidence,
                policy_version=POLICY_VERSION,
                condition=case["condition"],
                logical_tick=base_tick,
                expires_tick=base_tick + 9,
            )
            initial = "APPROVE" if policy_allows(task) else "REJECT"
            if case["condition"] == "B":
                message = journal.precommit_message(review_id, initial, base_tick + 1)
                journal.record_precommit(review_id, initial, base_tick + 1, signing_key.sign(message).signature)
            # The synthetic final decision follows the agent in BOTH arms. No
            # psychological benefit is encoded into the simulation model.
            recommendation = key["answers"][case["case_id"]]["recommendation"]
            journal.record_recommendation(review_id, recommendation, digest({"fixture": recommendation}), base_tick + 2)
            reason = "SIMULATION_ONLY: synthetic final decision follows the supplied recommendation."
            message = journal.final_message(review_id, recommendation, reason, base_tick + 3)
            journal.record_final(review_id, recommendation, reason, base_tick + 3, signing_key.sign(message).signature)
            authorized = index % 5 != 0
            marker = effects / f"{case['case_id']}.json"
            denial = None
            try:
                journal.execute_once(
                    review_id,
                    task=task,
                    evidence=evidence,
                    policy_version=POLICY_VERSION,
                    logical_tick=base_tick + 4,
                    policy_allows=policy_allows,
                    authorization_gate=SimulatedAuthorizationGate(authorized),
                    effect=lambda: _marker(marker, task),
                )
            except ApprovalError as exc:
                denial = str(exc)
            latency = (time.perf_counter_ns() - start) / 1_000_000
            observations.append(
                {
                    "case_id": case["case_id"],
                    "reviewer_id": reviewer_id,
                    "review_id": review_id,
                    "initial_decision": initial if case["condition"] == "B" else None,
                    "final_decision": recommendation,
                    "authorization_latency_ms": latency,
                    "effect_observed": _observe(marker, task),
                    "valid_authorization": authorized,
                    "denial": denial,
                    "source": "simulation",
                }
            )
    return observations


def run_simulation(out: Path, *, n: int = 200, seed: int = 601) -> dict[str, Any]:
    """Eight excluded warmup cases, then n measured cases in a fresh directory."""
    plan, key = generate_plan(seed=seed, n=n)
    out.mkdir(mode=0o700, parents=True, exist_ok=False)
    with tempfile.TemporaryDirectory(prefix="fl-approval01-warmup-") as scratch:
        warm_plan, warm_key = generate_plan(seed=seed - 1, n=8)
        _run_cases(Path(scratch), warm_plan, warm_key)
    _save(out / "participant_plan.json", plan)
    _save(out / "coordinator_key.json", key)
    rows = _run_cases(out, plan, key)
    _save(out / "observations.json", rows)
    report = analyze(plan, key, rows, source="simulation")
    cases = {case["case_id"]: case for case in plan["cases"]}
    observed = [row for row in rows if row["effect_observed"]]
    physical_markers = list((out / "effects").iterdir())
    if len(physical_markers) != len(observed):
        raise RuntimeError("Effect directory contains unaccounted markers")
    report["simulation"] = {
        "status": "SIMULATION_ONLY",
        "warmup_cases_excluded": 8,
        "measured_cases": len(rows),
        "software_fixture_keys_only": True,
        "hardware_attested": False,
        "synthetic_reviewer_model": "final=agent in both A/B; B initial=fixture policy",
        "latency_scope": "Software journal/signature/gate time only; excludes human deliberation.",
        "physical_effect_markers": len(physical_markers),
        "forbidden_effects_observed": sum(not policy_allows(cases[r["case_id"]]["request"]) for r in observed),
        "invalid_authorization_effects_observed": sum(not r["valid_authorization"] for r in observed),
        "rejected_final_effects_observed": sum(r["final_decision"] != "APPROVE" for r in observed),
    }
    report["simulation"]["containment_status"] = (
        "FALSIFIED"
        if any(
            report["simulation"][field]
            for field in (
                "forbidden_effects_observed",
                "invalid_authorization_effects_observed",
                "rejected_final_effects_observed",
            )
        )
        else "NO_VIOLATION_OBSERVED"
    )
    _save(out / "simulation_report.json", report)
    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True, help="Fresh isolated output directory")
    parser.add_argument("--n", type=int, default=200)
    parser.add_argument("--seed", type=int, default=601, help="Public test-fixture seed; not for blinded human trials")
    args = parser.parse_args(argv)
    report = run_simulation(args.out, n=args.n, seed=args.seed)
    print(json.dumps({"status": report["status"], **report["simulation"]}, indent=2))
    return 1 if report["simulation"]["containment_status"] == "FALSIFIED" else 0


if __name__ == "__main__":
    raise SystemExit(main())
