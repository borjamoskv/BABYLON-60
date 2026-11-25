"""Isolated regressions for public projection manifest and sidecar reference contexts."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import subprocess
import sys

import pytest

from scripts.c5_quality_gates import audit_domain_bleed as adb
from scripts.c5_quality_gates.detect_ghost_nodes import _load_contexts
from scripts.c5_quality_gates.public_projection import MANIFEST_REL_PATH, SCHEMA_VERSION, load_omitted_prefixes

ROOT = Path(__file__).absolute().parents[1]


def _write_manifest(repo_root: Path, payload: object) -> Path:
    path = repo_root / MANIFEST_REL_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return path


def test_load_omitted_prefixes_absent_returns_empty(tmp_path: Path) -> None:
    assert load_omitted_prefixes(tmp_path) == frozenset()


def test_load_omitted_prefixes_valid_manifest(tmp_path: Path) -> None:
    _write_manifest(
        tmp_path,
        {
            "schema": SCHEMA_VERSION,
            "omitted_prefixes": [".agents/rules", "docs/security/evidence", "tools/skill_library"],
        },
    )
    assert load_omitted_prefixes(tmp_path) == frozenset(
        {".agents/rules", "docs/security/evidence", "tools/skill_library"}
    )


@pytest.mark.parametrize(
    "payload",
    [
        {"schema": "WRONG", "omitted_prefixes": []},
        {"schema": SCHEMA_VERSION, "omitted_prefixes": "not-a-list"},
        {"schema": SCHEMA_VERSION, "omitted_prefixes": ["src"]},
    ],
)
def test_load_omitted_prefixes_fails_closed_on_invalid_manifest(tmp_path: Path, payload: object) -> None:
    _write_manifest(tmp_path, payload)
    with pytest.raises(ValueError):
        load_omitted_prefixes(tmp_path)


def test_load_omitted_prefixes_fails_closed_when_omitted_prefix_exists_on_disk(tmp_path: Path) -> None:
    (tmp_path / ".agents/rules").mkdir(parents=True)
    _write_manifest(tmp_path, {"schema": SCHEMA_VERSION, "omitted_prefixes": [".agents/rules"]})
    with pytest.raises(ValueError, match="present on disk"):
        load_omitted_prefixes(tmp_path)


def test_detect_ghost_nodes_sidecar_enforces_prefix_confinement(tmp_path: Path) -> None:
    doc = tmp_path / "README.md"
    line = "Reference `ExternalSymbol` here."
    doc.write_text(line + "\n", encoding="utf-8")
    digest = hashlib.sha256(line.encode("utf-8")).hexdigest()
    sidecar = tmp_path / ".agents/rules/documented_reference_contexts.json"
    sidecar.parent.mkdir(parents=True)
    sidecar.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "references": [
                    {
                        "path": "README.md",
                        "symbol": "ExternalSymbol",
                        "kind": "external",
                        "reason": "escape test",
                        "evidence": "test",
                        "context_sha256": digest,
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="escapes sidecar prefix"):
        _load_contexts(tmp_path)


def test_audit_semantic_contracts_requires_rules_without_manifest_and_accepts_manifest(tmp_path: Path) -> None:
    script = ROOT / "scripts/c5_quality_gates/audit_semantic_contracts.py"
    (tmp_path / ".agents/skills").mkdir(parents=True)
    (tmp_path / "scripts/c5_quality_gates").mkdir(parents=True)
    for rel in (
        ".babylon60rules",
        "AGENTS.md",
        "docs/03_guides/agent_contracts.md",
        "docs/03_guides/guide_agent_workflow.md",
        "docs/03_guides/guide_portable_signature.md",
        "01_KISH_ENGINE/babylon60/presentation.md",
        "01_KISH_ENGINE/babylon60/session_profile.md",
        "01_KISH_ENGINE/babylon60/mcp_instructions.md",
    ):
        target = tmp_path / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text("# Doc\n", encoding="utf-8")

    # Without manifest (VAULT semantics): missing .agents/rules fails closed with exit 2.
    without = subprocess.run(
        [sys.executable, str(script), "--repo-root", str(tmp_path), "--workspace-only"],
        capture_output=True,
        text=True,
        check=False,
    )
    assert without.returncode == 2
    assert "NO_VERIFICADO: missing scope:" in without.stderr

    # With valid projection manifest omitting .agents/rules: succeeds and declares NOT_CHECKED.
    _write_manifest(tmp_path, {"schema": SCHEMA_VERSION, "omitted_prefixes": [".agents/rules"]})
    with_manifest = subprocess.run(
        [sys.executable, str(script), "--repo-root", str(tmp_path), "--workspace-only"],
        capture_output=True,
        text=True,
        check=False,
    )
    assert with_manifest.returncode == 0, with_manifest.stderr
    assert "NOT_CHECKED: .agents/rules omitted by public projection manifest" in with_manifest.stdout


def test_audit_domain_bleed_respects_public_projection_and_still_fails_closed_without_manifest(
    tmp_path: Path,
) -> None:
    for rel_json in ("docs/skills.json", ".agents/skills/skills.json"):
        p = tmp_path / rel_json
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text('{"entries": [], "adjacency": []}\n', encoding="utf-8")
    for rel_lock in ("skills-lock.json", "docs/skills-lock.json"):
        p = tmp_path / rel_lock
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text('{"skills": {}}\n', encoding="utf-8")

    # Without manifest (VAULT semantics): missing tools/skill_library files must fail closed.
    vault_violations = adb.check_extrinsic_domain_isolation(repo_root=tmp_path)
    assert len(vault_violations) == 2

    # With valid manifest omitting tools/skill_library: passes cleanly.
    _write_manifest(tmp_path, {"schema": SCHEMA_VERSION, "omitted_prefixes": ["tools/skill_library"]})
    assert adb.check_extrinsic_domain_isolation(repo_root=tmp_path) == []

    # With malformed manifest: fails closed.
    _write_manifest(tmp_path, {"schema": "BROKEN", "omitted_prefixes": ["tools/skill_library"]})
    broken_violations = adb.check_extrinsic_domain_isolation(repo_root=tmp_path)
    assert broken_violations
