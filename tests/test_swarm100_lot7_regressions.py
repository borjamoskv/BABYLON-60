"""Catalogue/report regressions in copied scripts and owned temporary roots."""

import ast
from concurrent.futures import ThreadPoolExecutor
from copy import deepcopy
import importlib.util
import json
from pathlib import Path
import shutil
import socket
import subprocess
import sys
from types import SimpleNamespace

import pytest
from blake3 import blake3

ROOT = Path(__file__).absolute().parents[1]
SOURCE = ROOT / "scripts/c5_verifiers/fast_smt_gate.py"


@pytest.fixture
def fixture(tmp_path, monkeypatch):
    root = tmp_path / "workspace"
    root.mkdir()
    (root / "README.md").write_text("fixture workspace marker, not a causal DAG")
    (root / ".agents").mkdir()
    copied = root / "fast_smt_gate.py"
    shutil.copyfile(SOURCE, copied)
    monkeypatch.chdir(root)
    monkeypatch.setenv("HOME", str(tmp_path))

    def forbidden(*args, **kwargs):
        raise AssertionError("network/solver execution forbidden in this fixture")

    monkeypatch.setattr(socket.socket, "connect", forbidden)
    monkeypatch.setattr(socket.socket, "connect_ex", forbidden)
    monkeypatch.setattr(socket, "getaddrinfo", forbidden)
    name = "lot7_gate_fixture"
    spec = importlib.util.spec_from_file_location(name, copied)
    module = importlib.util.module_from_spec(spec)
    monkeypatch.setitem(sys.modules, name, module)
    spec.loader.exec_module(module)

    def cli(*args):
        return subprocess.run(
            [sys.executable, str(copied), *args],
            cwd=root,
            env={"HOME": str(tmp_path), "PATH": "/usr/bin:/bin", "LC_ALL": "C"},
            capture_output=True,
            timeout=10,
        )

    return SimpleNamespace(root=root, module=module, cli=cli)


@pytest.mark.parametrize("flag", ["--json", "--scitt"])
def test_c0556_markers_do_not_authorize_quality_gate(fixture, flag):
    result = fixture.cli(flag)
    assert result.returncode != 0, result.stdout
    value = json.loads(result.stdout)
    assert value.get("passed") is not True


def test_default_text_mode_also_rejects_missing_verification(fixture):
    (fixture.root / "README.md").unlink()
    (fixture.root / ".agents").rmdir()
    result = fixture.cli()
    assert result.returncode != 0, result.stdout


def test_c0557_legacy_boolean_records_are_not_silently_upgraded(fixture):
    m = fixture.module
    legacy = [("AX-DAG-1", "fixture", True, "no checker executed")]
    with pytest.raises(ValueError):
        m.generate_scitt_receipt(legacy, 1.0)


def test_c0557_receipt_is_not_a_fabricated_ed25519_signature(fixture):
    m = fixture.module
    try:
        receipt = m.generate_scitt_receipt([("AX-DAG-1", "fixture", False, "fixture failure")], 1.0)
    except ValueError:
        return  # A new schema must reject the unsupported legacy data.
    assert not receipt.get("signature_ed25519")
    assert receipt.get("signature_status") == "UNSIGNED"


def test_c0557_outcome_and_detail_cannot_keep_ids_only_digest(fixture, monkeypatch):
    m = fixture.module
    monkeypatch.setattr(m, "time", SimpleNamespace(time=lambda: 12345))
    before = [("AX-DAG-1", "fixture", True, "before")]
    after = [("AX-DAG-1", "fixture", False, "after")]
    try:
        first = m.generate_scitt_receipt(before, 1.0)
        second = m.generate_scitt_receipt(after, 1.0)
    except ValueError:
        return  # Detailed positive coverage of the new export schema follows.
    assert first.get("merkle_root_sha3_256") != second.get("merkle_root_sha3_256")


def test_empty_export_is_not_a_verified_receipt(fixture):
    with pytest.raises(ValueError):
        fixture.module.generate_scitt_receipt([], 0)


