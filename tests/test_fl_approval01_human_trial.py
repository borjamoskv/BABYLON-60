"""Feasibility materials stay blinded and cannot authorize CORTEX activation."""

from collections import Counter, defaultdict
import copy
import json

import pytest

from babylon60.cortex.approval_human_trial import (
    PREPARED,
    _binding,
    _digest,
    adjudication_template,
    analyze_pilot,
    export_pilot,
    generate_pilot,
    main,
    merge_adjudications,
    validate_readiness,
)


@pytest.fixture
def pilot():
    return generate_pilot(seed=42601)


def completed_prerequisites(pilot):
    """Synthetic declarations, not human participation or production readiness."""
    adjudications = adjudication_template(pilot)
    for record in adjudications["records"]:
        for index, entry in enumerate(record["evaluations"]):
            entry.update(
                adjudicator_id=f"software-fixture-adjudicator-{index}",
                decision=pilot["answers"][record["case_id"]]["reference_decision"],
                decisive_evidence="Synthetic fixture citation, not an actual human evaluation.",
                policy_clear=True,
                human_attested=True,
            )
    enrollment = copy.deepcopy(pilot["roster"])
    for entry in enrollment:
        entry.update(consent=True, training_passed=True, human_attested=True)
    return adjudications, enrollment


def independent_forms(pilot):
    forms = []
    for index in range(2):
        forms.append(
            {
                "schema": pilot["schema"],
                "bank_digest": pilot["bank_digest"],
                "adjudicator_id": f"independent-fixture-{index}",
                "records": [
                    {
                        "case_id": case["case_id"],
                        "decision": None,
                        "decisive_evidence": None,
                        "policy_clear": None,
                        "human_attested": None,
                    }
                    for case in pilot["bank"]
                ],
            }
        )
    return forms


def observations_for(pilot):
    rows = []
    for reviewer in pilot["assignments"]:
        for entry in reviewer["cases"]:
            correct = pilot["answers"][entry["case_id"]]["reference_decision"]
            rows.append(
                {
                    "reviewer_id": reviewer["reviewer_id"],
                    "case_id": entry["case_id"],
                    "initial_decision": correct if reviewer["condition"] == "B" else None,
                    "final_decision": entry["recommendation"],
                    "case_elapsed_ms": 10,
                    "precommit_record_id": f"synthetic-{reviewer['reviewer_id']}-{entry['case_id']}",
                    "precommit_verified": True,
                    "recorded_before_recommendation": True,
                }
            )
    return rows


def test_allocation_is_reproducible_paired_and_balanced(pilot):
    assert pilot == generate_pilot(seed=42601)
    assert pilot["pilot_digest"] != generate_pilot(seed=42602)["pilot_digest"]
    by_pair = defaultdict(list)
    bank = {row["case_id"]: row for row in pilot["bank"]}
    for row in pilot["assignments"]:
        by_pair[row["pair_id"]].append(row)
        counts = Counter(
            (pilot["answers"][entry["case_id"]]["policy_allows"], entry["recommendation"]) for entry in row["cases"]
        )
        assert set(counts.values()) == {6} and len(counts) == 4
        assert len({bank[entry["case_id"]]["family_id"] for entry in row["cases"]}) == 24
    assert len(by_pair) == 6
    assert Counter(row["stratum"] for row in pilot["assignments"]) == {"operativo": 6, "avanzado": 6}
    for rows in by_pair.values():
        assert len(rows) == 2
        assert {row["condition"] for row in rows} == {"A", "B"}
        assert rows[0]["cases"] == rows[1]["cases"]
        assert rows[0]["stratum"] == rows[1]["stratum"]


def test_prepared_materials_have_no_fabricated_humans(pilot):
    result = validate_readiness(pilot)
    assert result["status"] == PREPARED
    assert result["adjudicated_cases"] == 0
    assert len(result["unresolved_case_ids"]) == 200
    assert len(result["pending_reviewer_ids"]) == 12
    assert not result["ready_for_pilot"] and not result["activation_allowed"]
    assert all(row["consent"] is None for row in pilot["roster"])


