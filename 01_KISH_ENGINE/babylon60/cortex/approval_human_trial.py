"""Prepare a supervised FL-APPROVAL-01 feasibility pilot; never activate CORTEX.

Allocation, recommendations and answer labels are coordinator-only. Imported
adjudication/enrollment declarations do not establish identity or signatures.
The pilot estimates feasibility, not a 30% efficacy claim.
"""

from __future__ import annotations

import argparse
from collections import defaultdict
import json
import math
import os
from pathlib import Path
import random
import secrets
from typing import Any

from blake3 import blake3

from babylon60.cortex.approval_trial_cases import bank_manifest, build_case_bank

SCHEMA = "FL-APPROVAL-01/human-pilot-v1"
PREPARED = "PREPARED_PENDING_HUMAN_ADJUDICATION"
DECISIONS = {"APPROVE", "REJECT"}


def _digest(value: object) -> str:
    data = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode()
    return blake3(b"FL-APPROVAL-01/human-pilot\x00" + data).hexdigest()


def _binding(pilot: dict[str, Any]) -> str:
    return _digest({key: pilot[key] for key in ("schema", "bank_digest", "answers_digest", "assignments", "roster")})


def _validate(pilot: dict[str, Any]) -> None:
    """Validate the design as well as its unkeyed corruption-detection digests."""
    try:
        if not isinstance(pilot, dict) or pilot.get("schema") != SCHEMA:
            raise ValueError("Unknown pilot schema")
        bank = _objects(pilot["bank"], "Case bank")
        assignments = _objects(pilot["assignments"], "Assignments")
        roster = _objects(pilot["roster"], "Reviewer roster")
        answers = pilot["answers"]
        if not isinstance(answers, dict) or len(bank) != 200 or len(answers) != 200:
            raise ValueError("Expected exactly 200 cases and matching coordinator answers")
        if len(assignments) != 12 or len(roster) != 12:
            raise ValueError("Expected exactly 12 unique assigned reviewers and roster slots")
        if _digest(bank) != pilot["bank_digest"] or _digest(answers) != pilot["answers_digest"]:
            raise ValueError("Pilot bank or coordinator key changed")
        if _binding(pilot) != pilot["pilot_digest"]:
            raise ValueError("Pilot assignment binding changed")
        for case in bank:
            _identifier(case["case_id"], "Case identifier")
            _identifier(case["family_id"], "Family identifier")
        manifest = bank_manifest(bank, answers)
        if manifest["case_count"] != 200 or manifest["family_count"] != 50:
            raise ValueError("Expected a 200-case bank in 50 policy families")
        by_case = {case["case_id"]: case for case in bank}
        by_reviewer: dict[str, dict[str, Any]] = {}
        pairs: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for assignment in assignments:
            reviewer = _identifier(assignment["reviewer_id"], "Reviewer identifier")
            pair = _identifier(assignment["pair_id"], "Pair identifier")
            if reviewer in by_reviewer:
                raise ValueError("Duplicate assigned reviewer")
            if assignment["condition"] not in {"A", "B"} or assignment["stratum"] not in {"operativo", "avanzado"}:
                raise ValueError("Unknown assigned condition or experience stratum")
            book = _objects(assignment["cases"], "Assigned case book")
            if len(book) != 24 or [entry.get("position") for entry in book] != list(range(1, 25)):
                raise ValueError("Each case book requires positions 1 through 24 in order")
            if any(type(entry["position"]) is not int for entry in book):
                raise ValueError("Case positions must be integers, excluding booleans")
            seen_cases, seen_families = set(), set()
            cells: dict[tuple[bool, str], int] = defaultdict(int)
            for entry in book:
                case_id = _identifier(entry["case_id"], "Assigned case identifier")
                recommendation = entry["recommendation"]
                if case_id not in by_case or recommendation not in DECISIONS:
                    raise ValueError("Unknown assigned case or recommendation")
                family = by_case[case_id]["family_id"]
                if case_id in seen_cases or family in seen_families:
                    raise ValueError("A reviewer must see distinct cases from 24 distinct families")
                seen_cases.add(case_id)
                seen_families.add(family)
                cells[(answers[case_id]["policy_allows"], recommendation)] += 1
            if len(cells) != 4 or set(cells.values()) != {6}:
                raise ValueError("Each case book requires six cases in every truth/recommendation cell")
            by_reviewer[reviewer] = assignment
            pairs[pair].append(assignment)
        if len(pairs) != 6:
            raise ValueError("Expected six matched reviewer pairs")
        stratum_pairs: dict[str, int] = defaultdict(int)
        for pair_rows in pairs.values():
            if len(pair_rows) != 2 or {row["condition"] for row in pair_rows} != {"A", "B"}:
                raise ValueError("Each matched pair requires one reviewer in A and one in B")
            if pair_rows[0]["stratum"] != pair_rows[1]["stratum"] or pair_rows[0]["cases"] != pair_rows[1]["cases"]:
                raise ValueError("Matched reviewers must share stratum, cases, recommendations and order")
            stratum_pairs[pair_rows[0]["stratum"]] += 1
        if dict(stratum_pairs) != {"operativo": 3, "avanzado": 3}:
            raise ValueError("Expected three matched pairs in each experience stratum")
        roster_ids = set()
        for slot in roster:
            reviewer = _identifier(slot["reviewer_id"], "Roster reviewer identifier")
            if reviewer in roster_ids or reviewer not in by_reviewer:
                raise ValueError("Roster reviewers must be unique and match assigned reviewers")
            if slot["stratum"] != by_reviewer[reviewer]["stratum"]:
                raise ValueError("Roster and assigned experience strata differ")
            roster_ids.add(reviewer)
        if roster_ids != set(by_reviewer):
            raise ValueError("Roster and assigned reviewers differ")
    except (KeyError, TypeError, AttributeError, OverflowError) as exc:
        raise ValueError("Malformed pilot structure") from exc


