"""Regression inputs for report semantics; these fixtures are not NEMESIS evidence."""

import base64
import hashlib
import json
import os
import signal
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from typing import cast

from scripts.c5_quality_gates import generate_nemesis_report as generator

GENERATOR = Path(__file__).resolve().parents[1] / "scripts/c5_quality_gates/generate_nemesis_report.py"


def runner_output(
    cases: list[tuple[str, str]],
    passed: int,
    failed: int = 0,
    ignored: int = 0,
    outcome: str = "ok",
) -> str:
    return (
        "\n".join(
            [
                f"running {len(cases)} tests",
                *[f"test {name} ... {result}" for name, result in cases],
                f"test result: {outcome}. {passed} passed; {failed} failed; {ignored} ignored; "
                "0 measured; 0 filtered out; finished in 0.00s",
            ]
        )
        + "\n"
    )


class NemesisReportTests(unittest.TestCase):
    def execute_fixture(self, code: str, timeout_seconds: float = 2.0) -> dict[str, object]:
        original_command = generator.TEST_COMMAND
        generator.TEST_COMMAND = [sys.executable, "-c", code]
        try:
            with tempfile.TemporaryDirectory() as directory:
                return cast(
                    dict[str, object], generator.run_adversarial_suite(Path(directory), timeout_seconds=timeout_seconds)
                )
        finally:
            generator.TEST_COMMAND = original_command

    def test_binary_stdout_is_retained_and_cannot_pass(self) -> None:
        raw = b"\xffbinary-stdout\n"
        result = self.execute_fixture(f"import os; os.write(1, {raw!r})")
        self.assertEqual(base64.b64decode(cast(str, result["stdout_raw_base64"])), raw)
        self.assertFalse(result["output_decoding_complete"])
        self.assertFalse(result["success"])
        self.assertEqual(result["result"], "INCOMPLETE")

    def test_binary_stderr_cannot_turn_valid_summary_into_pass(self) -> None:
        output = runner_output([("fixture_case", "ok")], 1)
        raw = b"\xfediagnostic\n"
        result = self.execute_fixture(f"import os; os.write(1, {output.encode()!r}); os.write(2, {raw!r})")
        self.assertTrue(result["parsing_complete"])
        self.assertEqual(base64.b64decode(cast(str, result["stderr_raw_base64"])), raw)
        self.assertEqual(result["result"], "INCOMPLETE")

    def test_timeout_retains_partial_output_and_fails(self) -> None:
        result = self.execute_fixture("import time; print('partial-output', flush=True); time.sleep(60)", 0.2)
        self.assertTrue(result["timed_out"])
        self.assertEqual(result["result"], "TIMEOUT")
        self.assertFalse(result["success"])
        self.assertTrue(result["cleanup_complete"])
        self.assertIn("partial-output", cast(str, result["stdout"]))
        self.assertLess(cast(float, result["duration_s"]), 5.0)

    @unittest.skipUnless(os.name == "posix", "process-group termination requires POSIX")
    def test_timeout_terminates_child_process_group(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            pid_file = Path(directory) / "child.pid"
            code = (
                "import subprocess, sys, time; from pathlib import Path; "
                "child=subprocess.Popen([sys.executable,'-c','import time; time.sleep(60)']); "
                f"Path({str(pid_file)!r}).write_text(str(child.pid)); "
                "print('child-ready', flush=True); time.sleep(60)"
            )
            result = self.execute_fixture(code, 0.5)
            self.assertEqual(result["termination_scope"], "posix_process_group")
            self.assertTrue(result["cleanup_complete"])
            self.assertTrue(pid_file.exists(), "fixture must create its child before the deadline")
            child_pid = int(pid_file.read_text())
            try:
                state = subprocess.run(
                    ["ps", "-o", "stat=", "-p", str(child_pid)],
                    capture_output=True,
                    text=True,
                )
                self.assertTrue(
                    not state.stdout.strip() or state.stdout.strip().startswith("Z"),
                    state.stdout,
                )
            finally:
                try:
                    os.kill(child_pid, signal.SIGKILL)
                except ProcessLookupError:
                    pass

    def test_invalid_timeout_rejected_before_launch(self) -> None:
        for timeout in (0.0, -1.0, float("nan"), float("inf")):
            with self.subTest(timeout=timeout), self.assertRaises(ValueError):
                generator.run_adversarial_suite(Path.cwd(), timeout_seconds=timeout)

    def test_cli_invalid_timeout_returns_argument_error(self) -> None:
        result = subprocess.run(
            [sys.executable, str(GENERATOR), "--stdout", "--timeout-seconds", "nan"],
            capture_output=True,
            text=True,
            timeout=5.0,
        )
        self.assertEqual(result.returncode, 2)
        self.assertEqual(result.stdout, "")

    def test_cli_timeout_writes_report_before_error_exit(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "scripts/c5_quality_gates/generate_nemesis_report.py"
            source.parent.mkdir(parents=True)
            source.write_bytes(GENERATOR.read_bytes())
            fixture = [
                sys.executable,
                "-c",
                "import time; print('partial',flush=True); time.sleep(60)",
            ]
            driver = (
                "import importlib.util,sys; "
                f"spec=importlib.util.spec_from_file_location('fixture_collector',{str(source)!r}); "
                "m=importlib.util.module_from_spec(spec); spec.loader.exec_module(m); "
                f"m.TEST_COMMAND={fixture!r}; "
                "sys.argv=['fixture_collector','--stdout','--timeout-seconds','0.2']; m.main()"
            )
            result = subprocess.run(
                [sys.executable, "-c", driver],
                capture_output=True,
                text=True,
                timeout=5.0,
            )
            report = json.loads(result.stdout)
            self.assertEqual(result.returncode, 1)
            self.assertEqual(report["test_suite"]["result"], "TIMEOUT")
            self.assertEqual(report["status"], "EVIDENCE_COLLECTED_PENDING_AUDIT")
            self.assertEqual(
                json.loads((root / "reports/nemesis_evidence_report_v2.json").read_text()),
                report,
            )

    def test_complete_success_contains_observed_cases(self) -> None:
        parsed = generator.parse_test_output(runner_output([("alpha", "ok"), ("beta", "ok")], 2))
        self.assertTrue(parsed["parsing_complete"])
        self.assertEqual(parsed["tests_executed"], 2)
        self.assertEqual([case["name"] for case in parsed["cases"]], ["alpha", "beta"])

    def test_failed_cases_are_retained(self) -> None:
        parsed = generator.parse_test_output(runner_output([("alpha", "FAILED")], 0, 1, outcome="FAILED"))
        self.assertTrue(parsed["parsing_complete"])
        self.assertEqual(parsed["tests_failed"], 1)
        self.assertEqual(parsed["summary_result"], "FAILED")

    def test_ignored_cases_with_reason_are_not_executed(self) -> None:
        parsed = generator.parse_test_output(runner_output([("alpha", "ignored, requires hardware")], 0, ignored=1))
        self.assertTrue(parsed["parsing_complete"])
        self.assertEqual(parsed["tests_executed"], 0)

    def test_empty_run_contains_no_executed_tests(self) -> None:
        parsed = generator.parse_test_output(runner_output([], 0))
        self.assertTrue(parsed["parsing_complete"])
        self.assertEqual(parsed["tests_executed"], 0)

    def test_summary_without_case_evidence_is_incomplete(self) -> None:
        parsed = generator.parse_test_output(runner_output([], 19))
        self.assertFalse(parsed["parsing_complete"])
        self.assertEqual(parsed["tests_passed"], 0)

    def test_duplicate_cases_are_incomplete(self) -> None:
        parsed = generator.parse_test_output(runner_output([("alpha", "ok"), ("alpha", "ok")], 2))
        self.assertFalse(parsed["parsing_complete"])

    def test_missing_summary_is_incomplete(self) -> None:
        parsed = generator.parse_test_output("running 1 test\ntest alpha ... ok\n")
        self.assertFalse(parsed["parsing_complete"])

    def test_multiple_summaries_are_incomplete(self) -> None:
        output = runner_output([("alpha", "ok")], 1)
        output += "test result: ok. 1 passed; 0 failed; 0 ignored; 0 measured; 0 filtered out; finished in 0s\n"
        self.assertFalse(generator.parse_test_output(output)["parsing_complete"])

    def test_running_count_mismatch_is_incomplete(self) -> None:
        output = runner_output([("alpha", "ok")], 1).replace("running 1 tests", "running 2 tests")
        self.assertFalse(generator.parse_test_output(output)["parsing_complete"])

    def test_missing_runner_cannot_pass(self) -> None:
        original_command = generator.TEST_COMMAND
        with tempfile.TemporaryDirectory() as directory:
            generator.TEST_COMMAND = [str(Path(directory) / "absent-executable")]
            try:
                result = generator.run_adversarial_suite(Path(directory))
            finally:
                generator.TEST_COMMAND = original_command
        self.assertFalse(result["success"])
        self.assertEqual(result["result"], "RUNNER_ERROR")
        self.assertIsNone(result["return_code"])
        self.assertEqual(result["tests_executed"], 0)

    def test_report_retains_output_without_certifying_invariants(self) -> None:
        output = runner_output([("alpha", "ok")], 1)
        suite = {
            **generator.parse_test_output(output),
            "command": ["fixture-only"],
            "return_code": 0,
            "success": True,
            "result": "PASS",
            "runner_error": None,
            "duration_s": 0.01,
            "stdout": output,
            "stderr": "runner diagnostic\n",
        }
        with tempfile.TemporaryDirectory() as directory:
            report = generator.build_report(Path(directory), suite)
        self.assertEqual(report["status"], "EVIDENCE_COLLECTED_PENDING_AUDIT")
        self.assertTrue(report["evidence_assessment"]["executed_test"])
        self.assertEqual(report["test_suite"]["stdout"], output)
        self.assertEqual(report["test_suite"]["stderr"], "runner diagnostic\n")
        self.assertEqual(report["commit"], "UNKNOWN_COMMIT")
        self.assertIsNone(report["working_tree_dirty"])
        for field in (
            "invariants",
            "attestation",
            "merkle_evidence_root",
            "kernel_adversarial",
            "crash_recovery",
        ):
            self.assertNotIn(field, report)
        sha256 = report.pop("evidence_payload_sha256")
        sha3 = report.pop("evidence_payload_sha3_256")
        payload = json.dumps(report, sort_keys=True, separators=(",", ":")).encode("utf-8")
        self.assertEqual(sha256, "sha256:" + hashlib.sha256(payload).hexdigest())
        self.assertEqual(sha3, "sha3-256:" + hashlib.sha3_256(payload).hexdigest())
        report["test_suite"]["stdout"] += "tampered"
        changed = json.dumps(report, sort_keys=True, separators=(",", ":")).encode("utf-8")
        self.assertNotEqual(sha256, "sha256:" + hashlib.sha256(changed).hexdigest())

    def test_failed_serialization_preserves_previous_report(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / "report.json"
            target.write_text('{"previous": true}\n')
            with self.assertRaises(TypeError):
                generator.write_report(target, {"bad": set()})
            self.assertEqual(target.read_text(), '{"previous": true}\n')
            self.assertEqual(list(Path(directory).iterdir()), [target])

    def test_successful_write_replaces_complete_json(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / "reports/report.json"
            generator.write_report(target, {"new": True})
            self.assertEqual(json.loads(target.read_text()), {"new": True})
            self.assertEqual(list(target.parent.iterdir()), [target])


if __name__ == "__main__":
    unittest.main()