def test_two_independent_adjudications_and_enrollment_are_needed(pilot):
    adjudications, enrollment = completed_prerequisites(pilot)
    result = validate_readiness(pilot, adjudications, enrollment)
    assert result["ready_for_pilot"]
    assert not result["activation_allowed"] and not result["confirmatory_trial_ready"]
    adjudications["records"][0]["evaluations"][1]["adjudicator_id"] = "software-fixture-adjudicator-0"
    assert not validate_readiness(pilot, adjudications, enrollment)["ready_for_pilot"]


def test_disagreement_requires_case_revision_not_a_tiebreak(pilot):
    adjudications, enrollment = completed_prerequisites(pilot)
    evaluation = adjudications["records"][0]["evaluations"][1]
    evaluation["decision"] = "REJECT" if evaluation["decision"] == "APPROVE" else "APPROVE"
    result = validate_readiness(pilot, adjudications, enrollment)
    assert result["adjudicated_cases"] == 199
    assert not result["ready_for_pilot"]
    adjudications["records"][0]["coordinator_override"] = "APPROVED"
    assert not validate_readiness(pilot, adjudications, enrollment)["ready_for_pilot"]


@pytest.mark.parametrize("mutation", ["bank", "answers", "assignment", "adjudication_bank", "duplicate", "unknown"])
def test_altered_inputs_and_unassigned_humans_are_rejected(pilot, mutation):
    adjudications, enrollment = completed_prerequisites(pilot)
    if mutation == "bank":
        pilot["bank"][0]["title"] += " altered"
    elif mutation == "answers":
        answer = next(iter(pilot["answers"].values()))
        answer["policy_allows"] = not answer["policy_allows"]
    elif mutation == "assignment":
        pilot["assignments"][0]["condition"] = "BOTH"
    elif mutation == "adjudication_bank":
        adjudications["bank_digest"] = "00"
    elif mutation == "duplicate":
        enrollment.append(copy.deepcopy(enrollment[0]))
    else:
        enrollment[0]["reviewer_id"] = "unassigned"
    with pytest.raises(ValueError):
        validate_readiness(pilot, adjudications, enrollment)


def test_export_separates_sensitive_material_and_has_empty_observations(tmp_path):
    destination = tmp_path / "pilot"
    result = export_pilot(destination, seed=42601)
    assert result["actual_human_observations"] == 0
    assert result["activation_allowed"] is False
    participant_text = "\n".join(p.read_text() for p in (destination / "participant").glob("*"))
    for secret in ('"private_seed"', '"policy_allows"', '"recommendation"', '"assignments"', '"answers"'):
        assert secret not in participant_text
    for path in (destination / "coordinator").glob("*"):
        assert path.stat().st_mode & 0o777 == 0o600
    assert (destination / "coordinator").stat().st_mode & 0o777 == 0o700
    assert json.loads((destination / "coordinator/observations_template.json").read_text()) == []
    with pytest.raises(FileExistsError):
        export_pilot(destination)


def test_pilot_analysis_aggregates_reviewers_without_claiming_efficacy(pilot):
    result = analyze_pilot(pilot, observations_for(pilot), source="simulation")
    assert result["status"] == "SIMULATION_ONLY" and result["complete"]
    assert result["observed_decisions"] == 288 and len(result["reviewers"]) == 12
    assert not result["hypothesis_confirmed"] and not result["activation_allowed"]
    for arm in result["conditions"].values():
        assert arm["reviewers_complete"] == 6
        assert arm["mean_reviewer_primary_incorrect_approval_rate"] == {"value": 1, "reviewer_denominator": 6}
        assert arm["mean_reviewer_legitimate_approval_rate"] == {"value": 0.5, "reviewer_denominator": 6}
    assert all(row["protocol_deviations"] == 0 for row in result["reviewers"])