def _objects(value: object, field: str) -> list[dict[str, Any]]:
    if not isinstance(value, list) or any(not isinstance(row, dict) for row in value):
        raise ValueError(f"{field} must be a list of objects")
    return value


def _identifier(value: object, field: str) -> str:
    if not isinstance(value, str) or not value.strip() or value != value.strip():
        raise ValueError(f"{field} must be nonempty text without surrounding whitespace")
    return value


def generate_pilot(seed: int | None = None) -> dict[str, Any]:
    """Six independent reviewer pairs, each with a matched 24-case book.

    Three pairs belong to each experience stratum. A slot receives one arm for
    its entire session. Within each book, truth × recommendation has six cases
    per cell; each family occurs once. IDs and ordering do not encode truth.
    """
    if seed is not None and type(seed) is not int:
        raise ValueError("seed must be an integer")
    seed = secrets.randbits(256) if seed is None else seed
    rng = random.Random(seed)
    cases, answers = build_case_bank(seed=rng.getrandbits(256))
    by_family: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for case in cases:
        by_family[case["family_id"]].append(case)
    if len(cases) != 200 or len(by_family) != 50:
        raise ValueError("Expected 200 cases in 50 distinct families")
    for variants in by_family.values():
        if len(variants) != 4 or sum(answers[c["case_id"]]["policy_allows"] is True for c in variants) != 2:
            raise ValueError("Each family must supply two permitted and two forbidden variants")

    assignments, roster = [], []
    for stratum in ("operativo", "avanzado"):
        for _ in range(3):
            family_ids = rng.sample(sorted(by_family), 24)
            cells = [
                (truth, recommendation)
                for truth in (False, True)
                for recommendation in ("APPROVE", "REJECT")
                for _ in range(6)
            ]
            rng.shuffle(cells)
            book = []
            for family_id, (truth, recommendation) in zip(family_ids, cells):
                eligible = [c for c in by_family[family_id] if answers[c["case_id"]]["policy_allows"] is truth]
                case = rng.choice(eligible)
                book.append({"case_id": case["case_id"], "recommendation": recommendation})
            rng.shuffle(book)
            book = [{"position": index + 1, **entry} for index, entry in enumerate(book)]
            pair_id = f"P-{rng.getrandbits(64):016x}"
            conditions = ["A", "B"]
            rng.shuffle(conditions)
            for condition in conditions:
                reviewer_id = f"R-{rng.getrandbits(96):024x}"
                assignments.append(
                    {
                        "reviewer_id": reviewer_id,
                        "pair_id": pair_id,
                        "stratum": stratum,
                        "condition": condition,
                        "cases": json.loads(json.dumps(book)),
                    }
                )
                roster.append(
                    {
                        "reviewer_id": reviewer_id,
                        "stratum": stratum,
                        "consent": None,
                        "training_passed": None,
                        "human_attested": None,
                    }
                )
    rng.shuffle(assignments)
    rng.shuffle(roster)
    pilot = {
        "schema": SCHEMA,
        "status": PREPARED,
        "private_seed": seed,
        "bank": cases,
        "answers": answers,
        "bank_digest": _digest(cases),
        "answers_digest": _digest(answers),
        "assignments": assignments,
        "roster": roster,
        "activation_allowed": False,
        "bank_manifest": bank_manifest(cases, answers),
    }
    pilot["pilot_digest"] = _binding(pilot)
    return pilot


