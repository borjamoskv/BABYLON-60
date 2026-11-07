"""Isolated synthetic records test the pilot machinery, never human/model quality."""

import copy
from pathlib import Path
import shutil
from typing import Literal, cast

import pytest

from scripts.c5_quality_gates import experience_pilot as pilot


@pytest.fixture
def prepared(tmp_path: Path) -> Path:
    directory = tmp_path / "piloto ágil con espacios"
    pilot.prepare(directory, 42)
    return directory


def record(directory: Path, run: pilot.Run, tmp_path: Path) -> Path:
    """Build clearly labeled simulation evidence inside pytest's temporary tree."""
    source = tmp_path / "incoming" / run["run_id"]
    source.mkdir(parents=True)
    result = cast(pilot.Result, pilot.read_json(directory / "runs" / run["run_id"] / "result.template.json"))
    result["session"].update(
        {
            "client_version": "TEST-SIMULATION",
            "model": "test-model",
            "reasoning_effort": "test",
            "condition_verified": True,
        }
    )
    if run["condition"] == "babylon":
        result["session"]["babylon_version"] = "TEST-SIMULATION"
    for index, turn in enumerate(result["turns"]):
        (source / turn["final_file"]).write_text(
            f"TEST SIMULATION; no model called. Turn {index}.\n\n| Result | Evidence |\n|---|---|\n| preserved | local |\n[ TOPOLOGÍA ACTIVA ]: MOSKV-1\n",
            encoding="utf-8",
        )
    result["metrics"]["time_to_acceptable_seconds"] = 10
    for kind in sorted(pilot.EVIDENCE_KINDS):
        name = f"{kind}.txt"
        (source / name).write_text("ISOLATED TEST SIMULATION, not runtime evidence.\n", encoding="utf-8")
        result["evidence"].append({"path": name, "kind": kind, "description": "Synthetic test artifact"})
    pilot.write_json(source / "result.json", result)
    return source / "result.json"


@pytest.fixture
def blinded(prepared: Path, tmp_path: Path) -> Path:
    manifest = pilot.load_manifest(prepared)
    for run in manifest["execution_order"]:
        pilot.import_result(prepared, record(prepared, run, tmp_path))
    pilot.blind(prepared)
    return prepared


def review_all(directory: Path, wins: int = 10) -> None:
    """Simulate judges only for acceptance-logic unit tests, never a delivered review."""
    mapping = cast(dict[str, dict[str, str]], pilot.read_json(directory / "private" / "blind_map.json"))
    for index, (pair, sides) in enumerate(mapping.items()):
        for role in pilot.ROLES[:2]:
            template = directory / "blind" / "reviews" / pair / f"{role}.template.json"
            value = cast(pilot.Review, pilot.read_json(template))
            value.update(
                {
                    "reviewer_id": f"TEST-SIMULATION-{role}",
                    "independent_from_other_reviewers": True,
                    "winner": next(
                        side
                        for side, condition in sides.items()
                        if condition == ("babylon" if index < wins else "control")
                    ),
                    "rationale": "Synthetic test record; no person evaluated these responses.",
                    "evidence_reviewed": [
                        f"{side}:{kind}" for side in ("A", "B") for kind in sorted(pilot.EVIDENCE_KINDS)
                    ],
                }
            )
            for side in value["sides"].values():
                side.update(
                    {
                        "requirements": dict.fromkeys(side["requirements"], True),
                        "serious_errors": 0,
                        "fabricated_verifications": 0,
                        "metrics_verified": True,
                    }
                )
            pilot.write_json(template.with_name(f"{role}.json"), value)


def first_review(directory: Path, role: str = "independent") -> tuple[Path, pilot.Review]:
    pair = next(iter(cast(dict[str, object], pilot.read_json(directory / "private" / "blind_map.json"))))
    path = directory / "blind" / "reviews" / pair / f"{role}.json"
    return path, cast(pilot.Review, pilot.read_json(path))


