"""Package checks use untouched baseline copies, never a reference solution."""

import importlib.util
import json
import os
from pathlib import Path
import shutil
from types import SimpleNamespace

import pytest


PACKAGE = Path(__file__).absolute().parents[1]
SPEC = importlib.util.spec_from_file_location("comparison_harness", PACKAGE / "benchmark.py")
assert SPEC is not None and SPEC.loader is not None
bench = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(bench)


@pytest.fixture
def environment():
    return Path(os.environ["CG_HARNESS_ENV"]).absolute()


def prepare(path):
    bench.prepare(SimpleNamespace(destination=path))
    return path


def test_frozen_package_verifies():
    manifest = bench.verify()
    assert manifest["acceptance_test_count"] == 127


def test_canonical_source_bytes_are_retained():
    manifest = bench.read_json(PACKAGE / "source-manifest.json")
    for source in manifest["canonical_sources"]:
        actual = (PACKAGE / source["package_path"]).read_bytes()
        assert bench.sha(actual) == source["sha256"]


def test_prepare_never_resets_existing_work(tmp_path):
    destination = prepare(tmp_path / "work")
    before = bench.inventory(destination, submission=True)
    with pytest.raises(ValueError, match="already exists"):
        prepare(destination)
    assert bench.inventory(destination, submission=True) == before


def test_prompt_tampering_is_rejected(tmp_path, monkeypatch):
    copied = tmp_path / "bundle"
    shutil.copytree(PACKAGE, copied)
    prompt = copied / "PROMPT.txt"
    prompt.write_text(prompt.read_text() + "\nTampered fixture\n")
    monkeypatch.setattr(bench, "ROOT", copied)
    with pytest.raises(ValueError, match="Frozen package changed"):
        bench.verify()


def test_extra_file_in_frozen_package_is_rejected(tmp_path, monkeypatch):
    copied = tmp_path / "bundle"
    shutil.copytree(PACKAGE, copied)
    (copied / "extra.txt").write_text("unexpected fixture\n")
    monkeypatch.setattr(bench, "ROOT", copied)
    with pytest.raises(ValueError, match="Frozen package changed"):
        bench.verify()


def test_modified_baseline_cannot_start_a_trial(tmp_path):
    workspace = prepare(tmp_path / "work")
    target = workspace / bench.TARGET
    target.write_text(target.read_text() + "\n# changed fixture, no solution\n")
    with pytest.raises(ValueError, match="untouched snapshot"):
        bench.start(SimpleNamespace(workspace=workspace, run_id="A01", run=tmp_path / "run"))


def test_results_cannot_be_written_into_workspace(tmp_path):
    workspace = tmp_path / "work"
    with pytest.raises(ValueError, match="outside the participant"):
        bench.reject_overlap(workspace / "evaluation", workspace)
    with pytest.raises(ValueError, match="outside the participant"):
        bench.reject_overlap(tmp_path, workspace)


def test_acceptance_keeps_positive_and_negative_witnesses():
    cases = bench.read_json(PACKAGE / "acceptance/cases.json")
    assert len(cases) == 124
    assert sum(case["expected"] is True for case in cases) == 15
    assert {case["criterion"] for case in cases} == {"CG-01..04", "CG-05", "CG-06"}


def test_baseline_rejection_records_real_attempts_and_unknown_metrics(tmp_path, environment):
    workspace = prepare(tmp_path / "work")
    directory = tmp_path / "metrics"
    bench.start(SimpleNamespace(workspace=workspace, environment=environment,
                              run=directory, run_id="A01", purpose="harness_validation"))
    for attempt in (1, 2):
        result = bench.evaluate(SimpleNamespace(workspace=workspace, environment=environment,
                                              run=directory, output=tmp_path / f"attempt-{attempt}"))
        assert result["technical_acceptance"] is False
        assert result["manifest_sha256"] == bench.sha((PACKAGE / "manifest.json").read_bytes())
        assert result["acceptance"]["counts"] == {"tests": 127, "failures": 85, "errors": 0, "skipped": 0}
        assert result["scope_ok"] is True
        assert result["participant_tests"] is None
    metrics = bench.read_json(directory / "metrics.json")
    assert metrics["status"] == "needs_rework"
    assert metrics["purpose"] == "harness_validation"
    assert len(metrics["attempts"]) == 2
    assert metrics["resubmissions_after_first"] == 1
    assert metrics["first_technically_accepted_submission_seconds"] is None
    assert metrics["operator_observations"]["cost_amount"] is None
    assert metrics["operator_observations"]["interventions_count"] is None
    events = [json.loads(line) for line in (directory / "events.jsonl").read_text().splitlines()]
    assert [event["kind"] for event in events] == ["started", "evaluated", "evaluated"]


def test_enum_edit_is_rejected_by_scope_even_when_only_a_comment(tmp_path, environment):
    workspace = prepare(tmp_path / "work")
    enum = workspace / "src/babylon60/guards/capabilities.py"
    enum.write_text(enum.read_text() + "\n# forbidden fixture edit, no solution\n")
    result = bench.evaluate(SimpleNamespace(workspace=workspace, environment=environment,
                                          run=None, output=tmp_path / "evaluation"))
    assert result["technical_acceptance"] is False
    assert result["scope_ok"] is False
    assert result["forbidden_changes"] == ["src/babylon60/guards/capabilities.py"]
