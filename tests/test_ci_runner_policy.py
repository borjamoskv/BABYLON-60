"""Keep general CI on Linux and preserve deliberate native macOS coverage."""

from fnmatch import fnmatchcase
from itertools import product
from pathlib import Path
from typing import TypedDict, cast

import pytest
import yaml


ROOT = Path(__file__).absolute().parents[1]

VAULT_PAID_RUNNER_GUARD = (
    "github.repository != 'borjamoskv/BABYLON-60-VAULT' || "
    "github.event_name == 'workflow_dispatch' || "
    "startsWith(github.ref, 'refs/tags/v')"
)
VAULT_SCHEDULE_GUARD = "github.event_name != 'schedule' || github.repository != 'borjamoskv/BABYLON-60-VAULT'"
VAULT_PR_OR_PUBLIC_GUARD = (
    "github.repository != 'borjamoskv/BABYLON-60-VAULT' || "
    "github.event_name == 'pull_request' || "
    "github.event_name == 'workflow_dispatch'"
)
VAULT_NON_PUBLIC_JOB_GUARD = (
    "github.repository != 'borjamoskv/BABYLON-60-VAULT' || github.event_name == 'workflow_dispatch'"
)


Step = TypedDict("Step", {"id": str, "run": str, "uses": str, "if": str, "env": dict[str, str]}, total=False)


class Strategy(TypedDict):
    matrix: dict[str, list[str]]


Job = TypedDict(
    "Job",
    {"runs-on": str, "strategy": Strategy, "steps": list[Step], "timeout-minutes": str, "if": str},
    total=False,
)


class DispatchInput(TypedDict):
    type: str
    default: str


class Trigger(TypedDict, total=False):
    branches: list[str]
    paths: list[str]
    tags: list[str]
    inputs: dict[str, DispatchInput]


Workflow = TypedDict("Workflow", {"on": dict[str, Trigger], "jobs": dict[str, Job], "concurrency": dict[str, str]})


def workflow(name: str) -> Workflow:
    # BaseLoader preserves the GitHub key `on` instead of treating it as YAML 1.1 True.
    return cast(Workflow, yaml.load((ROOT / ".github/workflows" / name).read_text(), Loader=yaml.BaseLoader))


def test_general_test_matrices_use_linux_without_dropping_coverage() -> None:
    python = workflow("python-tests.yml")["jobs"]["test"]
    assert python["runs-on"] == "ubuntu-latest"
    assert python["strategy"]["matrix"]["python-version"] == ["3.11", "3.12"]
    commands = "\n".join(step.get("run", "") for step in python["steps"])
    assert "pytest tests/ 02_EDIN_SWARMS/tests/" in commands
    assert "cargo build --locked -p babylon-attest" in commands
    assert "brew" not in commands
    assert "libudev-dev" in commands and "libssl-dev" in commands

    ci = workflow("ci.yml")["jobs"]
    assert ci["rust"]["strategy"]["matrix"]["os"] == ["ubuntu-latest"]
    assert ci["quality"]["runs-on"] == "ubuntu-latest"
    commands = "\n".join(step.get("run", "") for step in ci["rust"]["steps"])
    for command in ("cargo check --workspace --locked", "cargo test --workspace --locked", "cargo clippy --locked"):
        assert command in commands
    quality_commands = "\n".join(step.get("run", "") for step in ci["quality"]["steps"])
    assert "scripts/c5_quality_gates/detect_ghost_nodes.py --scope product" in quality_commands
    assert "tests/test_ghost_node_detector.py" in quality_commands


def test_python_suite_runs_native_broker_tests_against_a_separate_python_build() -> None:
    steps = workflow("python-tests.yml")["jobs"]["test"]["steps"]
    default_build = next((step for step in steps if "-p babylon-attest" in step.get("run", "")), None)
    python_build = next((step for step in steps if "--features python" in step.get("run", "")), None)
    suite = next((step for step in steps if "pytest tests/ 02_EDIN_SWARMS/tests/" in step.get("run", "")), None)
    assert default_build is not None, "missing the default cargo build step"
    assert python_build is not None, "missing the separate `--features python` build step"
    assert suite is not None, "missing the pytest suite step"
    # Own step and target dir: target/debug keeps the library behind BABYLON60_DYLIB_PATH free of pyo3.
    assert "python" not in default_build["run"] and "--all-features" not in default_build["run"]
    assert "cargo build --locked" in python_build["run"] and "--target-dir target/py" in python_build["run"]
    assert steps.index(python_build) < steps.index(suite)
    assert suite["env"]["BABYLON60_DYLIB_PATH"].endswith("/target/debug/libbabylon60.so")
    # Without this variable the native-broker tests skip instead of running.
    assert suite["env"]["BABYLON60_TEST_CAPABILITY_LIBRARY"].endswith("/target/py/debug/libbabylon60.so")
    # The CORTEX memory harness (ledger concurrency) skips as a whole without its own variable.
    assert suite["env"]["CORTEX_MEMORY_BROKER_LIB"].endswith("/target/py/debug/libbabylon60.so")