@pytest.mark.parametrize("flag", [[], ["--json"], ["--scitt"], ["--json", "--scitt"]])
@pytest.mark.parametrize("strict", [[], ["--strict"]])
def test_all_cli_modes_block_without_checkers(fixture, flag, strict):
    result = fixture.cli(*flag, *strict)
    assert result.returncode == 2, result.stderr
    if not flag:
        assert b"VERDICT: NOT_EXECUTED" in result.stdout
        assert b"SIGNATURE: UNSIGNED" in result.stdout
        return
    report = json.loads(result.stdout)
    assert report["passed"] is False and report["verification_performed"] is False
    assert report["verdict"] == "NOT_EXECUTED"
    assert report["registered_checkers"] == []
    assert len(report["invariants"]) == 25
    assert {x["status"] for x in report["invariants"]} == {"NOT_EXECUTED"}
    assert report["metrics"]["not_executed_invariants"] == 25
    assert report["metrics"]["failed_invariants"] == report["metrics"]["passed_invariants"] == 0
    assert report["metrics"]["smt_verification_latency_ms"] is None
    assert report["signature"] is None and report["signature_status"] == "UNSIGNED"
    assert report["scitt_receipt_status"] == "NOT_ISSUED"
    assert report["hw_provenance"] == "UNVERIFIED"
    assert report["legal_compliance"] == "NOT_ASSESSED"
    assert report["certification"] == "NONE"
    assert report["configuration"]["strict"] == bool(strict)


@pytest.mark.parametrize("status,code,verdict", [("FAIL", 1, "REPORTED_FAILURE"), ("UNKNOWN", 2, "UNKNOWN")])
@pytest.mark.parametrize(
    "flags", [{}, {"json_output": True}, {"scitt_output": True}, {"strict": True, "json_output": True}]
)
def test_reported_failures_and_unknown_always_block(fixture, monkeypatch, capsys, status, code, verdict, flags):
    m = fixture.module
    records = m._collect_invariants()
    records[0]["status"] = status
    monkeypatch.setattr(m, "_collect_invariants", lambda: records)
    assert m.run_fast_smt_verification(**flags) == code
    output = capsys.readouterr().out
    if flags.get("json_output") or flags.get("scitt_output"):
        report = json.loads(output)
        assert report["verdict"] == verdict
        assert report["metrics"]["not_executed_invariants"] == 24
        assert report["metrics"]["failed_invariants"] == int(status == "FAIL")
        assert report["metrics"]["unknown_invariants"] == int(status == "UNKNOWN")
        assert report["passed"] is False
    else:
        assert f"VERDICT: {verdict}" in output


@pytest.mark.parametrize(
    "mutation",
    [
        "missing",
        "duplicate",
        "unknown-id",
        "tuple",
        "extra-field",
        "missing-detail",
        "boolean",
        "pass",
        "string-true",
        "unknown-status",
        "blank-description",
        "blank-detail",
        "huge-detail",
    ],
)
def test_invalid_result_inventory_cannot_be_exported_or_pass(fixture, monkeypatch, capsys, mutation):
    m = fixture.module
    records = m._collect_invariants()
    if mutation == "missing":
        records.pop()
    elif mutation == "duplicate":
        records[-1] = deepcopy(records[0])
    elif mutation == "unknown-id":
        records[0]["id"] = "AX-UNKNOWN-1"
    elif mutation == "tuple":
        records[0] = ("AX-DAG-1", "legacy", True, "fake")
    elif mutation == "extra-field":
        records[0]["verified"] = True
    elif mutation == "missing-detail":
        del records[0]["detail"]
    elif mutation == "boolean":
        records[0]["status"] = True
    elif mutation == "pass":
        records[0]["status"] = "PASS"
    elif mutation == "string-true":
        records[0]["status"] = "True"
    elif mutation == "unknown-status":
        records[0]["status"] = "ATTESTED"
    elif mutation == "blank-description":
        records[0]["description"] = " "
    elif mutation == "blank-detail":
        records[0]["detail"] = " "
    elif mutation == "huge-detail":
        records[0]["detail"] = "x" * 16385
    with pytest.raises(ValueError):
        m.generate_scitt_receipt(records, 1)
    monkeypatch.setattr(m, "_collect_invariants", lambda: records)
    assert m.run_fast_smt_verification(json_output=True) == 1
    report = json.loads(capsys.readouterr().out)
    assert report["verdict"] == "INVALID_REPORT" and report["passed"] is False


