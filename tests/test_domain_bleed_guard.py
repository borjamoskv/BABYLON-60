"""Confinement tests for scripts/c5_quality_gates/audit_domain_bleed.py."""

from __future__ import annotations

from pathlib import Path

from scripts.c5_quality_gates import audit_domain_bleed as adb


def test_longmemeval_allowlist_permits_only_documented_paths(tmp_path: Path) -> None:
    lme = tmp_path / "experiments" / "longmemeval"
    allowed = [
        lme / "cache" / "embeddings.db",
        lme / "runs" / "c2-s-session-full" / "ledgers" / "00997f100a0d67dc17cf.db",
        lme / "runs" / "qa-v2-c12-n50" / "qa_audit_ledger.db",
    ]
    for path in allowed:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(b"")

    assert adb.check_database_confinement(repo_root=tmp_path) == []

    forbidden = [
        tmp_path / "experiments" / "oncology" / "leak.db",
        lme / "rogue.db",
        lme / "runs" / "rogue.db",
        lme / "runs" / "c2-s-session-full" / "ledgers" / "nested" / "extra.db",
        lme / "runs" / "c2-s-session-full" / "ledgers" / "bad.sqlite",
    ]
    for path in forbidden:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(b"")

    outside = tmp_path / "outside.db"
    outside.write_bytes(b"")
    symlink_target = lme / "runs" / "symlinked-run" / "ledgers"
    symlink_target.mkdir(parents=True)
    (symlink_target / "linked.db").symlink_to(outside)

    violations = {
        Path(p).relative_to(tmp_path).as_posix() for p, _ in adb.check_database_confinement(repo_root=tmp_path)
    }
    expected_bad = {path.relative_to(tmp_path).as_posix() for path in forbidden} | {
        "outside.db",
        "experiments/longmemeval/runs/symlinked-run/ledgers/linked.db",
    }
    assert violations == expected_bad

    # Parent directory symlink traversal must fail closed as well.
    escaped_cache = tmp_path / "escaped_cache"
    escaped_cache.mkdir()
    (escaped_cache / "embeddings.db").write_bytes(b"")
    (lme / "cache" / "embeddings.db").unlink()
    (lme / "cache").rmdir()
    (lme / "cache").symlink_to(escaped_cache)
    assert not adb._is_allowed_longmemeval_db(lme / "cache" / "embeddings.db", repo_root=tmp_path)


def test_extrinsic_domain_isolation_rejects_phase2a_paths(tmp_path: Path) -> None:
    for rel_json in ("docs/skills.json", "tools/skill_library/global/skills.json", ".agents/skills/skills.json"):
        p = tmp_path / rel_json
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text('{"entries": [], "adjacency": []}\n', encoding="utf-8")
    for rel_lock in ("skills-lock.json", "docs/skills-lock.json"):
        p = tmp_path / rel_lock
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text('{"skills": {}}\n', encoding="utf-8")
    cat = tmp_path / "tools" / "skill_library" / "catalog.json"
    cat.parent.mkdir(parents=True, exist_ok=True)
    cat.write_text('{"scopes": {}, "capabilities": {}}\n', encoding="utf-8")

    assert adb.check_extrinsic_domain_isolation(repo_root=tmp_path) == []

    phase2a_targets = [
        "docs/02_ontology/axiom_oncologia_300_primitivas.md",
        "examples/remotion/README.md",
        "01_KISH_ENGINE/babylon60/transducers/catvton_spatial_concat.py",
        "01_KISH_ENGINE/babylon60/services/dataset_harvester.py",
        "scripts/c5_setup/setup_nacho_cortex.sh",
        "scripts/c5_setup/setup_nacho_cortex.ps1",
    ]
    for rel in phase2a_targets:
        target = tmp_path / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text("# forbidden\n", encoding="utf-8")

    violations = {
        Path(p).relative_to(tmp_path).as_posix() for p, _ in adb.check_extrinsic_domain_isolation(repo_root=tmp_path)
    }
    assert violations == {
        "docs/02_ontology/axiom_oncologia_300_primitivas.md",
        "examples/remotion",
        "01_KISH_ENGINE/babylon60/transducers/catvton_spatial_concat.py",
        "01_KISH_ENGINE/babylon60/services/dataset_harvester.py",
        "scripts/c5_setup/setup_nacho_cortex.sh",
        "scripts/c5_setup/setup_nacho_cortex.ps1",
    }


def test_extrinsic_domain_isolation_rejects_phase2b_and_2c_paths(tmp_path: Path) -> None:
    for rel_json in ("docs/skills.json", "tools/skill_library/global/skills.json", ".agents/skills/skills.json"):
        p = tmp_path / rel_json
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text('{"entries": [], "adjacency": []}\n', encoding="utf-8")
    for rel_lock in ("skills-lock.json", "docs/skills-lock.json"):
        p = tmp_path / rel_lock
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text('{"skills": {}}\n', encoding="utf-8")
    cat = tmp_path / "tools" / "skill_library" / "catalog.json"
    cat.write_text('{"scopes": {}, "capabilities": {}}\n', encoding="utf-8")

    phase2b = {
        "experiments/oncology": "experiments/oncology/README.md",
        "docs/06_theory/axiom_oncology_protocol.md": None,
        "docs/03_guides/guide_bio_silico_transduction.md": None,
        "01_KISH_ENGINE/babylon60/services/voice_cloner.py": None,
        "01_KISH_ENGINE/babylon60/utils/record_voice.scpt": None,
        "scripts/c5_assets/gen_voice_assets.py": None,
        "scripts/c5_demos/batch_gen_borja_voices.py": None,
        "scripts/c5_demos/c5_model_voice_announcer.py": None,
        "scripts/c5_demos/c5_topology_ctl.py": None,
        "scripts/c5_demos/c5_swarm_1000_audiovisual_compiler.py": None,
        "02_EDIN_SWARMS/social_agent": "02_EDIN_SWARMS/social_agent/creatives/reel_builder.py",
        "tools/babylon_social": None,
        "tools/ui_youtube_audit": "tools/ui_youtube_audit/template.html",
        "02_EDIN_SWARMS/agents_archi/topologies/distribution_design.py": None,
        "02_EDIN_SWARMS/agents_archi/topologies/social_media_team.py": None,
        "tools/social_calendar_generator.py": None,
        "tools/tamkarum_swarm_orchestrator.py": None,
        "tools/tamkarum_batch_signer.py": None,
        "tools/tamkarum_top.py": None,
        "tools/tamkarum_attestation_engine.py": None,
        "scripts/outreach_cockpit.py": None,
        "scripts/partition_campaigns.py": None,
        "scripts/zero_touch_fundraising_poc.py": None,
    }
    for rel, nested in phase2b.items():
        target = tmp_path / (nested or rel)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text("# forbidden\n", encoding="utf-8")

    violations = {
        Path(p).relative_to(tmp_path).as_posix() for p, _ in adb.check_extrinsic_domain_isolation(repo_root=tmp_path)
    }
    assert violations == set(phase2b)


def test_extrinsic_surfaces_are_absent_from_this_checkout() -> None:
    root = Path(adb.__file__).absolute().parents[2]
    present = [rel for rel in adb.EXTRINSIC_FORBIDDEN_PATHS if (root / rel).exists()]
    assert present == []
