"""CLI regressions for optional instruction signatures and workspace budgets."""

from pathlib import Path
import subprocess
import sys

import pytest

from scripts.guards.verify_active_topology import MCP_MANIFESTS, NESTED_SYMLINKS, ROOT_SYMLINKS

REPO = Path(__file__).absolute().parents[1]
TOPOLOGY = REPO / "scripts/guards/verify_active_topology.py"
BUDGET = REPO / "scripts/c5_quality_gates/audit_token_budget.py"


def run_gate(script: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(script), *args],
        capture_output=True,
        text=True,
        check=False,
        timeout=30,
    )


@pytest.fixture
def workspace(tmp_path: Path) -> Path:
    root = tmp_path / "workspace"
    root.mkdir()
    for name in (".babylon60rules", "AGENTS.md"):
        (root / name).write_text("# Instructions\n\nMOSKV-1. Preserve existing changes.\n", encoding="utf-8")
    for name in ROOT_SYMLINKS:
        (root / name).symlink_to(".babylon60rules")
    for name, target in NESTED_SYMLINKS.items():
        path = root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.symlink_to(target)
    for name in MCP_MANIFESTS:
        path = root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text('"babylon60-kernel": "scripts/c5_cli/launch_kernel_mcp.py"\n', encoding="utf-8")
    return root


def test_instruction_documents_do_not_require_response_signature(workspace: Path) -> None:
    result = run_gate(TOPOLOGY, "--repo-root", str(workspace), "--workspace-instructions", str(workspace / "AGENTS.md"))
    assert result.returncode == 0, result.stderr
    assert "signature" not in result.stdout.casefold()


def test_requested_response_signature_remains_strict(workspace: Path) -> None:
    result = run_gate(TOPOLOGY, "--repo-root", str(workspace), "--response", str(workspace / "AGENTS.md"))
    assert result.returncode == 1
    assert "signature" in result.stderr.casefold()


@pytest.mark.parametrize("content", ["", "# Instructions\nMOSKV-1\n```text\nunclosed\n"])
def test_invalid_instruction_document_is_rejected(workspace: Path, content: str) -> None:
    (workspace / "AGENTS.md").write_text(content, encoding="utf-8")
    result = run_gate(TOPOLOGY, "--repo-root", str(workspace))
    assert result.returncode == 1
    assert "AGENTS.md" in result.stderr


def test_wrong_ide_symlink_still_fails(workspace: Path) -> None:
    link = workspace / ".codexrules"
    link.unlink()
    link.symlink_to("AGENTS.md")
    result = run_gate(TOPOLOGY, "--repo-root", str(workspace))
    assert result.returncode == 1
    assert ".codexrules" in result.stderr


def test_staged_instructions_use_index_without_signature(workspace: Path) -> None:
    subprocess.run(["git", "init", "--quiet", str(workspace)], check=True)
    # The fixture must not inherit the operator's global excludes (e.g. .vscode).
    subprocess.run(["git", "-C", str(workspace), "add", "--force", "."], check=True)
    (workspace / "AGENTS.md").write_text("", encoding="utf-8")
    staged = run_gate(TOPOLOGY, "--repo-root", str(workspace), "--staged")
    assert staged.returncode == 0, staged.stderr
    assert run_gate(TOPOLOGY, "--repo-root", str(workspace)).returncode == 1
    subprocess.run(["git", "-C", str(workspace), "add", "AGENTS.md"], check=True)
    rejected = run_gate(TOPOLOGY, "--repo-root", str(workspace), "--staged")
    assert rejected.returncode == 1
    assert "index:AGENTS.md" in rejected.stderr


def test_workspace_budget_excludes_global_rules(workspace: Path, tmp_path: Path) -> None:
    global_config = tmp_path / "global"
    rules = global_config / "rules"
    rules.mkdir(parents=True)
    (rules / "missing-trigger.md").write_text("global rule without trigger\n", encoding="utf-8")
    args = ("--workspace", str(workspace), "--global-config", str(global_config), "--skip-ghost-listeners")
    local = run_gate(BUDGET, *args, "--workspace-only")
    assert local.returncode == 0, local.stderr
    assert "Global rules: NOT_CHECKED" in local.stdout
    assert "zero duplicate always_on rules" not in local.stdout
    assert "RUNNING=0" not in local.stdout
    combined = run_gate(BUDGET, *args)
    assert combined.returncode == 1
    assert "GLOBAL RULE MISSING TRIGGER" in combined.stderr


def test_workspace_budget_still_enforces_local_ceiling(workspace: Path) -> None:
    result = run_gate(
        BUDGET,
        "--workspace",
        str(workspace),
        "--workspace-only",
        "--skip-ghost-listeners",
        "--max-always-on-bytes",
        "1",
    )
    assert result.returncode == 1
    assert "BUDGET EXCEEDED" in result.stderr


def test_workspace_budget_still_checks_local_rule_trigger(workspace: Path) -> None:
    rules = workspace / ".agents/rules"
    rules.mkdir(parents=True)
    (rules / "bad.md").write_text("no trigger\n", encoding="utf-8")
    result = run_gate(BUDGET, "--workspace", str(workspace), "--workspace-only", "--skip-ghost-listeners")
    assert result.returncode == 1
    assert "WORKSPACE RULE MISSING TRIGGER" in result.stderr


def test_workspace_scope_does_not_silently_skip_telemetry(workspace: Path, tmp_path: Path) -> None:
    missing = tmp_path / "missing.db"
    result = run_gate(BUDGET, "--workspace", str(workspace), "--workspace-only", "--telemetry-db", str(missing))
    assert result.returncode == 2
    assert "NO_VERIFICADO" in result.stderr
    assert not missing.exists()
