"""Skill generators keep the kernel root, declared aliases and out-of-reach entries stable."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest
import yaml

from scripts.c5_skills_ontology import c5_skill_router as router
from scripts.c5_skills_ontology import sync_skills_registry as registry

ROOT = Path(__file__).absolute().parents[1]
KERNEL_DESCRIPTION = "Manifiesto de invariantes transversales (árbol de roles y gobernanza declarativa)."
STAMP = "2026-10-18T18:29:58Z"


def write_skill(root: Path, name: str, description: str, **frontmatter: Any) -> None:
    meta: dict[str, Any] = {
        "name": name,
        "description": description,
        "role": "auditor",
        "directives": {"worktree_mode": "audit-only"},
    }
    meta.update(frontmatter)
    folder = root / name
    folder.mkdir(parents=True, exist_ok=True)
    body = "\n".join(f"Paso {i}." for i in range(25))
    (folder / "SKILL.md").write_text(
        "---\n" + yaml.safe_dump(meta, allow_unicode=True, sort_keys=False) + "---\n" + body + "\n",
        encoding="utf-8",
    )


def by_name(catalog: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {entry["name"]: entry for entry in catalog["entries"]}


def run_registry() -> dict[str, Any]:
    assert registry.sync_skills_json() is True
    return json.loads(registry.DOCS_SKILLS_JSON.read_text(encoding="utf-8"))


@pytest.fixture
def projection(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Workspace skills and a catalog without the global skills root, as in the public tree."""
    workspace = tmp_path / "workspace"
    absent = tmp_path / "absent-global"
    monkeypatch.setattr(registry, "SKILLS_DIR", absent)
    monkeypatch.setattr(registry, "GLOBAL_SKILLS_JSON", absent / "skills.json")
    monkeypatch.setattr(registry, "CONFIG_SKILLS_MD", absent / "SKILLS.md")
    monkeypatch.setattr(registry, "WS_SKILLS_DIR", workspace)
    monkeypatch.setattr(registry, "DOCS_SKILLS_JSON", tmp_path / "skills.json")
    write_skill(
        workspace,
        "cortex-kernel",
        KERNEL_DESCRIPTION,
        canonical_alias="kernel-root",
        role="arquitecto",
        directives={"worktree_mode": "spec-only"},
    )
    write_skill(workspace, "wait-what", "Freno epistémico en prosa.", canonical_alias="epistemic-simplifier")
    generated = {
        "version": 2,
        "skills": {},
        "capabilities": {"wait-what": {"aliases": ["Explícalo simple", "/wait-what", "itera", "no"]}},
        "policy": {"generic": ["itera"]},
    }
    (workspace / registry.GENERATED_CATALOG_NAME).write_text(json.dumps(generated), encoding="utf-8")
    catalog = {
        "version": "26.400",
        "updated_at": STAMP,
        "entries": [
            {
                "name": "cortex-kernel",
                "tier": 23000,
                "category": "Kernel",
                "scope": "kernel",
                "role": "arquitecto",
                "canonical_alias": "kernel-root",
                "description": registry.KERNEL_FALLBACK_DESCRIPTION,
                "triggers": list(registry.KERNEL_TRIGGERS),
            },
            {
                "name": "thermo-audit",
                "tier": 21500,
                "category": "Kernel",
                "display_name": "Nombre leído de su SKILL.md",
                "canonical_alias": "kernel-thermo-audit",
                "scope": "global",
                "role": "auditor",
                "description": "Skill global fuera de este checkout.",
                "triggers": ["kernel-thermo-audit", "thermo-audit"],
                "exergy_audit": {
                    "e1_silicon": 7000,
                    "e2_kolmogorov": 7000,
                    "e3_causal": 7000,
                    "ring0_bonus": 500,
                    "compiler_verified": True,
                },
            },
            {
                "name": "wait-what",
                "tier": 19600,
                "category": "Nucleus",
                "scope": "workspace",
                "triggers": ["wait-what"],
            },
            {"name": "retired-workspace-skill", "tier": 18000, "category": "Operations", "scope": "workspace"},
        ],
        "adjacency": [],
    }
    registry.DOCS_SKILLS_JSON.write_text(json.dumps(catalog, ensure_ascii=False), encoding="utf-8")
    return tmp_path


