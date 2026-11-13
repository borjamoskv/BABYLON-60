"""Isolated regressions for ledger and publication gates; never publish."""

import json
import os
from pathlib import Path
import re
import subprocess
import sys

import pytest
import yaml

ROOT = Path(__file__).absolute().parents[1]


def test_privileged_production_actions_are_pinned() -> None:
    workflow = yaml.safe_load((ROOT / ".github/workflows/production-deploy.yml").read_text())
    for job in workflow["jobs"].values():
        for step in job.get("steps", []):
            if "uses" in step:
                assert re.fullmatch(r"[^@]+@[0-9a-f]{40}", step["uses"]), step["uses"]


def git(repo: Path, *args: str) -> str:
    return subprocess.run(["git", "-C", str(repo), *args], check=True, capture_output=True, text=True).stdout.strip()


def commit(repo: Path, body: str) -> str:
    git(
        repo,
        "-c",
        "user.name=Test",
        "-c",
        "user.email=test@example.invalid",
        "-c",
        "commit.gpgsign=false",
        "commit",
        "--allow-empty",
        "-m",
        body,
    )
    return git(repo, "rev-parse", "HEAD")


def ledger(repo: Path, base: str, head: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(ROOT / "scripts/guards/verify_commit_trailers.py"), "--base", base, "--head", head],
        cwd=repo,
        capture_output=True,
        text=True,
        timeout=10,
    )


@pytest.mark.parametrize(
    "trailers",
    [
        "",
        "Ledger-Head: " + "a" * 64,
        "Ledger-Head: bad\nLedger-Seq: 1",
        "Ledger-Head: " + "a" * 64 + "\nLedger-Seq: -1",
        "Ledger-Head: " + "a" * 64 + "\nLedger-Seq: 1\nLedger-Seq: 2",
    ],
)
def test_ledger_rejects_invalid_new_commit(tmp_path: Path, trailers: str) -> None:
    git(tmp_path, "init")
    base = commit(tmp_path, "Historical baseline without trailers")
    head = commit(tmp_path, "Introduced change\n\n" + trailers)
    assert ledger(tmp_path, base, head).returncode != 0


def test_ledger_checks_whole_range_and_excludes_history(tmp_path: Path) -> None:
    git(tmp_path, "init")
    historical = commit(tmp_path, "Historical baseline without trailers")
    invalid = commit(tmp_path, "Invalid new commit")
    valid = "Change\n\nLedger-Head: " + "a" * 64 + "\nLedger-Seq: 1"
    head = invalid
    for _ in range(6):
        head = commit(tmp_path, valid)
    assert ledger(tmp_path, historical, head).returncode != 0
    assert ledger(tmp_path, invalid, head).returncode == 0
    assert ledger(tmp_path, "0" * 40, head).returncode != 0


@pytest.mark.parametrize(
    "mutation",
    [
        {},
        {"headSha": "b" * 40},
        {"status": "in_progress"},
        {"conclusion": "failure"},
        {"event": "pull_request"},
        {"headBranch": "feature"},
    ],
)
def test_publish_gate_checks_identity_and_success(mutation: dict[str, str]) -> None:
    run = {"headSha": "a" * 40, "status": "completed", "conclusion": "success", "event": "push", "headBranch": "main"}
    run.update(mutation)
    result = subprocess.run(
        [sys.executable, str(ROOT / "scripts/guards/verify_publish_run.py")],
        input=json.dumps([run]),
        env={**os.environ, "GITHUB_SHA": "a" * 40},
        capture_output=True,
        text=True,
        timeout=10,
    )
    assert (result.returncode == 0) == (not mutation)


def test_publish_gate_rejects_missing_evidence() -> None:
    result = subprocess.run(
        [sys.executable, str(ROOT / "scripts/guards/verify_publish_run.py")],
        input="[]",
        env={**os.environ, "GITHUB_SHA": "a" * 40},
        capture_output=True,
        text=True,
        timeout=10,
    )
    assert result.returncode != 0