def test_full_macos_certification_requires_a_release_or_explicit_opt_in() -> None:
    ci = workflow("ci.yml")
    assert ci["on"]["push"]["tags"] == ["v*"]
    opt_in = ci["on"]["workflow_dispatch"]["inputs"]["full_release_evidence"]
    assert opt_in["type"] == "boolean" and opt_in["default"] == "false"
    claims = ci["jobs"]["release-evidence"]
    assert claims["if"] == (
        "startsWith(github.ref, 'refs/tags/v') || "
        "(github.event_name == 'workflow_dispatch' && inputs.full_release_evidence)"
    )
    assert claims["runs-on"] == "macos-15"
    assert claims["timeout-minutes"] == "90"
    commands = "\n".join(step.get("run", "") for step in claims["steps"])
    for command in (
        "verify_claims.py",
        "compile_claims_manifest.py",
        "audit_entropy_3strata.py",
        "swarm_100_stress_campaign.py",
    ):
        assert command in commands
    attest = next(step for step in claims["steps"] if step.get("id") == "attest")
    assert "startsWith(github.ref, 'refs/tags/v')" in attest["if"]


@pytest.mark.parametrize("event", ["push", "pull_request"])
@pytest.mark.parametrize(
    ("path", "native_required"),
    [
        ("src/confinement.rs", True),
        ("crates/babylon-attest/src/lib.rs", True),
        ("Cargo.lock", True),
        ("build.rs", True),
        (".cargo/config.toml", True),
        ("tests/omega_mediation_campaign.rs", True),
        (".github/workflows/macos-native.yml", True),
        ("README.md", False),
        ("docs/03_guides/guide_agent_workflow.md", False),
        ("01_KISH_ENGINE/babylon60/presentation.md", False),
        ("tests/test_response_signature.py", False),
    ],
)
def test_native_workflow_only_triggers_for_native_inputs(event: str, path: str, native_required: bool) -> None:
    native = workflow("macos-native.yml")
    trigger = native["on"][event]
    assert trigger["branches"] == ["main"]
    assert any(fnmatchcase(path, pattern) for pattern in trigger["paths"]) is native_required


def test_native_job_checks_the_real_darwin_boundary_with_a_time_limit() -> None:
    native = workflow("macos-native.yml")
    job = native["jobs"]["seatbelt"]
    assert job["runs-on"] == "macos-15"
    assert job["timeout-minutes"] == "20"
    assert native["concurrency"]["cancel-in-progress"] == "true"
    expected_protoc_action = "arduino/setup-protoc@c65c819552d16ad3c9b72d9dfd5ba5237b9c906b"
    assert any(step.get("uses") == expected_protoc_action for step in job["steps"])
    command = job["steps"][-1]["run"]
    assert "--locked" in command and "--exact" in command
    test_name = "test_omega_bypass_001_os_blocks_direct_agent_access_and_broker_executes_authorized"
    assert test_name in command
    assert f"fn {test_name}()" in (ROOT / "tests/omega_mediation_campaign.rs").read_text()


def test_required_checks_have_one_unconditional_producer() -> None:
    required = {
        "quality",
        "rust (ubuntu-latest)",
        "rust (macos-latest)",
        "claims",
        "conformance",
        "test (3.11, 1)",
        "test (3.11, 2)",
        "test (3.12, 1)",
        "test (3.12, 2)",
        "SAST (bloqueado por la etapa de existencia)",
    }
    vault_paid_required = {
        "rust (macos-latest)",
        "claims",
        "test (3.11, 1)",
        "test (3.11, 2)",
        "test (3.12, 1)",
        "test (3.12, 2)",
    }
    producers: dict[str, list[str]] = {name: [] for name in required}
    for path in sorted((ROOT / ".github/workflows").glob("*.yml")):
        data = yaml.load(path.read_text(), Loader=yaml.BaseLoader)
        for job_id, job in data.get("jobs", {}).items():
            matrix = job.get("strategy", {}).get("matrix", {})
            axes = [values for key, values in matrix.items() if key not in {"include", "exclude"}]
            names = [job.get("name", job_id)]
            if axes and "name" not in job:
                names = [f"{job_id} ({', '.join(values)})" for values in product(*axes)]
            for name in required.intersection(names):
                if name in vault_paid_required:
                    assert job.get("if") == VAULT_PAID_RUNNER_GUARD, (
                        f"vault-guarded required check {name} must stay unconditional on public repo "
                        "and use exact VAULT_PAID_RUNNER_GUARD"
                    )
                else:
                    assert "if" not in job, f"required check {name} can skip its validation"
                producers[name].append(path.name)
    assert all(len(files) == 1 for files in producers.values()), producers


def test_mandatory_claims_executes_evidence_and_preserves_failures() -> None:
    verifier = workflow("verify_claims.yml")
    assert verifier["on"]["pull_request"]["branches"] == ["main"]
    assert verifier["on"]["push"]["branches"] == ["main"]
    job = verifier["jobs"]["claims"]
    assert job["if"] == VAULT_PAID_RUNNER_GUARD
    steps = job["steps"]
    evidence = next(step for step in steps if "verify_claims.py" in step.get("run", ""))
    assert "--list" not in evidence["run"]
    assert "||" not in evidence["run"] and "--locked" in evidence["run"]
    assert "continue-on-error" not in evidence
    upload = next(step for step in steps if "actions/upload-artifact@" in step.get("uses", ""))
    assert upload["if"] == "always()"