def test_unsigned_report_digest_independently_binds_every_body_field(fixture, monkeypatch):
    m = fixture.module
    monkeypatch.setattr(m.time, "time", lambda: 12345)
    records = m._collect_invariants()
    records[0]["detail"] = "Información sintética: Ω"
    report = m.generate_scitt_receipt(
        records,
        1.5,
        configuration=m._configuration(fixture.root, False),
        observations=m.observe_workspace(fixture.root),
    )
    digest = report["content_digest"]
    body = {key: value for key, value in report.items() if key != "content_digest"}

    def independently_hash(value):
        canonical = json.dumps(
            value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False
        ).encode()
        return blake3(b"BABYLON60:INVARIANT:REPORT:v3\0" + canonical).hexdigest()

    assert digest == {
        "algorithm": "BLAKE3",
        "domain": "BABYLON60:INVARIANT:REPORT:v3",
        "value": independently_hash(body),
    }
    for key in body:
        changed = deepcopy(body)
        changed[key] = {"synthetic_mutation": key}
        assert independently_hash(changed) != digest["value"], key
    assert report["path_observation_state"] == "REPORTED_OBSERVATIONS_NOT_PROOF"
    assert report["provenance"] == "REPORTED_STATUSES_NOT_PROOF"
    assert report["timestamp_source"] == "LOCAL_CLOCK_UNATTESTED"


@pytest.mark.parametrize(
    "field", ["status", "detail", "description", "root", "strict", "observation", "latency", "timestamp"]
)
def test_same_ids_do_not_hide_content_changes(fixture, monkeypatch, field):
    m = fixture.module
    clock = [100]
    monkeypatch.setattr(m.time, "time", lambda: clock[0])
    records = m._collect_invariants()
    config = m._configuration(fixture.root, False)
    observations = m.observe_workspace(fixture.root)
    first = m.generate_scitt_receipt(records, 1, configuration=config, observations=observations)
    latency = 1
    if field == "status":
        records[0]["status"] = "FAIL"
    elif field == "detail":
        records[0]["detail"] = "changed explanation"
    elif field == "description":
        records[0]["description"] = "changed declaration"
    elif field == "root":
        config["root"] = str(fixture.root / "other")
    elif field == "strict":
        config["strict"] = True
    elif field == "observation":
        observations[0]["status"] = "UNINSPECTABLE"
    elif field == "latency":
        latency = 2
    elif field == "timestamp":
        clock[0] = 101
    second = m.generate_scitt_receipt(records, latency, configuration=config, observations=observations)
    assert first["required_invariant_ids"] == second["required_invariant_ids"]
    assert first["content_digest"]["value"] != second["content_digest"]["value"]


def test_export_is_pure_deterministic_and_does_not_mutate_inputs(fixture, monkeypatch):
    m = fixture.module
    monkeypatch.setattr(m.time, "time", lambda: 123)

    def forbidden(*args, **kwargs):
        raise AssertionError("pure export must not access workspace")

    monkeypatch.setattr(m.os, "open", forbidden)
    records = m._collect_invariants()
    original = deepcopy(records)
    first = m.generate_scitt_receipt(records, 1)
    second = m.generate_scitt_receipt(list(reversed(records)), 1)
    assert first == second
    assert first["path_observation_state"] == "NOT_COLLECTED" and first["observations"] == []
    assert records == original
    first["invariants"][0]["detail"] = "caller mutated export"
    assert records == original
    with ThreadPoolExecutor(max_workers=4) as pool:
        values = list(pool.map(lambda _: m.generate_scitt_receipt(records, 1)["content_digest"]["value"], range(32)))
    assert set(values) == {second["content_digest"]["value"]}


@pytest.mark.parametrize("latency", [True, "1", None, -1, float("nan"), float("inf"), float("-inf")])
def test_invalid_latency_is_rejected(fixture, latency):
    with pytest.raises(ValueError):
        fixture.module.generate_scitt_receipt(fixture.module._collect_invariants(), latency)


@pytest.mark.parametrize(
    "change",
    [
        {"schema": "legacy"},
        {"checker_profile": "all-proven"},
        {"strict": 1},
        {"root": "relative"},
        {"root": "/tmp/\x00injected"},
        {"root": False},
        {"extra": True},
    ],
)
def test_configuration_cannot_claim_unsupported_profile(fixture, change):
    m = fixture.module
    config = m._configuration(fixture.root, False)
    config.update(change)
    with pytest.raises(ValueError):
        m.generate_scitt_receipt(m._collect_invariants(), 1, configuration=config)


