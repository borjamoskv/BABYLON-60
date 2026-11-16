"""Re-run the remaining red cases on the preserved pre-reservation source."""

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path


def main() -> int:
    evidence = Path(__file__).absolute().parent
    root = evidence.parents[4]
    before = json.loads((evidence / "reserved-baseline-source.json").read_text())
    with tempfile.TemporaryDirectory(prefix="b60-lot12-s1-red-") as name:
        fixture = Path(name)
        source = fixture / "scripts/c5_l1_ledger/ledger_snapshot_engine.py"
        source.parent.mkdir(parents=True)
        source.write_text(before["source"])
        tests = fixture / "tests/test_swarm100_lot12_s1_regressions.py"
        tests.parent.mkdir(parents=True)
        tests.write_bytes((root / tests.relative_to(fixture)).read_bytes())
        command = [
            sys.executable,
            "-m",
            "pytest",
            str(tests),
            "-q",
            "-o",
            "addopts=--tb=short",
            "-k",
            "source_removed_before_connect or manifest_created_during_publication or existing_zero_byte_database",
        ]
        env = os.environ.copy()
        env["HOME"] = str(fixture / "home")
        Path(env["HOME"]).mkdir()
        env["PYTHONPATH"] = str(root / "01_KISH_ENGINE")
        result = subprocess.run(command, cwd=fixture, env=env, capture_output=True, text=True)
        log = result.stdout + result.stderr
        (evidence / "red-replay.log").write_text(log)
        (evidence / "red-replay.json").write_text(
            json.dumps(
                {
                    "source_sha256": before["sha256"],
                    "command": command,
                    "pytest_exit_code": result.returncode,
                    "expected_failures": 3,
                    "scope": "Copied source/tests in a temporary directory; production source unchanged",
                },
                indent=2,
            )
            + "\n"
        )
        print(log)
        return 0 if result.returncode == 1 and "3 failed" in log else 1


if __name__ == "__main__":
    raise SystemExit(main())