def adjudication_template(pilot: dict[str, Any]) -> dict[str, Any]:
    _validate(pilot)
    return {
        "schema": SCHEMA,
        "bank_digest": pilot["bank_digest"],
        "records": [
            {
                "case_id": case["case_id"],
                "evaluations": [
                    {
                        "adjudicator_id": None,
                        "decision": None,
                        "decisive_evidence": None,
                        "policy_clear": None,
                        "human_attested": None,
                    }
                    for _ in range(2)
                ],
            }
            for case in pilot["bank"]
        ],
    }


def merge_adjudications(pilot: dict[str, Any], first: dict[str, Any], second: dict[str, Any]) -> dict[str, Any]:
    """Join two independent forms without filling missing human evaluations.

    The top-level adjudicator identifier is copied into each evaluation. Blank
    decisions, missing citations and false attestations remain unchanged;
    validate_readiness, not this merge, evaluates their completeness.
    """
    _validate(pilot)
    expected = {case["case_id"] for case in pilot["bank"]}
    participant_ids = {row["reviewer_id"] for row in pilot["roster"]}
    merged_forms = []
    identities = []
    for form in (first, second):
        if form.get("schema") != SCHEMA or form.get("bank_digest") != pilot["bank_digest"]:
            raise ValueError("Adjudication form refers to a different schema or bank")
        identity = form.get("adjudicator_id")
        if not isinstance(identity, str) or not identity.strip() or identity.strip() in participant_ids:
            raise ValueError("A distinct adjudicator identifier outside reviewer slots is required")
        identity = identity.strip()
        indexed = {}
        records = form.get("records")
        if not isinstance(records, list) or len(records) != 200:
            raise ValueError("Each independent adjudication form must contain exactly 200 cases")
        for original in records:
            if not isinstance(original, dict):
                raise ValueError("Adjudication records must be objects")
            case_id = original.get("case_id")
            if not isinstance(case_id, str) or case_id not in expected or case_id in indexed:
                raise ValueError("Unknown or duplicate independent adjudication case")
            if "adjudicator_id" in original and original["adjudicator_id"] != identity:
                raise ValueError("Record adjudicator differs from its independent form")
            evaluation = {key: value for key, value in original.items() if key != "case_id"}
            evaluation["adjudicator_id"] = identity
            indexed[case_id] = evaluation
        if set(indexed) != expected:
            raise ValueError("Independent adjudication form has missing cases")
        identities.append(identity)
        merged_forms.append(indexed)
    if identities[0] == identities[1]:
        raise ValueError("Two distinct adjudicators are required")
    return {
        "schema": SCHEMA,
        "bank_digest": pilot["bank_digest"],
        "records": [
            {"case_id": case["case_id"], "evaluations": [form[case["case_id"]] for form in merged_forms]}
            for case in pilot["bank"]
        ],
    }


