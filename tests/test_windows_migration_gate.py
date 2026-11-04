"""Synthetic report fixtures test the gate; they are not evidence of native Windows execution."""

import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import xml.etree.ElementTree as ET

import pytest

from scripts.guards.verify_windows_migrations import MigrationEvidence

ROOT = Path(__file__).absolute().parents[1]
CASES = ("none", "editable", "wheel", "source-wheel")
TEST = "test_source_installer_respects_wheel_exclusions"
MODULES = ("babylon60.oncology_primitives", "babylon60.genomics", "babylon60.cli.onco_transducer")


@pytest.fixture
def reports(tmp_path):
    installer = tmp_path / "install.ps1"
    installer.write_text("# synthetic installer digest fixture", encoding="utf-8")
    evidence = tmp_path / "evidence"
    evidence.mkdir()
    suite = ET.Element("testsuite")
    for case in CASES:
        ET.SubElement(suite, "testcase", classname="tests.test_onco_distribution", name=f"{TEST}[{case}]")
        after = {"modules": dict.fromkeys(MODULES, False), "entry_points": [], "old_command_exists": False,
                 "editable": False, "version": "5.0.1", "lock_unchanged": True}
        observations = {"installer_sha256": hashlib.sha256(installer.read_bytes()).hexdigest(), "after-1": after}
        phases = {"install-1": 0, "probe-after-1": 0, "cli-help": 0, "cli-onco": 2, "cli-boolean-sim": 2}
        if case != "none":
            observations.update({"after-2": after, "before": {
                "modules": dict.fromkeys(MODULES, True), "entry_points": ["babylon60-onco"],
                "old_command_exists": True, "editable": case == "editable", "version": "5.0.1",
            }})
            phases.update({"legacy-install": 0, "probe-before": 0, "install-2": 0, "probe-after-2": 0})
        if case == "wheel":
            phases.update({"legacy-build": 0, "legacy-dependencies": 0})
        data = {"schema": 1, "case": case, "nodeid": f"tests/test_onco_distribution.py::{TEST}[{case}]",
                "status": "passed", "platform": "win32", "python": "3.11", "revision": "a" * 40,
                "run_id": "42-1", "observations": observations,
                "commands": [{"phase": name, "command": ["synthetic-fixture"], "status": "finished",
                              "returncode": code, "stdout": "fixture output", "stderr": ""}
                             for name, code in phases.items()]}
        (evidence / f"{case}.json").write_text(json.dumps(data), encoding="utf-8")
    junit = tmp_path / "results.xml"
    ET.ElementTree(suite).write(junit, encoding="utf-8")
    return tmp_path, junit, evidence, installer


def run_gate(reports):
    directory, junit, evidence, installer = reports
    output = directory / "verdict.json"
    result = subprocess.run(
        [sys.executable, str(ROOT / "scripts/guards/verify_windows_migrations.py"),
         "--junit", str(junit), "--evidence", str(evidence), "--installer", str(installer),
         "--revision", "a" * 40, "--run-id", "42-1", "--python", "3.11", "--output", str(output)],
        capture_output=True, encoding="utf-8", timeout=10,
    )
    return result, json.loads(output.read_text(encoding="utf-8"))


def test_gate_accepts_complete_matching_reports(reports):
    result, verdict = run_gate(reports)
    assert result.returncode == 0, result.stderr
    assert verdict["passed"] is True
    assert verdict["cases"] == dict.fromkeys(CASES, "passed")


@pytest.mark.parametrize("selection", ["all-skipped", "one-selected"])
def test_gate_rejects_real_pytest_skips_and_partial_selection(reports, selection):
    _, junit, _, _ = reports
    target = f"tests/test_onco_distribution.py::{TEST}"
    if selection == "one-selected":
        target += "[wheel]"
    env = os.environ.copy()
    env.pop("BABYLON_TEST_INSTALL_BUNDLE", None)
    env.pop("PYTEST_ADDOPTS", None)
    result = subprocess.run(
        [sys.executable, "-m", "pytest", target, "-q", f"--junitxml={junit}"],
        cwd=ROOT, env=env, capture_output=True, encoding="utf-8", timeout=20,
    )
    assert result.returncode == 0, result.stderr
    cases = list(ET.parse(junit).iter("testcase"))
    assert len(cases) == (4 if selection == "all-skipped" else 1)
    assert all(case.find("skipped") is not None for case in cases)
    result, verdict = run_gate(reports)
    assert result.returncode == 1
    assert verdict["passed"] is False
    assert all(value == "failed" for value in verdict["cases"].values())