def test_missing_precommits_are_reported_not_silently_dropped(pilot):
    rows = observations_for(pilot)
    b_id = next(row["reviewer_id"] for row in pilot["assignments"] if row["condition"] == "B")
    for row in rows:
        if row["reviewer_id"] == b_id:
            row.pop("precommit_verified")
    result = analyze_pilot(pilot, rows, source="human")
    assert result["observed_decisions"] == 288
    assert next(r for r in result["reviewers"] if r["reviewer_id"] == b_id)["protocol_deviations"] == 24
    assert not result["activation_allowed"]


def test_reused_commitment_references_are_protocol_deviations(pilot):
    rows = observations_for(pilot)
    b_id = next(row["reviewer_id"] for row in pilot["assignments"] if row["condition"] == "B")
    for row in rows:
        if row["reviewer_id"] == b_id:
            row["precommit_record_id"] = "reused-reference"
    result = analyze_pilot(pilot, rows, source="simulation")
    assert next(r for r in result["reviewers"] if r["reviewer_id"] == b_id)["protocol_deviations"] == 24


def test_case_adjudicator_cannot_also_fill_a_trial_reviewer_slot(pilot):
    adjudications, enrollment = completed_prerequisites(pilot)
    reviewer = enrollment[0]["reviewer_id"]
    adjudications["records"][0]["evaluations"][0]["adjudicator_id"] = reviewer
    result = validate_readiness(pilot, adjudications, enrollment)
    assert reviewer in result["pending_reviewer_ids"]
    assert not result["ready_for_pilot"]


def test_empty_and_incomplete_records_are_unknown_not_zero(pilot):
    empty = analyze_pilot(pilot, [], source="human")
    assert not empty["complete"]
    assert all(
        group["mean_reviewer_primary_incorrect_approval_rate"]["value"] is None
        for group in empty["conditions"].values()
    )
    rows = observations_for(pilot)
    partial = analyze_pilot(pilot, rows[:-1], source="human")
    assert not partial["complete"] and partial["observed_decisions"] == 287
    with pytest.raises(ValueError):
        analyze_pilot(pilot, rows + [rows[0]], source="human")


def test_cli_prepare_and_empty_analysis_roundtrip(tmp_path):
    destination = tmp_path / "pilot"
    assert main(["prepare", "--out", str(destination), "--seed", "42601"]) == 0
    output = tmp_path / "empty-report.json"
    assert (
        main(
            [
                "analyze",
                "--pilot",
                str(destination / "coordinator/pilot_private.json"),
                "--observations",
                str(destination / "coordinator/observations_template.json"),
                "--source",
                "human",
                "--out",
                str(output),
            ]
        )
        == 0
    )
    assert json.loads(output.read_text())["hypothesis_confirmed"] is False


def test_merging_independent_blank_forms_does_not_invent_evaluations(pilot):
    first, second = independent_forms(pilot)
    second["records"].reverse()
    merged = merge_adjudications(pilot, first, second)
    assert len(merged["records"]) == 200
    for row in merged["records"]:
        assert {entry["adjudicator_id"] for entry in row["evaluations"]} == {
            first["adjudicator_id"],
            second["adjudicator_id"],
        }
        assert all(entry["decision"] is None and entry["human_attested"] is None for entry in row["evaluations"])
    ready = validate_readiness(pilot, merged)
    assert ready["adjudicated_cases"] == 0 and not ready["activation_allowed"]


