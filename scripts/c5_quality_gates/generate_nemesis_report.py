#!/usr/bin/env python3
"""Collect one bounded NEMESIS test invocation as unsigned evidence for audit."""

import argparse
import base64
import datetime
import hashlib
import json
import math
import os
import platform
import re
import signal
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from collections.abc import Mapping
from typing import TypedDict, cast


class ParsedTests(TypedDict):
    tests_total: int
    tests_executed: int
    tests_passed: int
    tests_failed: int
    tests_ignored: int
    cases: list[dict[str, str]]
    parsing_complete: bool
    reported_counts: dict[str, int] | None
    summary_result: str | None


class SuiteResult(ParsedTests):
    command: list[str]
    result: str
    success: bool
    return_code: int | None
    runner_error: str | None
    timeout_seconds: float
    timed_out: bool
    cleanup_complete: bool
    termination_scope: str
    duration_s: float
    stdout: str
    stderr: str
    output_decoding_complete: bool
    stdout_raw_base64: str | None
    stderr_raw_base64: str | None


class ReportSuite(TypedDict):
    name: str
    stdout: str
    stderr: str


class EvidenceReport(TypedDict, total=False):
    schema: str
    report_version: str
    commit: str
    working_tree_dirty: bool | None
    timestamp_iso: str
    status: str
    evidence_assessment: dict[str, bool | str]
    platform_observed: dict[str, str]
    test_suite: ReportSuite
    evidence_payload_sha256: str
    evidence_payload_sha3_256: str

TEST_LINE = re.compile(r"test\s+(\S+)\s+\.\.\.\s+(ok|FAILED|ignored)(?:, .*)?")
RUNNING_LINE = re.compile(r"running (\d+) tests?")
SUMMARY_LINE = re.compile(
    r"test result: (ok|FAILED)\. (\d+) passed; (\d+) failed;"
    r" (\d+) ignored; (\d+) measured; (\d+) filtered out; finished in .+"
)
TEST_COMMAND = [
    "cargo",
    "test",
    "--test",
    "adversarial_nemesis",
    "--features",
    "cortex-persist",
]


def get_git_commit(repo_root: Path) -> str:
    try:
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=repo_root,
            capture_output=True,
            text=True,
            check=True,
        )
        return result.stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        return "UNKNOWN_COMMIT"


def working_tree_dirty(repo_root: Path) -> bool | None:
    try:
        result = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=repo_root,
            capture_output=True,
            text=True,
            check=True,
        )
        return bool(result.stdout.strip())
    except (OSError, subprocess.CalledProcessError):
        return None


def detect_filesystem(path: Path) -> str:
    """Observe a filesystem label; an unavailable observation stays UNKNOWN."""
    try:
        if platform.system() == "Darwin":
            result = subprocess.run(["df", str(path)], capture_output=True, text=True, check=True)
            lines = result.stdout.strip().splitlines()
            if len(lines) < 2:
                return "UNKNOWN"
            device = lines[1].split()[0]
            mounts = subprocess.run(["mount"], capture_output=True, text=True, check=True)
            for line in mounts.stdout.splitlines():
                if line.startswith(device + " "):
                    if "apfs" in line.lower():
                        return "APFS"
                    if "hfs" in line.lower():
                        return "HFS+"
        elif platform.system() == "Linux":
            result = subprocess.run(
                ["stat", "-f", "-c", "%T", str(path)],
                capture_output=True,
                text=True,
                check=True,
            )
            return result.stdout.strip().upper() or "UNKNOWN"
    except (OSError, subprocess.CalledProcessError, IndexError):
        pass
    return "UNKNOWN"


