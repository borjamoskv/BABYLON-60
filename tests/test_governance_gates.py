"""Governance regressions use isolated files and Git indexes; no host hooks or effects."""

from pathlib import Path
import json
import subprocess
import sys

import pytest

from scripts.c5_quality_gates import audit_semantic_contracts, audit_token_budget
from scripts.c5_quality_gates.governance_documents import (
    GOVERNANCE_DOCUMENTS,
    MAX_ROOT_INSTRUCTION_BYTES,
    markdown_anchors,
    validate_local_links,
)
from scripts.guards.verify_active_topology import (
    MCP_MANIFESTS,
    NESTED_SYMLINKS,
    ROOT_SYMLINKS,
    validate_index,
    validate_instruction_file,
    validate_instruction_text,
    validate_text,
    validate_worktree,
)

ROOT = Path(__file__).absolute().parents[1]
IDE_LINKS = ROOT_SYMLINKS + (".github/copilot-instructions.md",)


def write(root: Path, name: str, text: str) -> Path:
    path = root / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


@pytest.fixture
def governance(tmp_path: Path) -> Path:
    root = tmp_path / "project with spaces"
    for name in GOVERNANCE_DOCUMENTS:
        write(root, name, "# Instrucciones\n\nResultado verificable.\n")
    for name in (".agents/rules", ".agents/skills", "scripts/c5_quality_gates"):
        (root / name).mkdir(parents=True, exist_ok=True)
    return root


def semantic_cli(root: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(ROOT / "scripts/c5_quality_gates/audit_semantic_contracts.py"),
         "--repo-root", str(root), "--workspace-only"],
        cwd=root.parent, capture_output=True, text=True, check=False,
    )


def budget_cli(root: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(ROOT / "scripts/c5_quality_gates/audit_token_budget.py"),
         "--workspace", str(root), "--skip-ghost-listeners", *args],
        cwd=root.parent, capture_output=True, text=True, check=False,
    )


@pytest.mark.parametrize("name", GOVERNANCE_DOCUMENTS)
def test_semantic_gate_covers_every_core_document(governance: Path, name: str) -> None:
    write(governance, name, "Toda mutación causal exige atestación biométrica.\n")
    result = semantic_cli(governance)
    assert result.returncode == 1
    assert name in result.stderr and "SEM-001" in result.stderr
    assert "PASS" not in result.stdout


@pytest.mark.parametrize("name", GOVERNANCE_DOCUMENTS)
def test_missing_required_document_is_not_silently_skipped(governance: Path, name: str) -> None:
    (governance / name).unlink()
    result = semantic_cli(governance)
    assert result.returncode == 1
    assert name in result.stderr and "IO-READ-ERROR" in result.stderr


def test_invalid_utf8_document_fails(governance: Path) -> None:
    (governance / ".babylon60rules").write_bytes(b"\xff")
    result = semantic_cli(governance)
    assert result.returncode == 1
    assert "IO-READ-ERROR" in result.stderr


def test_unreadable_document_fails_without_chmod_assumptions(governance: Path, monkeypatch, capsys) -> None:
    original = Path.read_text

    def denied(path, *args, **kwargs):
        if path == governance / "AGENTS.md":
            raise PermissionError("test read denied")
        return original(path, *args, **kwargs)

    monkeypatch.setattr(Path, "read_text", denied)
    monkeypatch.setattr(sys, "argv", ["audit", "--repo-root", str(governance), "--workspace-only"])
    assert audit_semantic_contracts.main() == 1
    assert "test read denied" in capsys.readouterr().err


def test_semantic_cli_checks_core_and_rule_links(governance: Path) -> None:
    assert semantic_cli(governance).returncode == 0
    write(governance, ".agents/rules/example.md", "[Broken](../../missing.md)\n")
    write(governance, "AGENTS.md", "[Broken](.babylon60rules#absent)\n")
    result = semantic_cli(governance)
    assert result.returncode == 1
    assert "missing local target" in result.stderr
    assert "missing local anchor" in result.stderr


def declare_public_projection(root: Path) -> None:
    write(root, audit_semantic_contracts.PUBLIC_PROFILE_MARKER,
          json.dumps(audit_semantic_contracts.PUBLIC_PROFILE))
    (root / ".agents/rules").rmdir()


def test_declared_public_projection_passes_without_private_rules(governance: Path) -> None:
    declare_public_projection(governance)
    result = semantic_cli(governance)
    assert result.returncode == 0, result.stderr
    assert "Profile: public" in result.stdout
    assert "NOT_CHECKED: .agents/rules omitted" in result.stdout
    full = subprocess.run(
        [sys.executable, str(ROOT / "scripts/c5_quality_gates/audit_semantic_contracts.py"),
         "--repo-root", str(governance), "--workspace-only", "--profile", "full"],
        capture_output=True, text=True, check=False,
    )
    assert full.returncode == 2
    assert "missing scope" in full.stderr and ".agents/rules" in full.stderr


