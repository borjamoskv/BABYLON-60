"""Independent Lot 7 controls; only owned temporary paths and pure report logic."""
from __future__ import annotations

import ast
from contextlib import redirect_stdout
from copy import deepcopy
import hashlib
import importlib.util
import io
import json
import os
from pathlib import Path
import socket
import subprocess
import sys
import tempfile
from types import SimpleNamespace
from typing import Any
from unittest.mock import patch

from blake3 import blake3

sys.dont_write_bytecode = True
ROOT = Path(__file__).absolute().parents[4]
SOURCE = ROOT / "scripts/c5_verifiers/fast_smt_gate.py"
TEST = ROOT / "tests/test_swarm100_lot7_regressions.py"
CONSUMER = ROOT / "scripts/c5_quality_gates/daily_sovereign_maintenance.py"
DOMAIN = b"BABYLON60:INVARIANT:REPORT:v3\0"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def digest(body):
    raw = json.dumps(body, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode()
    return blake3(DOMAIN + raw).hexdigest()


def rejected(callback):
    try:
        callback()
    except (ValueError, TypeError, OverflowError):
        return
    raise AssertionError("unsupported value accepted")


def main():
    hashes_before = {str(path.relative_to(ROOT)): sha(path) for path in (SOURCE, TEST, CONSUMER)}
    original_cwd = Path.cwd()
    original_env = dict(os.environ)
    checks = []
    forbidden_calls = []

    def forbidden(*args, **kwargs):
        forbidden_calls.append("network/process attempt")
        raise AssertionError("network and subprocess execution forbidden")

    try:
        with tempfile.TemporaryDirectory(prefix="lot7-independent-") as temporary:
            home = Path(temporary)
            root = home / "workspace"
            root.mkdir()
            os.environ.clear()
            os.environ.update(HOME=str(home), PATH="/usr/bin:/bin", LC_ALL="C")
            os.chdir(root)
            (root / "README.md").write_text("fixture marker only")
            for name in ("docs", ".agents", ".agent"):
                (root / name).mkdir()
            with patch.object(socket.socket, "connect", forbidden), \
                    patch.object(socket.socket, "connect_ex", forbidden), \
                    patch.object(socket, "getaddrinfo", forbidden), \
                    patch.object(subprocess, "Popen", forbidden):
                spec = importlib.util.spec_from_file_location("independent_lot7_gate", SOURCE)
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                records = module._collect_invariants()
                assert len(records) == len({item["id"] for item in records}) == 25
                assert {item["status"] for item in records} == {"NOT_EXECUTED"}
                checks.append(dict(name="complete_catalogue_unexecuted_despite_markers", passed=True, count=25))

                combinations = 0
                for status, expected in (("NOT_EXECUTED", 2), ("FAIL", 1), ("UNKNOWN", 2)):
                    sample = deepcopy(records)
                    sample[0]["status"] = status
                    with patch.object(module, "_collect_invariants", lambda: sample):
                        for strict in (False, True):
                            for json_output, scitt_output in ((False, False), (True, False), (False, True), (True, True)):
                                output = io.StringIO()
                                with redirect_stdout(output):
                                    result = module.run_fast_smt_verification(json_output, scitt_output, strict, root=root)
                                assert result == expected
                                if json_output or scitt_output:
                                    report = json.loads(output.getvalue())
                                    assert report["passed"] is False and report["verification_performed"] is False
                                    assert report["metrics"]["passed_invariants"] == 0
                                    assert report["configuration"]["strict"] is strict
                                combinations += 1
                checks.append(dict(name="all_modes_fail_closed", passed=True, combinations=combinations))

                malformed = [[], records[:-1], [*deepcopy(records[:-1]), deepcopy(records[0])]]
                for status in (True, False, "PASS", "True", "", "COMPLIANT", None):
                    sample = deepcopy(records)
                    sample[0]["status"] = status
                    malformed.append(sample)
                sample = deepcopy(records)
                sample[0] = ("AX-DAG-1", "legacy", True, "SECRET-SYNTHETIC")
                malformed.append(sample)
                sample = deepcopy(records)
                sample[0]["id"] = "UNKNOWN-ID"
                malformed.append(sample)
                sample = deepcopy(records)
                sample[0]["detail"] = "\ud800"
                malformed.append(sample)
                for sample in malformed:
                    rejected(lambda: module.generate_scitt_receipt(sample, 0))
                    with patch.object(module, "_collect_invariants", lambda: sample), redirect_stdout(io.StringIO()) as output:
                        assert module.run_fast_smt_verification(json_output=True, root=root) == 1
                    error = json.loads(output.getvalue())
                    assert error["verdict"] == "INVALID_REPORT" and error["passed"] is False
                    assert "SECRET-SYNTHETIC" not in output.getvalue()
                checks.append(dict(name="schema_inventory_and_legacy_rejection", passed=True, cases=len(malformed)))

                config = module._configuration(root, False)
                observations = module.observe_workspace(root)
                with patch.object(module, "time", SimpleNamespace(time=lambda: 12345)):
                    report = module.generate_scitt_receipt(records, 1, configuration=config, observations=observations)
                    body = {key: value for key, value in report.items() if key != "content_digest"}
                    assert report["content_digest"]["value"] == digest(body)
                    for key in body:
                        changed = deepcopy(body)
                        changed[key] = {"independent_mutation": key}
                        assert digest(changed) != report["content_digest"]["value"]
                    reversed_report = module.generate_scitt_receipt(
                        list(reversed(records)), 1, configuration=config, observations=list(reversed(observations))
                    )
                    assert reversed_report == report
                    for field in ("description", "detail", "status"):
                        changed_records = deepcopy(records)
                        changed_records[0][field] = "UNKNOWN" if field == "status" else "independently changed field"
                        changed_report = module.generate_scitt_receipt(changed_records, 1, configuration=config, observations=observations)
                        assert changed_report["required_invariant_ids"] == report["required_invariant_ids"]
                        assert changed_report["content_digest"] != report["content_digest"]
                checks.append(dict(name="complete_body_domain_digest_and_order", passed=True, body_fields=len(body), same_id_mutations=3))

                with patch.object(module, "os", SimpleNamespace(open=forbidden)), \
                        patch.object(module, "observe_workspace", forbidden):
                    supplied = module.generate_scitt_receipt(records, 0, configuration=config, observations=observations)
                    empty = module.generate_scitt_receipt(records, 0, configuration=config)
                assert supplied["path_observation_state"] == "REPORTED_OBSERVATIONS_NOT_PROOF"
                assert empty["path_observation_state"] == "NOT_COLLECTED"
                for report in (supplied, empty):
                    assert report["provenance"] == "REPORTED_STATUSES_NOT_PROOF"
                    assert report["signature"] is None and report["signature_status"] == "UNSIGNED"
                    assert report["scitt_receipt_status"] == "NOT_ISSUED"
                    assert report["legal_compliance"] == "NOT_ASSESSED"
                    assert report["certification"] == "NONE" and report["hw_provenance"] == "UNVERIFIED"
                    assert report["metrics"]["smt_verification_latency_ms"] is None
                checks.append(dict(name="pure_export_provenance_and_unsigned_claims", passed=True))

                before_inputs = deepcopy((records, config, observations))
                report = module.generate_scitt_receipt(records, 1, configuration=config, observations=observations)
                report["configuration"]["root"] = "/synthetic-mutation"
                report["invariants"][0]["detail"] = "synthetic-mutation"
                report["observations"][0]["detail"] = "synthetic-mutation"
                assert (records, config, observations) == before_inputs
                for value in (True, -1, float("nan"), float("inf"), "0", None):
                    rejected(lambda: module.generate_scitt_receipt(records, value))
                for change in ({"root": "../escape"}, {"root": "/bad\0root"}, {"strict": 1}, {"checker_profile": "proven"}):
                    bad_config = {**config, **change}
                    rejected(lambda: module.generate_scitt_receipt(records, 0, configuration=bad_config))
                checks.append(dict(name="input_copying_and_invalid_configuration_latency", passed=True, invalid_cases=10))

                (root / "README.md").unlink()
                (root / "README.md").symlink_to(root / "absent-target")
                assert {item["id"]: item["status"] for item in module.observe_workspace(root)}["OBS-README"] == "TYPE_MISMATCH"
                (root / "README.md").unlink()
                os.mkfifo(root / "README.md")
                assert {item["id"]: item["status"] for item in module.observe_workspace(root)}["OBS-README"] == "TYPE_MISMATCH"
                child = root / "child"
                child.mkdir()
                assert {item["id"]: item["status"] for item in module.observe_workspace(child)}["OBS-AGENTS"] == "ABSENT"
                link = root / "root-link"
                link.symlink_to(child, target_is_directory=True)
                for candidate, expected in ((link, "UNINSPECTABLE"), (root / "missing-root", "ABSENT")):
                    observed = module.observe_workspace(candidate)
                    assert observed[0]["status"] == expected
                    assert {item["status"] for item in observed[1:]} == {"NOT_CHECKED"}
                checks.append(dict(name="entries_no_symlink_or_fifo_following_no_parent_claim", passed=True, cases=5))

                calls = []
                original_os = module.os

                def recording_open(path, flags):
                    calls.append((str(path), flags))
                    return original_os.open(path, flags)

                def recording_stat(path, **kwargs):
                    assert kwargs["follow_symlinks"] is False
                    assert isinstance(kwargs["dir_fd"], int)
                    return original_os.stat(path, **kwargs)

                os_double = SimpleNamespace(open=recording_open, stat=recording_stat, close=original_os.close,
                                            O_RDONLY=original_os.O_RDONLY, O_DIRECTORY=original_os.O_DIRECTORY,
                                            O_NOFOLLOW=original_os.O_NOFOLLOW)
                with patch.object(module, "os", os_double):
                    module.observe_workspace(root)
                assert len(calls) == 1 and calls[0][0] == str(root)
                assert calls[0][1] & original_os.O_NOFOLLOW and calls[0][1] & original_os.O_DIRECTORY
                checks.append(dict(name="observation_opens_only_root_then_descriptor_stat", passed=True, open_calls=1))

                tree = ast.parse(CONSUMER.read_text())
                function = next(node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == "phase_4_quality_gates")
                scripts = root / "scripts"
                paths = ("c5_quality_gates/audit_scripts_quality.py", "c5_verifiers/fast_smt_gate.py", "c5_quality_gates/canary_check.py")
                for relative in paths:
                    target = scripts / relative
                    target.parent.mkdir(parents=True, exist_ok=True)
                    target.write_text("placeholder never executed")
                consumer_calls = []
                gate_status = [2]

                def fake_run(command, **kwargs):
                    consumer_calls.append(command)
                    return SimpleNamespace(returncode=gate_status[0] if str(command[1]).endswith("fast_smt_gate.py") else 0)

                namespace = dict(SCRIPTS_DIR=scripts, subprocess=SimpleNamespace(run=fake_run), sys=sys, Any=Any)
                exec(compile(ast.Module(body=[function], type_ignores=[]), "<isolated-phase-four>", "exec"), namespace)
                for gate_status[0] in (1, 2):
                    consumer_calls.clear()
                    value = namespace["phase_4_quality_gates"]()
                    assert value["status"] == "FAIL" and value["fast_smt_gate_pass"] is False
                    assert len(consumer_calls) == 3
                (scripts / "c5_verifiers/fast_smt_gate.py").unlink()
                value = namespace["phase_4_quality_gates"]()
                assert value["status"] == "PASS" and value["fast_smt_gate_pass"] is True
                checks.append(dict(name="consumer_ast_with_three_doubles_propagates_nonzero", passed=True,
                                   limitation="Missing gate defaults to PASS in unchanged consumer, outside Lot 7 scope."))
                assert not forbidden_calls
    finally:
        os.chdir(original_cwd)
        os.environ.clear()
        os.environ.update(original_env)
    hashes_after = {str(path.relative_to(ROOT)): sha(path) for path in (SOURCE, TEST, CONSUMER)}
    assert hashes_before == hashes_after
    print(json.dumps(dict(reviewer="03", scope="Temporary fixtures and pure/extracted Python only; no maintenance, solver, network or protected runtime.",
                          checks=checks, check_count=len(checks), status="PASS", forbidden_calls=forbidden_calls,
                          source_sha256_before=hashes_before, source_sha256_after=hashes_after), indent=2))


if __name__ == "__main__":
    main()
