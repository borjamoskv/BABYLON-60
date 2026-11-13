"""Keep general CI on Linux and preserve deliberate native macOS coverage."""

import importlib.util
from pathlib import Path
from typing import TypedDict, cast

import pytest
import yaml


ROOT = Path(__file__).absolute().parents[1]


Step = TypedDict("Step", {"id": str, "run": str, "uses": str, "if": str}, total=False)


class Strategy(TypedDict):
    matrix: dict[str, list[str]]


Job = TypedDict(
    "Job",
    {"runs-on": str, "strategy": Strategy, "steps": list[Step], "timeout-minutes": str,
     "if": str, "name": str, "needs": str},
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


def test_full_macos_certification_requires_a_release_or_explicit_opt_in() -> None:
    ci = workflow("ci.yml")
    assert ci["on"]["push"]["tags"] == ["v*"]
    opt_in = ci["on"]["workflow_dispatch"]["inputs"]["full_release_evidence"]
    assert opt_in["type"] == "boolean" and opt_in["default"] == "false"
    claims = ci["jobs"]["claims"]
    assert claims["if"] == (
        "startsWith(github.ref, 'refs/tags/v') || "
        "(github.event_name == 'workflow_dispatch' && inputs.full_release_evidence)"
    )
    assert claims["runs-on"] == "macos-15"
    assert claims["timeout-minutes"] == "45"
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
def test_native_workflow_reports_a_context_for_every_main_change(event: str, path: str, native_required: bool) -> None:
    native = workflow("macos-native.yml")
    trigger = native["on"][event]
    assert trigger["branches"] == ["main"]
    assert "paths" not in trigger and "paths-ignore" not in trigger
    spec = importlib.util.spec_from_file_location("native_ci_scope", ROOT / "scripts/guards/native_ci_scope.py")
    assert spec and spec.loader
    scope = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(scope)
    assert scope.native_path(path) is native_required


def test_native_job_checks_the_real_darwin_boundary_with_a_time_limit() -> None:
    native = workflow("macos-native.yml")
    job = native["jobs"]["seatbelt"]
    assert job["name"] == "rust (macos-latest)"
    assert job["needs"] == "native-inputs"
    assert "needs.native-inputs.result != 'success'" in job["if"]
    assert "needs.native-inputs.outputs.required != 'false'" in job["if"]
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