def test_macos_required_check_exercises_the_real_native_boundary() -> None:
    job = workflow("ci.yml")["jobs"]["rust-macos"]
    assert job["runs-on"] == "macos-15"
    assert job["if"] == VAULT_PAID_RUNNER_GUARD
    commands = "\n".join(step.get("run", "") for step in job["steps"])
    assert "cargo check --workspace --locked" in commands
    assert "cargo test --locked --test omega_mediation_campaign" in commands
    assert "test_omega_bypass_001_os_blocks_direct_agent_access_and_broker_executes_authorized" in commands
    assert "--exact" in commands


def test_paid_runners_and_vault_schedules_are_cost_guarded() -> None:
    paid_jobs = [
        ("ci.yml", "rust-macos"),
        ("verify_claims.yml", "claims"),
        ("python-tests.yml", "test"),
        ("macos-native.yml", "seatbelt"),
        ("confine.yml", "seatbelt"),
        ("windows-terminal.yml", "package"),
        ("windows-terminal.yml", "windows"),
    ]
    for filename, job_id in paid_jobs:
        job = workflow(filename)["jobs"][job_id]
        assert job.get("if") == VAULT_PAID_RUNNER_GUARD, (filename, job_id)

    conformance = workflow("conformance.yml")
    assert conformance["on"]["push"]["branches"] == ["main"]
    assert conformance["on"]["pull_request"]["branches"] == ["main"]
    assert conformance["jobs"]["conformance"]["timeout-minutes"] == "25"

    loom_wf = workflow("loom.yml")
    assert loom_wf["on"]["push"]["paths"]
    assert loom_wf["on"]["pull_request"]["paths"]

    # Release gates (production-deploy.yml / pypi-publish.yml) require an exact-commit
    # push run on main in the public repo even when Cargo.* did not change.
    dep_wf = workflow("dependency-audit.yml")
    assert "paths" not in dep_wf["on"]["push"]
    assert dep_wf["on"]["pull_request"]["paths"]
    assert dep_wf["jobs"]["audit"]["if"] == VAULT_PR_OR_PUBLIC_GUARD

    win_wf = workflow("windows-terminal.yml")
    assert win_wf["on"]["pull_request"]["branches"] == ["main"]
    assert win_wf["on"]["pull_request"]["paths"]

    scheduled_jobs = [
        ("dependency-audit.yml", "audit", VAULT_PR_OR_PUBLIC_GUARD),
        ("gitleaks.yml", "gitleaks", VAULT_SCHEDULE_GUARD),
        ("secret_audit.yml", "audit-secrets", VAULT_SCHEDULE_GUARD),
        ("stale.yml", "stale", VAULT_SCHEDULE_GUARD),
        ("fuzz.yml", "fuzzing", VAULT_SCHEDULE_GUARD),
        ("codeql.yml", "analyze", VAULT_SCHEDULE_GUARD),
    ]
    for filename, job_id, expected_guard in scheduled_jobs:
        raw = yaml.load((ROOT / ".github/workflows" / filename).read_text(), Loader=yaml.BaseLoader)
        entries = raw["on"]["schedule"]
        assert entries, filename
        for entry in entries:
            cron_fields = entry["cron"].split()
            assert len(cron_fields) == 5 and cron_fields[4] != "*", (filename, entry["cron"])
        assert raw["jobs"][job_id].get("if") == expected_guard, (filename, job_id)


def test_all_workflows_enforce_timeouts_main_branch_scope_and_root_least_privilege() -> None:
    non_public_jobs = [
        ("canary.yml", "canary"),
        ("deploy_docs.yml", "deploy-docs"),
        ("skill-convergence-audit.yml", "remote-links"),
        ("labeler.yml", "label"),
    ]
    for filename, job_id in non_public_jobs:
        job = workflow(filename)["jobs"][job_id]
        assert job.get("if") == VAULT_NON_PUBLIC_JOB_GUARD, (filename, job_id)

    for path in sorted((ROOT / ".github/workflows").glob("*.yml")):
        raw = yaml.load(path.read_text(), Loader=yaml.BaseLoader)
        if path.name != "docker-ghcr.yml":
            assert raw.get("permissions") == {"contents": "read"}, path.name

        on_cfg = raw.get("on", {})
        assert isinstance(on_cfg, dict), path.name
        for event in ("push", "pull_request"):
            if event in on_cfg:
                trigger = on_cfg[event]
                assert isinstance(trigger, dict) and trigger.get("branches") == ["main"], (path.name, event)

        for job_id, job in raw.get("jobs", {}).items():
            if "uses" in job:
                continue
            timeout = int(job.get("timeout-minutes", "0"))
            assert 1 <= timeout <= 90, (path.name, job_id, job.get("timeout-minutes"))
