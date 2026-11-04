"""Status reports describe declarations without certifying human participation."""

import json

import pytest

from babylon60.cortex.approval_human_trial import adjudication_template, export_pilot
from babylon60.cortex.approval_trial_status import main, trial_status


@pytest.fixture
def kit(tmp_path):
    destination = tmp_path / "pilot"
    export_pilot(destination, seed=42601)
    return destination


def read(path):
    return json.loads(path.read_text())


def write(path, data):
    path.write_text(json.dumps(data))


def add_one_observation(kit, *, source="simulation"):
    pilot = read(kit / "coordinator/pilot_private.json")
    assignment = pilot["assignments"][0]
    case = assignment["cases"][0]
    row = {"reviewer_id": assignment["reviewer_id"], "case_id": case["case_id"],
           "final_decision": "APPROVE", "case_elapsed_ms": 10, "source": source}
    write(kit / "coordinator/observations_template.json", [row])


def complete_fixture_declarations(kit):
    """Synthetic check inputs; these do not document any actual people."""
    pilot = read(kit / "coordinator/pilot_private.json")
    adjudications = adjudication_template(pilot)
    for record in adjudications["records"]:
        for index, evaluation in enumerate(record["evaluations"]):
            evaluation.update(adjudicator_id=f"SOFTWARE-ONLY-{index}",
                              decision=pilot["answers"][record["case_id"]]["reference_decision"],
                              decisive_evidence="Synthetic test-only declaration.",
                              policy_clear=True, human_attested=True)
    enrollment = pilot["roster"]
    for slot in enrollment:
        slot.update(consent=True, training_passed=True, human_attested=True)
    write(kit / "coordinator/adjudication_template.json", adjudications)
    write(kit / "coordinator/enrollment_template.json", enrollment)


def test_empty_kit_reports_pending_slots_and_first_human_step(kit, capsys):
    result = trial_status(kit)
    assert result["status"] == "PREPARACION_PENDIENTE"
    assert result["pending_cases"] == 200
    assert result["reviewer_slots_pending"] == 12
    assert result["human_observations_declared"] == result["simulation_observations"] == 0
    assert result["source"] is None
    assert not result["declared_ready_for_pilot"] and not result["activation_allowed"]
    assert "Dos especialistas" in result["next_step"]
    assert main(["--kit", str(kit)]) == 0
    text = capsys.readouterr().out
    assert "Puestos de revisor pendientes: 12" in text
    assert "no autentica identidades ni firmas" in text


def test_json_output_omits_private_answers_and_ids(kit, capsys):
    assert main(["--kit", str(kit), "--json"]) == 0
    output = capsys.readouterr().out
    result = json.loads(output)
    assert result["human_identity_verified"] is False
    assert result["hypothesis_confirmed"] is False
    assert "private_seed" not in output and "policy_allows" not in output and "R-" not in output


def test_nonempty_observations_require_source_and_fail_legibly(kit, capsys):
    add_one_observation(kit)
    assert main(["--kit", str(kit)]) == 2
    output = capsys.readouterr()
    assert not output.out and "--source" in output.err and "Traceback" not in output.err


def test_explicit_simulation_rows_cannot_be_relabelled_human(kit, capsys):
    add_one_observation(kit, source="simulation")
    assert main(["--kit", str(kit), "--source", "human", "--json"]) == 2
    output = capsys.readouterr()
    assert not output.out and "Error de datos" in output.err and "Traceback" not in output.err


def test_simulation_is_counted_separately_even_with_complete_fixture_declarations(kit):
    complete_fixture_declarations(kit)
    add_one_observation(kit)
    result = trial_status(kit, source="simulation")
    assert result["status"] == "SIMULACION_SOLO_PRUEBA"
    assert result["simulation_observations"] == 1
    assert result["human_observations_declared"] == 0
    assert not result["declared_ready_for_pilot"]
    assert not result["hypothesis_confirmed"] and not result["activation_allowed"]


def test_declared_complete_inputs_never_become_authenticated_humans(kit):
    complete_fixture_declarations(kit)
    result = trial_status(kit)
    assert result["status"] == "REQUISITOS_DECLARADOS_COMPLETOS"
    assert result["declared_ready_for_pilot"] is True
    assert result["human_identity_verified"] is False
    assert result["human_observations_declared"] == 0
    assert not result["hypothesis_confirmed"] and not result["activation_allowed"]


def test_human_source_with_unfinished_preparation_is_reported_as_declared(kit):
    add_one_observation(kit, source="human")
    result = trial_status(kit, source="human")
    assert result["status"] == "RESPUESTAS_CON_PREPARACION_PENDIENTE"
    assert result["human_observations_declared"] == 1 and result["simulation_observations"] == 0
    assert result["human_identity_verified"] is False


@pytest.mark.parametrize("problem", ["missing", "malformed", "wrong_type", "different_bank", "bad_structure"])
def test_invalid_kit_inputs_return_exit_two_without_traceback(kit, capsys, problem):
    path = kit / "coordinator/adjudication_template.json"
    if problem == "missing":
        path.unlink()
    elif problem == "malformed":
        path.write_text("not JSON")
    elif problem == "wrong_type":
        write(path, [])
    elif problem == "different_bank":
        value = read(path)
        value["bank_digest"] = "different"
        write(path, value)
    else:
        write(kit / "coordinator/pilot_private.json", {})
    assert main(["--kit", str(kit)]) == 2
    output = capsys.readouterr()
    assert not output.out and "Error de datos" in output.err and "Traceback" not in output.err


def test_explicit_override_files_are_used_instead_of_saved_reports(kit, tmp_path):
    add_one_observation(kit, source="human")
    empty_observations = tmp_path / "empty.json"
    write(empty_observations, [])
    saved = kit / "coordinator/readiness.json"
    write(saved, {"ready_for_pilot": True, "activation_allowed": True})
    result = trial_status(kit, observations=empty_observations)
    assert result["status"] == "PREPARACION_PENDIENTE"
    assert not result["declared_ready_for_pilot"] and not result["activation_allowed"]