@pytest.mark.parametrize(
    "mutation", ["bank", "same_id", "blank_id", "participant_id", "missing", "extra", "duplicate", "unknown"]
)
def test_merge_rejects_foreign_incomplete_or_reused_identity_forms(pilot, mutation):
    first, second = independent_forms(pilot)
    if mutation == "bank":
        second["bank_digest"] = "foreign"
    elif mutation == "same_id":
        second["adjudicator_id"] = " " + first["adjudicator_id"] + " "
    elif mutation == "blank_id":
        second["adjudicator_id"] = " "
    elif mutation == "participant_id":
        second["adjudicator_id"] = pilot["roster"][0]["reviewer_id"]
    elif mutation == "missing":
        second["records"].pop()
    elif mutation == "extra":
        second["records"].append(copy.deepcopy(second["records"][0]))
    elif mutation == "duplicate":
        second["records"][1]["case_id"] = second["records"][0]["case_id"]
    else:
        second["records"][0]["case_id"] = "unplanned-case"
    with pytest.raises(ValueError):
        merge_adjudications(pilot, first, second)


def test_complete_synthetic_merges_preserve_false_human_attestation(pilot):
    first, second = independent_forms(pilot)
    for form in (first, second):
        for row in form["records"]:
            row.update(
                decision=pilot["answers"][row["case_id"]]["reference_decision"],
                decisive_evidence="Software test fixture, never an actual human evaluation.",
                policy_clear=True,
                human_attested=False,
            )
    merged = merge_adjudications(pilot, first, second)
    _, enrollment = completed_prerequisites(pilot)
    ready = validate_readiness(pilot, merged, enrollment)
    assert ready["adjudicated_cases"] == 0 and not ready["ready_for_pilot"]
    assert not ready["activation_allowed"]


def test_cli_merges_independent_forms(tmp_path, pilot):
    first, second = independent_forms(pilot)
    paths = {}
    for name, value in (("pilot", pilot), ("first", first), ("second", second)):
        paths[name] = tmp_path / f"{name}.json"
        paths[name].write_text(json.dumps(value))
    output = tmp_path / "combined.json"
    assert (
        main(
            [
                "merge-adjudications",
                "--pilot",
                str(paths["pilot"]),
                "--first",
                str(paths["first"]),
                "--second",
                str(paths["second"]),
                "--out",
                str(output),
            ]
        )
        == 0
    )
    assert output.stat().st_mode & 0o777 == 0o600
    assert len(json.loads(output.read_text())["records"]) == 200


def rebind_fixture(pilot):
    """Unkeyed hashes detect corruption; recomputing them cannot validate design."""
    pilot["bank_digest"] = _digest(pilot["bank"])
    pilot["answers_digest"] = _digest(pilot["answers"])
    pilot["pilot_digest"] = _binding(pilot)