def test_prepare_is_frozen_balanced_reproducible(prepared: Path, tmp_path: Path) -> None:
    other = tmp_path / "other"
    pilot.prepare(other, 42)
    manifest = pilot.load_manifest(prepared)
    assert manifest == pilot.load_manifest(other)
    assert len(manifest["execution_order"]) == 20
    assert len({run["pair_id"] for run in manifest["execution_order"]}) == 10
    for task in pilot.TASKS:
        assert len([run for run in manifest["execution_order"] if run["task_id"] == task["id"]]) == 4
    assert pilot.report(prepared)["status"] == "pending"
    assert pilot.blind(prepared)["status"] == "pending"


def test_prepare_refuses_sources_and_overwrite(prepared: Path) -> None:
    with pytest.raises(pilot.PilotError, match="sources"):
        pilot.prepare(pilot.REPO / "docs" / "bad-pilot", 1)
    with pytest.raises(pilot.PilotError, match="empty"):
        pilot.prepare(prepared, 1)


def test_changed_task_or_execution_order_rejected(prepared: Path) -> None:
    path = prepared / "tasks" / "synthesis" / "task.json"
    task = cast(pilot.Task, pilot.read_json(path))
    task["requirements"]["counts"] = "Changed after seeing responses"
    pilot.write_json(path, task)
    with pytest.raises(pilot.PilotError, match="Frozen task"):
        pilot.report(prepared)


def test_order_tampering_rejected(prepared: Path) -> None:
    path = prepared / "manifest.json"
    manifest = cast(pilot.Manifest, pilot.read_json(path))
    manifest["execution_order"].reverse()
    pilot.write_json(path, manifest)
    with pytest.raises(pilot.PilotError, match="Execution order"):
        pilot.load_manifest(prepared)


def test_negative_seed_remains_reproducible(tmp_path: Path) -> None:
    directory = tmp_path / "negative-seed"
    pilot.prepare(directory, -42)
    assert pilot.load_manifest(directory)["seed"] == -42


@pytest.mark.parametrize("filename", ["packets.json", "blind_map.json"])
def test_report_rejects_malformed_private_mapping(blinded: Path, filename: str) -> None:
    path = blinded / "private" / filename
    pilot.write_json(path, None)
    with pytest.raises(pilot.PilotError, match="exactly ten"):
        pilot.report(blinded)


@pytest.mark.parametrize("filename", ["packets.json", "blind_map.json"])
def test_report_rejects_malformed_private_mapping_entries(blinded: Path, filename: str) -> None:
    path = blinded / "private" / filename
    value = cast(dict[str, object], pilot.read_json(path))
    value[next(iter(value))] = []
    pilot.write_json(path, value)
    with pytest.raises(pilot.PilotError, match="expected string mapping"):
        pilot.report(blinded)


def test_import_requires_final_outputs_and_operational_evidence(prepared: Path, tmp_path: Path) -> None:
    run = pilot.load_manifest(prepared)["execution_order"][0]
    source = record(prepared, run, tmp_path)
    data = cast(pilot.Result, pilot.read_json(source))
    data["evidence"] = data["evidence"][:-1]
    pilot.write_json(source, data)
    with pytest.raises(pilot.PilotError, match="Attach session"):
        pilot.import_result(prepared, source)
    unexpected = dict(data)
    unexpected["analysis"] = "Never store hidden deliberations"
    pilot.write_json(source, unexpected)
    with pytest.raises(pilot.PilotError, match="exactly"):
        pilot.import_result(prepared, source)


@pytest.mark.parametrize("value", [-1, float("nan"), float("inf"), True])
def test_import_rejects_invalid_times(prepared: Path, tmp_path: Path, value: float) -> None:
    run = pilot.load_manifest(prepared)["execution_order"][0]
    source = record(prepared, run, tmp_path)
    data = cast(pilot.Result, pilot.read_json(source))
    data["metrics"]["time_to_acceptable_seconds"] = value
    pilot.write_json(source, data)
    with pytest.raises(pilot.PilotError, match="positive, finite"):
        pilot.import_result(prepared, source)