def parse_test_output(stdout: str) -> ParsedTests:
    """Require one complete libtest summary consistent with observed case lines."""
    cases, summaries, running_counts = [], [], []
    for line in stdout.splitlines():
        line = line.strip()
        case = TEST_LINE.fullmatch(line)
        summary = SUMMARY_LINE.fullmatch(line)
        running = RUNNING_LINE.fullmatch(line)
        if case:
            cases.append({"name": case.group(1), "result": case.group(2).upper()})
        if summary:
            summaries.append(summary)
        if running:
            running_counts.append(int(running.group(1)))

    passed = sum(case["result"] == "OK" for case in cases)
    failed = sum(case["result"] == "FAILED" for case in cases)
    ignored = sum(case["result"] == "IGNORED" for case in cases)
    complete = False
    reported_counts = None
    summary_result = None
    if len(summaries) == 1:
        summary = summaries[0]
        summary_result = summary.group(1)
        reported_counts = dict(
            zip(
                ("passed", "failed", "ignored", "measured", "filtered_out"),
                map(int, summary.groups()[1:]),
            )
        )
        complete = (
            (passed, failed, ignored) == tuple(reported_counts[key] for key in ("passed", "failed", "ignored"))
            and reported_counts["measured"] == 0
            and running_counts == [len(cases)]
            and len({case["name"] for case in cases}) == len(cases)
        )
    return {
        "tests_total": len(cases),
        "tests_executed": passed + failed,
        "tests_passed": passed,
        "tests_failed": failed,
        "tests_ignored": ignored,
        "cases": cases,
        "parsing_complete": complete,
        "reported_counts": reported_counts,
        "summary_result": summary_result,
    }


def decode_runner_output(raw: bytes) -> tuple[str, str | None]:
    """Retain exact bytes in base64 when UTF-8 decoding would lose information."""
    try:
        return raw.decode("utf-8"), None
    except UnicodeDecodeError:
        return raw.decode("utf-8", errors="replace"), base64.b64encode(raw).decode("ascii")


