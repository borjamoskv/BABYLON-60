"""Reproducible trial preparation and honest descriptive metric contracts."""

from collections import Counter
import copy
import json

import pytest

from babylon60.cortex.approval_experiment import analyze, generate_plan, main, recommendation_packet, validate_plan


def observations_for(plan, key):
    rows = []
    for index, case in enumerate(plan["cases"]):
        correct = "APPROVE" if key["answers"][case["case_id"]]["policy_allows"] else "REJECT"
        rows.append({"case_id": case["case_id"], "reviewer_id": f"reviewer-{index % 20}",
                     "initial_decision": correct if case["condition"] == "B" else None,
                     "final_decision": correct, "authorization_latency_ms": index + 1,
                     "effect_observed": correct == "APPROVE", "valid_authorization": True})
    return rows


def test_reproducible_balanced_plan_hides_answers_and_recommendations():
    plan, key = generate_plan(seed=601)
    assert (plan, key) == generate_plan(seed=601)
    assert (plan, key) != generate_plan(seed=602)
    counts = Counter((c["condition"], key["answers"][c["case_id"]]["policy_allows"],
                      key["answers"][c["case_id"]]["recommendation"]) for c in plan["cases"])
    assert set(counts.values()) == {25}
    assert len(counts) == 8
    assert len(plan["cases"]) == 200
    assert set(c["category"] for c in plan["cases"]) == {"configuration", "permissions", "agent_action"}
    encoded = json.dumps(plan)
    assert "policy_allows" not in encoded
    assert '"recommendation"' not in encoded
    assert "seed" not in encoded


def test_default_seed_is_private_and_varies_between_trials():
    plan, key = generate_plan()
    other_plan, other_key = generate_plan()
    assert "seed" not in plan and "private_seed" not in plan
    assert key["private_seed"] != other_key["private_seed"]
    assert plan != other_plan
    assert generate_plan(seed=key["private_seed"]) == (plan, key)


def test_altered_dataset_and_mismatched_answer_key_are_rejected():
    plan, key = generate_plan()
    plan["cases"][0]["request"]["unexpected"] = True
    with pytest.raises(ValueError, match="digest mismatch"):
        analyze(plan, key, [])
    plan, key = generate_plan()
    del key["answers"][plan["cases"][0]["case_id"]]
    with pytest.raises(ValueError, match="match every"):
        validate_plan(plan, key)


def test_no_observations_never_validates_hypothesis_or_zero_effects():
    plan, key = generate_plan()
    report = analyze(plan, key, [])
    assert report["status"] == "NOT_EVALUATED_NO_OBSERVATIONS"
    assert report["hypothesis_confirmed"] is False
    assert report["descriptive_thresholds_met"] is None
    assert report["containment_status"] == "NOT_FULLY_OBSERVED"
    for arm in report["conditions"].values():
        assert arm["incorrect_approval_rate"] == {"value": None, "numerator": 0, "denominator": 0}
        assert arm["unauthorized_committed_effects"] is None
        assert arm["authorization_latency_p95_ms"] is None


def test_zero_baseline_and_synthetic_observations_cannot_confirm_hypothesis():
    plan, key = generate_plan()
    report = analyze(plan, key, observations_for(plan, key), source="simulation")
    assert report["status"] == "SIMULATION_ONLY_HYPOTHESIS_UNTESTED"
    assert report["hypothesis_confirmed"] is False
    assert report["containment_status"] == "NO_VIOLATION_OBSERVED"
    assert report["relative_incorrect_approval_reduction"] is None
    assert report["descriptive_thresholds_met"] is None
    assert report["conditions"]["A"]["agent_induced_decision_flip_rate"]["value"] is None
    for arm in report["conditions"].values():
        assert arm["incorrect_approval_rate"]["value"] == 0
        assert arm["legitimate_approval_rate"]["value"] == 1
        assert arm["unauthorized_committed_effects"] == 0


def test_metrics_include_denominators_recommendation_bias_and_actual_effects():
    plan, key = generate_plan(n=8)
    rows = observations_for(plan, key)
    for row in rows:
        row["final_decision"] = key["answers"][row["case_id"]]["recommendation"]
        row["effect_observed"] = row["final_decision"] == "APPROVE"
    report = analyze(plan, key, rows, source="simulation")
    for arm in report["conditions"].values():
        assert arm["incorrect_approval_rate"] == {"value": 0.5, "numerator": 1, "denominator": 2}
        assert arm["legitimate_approval_rate"]["value"] == 0.5
        assert arm["approval_biased_incorrect_approval_rate"]["value"] == 1
        assert arm["unauthorized_committed_effects"] == 1
    assert report["conditions"]["B"]["agent_induced_decision_flip_rate"]["value"] == 1
    assert report["descriptive_thresholds_met"] is False


def test_threshold_boundary_is_descriptive_and_requires_complete_plan():
    plan, key = generate_plan()
    rows = observations_for(plan, key)
    changed = {"A": 0, "B": 0}
    for row in rows:
        case = next(c for c in plan["cases"] if c["case_id"] == row["case_id"])
        answer = key["answers"][row["case_id"]]
        limit = 20 if case["condition"] == "A" else 14
        if not answer["policy_allows"] and answer["recommendation"] == "APPROVE" and changed[case["condition"]] < limit:
            changed[case["condition"]] += 1
            row["final_decision"] = "APPROVE"
    report = analyze(plan, key, rows, source="simulation")
    assert report["relative_incorrect_approval_reduction"] == pytest.approx(0.30)
    assert report["descriptive_thresholds_met"] is True
    assert report["hypothesis_confirmed"] is False
    assert analyze(plan, key, rows[:-1], source="simulation")["descriptive_thresholds_met"] is None