def test_undeclared_missing_rules_remain_an_error(governance: Path) -> None:
    (governance / ".agents/rules").rmdir()
    result = semantic_cli(governance)
    assert result.returncode == 2 and "missing scope" in result.stderr
    with pytest.raises(ValueError, match="requires projection declaration"):
        audit_semantic_contracts.select_profile(governance, "public")


@pytest.mark.parametrize("name", [".agents/skills", "scripts/c5_quality_gates", *GOVERNANCE_DOCUMENTS])
def test_public_projection_keeps_other_scopes_required(governance: Path, name: str) -> None:
    declare_public_projection(governance)
    path = governance / name
    path.rmdir() if path.is_dir() else path.unlink()
    result = semantic_cli(governance)
    assert result.returncode in (1, 2)
    assert name in result.stderr
    assert "PASS" not in result.stdout


@pytest.mark.parametrize("content", ["{", "{}", '{"profile":"public","omitted_scopes":[".agents/skills"]}'])
def test_invalid_public_projection_declaration_fails(governance: Path, content: str) -> None:
    write(governance, audit_semantic_contracts.PUBLIC_PROFILE_MARKER, content)
    result = semantic_cli(governance)
    assert result.returncode == 2 and "NO_VERIFICADO" in result.stderr


def test_present_public_rules_are_still_inspected(governance: Path) -> None:
    declare_public_projection(governance)
    write(governance, ".agents/rules/new.md", "Toda mutación causal exige atestación biométrica.\n")
    result = semantic_cli(governance)
    assert result.returncode == 1 and "SEM-001" in result.stderr


def test_budget_counts_canonical_file_once_despite_seven_aliases(governance: Path) -> None:
    write(governance, ".babylon60rules", "m" * 2000)
    write(governance, "AGENTS.md", "a" * 1000)
    for name in IDE_LINKS:
        path = governance / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.symlink_to("../.babylon60rules" if "/" in name else ".babylon60rules")
    result = budget_cli(governance, "--workspace-only", "--max-always-on-bytes", "3000")
    assert result.returncode == 0, result.stderr
    assert "INSPECTED ALWAYS_ON: 3,000 B / 3,000 B" in result.stdout
    assert "actual client context not measured" in result.stdout
    failed = budget_cli(governance, "--workspace-only", "--max-always-on-bytes", "2999")
    assert failed.returncode == 1
    assert "ALWAYS_ON BUDGET EXCEEDED" in failed.stderr


def test_root_budget_boundary(governance: Path) -> None:
    write(governance, "AGENTS.md", "a")
    write(governance, ".babylon60rules", "m" * (MAX_ROOT_INSTRUCTION_BYTES - 1))
    assert budget_cli(governance, "--workspace-only").returncode == 0
    write(governance, "AGENTS.md", "aa")
    failed = budget_cli(governance, "--workspace-only")
    assert failed.returncode == 1 and "ROOT INSTRUCTIONS BUDGET EXCEEDED" in failed.stderr


def test_workspace_budget_omits_global_configuration(governance: Path, tmp_path: Path) -> None:
    global_config = tmp_path / "global"
    write(global_config, "rules/global.md", '---\ntrigger: always_on\n---\n' + "x" * 40_000)
    local = budget_cli(governance, "--workspace-only", "--global-config", str(global_config))
    assert local.returncode == 0, local.stderr
    assert "Global rules: NOT_CHECKED" in local.stdout
    assert "Ghost Listeners (conversation_summaries.db): NOT_CHECKED" in local.stdout
    full = budget_cli(governance, "--global-config", str(global_config))
    assert full.returncode == 1 and "ALWAYS_ON BUDGET EXCEEDED" in full.stderr


@pytest.mark.parametrize("name", (".babylon60rules", "AGENTS.md"))
def test_missing_budget_source_is_unverified(governance: Path, name: str) -> None:
    (governance / name).unlink()
    result = budget_cli(governance, "--workspace-only")
    assert result.returncode == 2 and "NO_VERIFICADO" in result.stderr
    assert "PASS" not in result.stdout


def test_unreadable_budget_source_is_unverified(governance: Path, monkeypatch, capsys) -> None:
    original = Path.read_bytes

    def denied(path):
        if path == governance / ".babylon60rules":
            raise PermissionError("test read denied")
        return original(path)

    monkeypatch.setattr(Path, "read_bytes", denied)
    monkeypatch.setattr(sys, "argv", ["audit", "--workspace", str(governance), "--workspace-only", "--skip-ghost-listeners"])
    assert audit_token_budget.main() == 2
    assert "NO_VERIFICADO" in capsys.readouterr().err


def stage(root: Path) -> None:
    subprocess.run(["git", "add", "-A"], cwd=root, check=True, capture_output=True)


@pytest.fixture
def topology(governance: Path) -> Path:
    subprocess.run(["git", "init", "-q"], cwd=governance, check=True, capture_output=True)
    for name in MCP_MANIFESTS:
        write(governance, name, '{"babylon60-kernel": "scripts/c5_cli/launch_kernel_mcp.py"}\n')
    for name, target in {**dict.fromkeys(ROOT_SYMLINKS, ".babylon60rules"), **NESTED_SYMLINKS}.items():
        path = governance / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.symlink_to(target)
    stage(governance)
    return governance


