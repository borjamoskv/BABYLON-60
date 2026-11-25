#!/usr/bin/env python3
"""Build an isolated pinned Lean workspace and require both Seqlock regressions."""

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
from typing import Any

ROOT = Path(__file__).absolute().parents[2]
TESTS = (
    "lean_emitter::tests::test_verification_checks_option_like_output_names",
    "lean_emitter::tests::security_disconnected_aeons_cannot_verify_as_a_chain",
)
LAKEFILE = """name = "b60_seqlock_ci"
version = "0.1.0"
defaultTargets = ["BabylonTrace"]

[[lean_lib]]
name = "BabylonTrace"
"""


def require_one_passed_test(output: str) -> None:
    """Cargo exits successfully even when an exact filter selects zero tests."""
    summaries = re.findall(
        r"^test result: (\w+)\. (\d+) passed; (\d+) failed; (\d+) ignored; (\d+) measured;",
        output,
        re.MULTILINE,
    )
    if summaries != [("ok", "1", "0", "0", "0")]:
        raise ValueError(f"Expected exactly one executed, passing test; got {summaries!r}")


def prepare_workspace(root: Path, workspace: Path) -> str:
    workspace.mkdir(mode=0o700)
    for name in ("BabylonTrace.lean", "lean-toolchain"):
        shutil.copyfile(root / "proof/lean" / name, workspace / name)
    (workspace / "lakefile.toml").write_text(LAKEFILE, encoding="utf-8")
    pin = (workspace / "lean-toolchain").read_text(encoding="utf-8").strip()
    if not pin or len(pin.split()) != 1:
        raise ValueError("lean-toolchain must specify exactly one toolchain")
    return pin


def run_logged(command: list[str], cwd: Path, env: dict[str, str], log: Path) -> str:
    print(f"Running {log.stem}", flush=True)
    with log.open("w", encoding="utf-8") as stream:
        stream.write(f"command: {command!r}\ncwd: {cwd}\n")
        stream.flush()
        result = subprocess.run(
            command, cwd=cwd, env=env, stdout=stream, stderr=subprocess.STDOUT, timeout=900, check=False
        )
    output = log.read_text(encoding="utf-8")
    if result.returncode:
        raise RuntimeError(f"Command exited {result.returncode}; see {log}\n{output}")
    return output


def verify(output_dir: Path) -> int:
    # A fresh directory prevents stale success reports/oleans from hiding a failure.
    output_dir.mkdir(mode=0o700, parents=True, exist_ok=False)
    report: dict[str, Any] = {"status": "FAIL", "tests": []}
    try:
        workspace = output_dir / "workspace"
        pin = prepare_workspace(ROOT, workspace)
        report["toolchain"] = pin
        report["source_sha256"] = hashlib.sha256((workspace / "BabylonTrace.lean").read_bytes()).hexdigest()
        env = os.environ.copy()
        for name in ("LEAN_PATH", "LEAN_SYSROOT", "LAKE_HOME", "LAKE_OVERRIDE_LEAN", "LEAN", "LAKE"):
            env.pop(name, None)
        env["ELAN_TOOLCHAIN"] = pin
        run_logged(["elan", "run", "--install", pin, "lean", "--version"], workspace, env, output_dir / "install.log")
        # Query the pinned toolchain rather than inheriting the host's default Lean.
        prefix = subprocess.run(
            ["elan", "run", pin, "lean", "--print-prefix"],
            cwd=workspace,
            env=env,
            capture_output=True,
            text=True,
            timeout=60,
            check=True,
        ).stdout.strip()
        binaries = Path(prefix) / "bin"
        if not all((binaries / name).is_file() for name in ("lean", "lake")):
            raise ValueError(f"Pinned Lean toolchain has no lean/lake binaries: {prefix}")
        env["PATH"] = str(binaries) + os.pathsep + env.get("PATH", "")
        env["LEAN"] = str(binaries / "lean")
        env["LAKE"] = str(binaries / "lake")
        env["BABYLON_LEAN_TEST_WORKSPACE"] = str(workspace)
        run_logged([str(binaries / "lean"), "--version"], workspace, env, output_dir / "lean-version.log")
        run_logged(
            [str(binaries / "lake"), "--wfail", "build", "BabylonTrace"], workspace, env, output_dir / "build.log"
        )
        for index, name in enumerate(TESTS, 1):
            command = [
                "cargo",
                "test",
                "--locked",
                "-p",
                "b60-lang",
                "--lib",
                name,
                "--",
                "--exact",
                "--include-ignored",
                "--nocapture",
                "--test-threads=1",
                "--color",
                "never",
            ]
            output = run_logged(command, ROOT, env, output_dir / f"test-{index}.log")
            require_one_passed_test(output)
            report["tests"].append({"name": name, "passed": 1, "failed": 0, "ignored": 0})
        report["status"] = "PASS"
        print("PASS: 2 Seqlock tests executed; 0 failed; 0 ignored.")
        return 0
    except (OSError, RuntimeError, ValueError, subprocess.SubprocessError) as error:
        report["error"] = str(error)
        print(f"FAIL: {error}", file=sys.stderr)
        return 1
    finally:
        (output_dir / "summary.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, required=True, help="New directory for the workspace and logs")
    args = parser.parse_args()
    return verify(args.output_dir.absolute())


if __name__ == "__main__":
    sys.exit(main())