@pytest.mark.parametrize(
    "mutation",
    [
        "missing_answer",
        "extra_answer",
        "false_reference",
        "duplicate_bank_case",
        "duplicate_roster",
        "missing_roster",
        "unknown_roster",
        "roster_stratum",
        "duplicate_assignment",
        "condition",
        "same_arm_pair",
        "merged_pairs",
        "different_pair_order",
        "different_pair_strata",
        "stratum_balance",
        "short_book",
        "duplicate_assigned_case",
        "duplicate_family",
        "unknown_case",
        "recommendation",
        "bool_position",
        "position_order",
        "cell_balance",
    ],
)
def test_rehashed_malformed_design_is_still_rejected(pilot, mutation):
    """Regression: an imported, self-consistent digest is not structural evidence."""
    first = pilot["assignments"][0]
    pair = [row for row in pilot["assignments"] if row["pair_id"] == first["pair_id"]]
    by_id = {row["case_id"]: row for row in pilot["bank"]}
    book = first["cases"]
    if mutation == "missing_answer":
        del pilot["answers"][next(iter(pilot["answers"]))]
    elif mutation == "extra_answer":
        pilot["answers"]["unplanned"] = copy.deepcopy(next(iter(pilot["answers"].values())))
    elif mutation == "false_reference":
        answer = next(iter(pilot["answers"].values()))
        answer["policy_allows"] = not answer["policy_allows"]
        answer["reference_decision"] = "APPROVE" if answer["policy_allows"] else "REJECT"
    elif mutation == "duplicate_bank_case":
        pilot["bank"][1] = copy.deepcopy(pilot["bank"][0])
    elif mutation == "duplicate_roster":
        pilot["roster"] = [copy.deepcopy(pilot["roster"][0]) for _ in range(12)]
    elif mutation == "missing_roster":
        pilot["roster"].pop()
    elif mutation == "unknown_roster":
        pilot["roster"][0]["reviewer_id"] = "unassigned-slot"
    elif mutation == "roster_stratum":
        slot = pilot["roster"][0]
        slot["stratum"] = "avanzado" if slot["stratum"] == "operativo" else "operativo"
    elif mutation == "duplicate_assignment":
        pilot["assignments"][1]["reviewer_id"] = first["reviewer_id"]
    elif mutation == "condition":
        first["condition"] = "BOTH"
    elif mutation == "same_arm_pair":
        pair[1]["condition"] = pair[0]["condition"]
    elif mutation == "merged_pairs":
        other_pair = next(row["pair_id"] for row in pilot["assignments"] if row["pair_id"] != first["pair_id"])
        for row in pair:
            row["pair_id"] = other_pair
    elif mutation == "different_pair_order":
        book[0], book[1] = book[1], book[0]
        book[0]["position"], book[1]["position"] = 1, 2
    elif mutation == "different_pair_strata":
        first["stratum"] = "avanzado" if first["stratum"] == "operativo" else "operativo"
        next(row for row in pilot["roster"] if row["reviewer_id"] == first["reviewer_id"])["stratum"] = first["stratum"]
    elif mutation == "stratum_balance":
        for row in pair:
            row["stratum"] = "avanzado" if row["stratum"] == "operativo" else "operativo"
            next(slot for slot in pilot["roster"] if slot["reviewer_id"] == row["reviewer_id"])["stratum"] = row[
                "stratum"
            ]
    elif mutation == "short_book":
        book.pop()
    elif mutation == "duplicate_assigned_case":
        book[1]["case_id"] = book[0]["case_id"]
    elif mutation == "duplicate_family":
        first_case = by_id[book[0]["case_id"]]
        variant = next(
            row
            for row in pilot["bank"]
            if row["family_id"] == first_case["family_id"] and row["case_id"] != first_case["case_id"]
        )
        book[1]["case_id"] = variant["case_id"]
    elif mutation == "unknown_case":
        book[0]["case_id"] = "unplanned-case"
    elif mutation == "recommendation":
        book[0]["recommendation"] = "MAYBE"
    elif mutation == "bool_position":
        book[0]["position"] = True
    elif mutation == "position_order":
        book[0]["position"], book[1]["position"] = 2, 1
    else:
        book[0]["recommendation"] = "REJECT" if book[0]["recommendation"] == "APPROVE" else "APPROVE"
    rebind_fixture(pilot)
    with pytest.raises(ValueError):
        validate_readiness(pilot)


def test_duplicate_roster_cannot_report_ready_with_one_enrollment(pilot):
    """The observed pre-fix counterexample declared twelve slots ready from one."""
    adjudications, enrollment = completed_prerequisites(pilot)
    pilot["roster"] = [copy.deepcopy(pilot["roster"][0]) for _ in range(12)]
    rebind_fixture(pilot)
    with pytest.raises(ValueError):
        validate_readiness(pilot, adjudications, enrollment[:1])


def test_missing_answer_cannot_report_199_adjudications_ready_for_200_cases(pilot):
    adjudications, enrollment = completed_prerequisites(pilot)
    removed = next(iter(pilot["answers"]))
    del pilot["answers"][removed]
    adjudications["records"] = [row for row in adjudications["records"] if row["case_id"] != removed]
    rebind_fixture(pilot)
    with pytest.raises(ValueError):
        validate_readiness(pilot, adjudications, enrollment)


def test_valid_pilot_validation_preserves_existing_digests_and_contents(pilot):
    before = copy.deepcopy(pilot)
    assert validate_readiness(pilot)["adjudicated_cases"] == 0
    analyze_pilot(pilot, [], source="human")
    assert pilot == before