@pytest.mark.parametrize("defect", [
    "skip", "xfail", "failure", "error", "missing-case", "duplicate", "unexpected", "no-xml", "bad-xml",
    "no-evidence", "bad-json", "running", "no-phase", "bad-exit", "no-log", "stale-revision", "stale-run",
    "wrong-python", "wrong-platform", "wrong-installer", "residual-module", "residual-exe", "version-changed",
    "lock-changed", "missing-before", "wrong-case", "incomplete-command",
])
def test_gate_rejects_omissions_and_incomplete_evidence(reports, defect):
    _, junit, evidence, installer = reports
    tree = ET.parse(junit)
    root = tree.getroot()
    if defect in {"skip", "xfail", "failure", "error"}:
        ET.SubElement(root[0], "skipped" if defect in {"skip", "xfail"} else defect)
        tree.write(junit)
    elif defect == "missing-case":
        root.remove(root[0])
        tree.write(junit)
    elif defect in {"duplicate", "unexpected"}:
        ET.SubElement(root, "testcase", **root[0].attrib if defect == "duplicate" else {"name": "unexpected"})
        tree.write(junit)
    elif defect == "no-xml":
        junit.unlink()
    elif defect == "bad-xml":
        junit.write_text("<broken", encoding="utf-8")
    elif defect == "no-evidence":
        (evidence / "wheel.json").unlink()
    elif defect == "bad-json":
        (evidence / "wheel.json").write_text("{", encoding="utf-8")
    elif defect == "wrong-installer":
        installer.write_text("changed", encoding="utf-8")
    else:
        path = evidence / "wheel.json"
        data = json.loads(path.read_text(encoding="utf-8"))
        fields = {"running": ("status", "running"), "stale-revision": ("revision", "b" * 40),
                  "stale-run": ("run_id", "41-1"), "wrong-python": ("python", "3.12"),
                  "wrong-platform": ("platform", "darwin"), "wrong-case": ("case", "editable")}
        if defect in fields:
            key, value = fields[defect]
            data[key] = value
        elif defect == "no-phase":
            data["commands"].pop()
        elif defect == "bad-exit":
            data["commands"][0]["returncode"] = 1
        elif defect == "no-log":
            del data["commands"][0]["stdout"]
        elif defect == "incomplete-command":
            data["commands"][0]["status"] = "running"
        elif defect == "missing-before":
            del data["observations"]["before"]
        else:
            after = data["observations"]["after-1"]
            if defect == "residual-module":
                after["modules"][MODULES[0]] = True
            else:
                key, value = {"residual-exe": ("old_command_exists", True), "version-changed": ("version", "5.0.2"),
                              "lock-changed": ("lock_unchanged", False)}[defect]
                after[key] = value
        path.write_text(json.dumps(data), encoding="utf-8")
    result, verdict = run_gate(reports)
    assert result.returncode == 1, result.stdout
    assert verdict["passed"] is False
    assert verdict["errors"]


def test_recorder_preserves_failed_command_without_claiming_completion(tmp_path):
    path = tmp_path / "case.json"
    recorder = MigrationEvidence(path, "none", "synthetic-node")
    result = recorder.run("intentional-failure", [sys.executable, "-c", "print('retained output'); raise SystemExit(7)"],
                          capture_output=True, encoding="utf-8")
    assert result.returncode == 7
    data = json.loads(path.read_text(encoding="utf-8"))
    assert data["status"] == "running"
    assert data["commands"][0]["returncode"] == 7
    assert data["commands"][0]["stdout"] == "retained output\n"


def test_recorder_preserves_launch_error(tmp_path):
    path = tmp_path / "case.json"
    recorder = MigrationEvidence(path, "none", "synthetic-node")
    with pytest.raises(FileNotFoundError):
        recorder.run("cannot-launch", [str(tmp_path / "missing-program")])
    data = json.loads(path.read_text(encoding="utf-8"))
    assert data["status"] == "running"
    assert data["commands"][0]["status"] == "error"


def test_recorder_retains_partial_output_on_timeout(tmp_path):
    path = tmp_path / "case.json"
    recorder = MigrationEvidence(path, "none", "synthetic-node")
    with pytest.raises(subprocess.TimeoutExpired):
        recorder.run("timeout", [sys.executable, "-c", "import time; print('started', flush=True); time.sleep(10)"],
                     capture_output=True, encoding="utf-8", timeout=0.5)
    data = json.loads(path.read_text(encoding="utf-8"))
    assert data["status"] == "running"
    assert data["commands"][0]["status"] == "error"
    assert data["commands"][0]["stdout"] == "started\n"