def test_documents_need_no_signature_but_response_signature_stays_strict(topology: Path) -> None:
    assert validate_instruction_text("# MOSKV-1\n\nResultado y evidencia.\n") == []
    assert validate_instruction_file(topology / ".babylon60rules") == []
    assert validate_worktree(topology) == []
    assert validate_index(topology) == []
    assert validate_text("Respuesta sin firma", response=True)
    assert validate_instruction_text("")
    assert validate_instruction_text("```text\nexample\n")


@pytest.mark.parametrize("name", IDE_LINKS)
@pytest.mark.parametrize("kind", ("missing", "copy", "indirect", "dangling"))
def test_every_required_alias_is_strict_in_worktree_and_index(topology: Path, name: str, kind: str) -> None:
    path = topology / name
    path.unlink()
    if kind == "copy":
        path.write_text((topology / ".babylon60rules").read_text())
    elif kind in ("indirect", "dangling"):
        if kind == "indirect":
            (path.parent / "proxy").symlink_to("../.babylon60rules" if "/" in name else ".babylon60rules")
        path.symlink_to("proxy")
    assert any(name in error for error in validate_worktree(topology))
    assert validate_index(topology) == []  # Unstaged defect must not change the index verdict.
    stage(topology)
    assert any(name in error for error in validate_index(topology))


def test_unstaged_repair_does_not_hide_invalid_index(topology: Path) -> None:
    path = topology / "CLAUDE.md"
    path.unlink()
    stage(topology)
    path.symlink_to(".babylon60rules")
    assert validate_worktree(topology) == []
    assert any("CLAUDE.md" in error for error in validate_index(topology))


def test_source_missing_with_correct_symlink_targets_fails(topology: Path) -> None:
    (topology / ".babylon60rules").unlink()
    assert validate_worktree(topology)
    stage(topology)
    assert validate_index(topology)


def test_instruction_symlink_cannot_replace_canonical_source(topology: Path) -> None:
    path = topology / ".babylon60rules"
    path.unlink()
    path.symlink_to("AGENTS.md")
    assert validate_worktree(topology)
    stage(topology)
    assert validate_index(topology)


def test_staged_manifest_validation_never_uses_worktree_repair(topology: Path) -> None:
    name = ".mcp.json"
    original = (topology / name).read_text()
    write(topology, name, "wrong registration")
    assert validate_index(topology) == []
    stage(topology)
    write(topology, name, original)
    assert validate_worktree(topology) == []
    assert any(name in error for error in validate_index(topology))


def test_optional_vscode_manifest_is_checked_when_present(topology: Path) -> None:
    assert validate_worktree(topology) == []
    write(topology, ".vscode/mcp.json", "wrong registration")
    assert any(".vscode/mcp.json" in error for error in validate_worktree(topology))
    subprocess.run(["git", "add", "-f", ".vscode/mcp.json"], cwd=topology, check=True, capture_output=True)
    assert any(".vscode/mcp.json" in error for error in validate_index(topology))


def test_shell_guard_delegates_staged_checks_from_any_directory(topology: Path) -> None:
    (topology / ".github/copilot-instructions.md").unlink()
    stage(topology)
    result = subprocess.run(
        ["bash", str(ROOT / "scripts/guards/c5_ide_symlink_guard.sh"), "--repo-root", str(topology), "--staged"],
        cwd=topology.parent, capture_output=True, text=True, check=False,
    )
    assert result.returncode == 1 and "copilot-instructions.md" in result.stderr


def test_local_link_formats_anchors_and_fenced_examples(tmp_path: Path) -> None:
    write(tmp_path, "a b.md", "# Condición\n\n## Repetido\n\n## Repetido\n\n<a id=\"manual\"></a>\n")
    source = write(tmp_path, "source.md", '''# Inicio
[Unicode](a%20b.md#condici%C3%B3n)
[Title](<a b.md#repetido-1> "description")
[Ref][ok]
[ok]: <a b.md#manual>
[Self](#inicio)
[Web](https://invalid.example/not-fetched)
`[Example](missing.md)`
```md
[Example](also-missing.md)
```
''')
    assert validate_local_links([source]) == []
    assert "heading-with-code" in markdown_anchors("# Heading with `code`\n")


@pytest.mark.parametrize("content,expected", [
    ("[Missing](absent.md)", "missing local target"),
    ("[Missing](target.md#absent)", "missing local anchor"),
    ("[Missing][undefined]", "undefined link reference"),
    ("[Defined][ref]\n[ref]: target.md#absent", "missing local anchor"),
])
def test_broken_local_links_fail(tmp_path: Path, content: str, expected: str) -> None:
    write(tmp_path, "target.md", "# Present\n")
    source = write(tmp_path, "source.md", content)
    assert any(expected in error for error in validate_local_links([source]))