def test_all_ghcr_entries_use_protected_canonical_job() -> None:
    workflows = ROOT / ".github/workflows"
    wrapper = yaml.safe_load((workflows / "docker-ghcr.yml").read_text())
    production = yaml.safe_load((workflows / "production-deploy.yml").read_text())
    assert wrapper["jobs"] == {"publish": {"uses": "./.github/workflows/production-deploy.yml"}}
    jobs = production["jobs"]
    assert jobs["prepare-image"]["needs"] == "verify-release"
    assert jobs["verify-regulated-release"]["needs"] == "prepare-image"
    assert jobs["publish-image"]["needs"] == "verify-regulated-release"
    for name in ("prepare-image", "verify-regulated-release"):
        assert jobs[name]["permissions"].get("packages", "none") != "write"
    job = jobs["publish-image"]
    assert job["environment"]["name"] == "Production"
    assert job["steps"][0]["with"]["ref"] == "${{ github.sha }}"
    gate = jobs["verify-release"]["steps"][-1]
    assert gate["shell"] == "bash"
    assert '--commit "$GITHUB_SHA"' in gate["run"]
    recheck = next(step for step in job["steps"] if step.get("name") == "Recheck main and exact-commit CI gates")
    push = next(step for step in job["steps"] if step.get("id") == "publish")
    login = next(step for step in job["steps"] if step.get("name") == "Login after verification")
    assert job["steps"].index(recheck) < job["steps"].index(login) < job["steps"].index(push)
    assert "verify_regulated_release.py" in push["run"]
    assert push["run"].index("verify_regulated_release.py") < push["run"].index("skopeo copy")
    assert "--preserve-digests" in push["run"]
    assert not any("docker/build-push-action@" in step.get("uses", "") for step in job["steps"])
    for workflow in (
        "ci.yml",
        "python-tests.yml",
        "gitleaks.yml",
        "dependency-audit.yml",
        "verify_ledger.yml",
        "verify_claims.yml",
    ):
        assert workflow in gate["run"] and workflow in recheck["run"]


def test_pypi_requires_validated_exact_commit_before_build() -> None:
    workflow = yaml.safe_load((ROOT / ".github/workflows/pypi-publish.yml").read_text())
    assert workflow["jobs"]["build"]["needs"] == "verify-release"
    assert workflow["jobs"]["build"]["steps"][0]["with"]["ref"] == "${{ github.sha }}"
    production = yaml.safe_load((ROOT / ".github/workflows/production-deploy.yml").read_text())
    assert (
        workflow["jobs"]["verify-release"]["steps"][-1]["run"]
        == production["jobs"]["verify-release"]["steps"][-1]["run"]
    )


@pytest.mark.parametrize("workflow_name", ["production-deploy.yml", "pypi-publish.yml"])
@pytest.mark.parametrize("scenario", ["success", "feature", "stale", "failed", "missing", "api-error", "runs-error"])
def test_release_preflight_rejects_unvalidated_refs(
    tmp_path: Path,
    workflow_name: str,
    scenario: str,
) -> None:
    """Execute the real workflow shell against an isolated, deterministic gh fixture."""
    workflow = yaml.safe_load((ROOT / ".github/workflows" / workflow_name).read_text())
    step = workflow["jobs"]["verify-release"]["steps"][-1]
    assert step["shell"] == "bash"
    tools = tmp_path / "bin"
    tools.mkdir()
    fixture = tools / "gh"
    fixture.write_text(
        f"#!{sys.executable}\n"
        "import json, os, sys\n"
        "scenario = os.environ['RELEASE_TEST_SCENARIO']\n"
        "if sys.argv[1] == 'api':\n"
        "    if scenario == 'api-error': raise SystemExit(23)\n"
        "    print('b' * 40 if scenario == 'stale' else os.environ['GITHUB_SHA'])\n"
        "else:\n"
        "    if scenario == 'runs-error': raise SystemExit(23)\n"
        "    run = {'headSha': os.environ['GITHUB_SHA'], 'status': 'completed',\n"
        "           'conclusion': 'failure' if scenario == 'failed' else 'success',\n"
        "           'event': 'push', 'headBranch': 'main'}\n"
        "    print(json.dumps([] if scenario == 'missing' else [run]))\n",
        encoding="utf-8",
    )
    fixture.chmod(0o700)
    result = subprocess.run(
        ["bash", "--noprofile", "--norc", "-eo", "pipefail", "-c", step["run"]],
        cwd=ROOT,
        env={
            **os.environ,
            "PATH": str(tools) + os.pathsep + os.environ["PATH"],
            "GITHUB_REF": "refs/heads/feature" if scenario == "feature" else "refs/heads/main",
            "GITHUB_REPOSITORY": "fixture/fixture",
            "GITHUB_SHA": "a" * 40,
            "RELEASE_TEST_SCENARIO": scenario,
        },
        capture_output=True,
        text=True,
        timeout=10,
    )
    assert (result.returncode == 0) == (scenario == "success"), result.stdout + result.stderr
