#!/usr/bin/env python3
"""Prepare and evaluate isolated submissions. This file contains no solution."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import difflib
import hashlib
import json
import os
from pathlib import Path
import platform
import re
import shutil
import subprocess
import sys
import time
import xml.etree.ElementTree as ET


sys.dont_write_bytecode = True
ROOT = Path(__file__).absolute().parent
TARGET = "src/babylon60/guards/capability_guard.py"
IGNORED = {".git", ".venv", "__pycache__", ".pytest_cache", ".ruff_cache"}


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def canonical(value) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


def read_json(path: Path):
    return json.loads(path.read_text())


def write_json(path: Path, value) -> None:
    temporary = path.with_suffix(path.suffix + ".tmp")
    with temporary.open("x") as stream:
        stream.write(json.dumps(value, ensure_ascii=False, indent=2) + "\n")
    temporary.replace(path)


def utc() -> str:
    return datetime.now(timezone.utc).isoformat()


def inventory(folder: Path, *, submission: bool = False) -> dict[str, dict]:
    found = {}
    for directory, dirs, files in os.walk(folder, followlinks=False):
        if submission:
            dirs[:] = [name for name in dirs if name not in IGNORED]
        for name in dirs + files:
            path = Path(directory) / name
            if path.is_symlink():
                raise ValueError(f"Symlink is outside this exercise: {path}")
        for name in sorted(files):
            path = Path(directory) / name
            relative = path.relative_to(folder).as_posix()
            if relative == "manifest.json" and folder == ROOT:
                continue
            if submission and relative == ".benchmark.json":
                continue
            data = path.read_bytes()
            if len(data) > 1_048_576:
                raise ValueError(f"Exercise file exceeds 1 MiB: {relative}")
            found[relative] = {"sha256": sha(data), "bytes": len(data)}
    return dict(sorted(found.items()))


def verify() -> dict:
    manifest = read_json(ROOT / "manifest.json")
    actual = inventory(ROOT)
    if actual != manifest["files"]:
        changed = sorted(name for name in set(actual) | set(manifest["files"])
                         if actual.get(name) != manifest["files"].get(name))
        raise ValueError(f"Frozen package changed: {changed}")
    if sha(canonical(inventory(ROOT / "snapshot"))) != manifest["snapshot_sha256"]:
        raise ValueError("Snapshot digest differs")
    return manifest


def outside_package(path: Path) -> Path:
    absolute = path.absolute()
    physical = Path(os.path.realpath(absolute))
    package = Path(os.path.realpath(ROOT))
    if physical.is_relative_to(package) or package.is_relative_to(physical):
        raise ValueError("Use a separate directory outside the frozen package")
    return absolute


def new_directory(path: Path) -> Path:
    path = outside_package(path)
    path.mkdir(parents=True, exist_ok=False)
    return path


def marker(workspace: Path, manifest: dict) -> dict:
    value = read_json(workspace / ".benchmark.json")
    if value["snapshot_sha256"] != manifest["snapshot_sha256"] or value["prompt_sha256"] != manifest["prompt_sha256"]:
        raise ValueError("Submission belongs to another snapshot or prompt")
    if value["manifest_sha256"] != sha((ROOT / "manifest.json").read_bytes()):
        raise ValueError("Submission belongs to another evaluator package")
    return value


def prepared_workspace(workspace: Path, manifest: dict) -> Path:
    workspace = outside_package(workspace)
    marker(workspace, manifest)
    return workspace


def clean_env(environment: Path, candidate: Path | None = None) -> dict[str, str]:
    env = {key: value for key, value in os.environ.items()
           if not key.startswith(("PYTEST_", "UV_")) and key not in {"PYTHONPATH", "PYTHONHOME", "VIRTUAL_ENV"}}
    env.update(UV_PROJECT_ENVIRONMENT=str(environment), UV_NO_CONFIG="1",
               PYTHONDONTWRITEBYTECODE="1", PYTEST_DISABLE_PLUGIN_AUTOLOAD="1")
    if candidate is not None:
        env["CG_CANDIDATE_ROOT"] = str(candidate)
        env["PYTHONPATH"] = str(candidate / "src")
    return env


def run(command: list[str], output: Path, env: dict[str, str], timeout: int = 120) -> dict:
    started = time.monotonic()
    try:
        result = subprocess.run(command, cwd=output.parent, env=env, capture_output=True,
                                text=True, timeout=timeout, check=False)
        code, stdout, stderr = result.returncode, result.stdout, result.stderr
    except subprocess.TimeoutExpired as exc:
        code, stdout, stderr = 124, str(exc.stdout or ""), str(exc.stderr or "")
    output.write_text(f"exit_code={code}\nSTDOUT\n{stdout}\nSTDERR\n{stderr}")
    return {"argv": command, "exit_code": code, "seconds": round(time.monotonic() - started, 6),
            "log": output.name}


def uv(environment: Path, *arguments: str) -> list[str]:
    return ["uv", "run", "--project", str(ROOT / "env"), "--locked", "--no-sync", *arguments]


def observe_environment(environment: Path) -> dict:
    command = uv(environment, "python", "-c",
                 "import sys,platform,importlib.metadata as m,json; print(json.dumps({'python':sys.version,'platform':platform.platform(),'pytest':m.version('pytest'),'ruff':m.version('ruff')}))")
    actual = json.loads(subprocess.check_output(command, env=clean_env(environment), text=True))
    actual.update(lock_sha256=sha((ROOT / "env/uv.lock").read_bytes()),
                  uv=subprocess.check_output(["uv", "--version"], text=True).strip())
    return actual


def require_environment(path: Path) -> tuple[Path, dict]:
    path = outside_package(path)
    evidence = read_json(path / ".capabilityguard-environment.json")
    if evidence["lock_sha256"] != sha((ROOT / "env/uv.lock").read_bytes()):
        raise ValueError("Evaluation environment uses a different lock")
    if observe_environment(path) != evidence:
        raise ValueError("Observed environment changed after setup")
    return path, evidence


def setup(args) -> dict:
    verify()
    environment = outside_package(args.environment)
    if environment.exists():
        raise ValueError("Setup requires a new environment directory; existing environments are never overwritten")
    env = clean_env(environment)
    command = ["uv", "sync", "--project", str(ROOT / "env"), "--locked", "--python", "3.14.7"]
    result = subprocess.run(command, env=env, text=True, capture_output=True, check=False)
    if result.returncode:
        raise RuntimeError(result.stdout + result.stderr)
    actual = observe_environment(environment)
    write_json(environment / ".capabilityguard-environment.json", actual)
    return actual


def prepare(args) -> dict:
    manifest = verify()
    destination = outside_package(args.destination)
    if destination.exists():
        raise ValueError("Destination already exists; never reset a participant's work")
    shutil.copytree(ROOT / "snapshot", destination)
    value = {"snapshot_sha256": manifest["snapshot_sha256"], "prompt_sha256": manifest["prompt_sha256"],
             "manifest_sha256": sha((ROOT / "manifest.json").read_bytes())}
    write_json(destination / ".benchmark.json", value)
    return {"workspace": str(destination), **value}


def append_event(directory: Path, event: dict) -> None:
    with (directory / "events.jsonl").open("a") as stream:
        stream.write(json.dumps({"utc": utc(), **event}, ensure_ascii=False) + "\n")


def start(args) -> dict:
    manifest = verify()
    workspace = prepared_workspace(args.workspace, manifest)
    if inventory(workspace, submission=True) != inventory(ROOT / "snapshot"):
        raise ValueError("Start requires the untouched snapshot, not a previous solution")
    if not re.fullmatch(r"[AB]0[1-5]", args.run_id):
        raise ValueError("Use an anonymous campaign ID A01..A05 or B01..B05")
    environment, environment_info = require_environment(args.environment)
    reject_overlap(args.run, workspace)
    directory = new_directory(args.run)
    metrics = read_json(ROOT / "metrics-template.json")
    metrics.update(run_id=args.run_id, condition=args.run_id[0], repetition=int(args.run_id[1:]), purpose=args.purpose,
                   status="running", workspace=str(workspace), environment=str(environment),
                   started_at=utc(), started_monotonic_ns=time.monotonic_ns(),
                   clock_platform=platform.platform(), environment_observed=environment_info,
                   snapshot_sha256=manifest["snapshot_sha256"], prompt_sha256=manifest["prompt_sha256"],
                   manifest_sha256=sha((ROOT / "manifest.json").read_bytes()))
    write_json(directory / "metrics.json", metrics)
    append_event(directory, {"kind": "started", "run_id": args.run_id})
    return {"run": str(directory), "run_id": args.run_id, "prompt_file": str(ROOT / "PROMPT.txt")}


def xml_counts(path: Path) -> dict:
    if not path.is_file():
        return {"tests": 0, "failures": 0, "errors": 1, "skipped": 0}
    tree = ET.parse(path).getroot()
    suites = [tree] if tree.tag == "testsuite" else list(tree.iter("testsuite"))
    return {name: sum(int(suite.get(name, 0)) for suite in suites)
            for name in ("tests", "failures", "errors", "skipped")}


def reject_overlap(output: Path, workspace: Path) -> None:
    destination = Path(os.path.realpath(output.absolute()))
    source = Path(os.path.realpath(workspace))
    if destination.is_relative_to(source) or source.is_relative_to(destination):
        raise ValueError("Results and metrics must be outside the participant workspace")


def evaluate(args) -> dict:
    manifest = verify()
    workspace = prepared_workspace(args.workspace, manifest)
    environment, environment_info = require_environment(args.environment)
    submission_ns = time.monotonic_ns()
    reject_overlap(args.output, workspace)
    directory = new_directory(args.output)
    run_directory = outside_package(args.run) if args.run else None
    lock = None
    if run_directory:
        metrics = read_json(run_directory / "metrics.json")
        if metrics["workspace"] != str(workspace) or metrics["manifest_sha256"] != sha((ROOT / "manifest.json").read_bytes()):
            raise ValueError("Run and workspace/package differ")
        if metrics["environment_observed"] != environment_info or metrics["clock_platform"] != platform.platform():
            raise ValueError("Run environment or monotonic-clock host changed")
        if metrics["status"] == "awaiting_review":
            raise ValueError("This run already has a technically accepted submission")
        lock = run_directory / ".evaluate.lock"
        with lock.open("x"):
            pass
    try:
        before = inventory(workspace, submission=True)
        captured = directory / "candidate"
        captured.mkdir()
        for relative in before:
            target = captured / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes((workspace / relative).read_bytes())
        if inventory(captured) != before or inventory(workspace, submission=True) != before:
            raise ValueError("Submission changed during capture; no evaluation result is granted")
        base = inventory(ROOT / "snapshot")
        changed = sorted(name for name in set(base) | set(before) if base.get(name) != before.get(name))
        forbidden = [name for name in changed if name != TARGET and not (
            name.startswith("tests/") and Path(name).name.startswith("test_") and name.endswith(".py")
            and name not in base)]
        scope_ok = not forbidden and TARGET in before
        diff = []
        for name in changed:
            old = (ROOT / "snapshot" / name).read_text().splitlines(keepends=True) if name in base else []
            new = (captured / name).read_text().splitlines(keepends=True) if name in before else []
            diff.extend(difflib.unified_diff(old, new, fromfile="a/" + name, tofile="b/" + name))
        (directory / "submission.diff").write_text("".join(diff))
        env = clean_env(environment, captured)
        common = ["-c", str(ROOT / "env/pyproject.toml"), "--noconftest", "--import-mode=importlib", "-p", "no:cacheprovider", "--tb=short", "-q"]
        acceptance = run(uv(environment, "pytest", str(ROOT / "acceptance/test_acceptance.py"),
                            *common, "--junitxml", str(directory / "acceptance.xml")),
                         directory / "acceptance.log", env)
        acceptance["counts"] = xml_counts(directory / "acceptance.xml")
        own_files = sorted(captured.glob("tests/test_*.py"))
        own = None
        if own_files:
            own = run(uv(environment, "pytest", *map(str, own_files), *common,
                         "--junitxml", str(directory / "participant.xml")), directory / "participant.log", env)
            own["counts"] = xml_counts(directory / "participant.xml")
        lint = run(uv(environment, "ruff", "check", "--no-cache", "--config", str(ROOT / "env/pyproject.toml"),
                      str(captured / TARGET), *map(str, own_files)), directory / "ruff.log", env)
        counts = acceptance["counts"]
        functional = acceptance["exit_code"] == 0 and counts["tests"] == manifest["acceptance_test_count"] and not counts["skipped"]
        own_ok = own is not None and own["exit_code"] == 0 and own["counts"]["tests"] > 0 and not own["counts"]["skipped"]
        accepted = scope_ok and functional and own_ok and lint["exit_code"] == 0
        result = {"manifest_sha256": sha((ROOT / "manifest.json").read_bytes()),
                  "snapshot_sha256": manifest["snapshot_sha256"], "prompt_sha256": manifest["prompt_sha256"],
                  "submission_sha256": sha(canonical(before)), "submission_files": before,
                  "scope_ok": scope_ok, "forbidden_changes": forbidden,
                  "functional_acceptance": functional, "participant_tests_present_and_passing": own_ok,
                  "technical_acceptance": accepted, "human_review_status": "pending",
                  "acceptance": acceptance, "participant_tests": own, "ruff": lint,
                  "environment_observed": environment_info, "submission_observed_at": utc(),
                  "scope": "Unit contract only; validate_tool_execution and OS confinement are not repaired or certified"}
        write_json(directory / "result.json", result)
        if run_directory:
            elapsed = (submission_ns - metrics["started_monotonic_ns"]) / 1e9
            if elapsed < 0:
                raise ValueError("Monotonic clock moved backwards; interval is invalid")
            attempt = {"number": len(metrics["attempts"]) + 1, "result": str(directory / "result.json"),
                       "submission_sha256": result["submission_sha256"], "technical_acceptance": accepted,
                       "elapsed_trial_seconds_at_submission": elapsed}
            metrics["attempts"].append(attempt)
            metrics["resubmissions_after_first"] = len(metrics["attempts"]) - 1
            metrics["status"] = "awaiting_review" if accepted else "needs_rework"
            if accepted:
                metrics["first_technically_accepted_submission_seconds"] = elapsed
            write_json(run_directory / "metrics.json", metrics)
            append_event(run_directory, {"kind": "evaluated", **attempt})
        return result
    finally:
        if lock is not None:
            lock.unlink()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("verify")
    provision = commands.add_parser("setup")
    provision.add_argument("--environment", type=Path, required=True)
    materialize = commands.add_parser("prepare")
    materialize.add_argument("--destination", type=Path, required=True)
    trial = commands.add_parser("start")
    trial.add_argument("--workspace", type=Path, required=True)
    trial.add_argument("--environment", type=Path, required=True)
    trial.add_argument("--run", type=Path, required=True)
    trial.add_argument("--run-id", required=True)
    trial.add_argument("--purpose", choices=["comparison", "harness_validation"], default="comparison")
    evaluation = commands.add_parser("evaluate")
    evaluation.add_argument("--workspace", type=Path, required=True)
    evaluation.add_argument("--environment", type=Path, required=True)
    evaluation.add_argument("--output", type=Path, required=True)
    evaluation.add_argument("--run", type=Path)
    args = parser.parse_args()
    if args.command == "verify":
        manifest = verify()
        result = {"manifest_sha256": sha((ROOT / "manifest.json").read_bytes()),
                  "verified_files": len(manifest["files"]), "snapshot_sha256": manifest["snapshot_sha256"],
                  "prompt_sha256": manifest["prompt_sha256"]}
    else:
        result = {"setup": setup, "prepare": prepare, "start": start, "evaluate": evaluate}[args.command](args)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return int(args.command == "evaluate" and not result["technical_acceptance"])


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (ValueError, OSError, KeyError, RuntimeError) as error:
        print(f"Benchmark error: {error}", file=sys.stderr)
        raise SystemExit(2) from error