@pytest.mark.parametrize("mutation", ["missing", "duplicate", "path", "kind", "status", "extra", "boolean"])
def test_supplied_path_observations_are_validated(fixture, mutation):
    m = fixture.module
    observations = m.observe_workspace(fixture.root)
    if mutation == "missing":
        observations.pop()
    elif mutation == "duplicate":
        observations[-1] = deepcopy(observations[0])
    elif mutation == "path":
        observations[0]["path"] = "../operator"
    elif mutation == "kind":
        observations[0]["expected_kind"] = "socket"
    elif mutation == "status":
        observations[0]["status"] = "PROVEN"
    elif mutation == "extra":
        observations[0]["attested"] = True
    elif mutation == "boolean":
        observations[0]["status"] = True
    with pytest.raises(ValueError):
        m.generate_scitt_receipt(m._collect_invariants(), 1, observations=observations)


def test_path_observation_is_typed_local_and_never_follows_marker_links(fixture):
    m = fixture.module
    root = fixture.root
    (root / "docs").mkdir()
    (root / ".agent").write_text("not a directory")
    values = {x["id"]: x for x in m.observe_workspace(root)}
    assert values["OBS-ROOT"]["status"] == "PRESENT"
    assert values["OBS-DOCS"]["status"] == "PRESENT"
    assert values["OBS-README"]["status"] == "PRESENT"
    assert values["OBS-AGENT"]["status"] == "TYPE_MISMATCH"
    (root / "README.md").unlink()
    (root / "README.md").symlink_to(root / ".agent")
    assert {x["id"]: x["status"] for x in m.observe_workspace(root)}["OBS-README"] == "TYPE_MISMATCH"
    child = root / "child"
    child.mkdir()
    assert {x["id"]: x["status"] for x in m.observe_workspace(child)}["OBS-AGENTS"] == "ABSENT"
    link = root / "linked-root"
    link.symlink_to(child, target_is_directory=True)
    linked = m.observe_workspace(link)
    assert linked[0]["status"] == "UNINSPECTABLE"
    assert {x["status"] for x in linked[1:]} == {"NOT_CHECKED"}


def test_missing_or_uninspectable_root_keeps_properties_unverified(fixture, monkeypatch):
    m = fixture.module
    absent = m.observe_workspace(fixture.root / "missing")
    assert absent[0]["status"] == "ABSENT"
    assert {x["status"] for x in absent[1:]} == {"NOT_CHECKED"}

    def denied(*args, **kwargs):
        raise PermissionError("fixture permission denied")

    monkeypatch.setattr(m.os, "open", denied)
    values = m.observe_workspace(fixture.root)
    assert values[0]["status"] == "UNINSPECTABLE"
    assert {x["status"] for x in values[1:]} == {"NOT_CHECKED"}
    report = m.generate_scitt_receipt(m._collect_invariants(), 1, observations=values)
    assert report["passed"] is False


def test_daily_phase_rejects_present_gate_nonzero_without_running_maintenance(fixture):
    # Extract ONLY the function. Never import/execute maintenance, its --fix, or a canary.
    source = (ROOT / "scripts/c5_quality_gates/daily_sovereign_maintenance.py").read_text()
    tree = ast.parse(source)
    function = next(x for x in tree.body if isinstance(x, ast.FunctionDef) and x.name == "phase_4_quality_gates")
    scripts = fixture.root / "scripts"
    for relative in (
        "c5_verifiers/fast_smt_gate.py",
        "c5_quality_gates/audit_scripts_quality.py",
        "c5_quality_gates/canary_check.py",
    ):
        target = scripts / relative
        target.parent.mkdir(exist_ok=True, parents=True)
        target.write_text("fixture placeholder; never executed")
    gate_exit = fixture.cli("--json").returncode
    calls = []

    def fake_run(command, **kwargs):
        calls.append(command)
        code = gate_exit if str(command[1]).endswith("fast_smt_gate.py") else 0
        return SimpleNamespace(returncode=code, stdout="{}", stderr="")

    namespace = {"SCRIPTS_DIR": scripts, "sys": sys, "subprocess": SimpleNamespace(run=fake_run)}
    exec(compile(ast.Module(body=[function], type_ignores=[]), "<isolated-phase-4>", "exec"), namespace)
    result = namespace["phase_4_quality_gates"]()
    assert result["status"] == "FAIL" and result["fast_smt_gate_pass"] is False
    assert len(calls) == 3
    assert any(str(call[1]).endswith("fast_smt_gate.py") for call in calls)


def test_help_describes_unsigned_legacy_alias(fixture):
    result = fixture.cli("--help")
    assert result.returncode == 0 and b"no SCITT receipt" in result.stdout