def test_import_rejects_escaping_path_and_preserves_input(prepared: Path, tmp_path: Path) -> None:
    run = pilot.load_manifest(prepared)["execution_order"][0]
    source = record(prepared, run, tmp_path)
    data = cast(pilot.Result, pilot.read_json(source))
    data["turns"][0]["final_file"] = "../outside.md"
    pilot.write_json(source, data)
    with pytest.raises(pilot.PilotError, match="relative"):
        pilot.import_result(prepared, source)
    assert not (prepared / "results" / run["run_id"]).exists()


def test_import_rejects_symlink_escape(prepared: Path, tmp_path: Path) -> None:
    run = pilot.load_manifest(prepared)["execution_order"][0]
    source = record(prepared, run, tmp_path)
    outside = tmp_path / "outside.md"
    outside.write_text("outside")
    target = source.parent / "response-1.md"
    target.unlink()
    target.symlink_to(outside)
    with pytest.raises(pilot.PilotError, match="escaping"):
        pilot.import_result(prepared, source)


def test_import_is_immutable_and_receipts_detect_tampering(prepared: Path, tmp_path: Path) -> None:
    run = pilot.load_manifest(prepared)["execution_order"][0]
    source = record(prepared, run, tmp_path)
    pilot.import_result(prepared, source)
    with pytest.raises(pilot.PilotError, match="already imported"):
        pilot.import_result(prepared, source)
    (prepared / "results" / run["run_id"] / "evidence" / "response-1.md").write_text("changed")
    with pytest.raises(pilot.PilotError, match="evidence changed"):
        pilot.report(prepared)


