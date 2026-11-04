"""Record installation checks and reject incomplete native Windows migration reports."""

import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import xml.etree.ElementTree as ET

CASES = ("none", "editable", "wheel", "source-wheel")
TEST = "test_source_installer_respects_wheel_exclusions"
MODULES = ("babylon60.oncology_primitives", "babylon60.genomics", "babylon60.cli.onco_transducer")


class MigrationEvidence:
    """Persist observations as they happen; only the test's last statement marks success."""

    def __init__(self, path, case, nodeid):
        self.path = Path(path)
        self.data = {
            "schema": 1, "case": case, "nodeid": nodeid, "status": "running",
            "platform": sys.platform, "python": f"{sys.version_info.major}.{sys.version_info.minor}",
            "revision": os.environ.get("BABYLON_MIGRATION_REVISION", ""),
            "run_id": os.environ.get("BABYLON_MIGRATION_RUN", ""),
            "observations": {}, "commands": [],
        }
        self.save()

    def save(self):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        temporary = self.path.with_suffix(".tmp")
        temporary.write_text(json.dumps(self.data, indent=2, ensure_ascii=True), encoding="utf-8")
        temporary.replace(self.path)

    def observe(self, name, value):
        self.data["observations"][name] = value
        self.save()

    def run(self, phase, command, **kwargs):
        event = {"phase": phase, "command": [str(arg) for arg in command], "status": "running"}
        self.data["commands"].append(event)
        self.save()
        try:
            result = subprocess.run(command, **kwargs)
        except (OSError, subprocess.TimeoutExpired) as exc:
            event.update(status="error", error=str(exc))
            for key in ("stdout", "stderr"):
                value = getattr(exc, key, None) or ""
                event[key] = value.decode("utf-8", errors="replace") if isinstance(value, bytes) else value
            self.save()
            raise
        event.update(status="finished", returncode=result.returncode, stdout=result.stdout, stderr=result.stderr)
        self.save()
        return result

    def finish(self):
        self.data["status"] = "passed"
        self.save()


def validate_case(data, case, revision, run_id, python, installer_hash):
    expected_node = f"tests/test_onco_distribution.py::{TEST}[{case}]"
    for name, value in {
        "schema": 1, "case": case, "nodeid": expected_node, "status": "passed",
        "platform": "win32", "python": python, "revision": revision, "run_id": run_id,
    }.items():
        if data.get(name) != value:
            raise ValueError(f"{case}: invalid {name}")
    observations = data["observations"]
    if observations["installer_sha256"] != installer_hash:
        raise ValueError(f"{case}: installer digest mismatch")
    before = observations.get("before")
    phases = {"install-1": 0, "probe-after-1": 0, "cli-help": 0, "cli-onco": 2, "cli-boolean-sim": 2}
    if case != "none":
        if before["modules"] != dict.fromkeys(MODULES, True) or before["entry_points"] != ["babylon60-onco"]:
            raise ValueError(f"{case}: missing legacy modules or entry point")
        if before["old_command_exists"] is not True or before["editable"] is not (case == "editable"):
            raise ValueError(f"{case}: invalid legacy installation")
        phases.update({"legacy-install": 0, "probe-before": 0, "install-2": 0, "probe-after-2": 0})
    if case == "wheel":
        phases.update({"legacy-build": 0, "legacy-dependencies": 0})
    for number in range(1, 2 if case == "none" else 3):
        after = observations[f"after-{number}"]
        if after["modules"] != dict.fromkeys(MODULES, False) or after["entry_points"] != []:
            raise ValueError(f"{case}: residual modules or entry point")
        if after["editable"] is not False or after["old_command_exists"] is not False:
            raise ValueError(f"{case}: residual editable installation or executable")
        if after["lock_unchanged"] is not True or not isinstance(after["version"], str) or not after["version"]:
            raise ValueError(f"{case}: invalid lockfile or version evidence")
        if before is not None and after["version"] != before["version"]:
            raise ValueError(f"{case}: version changed")
    commands = data["commands"]
    if len({command["phase"] for command in commands}) != len(commands):
        raise ValueError(f"{case}: duplicate command phases")
    by_phase = {command["phase"]: command for command in commands}
    for phase, returncode in phases.items():
        command = by_phase[phase]
        if command["status"] != "finished" or command["returncode"] != returncode:
            raise ValueError(f"{case}: unsuccessful {phase}")
        if not command["command"] or not all(isinstance(command.get(key), str) for key in ("stdout", "stderr")):
            raise ValueError(f"{case}: incomplete command evidence for {phase}")


def verify(junit, evidence, revision, run_id, python, installer):
    errors = []
    results = {}
    junit_passed = set()
    if not all((revision, run_id, python)):
        errors.append("Revision, run ID and Python version must be nonempty")
    try:
        report = ET.parse(junit)
        expected = {("tests.test_onco_distribution", f"{TEST}[{case}]") for case in CASES}
        nodes = list(report.iter("testcase"))
        actual = [(node.get("classname"), node.get("name")) for node in nodes]
        if len(actual) != len(CASES) or set(actual) != expected:
            errors.append("JUnit must contain exactly the four distinct migration cases")
        if any(node.tag in {"skipped", "failure", "error"} for node in report.iter()):
            errors.append("JUnit contains a skipped, failed or errored case")
        for case in CASES:
            matches = [node for node in nodes if
                       (node.get("classname"), node.get("name")) == ("tests.test_onco_distribution", f"{TEST}[{case}]")]
            if len(matches) == 1 and not any(node.tag in {"skipped", "failure", "error"} for node in matches[0].iter()):
                junit_passed.add(case)
    except (OSError, ET.ParseError) as exc:
        errors.append(f"Missing or invalid JUnit: {exc}")
    try:
        installer_hash = hashlib.sha256(Path(installer).read_bytes()).hexdigest()
    except OSError as exc:
        errors.append(f"Cannot read installer: {exc}")
        installer_hash = ""
    for case in CASES:
        try:
            data = json.loads((Path(evidence) / f"{case}.json").read_text(encoding="utf-8"))
            validate_case(data, case, revision, run_id, python, installer_hash)
        except (OSError, ValueError, KeyError, TypeError, AttributeError) as exc:
            results[case] = "failed"
            errors.append(f"{case}: invalid or missing evidence: {exc}")
        else:
            results[case] = "passed" if case in junit_passed else "failed"
    return {"passed": not errors, "revision": revision, "run_id": run_id, "python": python,
            "cases": results, "errors": errors}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for option in ("junit", "evidence", "revision", "run-id", "python", "installer", "output"):
        parser.add_argument(f"--{option}", required=True)
    args = parser.parse_args()
    result = verify(args.junit, args.evidence, args.revision, args.run_id, args.python, args.installer)
    Path(args.output).write_text(json.dumps(result, indent=2), encoding="utf-8")
    print("PASS: four complete Windows migration reports" if result["passed"] else "FAIL: incomplete Windows migrations")
    for error in result["errors"]:
        print(error, file=sys.stderr)
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