def test_physical_kernel_root_keeps_scope_and_catalog_triggers(projection: Path) -> None:
    kernel = by_name(run_registry())["cortex-kernel"]
    assert kernel["scope"] == "kernel"
    assert kernel["triggers"] == registry.KERNEL_TRIGGERS
    assert kernel["description"] == KERNEL_DESCRIPTION
    assert (kernel["role"], kernel["canonical_alias"]) == ("arquitecto", "kernel-root")


def test_missing_global_root_keeps_global_entries_and_purges_only_workspace(projection: Path) -> None:
    before = by_name(json.loads(registry.DOCS_SKILLS_JSON.read_text(encoding="utf-8")))
    after = by_name(run_registry())
    assert after["thermo-audit"] == before["thermo-audit"]
    assert "retired-workspace-skill" not in after


def test_declared_aliases_drive_triggers_and_trigger_determinism(projection: Path) -> None:
    wait_what = by_name(run_registry())["wait-what"]
    assert wait_what["triggers"] == ["/wait-what", "epistemic-simplifier", "explícalo simple", "wait-what"]
    assert wait_what["exergy_audit"]["e2_kolmogorov"] == 7000


def test_description_phrase_is_the_fallback_without_declared_aliases(projection: Path) -> None:
    (registry.WS_SKILLS_DIR / registry.GENERATED_CATALOG_NAME).unlink()
    write_skill(
        registry.WS_SKILLS_DIR,
        "wait-what",
        'Freno epistémico. Dispara con "freno epistémico".',
        canonical_alias="epistemic-simplifier",
    )
    wait_what = by_name(run_registry())["wait-what"]
    assert wait_what["triggers"] == ["epistemic-simplifier", "freno epistémico", "wait-what"]
    assert wait_what["exergy_audit"]["e2_kolmogorov"] == 7000


def test_second_run_is_byte_identical(projection: Path) -> None:
    assert run_registry()["updated_at"] != STAMP
    first = registry.DOCS_SKILLS_JSON.read_bytes()
    run_registry()
    assert registry.DOCS_SKILLS_JSON.read_bytes() == first


def test_checked_in_catalog_is_the_generator_fixed_point(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setattr(registry, "SKILLS_DIR", tmp_path / "absent-global")
    assert registry.sync_skills_json(json_output=True) is True
    assert capsys.readouterr().out == (ROOT / "docs/skills.json").read_text(encoding="utf-8")


def test_router_merges_catalog_triggers_and_pins_the_kernel_scope() -> None:
    skills: dict[str, dict[str, Any]] = {
        "wait-what": {"name": "wait-what", "scope": "workspace", "triggers": ["epistemic-simplifier"]},
        "cortex-kernel": {"name": "cortex-kernel", "scope": "workspace", "triggers": ["kernel-root"]},
    }
    entries = {
        "wait-what": {"triggers": ["Explícalo simple", "wait-what", "no"]},
        "cortex-kernel": {"scope": "kernel", "triggers": registry.KERNEL_TRIGGERS},
    }
    router.apply_catalog_triggers(skills, entries)
    assert skills["wait-what"]["triggers"] == ["epistemic-simplifier", "explícalo simple", "wait-what"]
    assert skills["cortex-kernel"] == {
        "name": "cortex-kernel",
        "scope": "kernel",
        "triggers": sorted(registry.KERNEL_TRIGGERS),
    }


def test_router_routes_aliases_that_left_the_descriptions(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(router, "GLOBAL_SKILLS_DIR", tmp_path / "absent-global")
    skills = router.collect_all_skills()
    assert skills["cortex-kernel"]["scope"] == "kernel"
    for query, expected in [
        ("explícalo simple", "wait-what"),
        ("interrogatorio socrático", "grill-me-v2"),
        ("auditoría termodinámica código", "thermo-audit"),
    ]:
        assert router.score_skills_for_query(query, skills)[0][0] == expected