def positive_timeout(value: str) -> float:
    try:
        seconds = float(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("timeout must be a positive finite number") from exc
    if not math.isfinite(seconds) or seconds <= 0:
        raise argparse.ArgumentTypeError("timeout must be a positive finite number")
    return seconds


def run_adversarial_suite(repo_root: Path, timeout_seconds: float = 600.0) -> SuiteResult:
    if not math.isfinite(timeout_seconds) or timeout_seconds <= 0:
        raise ValueError("timeout must be a positive finite number")
    command = list(TEST_COMMAND)
    started_at = time.perf_counter()
    raw_stdout, raw_stderr = b"", b""
    runner_error, return_code = None, None
    timed_out, cleanup_complete = False, True
    try:
        process = subprocess.Popen(
            command,
            cwd=repo_root,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            start_new_session=os.name == "posix",
        )
        try:
            raw_stdout, raw_stderr = process.communicate(timeout=timeout_seconds)
        except subprocess.TimeoutExpired as exc:
            timed_out = True
            raw_stdout, raw_stderr = exc.output or b"", exc.stderr or b""
            if os.name == "posix":
                try:
                    os.killpg(process.pid, signal.SIGKILL)
                except ProcessLookupError:
                    pass
            else:
                process.kill()
            try:
                raw_stdout, raw_stderr = process.communicate(timeout=5.0)
            except subprocess.TimeoutExpired as cleanup_error:
                cleanup_complete = False
                raw_stdout = cleanup_error.output or raw_stdout
                raw_stderr = cleanup_error.stderr or raw_stderr
                # Escaped descendants may still hold pipes open. Close the readers
                # and bound parent reaping too; do not wait on those pipes forever.
                if process.stdout is not None:
                    process.stdout.close()
                if process.stderr is not None:
                    process.stderr.close()
                process.kill()
                try:
                    process.wait(timeout=5.0)
                except subprocess.TimeoutExpired:
                    pass
        return_code = process.returncode
    except OSError as exc:
        runner_error = str(exc)

    stdout, stdout_raw_base64 = decode_runner_output(raw_stdout)
    stderr, stderr_raw_base64 = decode_runner_output(raw_stderr)
    output_decoding_complete = stdout_raw_base64 is None and stderr_raw_base64 is None
    parsed = parse_test_output(stdout)
    if timed_out:
        outcome = "TIMEOUT"
    elif runner_error:
        outcome = "RUNNER_ERROR"
    elif not parsed["parsing_complete"] or not output_decoding_complete:
        outcome = "INCOMPLETE"
    elif parsed["tests_executed"] == 0:
        outcome = "NO_TESTS_EXECUTED"
    elif return_code == 0 and parsed["tests_failed"] == 0 and parsed["summary_result"] == "ok":
        outcome = "PASS"
    else:
        outcome = "FAIL"
    return {
        **parsed,
        "command": command,
        "result": outcome,
        "success": outcome == "PASS",
        "return_code": return_code,
        "runner_error": runner_error,
        "timeout_seconds": timeout_seconds,
        "timed_out": timed_out,
        "cleanup_complete": cleanup_complete,
        "termination_scope": "posix_process_group" if os.name == "posix" else "direct_process",
        "duration_s": round(time.perf_counter() - started_at, 6),
        "stdout": stdout,
        "stderr": stderr,
        "output_decoding_complete": output_decoding_complete,
        "stdout_raw_base64": stdout_raw_base64,
        "stderr_raw_base64": stderr_raw_base64,
    }


def build_report(repo_root: Path, suite_result: Mapping[str, object]) -> EvidenceReport:
    tests_executed = suite_result["tests_executed"]
    if not isinstance(tests_executed, int):
        raise TypeError("tests_executed must be an integer")
    report: EvidenceReport = {
        "schema": "nemesis-report/v2",
        "report_version": "2.1.0",
        "commit": get_git_commit(repo_root),
        "working_tree_dirty": working_tree_dirty(repo_root),
        "timestamp_iso": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "status": "EVIDENCE_COLLECTED_PENDING_AUDIT",
        "evidence_assessment": {
            "evidence_available": bool(
                suite_result["stdout"] or suite_result["stderr"] or suite_result["runner_error"]
            ),
            "executed_test": tests_executed > 0,
            "scope": (
                "One local invocation of the adversarial_nemesis Rust integration suite. "
                "This unsigned record collects runner output and observed test outcomes "
                "for audit. Invariant coverage and NEMESIS-100 acceptance remain unassessed."
            ),
        },
        "platform_observed": {
            "os": platform.system(),
            "arch": platform.machine(),
            "filesystem": detect_filesystem(repo_root),
        },
        "test_suite": cast(ReportSuite, {
            "name": "adversarial_nemesis",
            **{key: value for key, value in suite_result.items() if key != "success"},
        }),
    }
    # Hash the payload before adding these two digest fields. No signing key is used.
    payload = json.dumps(report, sort_keys=True, separators=(",", ":")).encode("utf-8")
    report["evidence_payload_sha256"] = "sha256:" + hashlib.sha256(payload).hexdigest()
    report["evidence_payload_sha3_256"] = "sha3-256:" + hashlib.sha3_256(payload).hexdigest()
    return report


def write_report(report_file: Path, report: Mapping[str, object]) -> None:
    """Replace the report only after the new JSON has been written successfully."""
    report_file.parent.mkdir(parents=True, exist_ok=True)
    temporary_path = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            dir=report_file.parent,
            prefix=".nemesis-",
            delete=False,
        ) as output_file:
            temporary_path = Path(output_file.name)
            json.dump(report, output_file, indent=2)
            output_file.write("\n")
            output_file.flush()
            os.fsync(output_file.fileno())
        os.replace(temporary_path, report_file)
    finally:
        if temporary_path is not None:
            temporary_path.unlink(missing_ok=True)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--stdout", action="store_true", help="emit the report as JSON on stdout")
    parser.add_argument(
        "--timeout-seconds",
        type=positive_timeout,
        default=600.0,
        help="maximum runner duration including compilation (default: 600 seconds)",
    )
    args = parser.parse_args()
    repo_root = Path(__file__).resolve().parent.parent.parent
    report_file = repo_root / "reports" / "nemesis_evidence_report_v2.json"
    print("Running one adversarial_nemesis test-suite invocation.", file=sys.stderr)
    suite_result = run_adversarial_suite(repo_root, timeout_seconds=args.timeout_seconds)
    report = build_report(repo_root, suite_result)
    write_report(report_file, report)
    print(
        f"Unsigned evidence report: {report_file}; suite result: {suite_result['result']}",
        file=sys.stderr,
    )
    if args.stdout:
        print(json.dumps(report, indent=2))
    if not suite_result["success"]:
        sys.exit(1)


if __name__ == "__main__":
    main()
