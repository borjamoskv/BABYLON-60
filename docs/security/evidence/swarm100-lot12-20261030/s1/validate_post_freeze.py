"""Revalidate the externally changed S1 source and the added cleanup case."""

import hashlib
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path


def main() -> int:
    evidence = Path(__file__).absolute().parent
    root = evidence.parents[4]
    production = root / "scripts/c5_l1_ledger/ledger_snapshot_engine.py"
    tests = root / "tests/test_swarm100_lot12_s1_regressions.py"
    captured = {str(p.relative_to(root)): p.read_bytes() for p in (production, tests)}
    hashes = {p: hashlib.sha256(data).hexdigest() for p, data in captured.items()}
    commands = {
        "regressions": [
            sys.executable, "-m", "pytest", str(tests),
            "tests/test_ledger_snapshot_engine.py", "-q", "-o", "addopts=--tb=short",
        ],
        "ruff": [sys.executable, "-m", "ruff", "check", str(production), str(tests)],
        "mypy": [
            sys.executable, "-m", "mypy", "--follow-imports=silent", "--check-untyped-defs",
            str(production), str(tests),
        ],
    }
    observations = {}
    for name, command in commands.items():
        result = subprocess.run(command, cwd=root, capture_output=True, text=True)
        output = result.stdout + result.stderr
        (evidence / f"post-freeze-{name}.log").write_text(output)
        observations[name] = {"command": command, "exit_code": result.returncode}
        print(name, result.returncode, output)

    previous = json.loads((evidence / "approved-source-reconstructed.json").read_text())
    with tempfile.TemporaryDirectory(prefix="b60-s1-cleanup-red-") as directory:
        fixture = Path(directory)
        original = fixture / production.relative_to(root)
        original.parent.mkdir(parents=True)
        original.write_text(previous["source"])
        current_tests = fixture / tests.relative_to(root)
        current_tests.parent.mkdir(parents=True)
        current_tests.write_bytes(captured[str(tests.relative_to(root))])
        command = [
            sys.executable, "-m", "pytest", str(current_tests), "-q", "-o", "addopts=--tb=short",
            "-k", "cleanup_without_exception_notes_preserves_primary_error_and_continues",
        ]
        env = os.environ.copy()
        env["PYTHONPATH"] = str(root / "01_KISH_ENGINE")
        env["HOME"] = str(fixture / "home")
        Path(env["HOME"]).mkdir()
        result = subprocess.run(command, cwd=fixture, env=env, capture_output=True, text=True)
        output = result.stdout + result.stderr
        (evidence / "post-freeze-added-case-before.log").write_text(output)
        observations["added_case_red"] = {
            "source_sha256": previous["sha256"], "command": command,
            "pytest_exit_code": result.returncode,
            "expected_failure_observed": result.returncode == 1 and "1 failed" in output,
        }
        print("added_case_red", result.returncode, output)

    assert all(hashlib.sha256((root / p).read_bytes()).hexdigest() == h for p, h in hashes.items())
    observations["source_sha256"] = hashes
    observations["production_source_edited_by_this_validation"] = False
    (evidence / "post-freeze-validation.json").write_text(json.dumps(observations, indent=2) + "\n")
    (evidence / "post-freeze-source-test-snapshot.json").write_text(
        json.dumps({p: {"sha256": hashes[p], "source": data.decode()} for p, data in captured.items()}, indent=2)
        + "\n"
    )
    return 0 if all(observations[n]["exit_code"] == 0 for n in commands) and observations["added_case_red"]["expected_failure_observed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