def test_missing_effect_witness_remains_unknown_and_forbidden_observation_falsifies():
    plan, key = generate_plan(n=8)
    rows = observations_for(plan, key)
    for row in rows:
        row.pop("effect_observed")
    report = analyze(plan, key, rows)
    assert all(arm["unauthorized_committed_effects"] is None for arm in report["conditions"].values())
    forbidden = next(row for row in rows if not key["answers"][row["case_id"]]["policy_allows"])
    forbidden["effect_observed"] = True
    report = analyze(plan, key, rows)
    assert sum(arm["confirmed_unauthorized_effects"] for arm in report["conditions"].values()) == 1
    assert report["containment_status"] == "FALSIFIED"


@pytest.mark.parametrize("mutation", ["duplicate", "unknown", "missing_initial", "negative_latency", "bool_latency"])
def test_invalid_imports_are_rejected(mutation):
    plan, key = generate_plan(n=8)
    rows = observations_for(plan, key)
    if mutation == "duplicate":
        rows.append(copy.deepcopy(rows[0]))
    elif mutation == "unknown":
        rows[0]["case_id"] = "unknown"
    elif mutation == "missing_initial":
        row = next(r for r in rows if next(c for c in plan["cases"] if c["case_id"] == r["case_id"])["condition"] == "B")
        row.pop("initial_decision")
    else:
        rows[0]["authorization_latency_ms"] = -1 if mutation == "negative_latency" else True
    with pytest.raises(ValueError):
        analyze(plan, key, rows)


def test_cli_roundtrip_and_private_key_file(tmp_path):
    trial = tmp_path / "trial"
    assert main(["prepare", "--out", str(trial)]) == 0
    assert (trial / "coordinator_key.json").stat().st_mode & 0o777 == 0o600
    report = tmp_path / "report.json"
    assert main(["analyze", "--plan", str(trial / "participant_plan.json"),
                 "--key", str(trial / "coordinator_key.json"),
                 "--observations", str(trial / "observations_template.json"), "--out", str(report)]) == 0
    assert json.loads(report.read_text())["status"] == "NOT_EVALUATED_NO_OBSERVATIONS"
    with pytest.raises(FileExistsError):
        main(["prepare", "--out", str(trial)])


def test_recommendation_packet_does_not_leak_answer():
    plan, key = generate_plan()
    packet = recommendation_packet(plan, key, plan["cases"][0]["case_id"])
    assert set(packet) == {"case_id", "recommendation", "rationale"}
    assert packet["recommendation"] in {"APPROVE", "REJECT"}


def test_simulation_observes_effects_separately_and_never_claims_human_benefit(tmp_path):
    from examples.fl_approval01_simulation import run_simulation

    out = tmp_path / "isolated-trial"
    report = run_simulation(out, n=8)
    rows = json.loads((out / "observations.json").read_text())
    key = json.loads((out / "coordinator_key.json").read_text())
    expected = [row for row in rows if key["answers"][row["case_id"]]["policy_allows"]
                and row["final_decision"] == "APPROVE" and row["valid_authorization"]]
    assert len(list((out / "effects").iterdir())) == len(expected)
    assert {row["case_id"] for row in rows if row["effect_observed"]} == {row["case_id"] for row in expected}
    assert report["simulation"]["forbidden_effects_observed"] == 0
    assert report["simulation"]["invalid_authorization_effects_observed"] == 0
    assert report["simulation"]["warmup_cases_excluded"] == 8
    assert report["simulation"]["measured_cases"] == 8
    assert report["simulation"]["containment_status"] == "NO_VIOLATION_OBSERVED"
    assert report["status"] == "SIMULATION_ONLY_HYPOTHESIS_UNTESTED"
    assert report["hypothesis_confirmed"] is False
    assert report["relative_incorrect_approval_reduction"] == 0
    assert report["descriptive_thresholds_met"] is False
    with pytest.raises(FileExistsError):
        run_simulation(out, n=8)


def test_simulation_policy_does_not_trust_answer_labels(tmp_path):
    from examples.fl_approval01_simulation import _run_cases

    plan, key = generate_plan(seed=601, n=8)
    original_truth = {case_id: answer["policy_allows"] for case_id, answer in key["answers"].items()}
    for answer in key["answers"].values():
        answer.update(policy_allows=True, recommendation="APPROVE")
    rows = _run_cases(tmp_path, plan, key)
    assert any(row["effect_observed"] for row in rows)
    assert all(not row["effect_observed"] for row in rows if not original_truth[row["case_id"]])


def test_simulation_cli_fails_when_an_independent_witness_finds_a_forbidden_effect(tmp_path, monkeypatch):
    from examples import fl_approval01_simulation as runner

    original_run = runner._run_cases

    def inject_forbidden_effect(out, plan, key):
        rows = original_run(out, plan, key)
        case = next(case for case in plan["cases"] if not runner.policy_allows(case["request"]))
        runner._marker(out / "effects" / f"{case['case_id']}.json", case["request"])
        row = next(row for row in rows if row["case_id"] == case["case_id"])
        row["effect_observed"] = runner._observe(out / "effects" / f"{case['case_id']}.json", case["request"])
        return rows

    monkeypatch.setattr(runner, "_run_cases", inject_forbidden_effect)
    out = tmp_path / "counterexample"
    assert runner.main(["--out", str(out), "--n", "8"]) == 1
    report = json.loads((out / "simulation_report.json").read_text())
    assert report["simulation"]["containment_status"] == "FALSIFIED"
    assert report["simulation"]["forbidden_effects_observed"] == 1
    assert report["containment_status"] == "FALSIFIED"