def validate_readiness(
    pilot: dict[str, Any],
    adjudications: dict[str, Any] | None = None,
    enrollment: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Check declared prerequisites, never manufacture their human completion.

    Two distinct reviewers must independently agree with the frozen reference
    decision on every case and cite evidence. Disagreement requires revising
    the bank and a fresh pair of evaluations; no coordinator tie-break exists.
    """
    _validate(pilot)
    adjudications = {"bank_digest": pilot["bank_digest"], "records": []} if adjudications is None else adjudications
    if not isinstance(adjudications, dict):
        raise ValueError("Adjudications must be an object")
    if "schema" in adjudications and adjudications["schema"] != SCHEMA:
        raise ValueError("Unknown adjudication schema")
    if adjudications.get("bank_digest") != pilot["bank_digest"]:
        raise ValueError("Adjudication refers to a different bank")
    answers = pilot["answers"]
    indexed: dict[str, dict[str, Any]] = {}
    for record in _objects(adjudications.get("records", []), "Adjudication records"):
        case_id = _identifier(record.get("case_id"), "Adjudication case identifier")
        if case_id not in answers or case_id in indexed:
            raise ValueError("Unknown or duplicate adjudication case")
        indexed[case_id] = record
    unresolved = []
    adjudicator_ids: set[str] = set()
    for case_id, answer in answers.items():
        evaluations = _objects(indexed.get(case_id, {}).get("evaluations", []), "Case evaluations")
        valid = len(evaluations) == 2
        identities = set()
        for entry in evaluations:
            identity = entry.get("adjudicator_id")
            citation = entry.get("decisive_evidence")
            if identity is not None and not isinstance(identity, str):
                raise ValueError("Adjudicator identifier must be text or null")
            if citation is not None and not isinstance(citation, str):
                raise ValueError("Decisive evidence must be text or null")
            decision = entry.get("decision")
            if decision is not None and (not isinstance(decision, str) or decision not in DECISIONS):
                raise ValueError("Adjudicator decision must be APPROVE, REJECT or null")
            for field in ("policy_clear", "human_attested"):
                if entry.get(field) is not None and type(entry[field]) is not bool:
                    raise ValueError(f"{field} must be boolean or null")
            valid = valid and isinstance(identity, str) and bool(identity.strip())
            valid = valid and decision == answer["reference_decision"]
            valid = valid and isinstance(citation, str) and bool(citation.strip())
            valid = valid and entry.get("policy_clear") is True and entry.get("human_attested") is True
            if isinstance(identity, str):
                identities.add(identity.strip())
                adjudicator_ids.add(identity.strip())
        if not valid or len(identities) != 2:
            unresolved.append(case_id)
    expected = {row["reviewer_id"]: row for row in pilot["roster"]}
    enrolled: dict[str, dict[str, Any]] = {}
    for record in _objects(enrollment if enrollment is not None else [], "Enrollment records"):
        reviewer_id = _identifier(record.get("reviewer_id"), "Enrolled reviewer identifier")
        if reviewer_id not in expected or reviewer_id in enrolled:
            raise ValueError("Unknown or duplicate enrolled reviewer")
        for field in ("consent", "training_passed", "human_attested"):
            if record.get(field) is not None and type(record[field]) is not bool:
                raise ValueError(f"{field} must be boolean or null")
        enrolled[reviewer_id] = record
    missing_reviewers = [
        reviewer_id
        for reviewer_id, slot in expected.items()
        if not (
            reviewer_id not in adjudicator_ids
            and enrolled.get(reviewer_id, {}).get("stratum") == slot["stratum"]
            and all(
                enrolled.get(reviewer_id, {}).get(field) is True
                for field in ("consent", "training_passed", "human_attested")
            )
        )
    ]
    ready = not unresolved and not missing_reviewers
    return {
        "schema": SCHEMA,
        "pilot_digest": pilot["pilot_digest"],
        "status": "DECLARED_PREREQUISITES_COMPLETE" if ready else PREPARED,
        "ready_for_pilot": ready,
        "adjudicated_cases": len(answers) - len(unresolved),
        "unresolved_case_ids": unresolved,
        "pending_reviewer_ids": missing_reviewers,
        "provenance": "IMPORTED_DECLARATIONS_NOT_IDENTITY_OR_SIGNATURE_VERIFIED",
        "confirmatory_trial_ready": False,
        "activation_allowed": False,
    }


def _rate(numerator: int, denominator: int) -> dict[str, int | float | None]:
    return {
        "numerator": numerator,
        "denominator": denominator,
        "value": numerator / denominator if denominator else None,
    }


def analyze_pilot(pilot: dict[str, Any], observations: list[dict[str, Any]], *, source: str) -> dict[str, Any]:
    """Reviewer-level descriptive summary; no confidence interval or p-value.

    Observations are declared data, not proof of participant identity. A B
    observation without an independently verified precommit remains in the
    descriptive counts and is flagged as a protocol deviation, not discarded.
    """
    _validate(pilot)
    if source not in {"human", "simulation"}:
        raise ValueError("Explicit source human or simulation is required")
    assignments = {row["reviewer_id"]: row for row in pilot["assignments"]}
    assigned = {reviewer: {entry["case_id"]: entry for entry in row["cases"]} for reviewer, row in assignments.items()}
    rows: dict[str, list[dict[str, Any]]] = defaultdict(list)
    seen = set()
    for original in _objects(observations, "Pilot observations"):
        row = dict(original)
        if "source" in row and row["source"] != source:
            raise ValueError("Observation source contradicts the declared dataset source")
        reviewer, case_id = row.get("reviewer_id"), row.get("case_id")
        if (
            not isinstance(reviewer, str)
            or not isinstance(case_id, str)
            or reviewer not in assigned
            or case_id not in assigned[reviewer]
            or (reviewer, case_id) in seen
        ):
            raise ValueError("Unknown, unassigned or duplicate pilot observation")
        seen.add((reviewer, case_id))
        if not isinstance(row.get("final_decision"), str) or row["final_decision"] not in DECISIONS:
            raise ValueError("Invalid final decision")
        if row.get("initial_decision") is not None and (
            not isinstance(row["initial_decision"], str) or row["initial_decision"] not in DECISIONS
        ):
            raise ValueError("Invalid initial decision")
        elapsed = row.get("case_elapsed_ms")
        if not isinstance(elapsed, (int, float)) or isinstance(elapsed, bool):
            raise ValueError("case_elapsed_ms must be finite and nonnegative")
        try:
            finite_elapsed = math.isfinite(elapsed)
        except OverflowError:
            finite_elapsed = False
        if not finite_elapsed or elapsed < 0:
            raise ValueError("case_elapsed_ms must be finite and nonnegative")
        for field in ("precommit_verified", "recorded_before_recommendation"):
            if row.get(field) is not None and type(row[field]) is not bool:
                raise ValueError(f"{field} must be boolean when supplied")
        if isinstance(row.get("precommit_record_id"), str):
            row["precommit_record_id"] = row["precommit_record_id"].strip()
        rows[reviewer].append(row)
    commitment_counts: dict[str, int] = defaultdict(int)
    for reviewer, observed in rows.items():
        if assignments[reviewer]["condition"] == "B":
            for row in observed:
                reference = row.get("precommit_record_id")
                if isinstance(reference, str) and reference.strip():
                    commitment_counts[reference] += 1
    summaries = []
    for reviewer, assignment in assignments.items():
        observed = rows[reviewer]
        primary = [
            r
            for r in observed
            if not pilot["answers"][r["case_id"]]["policy_allows"]
            and assigned[reviewer][r["case_id"]]["recommendation"] == "APPROVE"
        ]
        legitimate = [r for r in observed if pilot["answers"][r["case_id"]]["policy_allows"]]
        if assignment["condition"] == "B":
            violations = sum(
                not (
                    r.get("initial_decision") in DECISIONS
                    and r.get("precommit_verified") is True
                    and r.get("recorded_before_recommendation") is True
                    and isinstance(r.get("precommit_record_id"), str)
                    and bool(r["precommit_record_id"].strip())
                    and commitment_counts[r["precommit_record_id"]] == 1
                )
                for r in observed
            )
        else:
            violations = sum(r.get("initial_decision") is not None for r in observed)
        summaries.append(
            {
                "reviewer_id": reviewer,
                "condition": assignment["condition"],
                "pair_id": assignment["pair_id"],
                "stratum": assignment["stratum"],
                "observed": len(observed),
                "planned": 24,
                "complete": len(observed) == 24,
                "primary_incorrect_approval_rate": _rate(
                    sum(r["final_decision"] == "APPROVE" for r in primary), len(primary)
                ),
                "legitimate_approval_rate": _rate(
                    sum(r["final_decision"] == "APPROVE" for r in legitimate), len(legitimate)
                ),
                "protocol_deviations": violations,
            }
        )
    groups = {}
    for arm in ("A", "B"):
        group = [r for r in summaries if r["condition"] == arm]
        groups[arm] = {"reviewers_planned": len(group), "reviewers_complete": sum(r["complete"] for r in group)}
        for metric in ("primary_incorrect_approval_rate", "legitimate_approval_rate"):
            values = [r[metric]["value"] for r in group if r[metric]["value"] is not None]
            groups[arm]["mean_reviewer_" + metric] = {
                "value": sum(values) / len(values) if values else None,
                "reviewer_denominator": len(values),
            }
    return {
        "schema": SCHEMA,
        "pilot_digest": pilot["pilot_digest"],
        "source": source,
        "status": "SIMULATION_ONLY" if source == "simulation" else "PILOT_DESCRIPTIVE_ONLY",
        "observed_decisions": len(seen),
        "planned_decisions": 288,
        "complete": len(seen) == 288,
        "reviewers": summaries,
        "conditions": groups,
        "data_provenance": "IMPORTED_DECLARATIONS_NOT_IDENTITY_OR_SIGNATURE_VERIFIED",
        "hypothesis_confirmed": False,
        "activation_allowed": False,
        "notes": [
            "The reviewer is the unit of assignment and descriptive aggregation.",
            "This feasibility pilot cannot validate a 30% efficacy reduction.",
            "Incomplete records and precommit deviations are retained and reported.",
            "Source human is a declaration, not independently established provenance.",
        ],
    }


def _write_new(path: Path, value: object, *, private: bool) -> None:
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_NOFOLLOW", 0)
    fd = os.open(path, flags, 0o600 if private else 0o644)
    with os.fdopen(fd, "w", encoding="utf-8") as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2, allow_nan=False)
        stream.write("\n")


def export_pilot(out: Path, *, seed: int | None = None) -> dict[str, Any]:
    pilot = generate_pilot(seed)
    out.mkdir(mode=0o700, parents=True, exist_ok=False)
    coordinator, participant = out / "coordinator", out / "participant"
    coordinator.mkdir(mode=0o700)
    participant.mkdir(mode=0o755)
    _write_new(coordinator / "pilot_private.json", pilot, private=True)
    _write_new(
        coordinator / "casebank_key.json",
        {"bank_digest": pilot["bank_digest"], "answers_digest": pilot["answers_digest"], "answers": pilot["answers"]},
        private=True,
    )
    _write_new(coordinator / "bank_cases.json", pilot["bank"], private=True)
    _write_new(
        coordinator / "assignment_key.json",
        {
            "pilot_digest": pilot["pilot_digest"],
            "private_seed": pilot["private_seed"],
            "assignments": pilot["assignments"],
        },
        private=True,
    )
    _write_new(coordinator / "adjudication_template.json", adjudication_template(pilot), private=True)
    _write_new(coordinator / "enrollment_template.json", pilot["roster"], private=True)
    _write_new(coordinator / "observations_template.json", [], private=True)
    _write_new(coordinator / "readiness.json", validate_readiness(pilot), private=True)
    _write_new(
        participant / "participant_information.json",
        {
            "schema": SCHEMA,
            "language": "es",
            "status": "MATERIAL_INFORMATIVO",
            "instructions": [
                "Participarás voluntariamente en decisiones ficticias sobre solicitudes y reglas explícitas.",
                "Las recomendaciones del asistente pueden ser acertadas o erróneas y se varían deliberadamente.",
                "Decide APRUEBO o RECHAZO según la evidencia. Ninguna respuesta ejecutará una acción real.",
                "En algunas sesiones decidirás antes de conocer la recomendación y después podrás cambiar de opinión.",
                "Puedes pedir una pausa o terminar la sesión. Se usará un código de participante, sin nombres en las respuestas.",
                "El coordinador explicará la conservación de datos y recogerá tu consentimiento antes de empezar.",
            ],
        },
        private=False,
    )
    _write_new(participant / "response_template.json", [], private=False)
    manifest = {
        "schema": SCHEMA,
        "status": PREPARED,
        "pilot_digest": pilot["pilot_digest"],
        "bank_digest": pilot["bank_digest"],
        "case_count": 200,
        "family_count": 50,
        "reviewer_slots": 12,
        "matched_pairs": 6,
        "cases_per_reviewer": 24,
        "total_planned_decisions": 288,
        "actual_human_observations": 0,
        "activation_allowed": False,
        "release_note": "Coordinator material requires two human case evaluations and reviewer enrollment.",
    }
    _write_new(out / "manifest.json", manifest, private=False)
    return manifest


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    prepare = commands.add_parser("prepare")
    prepare.add_argument("--out", type=Path, required=True)
    prepare.add_argument("--seed", type=int)
    merge = commands.add_parser("merge-adjudications")
    merge.add_argument("--pilot", type=Path, required=True)
    merge.add_argument("--first", type=Path, required=True)
    merge.add_argument("--second", type=Path, required=True)
    merge.add_argument("--out", type=Path, required=True)
    for name in ("readiness", "analyze"):
        command = commands.add_parser(name)
        command.add_argument("--pilot", type=Path, required=True)
        command.add_argument("--out", type=Path, required=True)
        if name == "readiness":
            command.add_argument("--adjudications", type=Path)
            command.add_argument("--enrollment", type=Path)
        else:
            command.add_argument("--observations", type=Path, required=True)
            command.add_argument("--source", choices=("human", "simulation"), required=True)
    args = parser.parse_args(argv)

    def read(path: Path | None) -> Any:
        return json.loads(path.read_text(encoding="utf-8")) if path else None

    if args.command == "prepare":
        result = export_pilot(args.out, seed=args.seed)
    elif args.command == "merge-adjudications":
        result = merge_adjudications(read(args.pilot), read(args.first), read(args.second))
        _write_new(args.out, result, private=True)
    elif args.command == "readiness":
        result = validate_readiness(read(args.pilot), read(args.adjudications), read(args.enrollment))
        _write_new(args.out, result, private=True)
    else:
        result = analyze_pilot(read(args.pilot), read(args.observations), source=args.source)
        _write_new(args.out, result, private=True)
    summary = (
        {"status": "ADJUDICATION_DECLARATIONS_MERGED", "activation_allowed": False}
        if (args.command == "merge-adjudications")
        else {key: result[key] for key in ("status", "activation_allowed")}
    )
    print(json.dumps(summary, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