def test_failed_import_is_atomic_and_retryable(prepared: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    run = pilot.load_manifest(prepared)["execution_order"][0]
    source = record(prepared, run, tmp_path)
    with monkeypatch.context() as context:

        def fail_copy(source: Path, destination: Path) -> None:
            raise OSError("test copy failure")

        context.setattr(shutil, "copyfile", fail_copy)
        with pytest.raises(OSError, match="test copy failure"):
            pilot.import_result(prepared, source)
    assert not (prepared / "results" / run["run_id"]).exists()
    assert list((prepared / "results").iterdir()) == []
    assert pilot.import_result(prepared, source)["status"] == "imported"


def test_continuity_requires_both_final_turns(prepared: Path, tmp_path: Path) -> None:
    run = next(run for run in pilot.load_manifest(prepared)["execution_order"] if run["task_id"] == "continuity")
    source = record(prepared, run, tmp_path)
    data = cast(pilot.Result, pilot.read_json(source))
    data["turns"].pop()
    pilot.write_json(source, data)
    with pytest.raises(pilot.PilotError, match="both continuity turns"):
        pilot.import_result(prepared, source)


def test_redaction_removes_only_explicit_signature_and_preserves_format() -> None:
    text = "# Babylon helps\r\n\r\n| a | b |\r\n|---|---|\r\n\n[ LLM ]: Hidden label\r\nordinary MOSKV-1 content\n"
    rendered, audit = pilot.redact(text)
    assert rendered == text.replace("[ LLM ]: Hidden label\r\n", "")
    assert audit == [{"line": 6, "text": "[ LLM ]: Hidden label\r\n", "rule": "portable_signature_line"}]


def test_redaction_preserves_literal_code_and_substantive_brand_mentions() -> None:
    text = "Babylon is the topic.\n```text\n[ LLM ]: code example\n```\n[ LLM ]: signature\n"
    rendered, audit = pilot.redact(text)
    assert rendered == text.replace("[ LLM ]: signature\n", "")
    assert len(audit) == 1


def test_blind_package_requires_two_real_review_roles(blinded: Path) -> None:
    value = pilot.report(blinded)
    assert value["status"] == "pending"
    assert value["imported_runs"] == 20
    assert value["reviewed_pairs"] == 0
    assert len([item for item in value["pending"] if item.startswith("review:")]) == 20
    assert "not independently certified" in value["scope"]
    with pytest.raises(pilot.PilotError, match="already exists"):
        pilot.blind(blinded)


def test_blind_contains_artifacts_without_rewriting_them(prepared: Path, tmp_path: Path) -> None:
    manifest = pilot.load_manifest(prepared)
    for run in manifest["execution_order"]:
        source = record(prepared, run, tmp_path)
        if run["task_id"] == "code_fix":
            data = cast(pilot.Result, pilot.read_json(source))
            (source.parent / "patch.py").write_text("# unchanged artifact\n")
            data["turns"][0]["artifacts"].append("patch.py")
            pilot.write_json(source, data)
        pilot.import_result(prepared, source)
    pilot.blind(prepared)
    assert (
        prepared / "blind" / "pairs" / "code_fix-1" / "A-turn-1-artifact-1.py"
    ).read_text() == "# unchanged artifact\n"
    assert pilot.report(prepared)["status"] == "pending"


def test_blind_tampering_is_rejected(blinded: Path) -> None:
    packets = cast(dict[str, dict[str, str]], pilot.read_json(blinded / "private" / "packets.json"))
    pair = next(iter(packets))
    path = blinded / "blind" / "pairs" / pair / "A-turn-1.md"
    path.write_text("changed")
    with pytest.raises(pilot.PilotError, match="packet changed"):
        pilot.report(blinded)


def test_blind_omitted_pair_is_rejected(blinded: Path) -> None:
    path = blinded / "private" / "packets.json"
    packets = cast(dict[str, dict[str, str]], pilot.read_json(path))
    packets.pop(next(iter(packets)))
    pilot.write_json(path, packets)
    with pytest.raises(pilot.PilotError, match="exactly ten"):
        pilot.report(blinded)


def test_gate_accepts_only_all_evidence_and_eight_wins(blinded: Path) -> None:
    review_all(blinded, wins=8)
    value = pilot.report(blinded)
    assert value["status"] == "accepted"
    assert value["babylon_wins"] == 8
    assert value["median_acceptable_time_ratio"] == 1
    assert value["model_calls_by_runner"] == 0
    review_all(blinded, wins=7)
    value = pilot.report(blinded)
    assert value["status"] == "rejected"
    assert "fewer_than_8_of_10_wins" in value["failures"]


def test_disagreement_requires_third_distinct_person(blinded: Path) -> None:
    review_all(blinded)
    path, value = first_review(blinded)
    value["winner"] = "B" if value["winner"] == "A" else "A"
    pilot.write_json(path, value)
    assert any(item.endswith(":adjudicator") for item in pilot.report(blinded)["pending"])
    third = copy.deepcopy(value)
    third["role"] = "adjudicator"
    third["reviewer_id"] = "TEST-SIMULATION-third"
    third["winner"] = "B" if value["winner"] == "A" else "A"
    pilot.write_json(path.with_name("adjudicator.json"), third)
    assert pilot.report(blinded)["status"] == "accepted"
    third["reviewer_id"] = value["reviewer_id"]
    pilot.write_json(path.with_name("adjudicator.json"), third)
    with pytest.raises(pilot.PilotError, match="third person"):
        pilot.report(blinded)


def test_incomplete_assessment_and_self_review_are_rejected(blinded: Path) -> None:
    review_all(blinded)
    path, value = first_review(blinded)
    value["evidence_reviewed"] = ["A:timing"]
    pilot.write_json(path, value)
    with pytest.raises(pilot.PilotError, match="attest inspection"):
        pilot.report(blinded)
    review_all(blinded)
    path, value = first_review(blinded)
    value["reviewer_id"] = "TEST-SIMULATION-target_user"
    pilot.write_json(path, value)
    with pytest.raises(pilot.PilotError, match="different people"):
        pilot.report(blinded)


@pytest.mark.parametrize("kind", ["essential", "serious", "fabrication", "metrics"])
def test_adverse_evidence_cannot_be_hidden_by_winner(blinded: Path, kind: str) -> None:
    review_all(blinded)
    for role in pilot.ROLES[:2]:
        path, value = first_review(blinded, role)
        mapping = cast(dict[str, dict[str, str]], pilot.read_json(blinded / "private" / "blind_map.json"))[
            value["pair_id"]
        ]
        side = next(side for side, condition in mapping.items() if condition == "babylon")
        if kind == "essential":
            key = next(iter(value["sides"][side]["requirements"]))
            value["sides"][side]["requirements"][key] = False
        elif kind == "serious":
            value["sides"][side]["serious_errors"] = 1
        elif kind == "fabrication":
            value["sides"][side]["fabricated_verifications"] = 1
        else:
            value["sides"][side]["metrics_verified"] = False
        pilot.write_json(path, value)
    report = pilot.report(blinded)
    assert report["status"] == ("pending" if kind == "metrics" else "rejected")
    assert report["babylon_wins"] == 10


@pytest.mark.parametrize("kind", ["essential", "serious", "fabrication"])
def test_control_failures_remain_visible_without_rejecting_babylon(blinded: Path, kind: str) -> None:
    review_all(blinded)
    for role in pilot.ROLES[:2]:
        path, value = first_review(blinded, role)
        mapping = cast(dict[str, dict[str, str]], pilot.read_json(blinded / "private" / "blind_map.json"))[
            value["pair_id"]
        ]
        side = next(side for side, condition in mapping.items() if condition == "control")
        if kind == "essential":
            key = next(iter(value["sides"][side]["requirements"]))
            value["sides"][side]["requirements"][key] = False
        elif kind == "serious":
            value["sides"][side]["serious_errors"] = 1
        else:
            value["sides"][side]["fabricated_verifications"] = 1
        pilot.write_json(path, value)
    result = pilot.report(blinded)
    assert result["status"] == "accepted"
    assert result["failures"] == []
    assert result["control_observations"]
    comparison = next(item for item in result["comparisons"] if item["pair_id"] == value["pair_id"])
    assert len(comparison["assessments"]) == 2
    assert comparison["assessments"][0]["sides"]["control"] == value["sides"][side]


def test_cli_prepare_and_pending_report(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    directory = tmp_path / "cli"
    assert pilot.main(["prepare", str(directory)]) == 0
    assert pilot.main(["report", str(directory)]) == 1
    assert '"status": "pending"' in capsys.readouterr().out


@pytest.mark.parametrize("metric,value", [("time_to_acceptable_seconds", 13), ("corrections", 1), ("rework", 1)])
def test_report_rejects_more_time_corrections_or_rework(
    prepared: Path, tmp_path: Path, metric: Literal["time_to_acceptable_seconds", "corrections", "rework"], value: float
) -> None:
    for run in pilot.load_manifest(prepared)["execution_order"]:
        source = record(prepared, run, tmp_path)
        data = cast(pilot.Result, pilot.read_json(source))
        if run["condition"] == "babylon":
            data["metrics"][metric] = value
        pilot.write_json(source, data)
        pilot.import_result(prepared, source)
    pilot.blind(prepared)
    review_all(prepared)
    result = pilot.report(prepared)
    assert result["status"] == "rejected"
    assert result["failures"]


def test_report_rejects_model_mismatch(prepared: Path, tmp_path: Path) -> None:
    for run in pilot.load_manifest(prepared)["execution_order"]:
        source = record(prepared, run, tmp_path)
        data = cast(pilot.Result, pilot.read_json(source))
        if run["condition"] == "babylon":
            data["session"]["model"] = "different-test-model"
        pilot.write_json(source, data)
        pilot.import_result(prepared, source)
    pilot.blind(prepared)
    review_all(prepared)
    assert any("incomparable_model" in failure for failure in pilot.report(prepared)["failures"])