@pytest.mark.parametrize(
    "mutation",
    [
        "adjudications_list",
        "records_dict",
        "record_null",
        "case_id_list",
        "evaluations_null",
        "evaluation_null",
        "identity_list",
        "decision_list",
        "citation_dict",
        "attestation_string",
        "enrollment_dict",
        "enrolled_null",
        "reviewer_list",
        "consent_string",
    ],
)
def test_malformed_readiness_inputs_raise_clean_value_error(pilot, mutation):
    adjudications, enrollment = completed_prerequisites(pilot)
    first_record = adjudications["records"][0]
    first_evaluation = first_record["evaluations"][0]
    if mutation == "adjudications_list":
        adjudications = []
    elif mutation == "records_dict":
        adjudications["records"] = {}
    elif mutation == "record_null":
        adjudications["records"][0] = None
    elif mutation == "case_id_list":
        first_record["case_id"] = []
    elif mutation == "evaluations_null":
        first_record["evaluations"] = None
    elif mutation == "evaluation_null":
        first_record["evaluations"][0] = None
    elif mutation == "identity_list":
        first_evaluation["adjudicator_id"] = []
    elif mutation == "decision_list":
        first_evaluation["decision"] = []
    elif mutation == "citation_dict":
        first_evaluation["decisive_evidence"] = {}
    elif mutation == "attestation_string":
        first_evaluation["human_attested"] = "true"
    elif mutation == "enrollment_dict":
        enrollment = {}
    elif mutation == "enrolled_null":
        enrollment[0] = None
    elif mutation == "reviewer_list":
        enrollment[0]["reviewer_id"] = []
    else:
        enrollment[0]["consent"] = "true"
    with pytest.raises(ValueError):
        validate_readiness(pilot, adjudications, enrollment)


@pytest.mark.parametrize(
    "dataset_source,row_source", [("human", "simulation"), ("simulation", "human"), ("human", None)]
)
def test_explicit_contradictory_observation_source_is_rejected(pilot, dataset_source, row_source):
    rows = observations_for(pilot)
    rows[0]["source"] = row_source
    with pytest.raises(ValueError, match="source contradicts"):
        analyze_pilot(pilot, rows, source=dataset_source)


def test_missing_source_remains_compatible_without_claiming_verified_humans(pilot):
    rows = observations_for(pilot)
    assert all("source" not in row for row in rows)
    report = analyze_pilot(pilot, rows, source="human")
    assert report["data_provenance"] == "IMPORTED_DECLARATIONS_NOT_IDENTITY_OR_SIGNATURE_VERIFIED"
    assert not report["hypothesis_confirmed"] and not report["activation_allowed"]


def test_padded_reused_commitment_is_counted_as_a_duplicate_without_mutating_input(pilot):
    rows = observations_for(pilot)
    b_id = next(row["reviewer_id"] for row in pilot["assignments"] if row["condition"] == "B")
    b_rows = [row for row in rows if row["reviewer_id"] == b_id]
    b_rows[0]["precommit_record_id"] = "same-paper-record"
    b_rows[1]["precommit_record_id"] = " same-paper-record "
    report = analyze_pilot(pilot, rows, source="simulation")
    assert next(row for row in report["reviewers"] if row["reviewer_id"] == b_id)["protocol_deviations"] == 2
    assert b_rows[1]["precommit_record_id"] == " same-paper-record "


@pytest.mark.parametrize("mutation", ["null_row", "list_final", "list_initial", "overflow_elapsed"])
def test_malformed_observations_raise_clean_value_error(pilot, mutation):
    rows = observations_for(pilot)
    if mutation == "null_row":
        rows[0] = None
    elif mutation == "list_final":
        rows[0]["final_decision"] = []
    elif mutation == "list_initial":
        rows[0]["initial_decision"] = []
    else:
        rows[0]["case_elapsed_ms"] = 10**1000
    with pytest.raises(ValueError):
        analyze_pilot(pilot, rows, source="simulation")
