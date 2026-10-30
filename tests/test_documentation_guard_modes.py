"""Regression cases for checkout-only documentary gates and their failure modes."""

from __future__ import annotations

import importlib.util
from pathlib import Path
import sys

import pytest

ROOT = Path(__file__).absolute().parents[1]


def load_script(name: str, relative: str):
    spec = importlib.util.spec_from_file_location(name, ROOT / relative)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture
def budget_workspace(tmp_path):
    (tmp_path / "AGENTS.md").write_text("Workspace instructions\n")
    rules = tmp_path / ".agents/rules"
    rules.mkdir(parents=True)
    (rules / "local.md").write_text("---\ntrigger: always_on\n---\nA local rule.\n")
    return tmp_path


def test_workspace_budget_never_reads_host_settings_or_telemetry(monkeypatch, budget_workspace, capsys):
    budget = load_script("budget_workspace_guard", "scripts/c5_quality_gates/audit_token_budget.py")

    def forbidden_host_access(*_args, **_kwargs):
        raise AssertionError("checkout-only validation attempted host access")

    with monkeypatch.context() as patch:
        patch.setattr(Path, "home", forbidden_host_access)
        patch.setattr(budget, "audit_ghost_listeners", forbidden_host_access)
        patch.setattr(sys, "argv", ["budget", "--workspace", str(budget_workspace), "--workspace-only"])
        assert budget.main() == 0
    output = capsys.readouterr().out
    assert "OMITIDOS" in output
    assert "configuración global excluida" in output
    assert "RUNNING=0" not in output


def test_skip_telemetry_does_not_open_database(monkeypatch, budget_workspace, capsys):
    budget = load_script("budget_skip_guard", "scripts/c5_quality_gates/audit_token_budget.py")

    def forbidden_telemetry(*_args, **_kwargs):
        raise AssertionError("telemetry must be omitted")

    monkeypatch.setattr(budget, "audit_ghost_listeners", forbidden_telemetry)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "budget",
            "--workspace",
            str(budget_workspace),
            "--global-config",
            str(budget_workspace),
            "--skip-ghost-listeners",
        ],
    )
    assert budget.main() == 0
    assert "OMITIDOS" in capsys.readouterr().out


@pytest.mark.parametrize("scope_flag", ["--workspace-only", "--skip-ghost-listeners"])
def test_telemetry_mutation_is_rejected_when_excluded(monkeypatch, scope_flag):
    budget = load_script("budget_conflict_guard", "scripts/c5_quality_gates/audit_token_budget.py")
    monkeypatch.setattr(sys, "argv", ["budget", scope_flag, "--fix-ghosts"])
    with pytest.raises(SystemExit) as error:
        budget.main()
    assert error.value.code == 2


def test_missing_workspace_instructions_fail_budget(monkeypatch, tmp_path, capsys):
    budget = load_script("budget_missing_guard", "scripts/c5_quality_gates/audit_token_budget.py")
    monkeypatch.setattr(sys, "argv", ["budget", "--workspace", str(tmp_path), "--workspace-only"])
    assert budget.main() == 1
    assert "WORKSPACE INSTRUCTIONS MISSING" in capsys.readouterr().err


@pytest.fixture
def mcp_manifests(tmp_path):
    topology = load_script("topology_document_guard", "scripts/guards/verify_active_topology.py")
    for name in topology.MCP_MANIFESTS:
        if name in topology.OPTIONAL_MCP_MANIFESTS:
            continue
        path = tmp_path / name
        path.parent.mkdir(parents=True, exist_ok=True)
        text = "babylon60-kernel" if name == ".claude/settings.json" else "scripts/c5_cli/launch_kernel_mcp.py"
        path.write_text(text)
    return topology, tmp_path


def test_missing_local_vscode_config_does_not_invalidate_clone(mcp_manifests):
    topology, root = mcp_manifests
    assert topology.validate_mcp_manifests(root) == []


def test_present_vscode_config_is_still_validated(mcp_manifests):
    topology, root = mcp_manifests
    config = root / ".vscode/mcp.json"
    config.parent.mkdir()
    config.write_text('{"command": "/Users/private/python"}')
    errors = topology.validate_mcp_manifests(root)
    assert any(".vscode/mcp.json" in error and "forbidden absolute" in error for error in errors)
    assert any("does not reference" in error for error in errors)


def test_optional_manifest_dangling_symlink_is_rejected(mcp_manifests):
    topology, root = mcp_manifests
    config = root / ".vscode/mcp.json"
    config.parent.mkdir()
    config.symlink_to("absent.json")
    assert any(".vscode/mcp.json" in error for error in topology.validate_mcp_manifests(root))


@pytest.mark.parametrize("name", [".mcp.json", ".gemini/settings.json", ".claude/settings.json", ".codex/config.toml"])
def test_required_manifests_are_not_made_optional(mcp_manifests, name):
    topology, root = mcp_manifests
    (root / name).unlink()
    assert any(name in error and "missing" in error for error in topology.validate_mcp_manifests(root))


@pytest.fixture
def semantic_docs(tmp_path):
    guard = load_script("semantic_document_guard", "scripts/c5_quality_gates/audit_semantic_contracts.py")
    names = (
        *guard.REQUIRED_DOCS,
        *guard.FORMAL_DOCS,
        "docs/03_guides/tutorial_hello_causal.md",
        "docs/03_guides/guide_repository_source_of_truth.md",
    )
    for name in names:
        path = tmp_path / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("# Scoped documentation\n")
    return guard, tmp_path


def test_missing_required_document_is_not_silently_accepted(semantic_docs):
    guard, root = semantic_docs
    (root / "docs/01_spec/spec_cryptographic_profile.md").unlink()
    assert any("required document unreadable" in error for error in guard.semantic_errors(root))


@pytest.mark.parametrize(
    ("path", "regression", "expected"),
    [
        ("docs/PROJECT.md", "axiom ax_canonical_invariant : ∀ (x : X), True", "empty canonical axiom"),
        ("docs/README.md", "es el único sustrato que hace físicamente imposible actuar", "universal human-oversight"),
        ("docs/05_compliance_eu_ai_act.md", "[OBSOLETO: BABYLON60_SIGNING_SEED]", "active interface"),
        ("docs/05_compliance_eu_ai_act.md", "cortex-compliance --format json", "unregistered"),
        ("docs/03_guides/tutorial_hello_causal.md", "./target/release/b60_kernel example.b60", "undeclared"),
    ],
)
def test_known_false_documentation_contracts_are_rejected(semantic_docs, path, regression, expected):
    guard, root = semantic_docs
    assert guard.semantic_errors(root) == []
    (root / path).write_text(regression)
    assert any(expected in error for error in guard.semantic_errors(root))
