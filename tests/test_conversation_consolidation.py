"""Isolated C5-REAL regressions and invariants for conversation consolidation."""

from __future__ import annotations

import importlib.util
import json
import os
import sqlite3
import subprocess
import sys
from contextlib import closing
from pathlib import Path
from typing import Any

import pytest

ROOT = Path(__file__).resolve().parents[1]
ENGINE_ROOT = ROOT / "01_KISH_ENGINE"
if str(ENGINE_ROOT) not in sys.path:
    sys.path.insert(0, str(ENGINE_ROOT))

from babylon60.memory.conversation_consolidation import (  # noqa: E402
    REPO_ROOT,
    _classify_domains,
    _configure_wal_connection,
    canonical_manifest_digest,
    consolidate_conversations,
    render_markdown_catalog,
)


@pytest.fixture(autouse=True)
def isolated_env(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    fake_home = tmp_path / "home"
    fake_home.mkdir()
    monkeypatch.setenv("HOME", str(fake_home))
    monkeypatch.setenv("BABYLON_HOME", str(fake_home / ".babylon60"))
    monkeypatch.delenv("CORTEX_CONVERSATION_VAULT_DB", raising=False)
    return fake_home


def _write_transcript(session_dir: Path, events: list[dict[str, Any]]) -> Path:
    log_path = session_dir / ".system_generated" / "logs" / "transcript.jsonl"
    log_path.parent.mkdir(parents=True, exist_ok=True)
    log_path.write_text("\n".join(json.dumps(e) for e in events) + "\n", encoding="utf-8")
    return log_path


def _load_script(rel_path: str, module_name: str) -> Any:
    spec = importlib.util.spec_from_file_location(module_name, ROOT / rel_path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


def test_sw100_c0478_and_c0563_passive_mode_never_fabricates_or_reads_home(isolated_env: Path) -> None:
    implicit_session = isolated_env / ".gemini" / "antigravity" / "brain" / "11111111-1111-4111-8111-111111111111"
    _write_transcript(
        implicit_session,
        [{"type": "USER_INPUT", "created_at": "2026-11-16T10:00:00Z", "content": "secret implicit session"}],
    )
    (implicit_session / "hidden_crystal.md").write_text("# Hidden\n", encoding="utf-8")

    proc = subprocess.run(
        [sys.executable, str(ROOT / "scripts/c5_cortex/consolidate_babylon_vault.py"), "--json"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        timeout=10,
        env={**os.environ, "HOME": str(isolated_env), "BABYLON_HOME": str(isolated_env / ".babylon60")},
    )
    assert proc.returncode == 0
    payload = json.loads(proc.stdout)
    assert payload["status"] == "NO_EXPLICIT_SOURCE"
    assert payload["metrics"]["sessions_scanned"] == 0
    assert payload["metrics"]["sessions_consolidated_now"] == 0
    assert not Path(payload["db_path"]).exists()

    fail_exec = subprocess.run(
        [sys.executable, str(ROOT / "scripts/c5_cortex/consolidate_babylon_vault.py"), "--execute", "--json"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        timeout=10,
        env={**os.environ, "HOME": str(isolated_env), "BABYLON_HOME": str(isolated_env / ".babylon60")},
    )
    assert fail_exec.returncode == 2
    assert json.loads(fail_exec.stdout)["status"] == "ERROR"


def test_rejects_database_inside_repository_root(tmp_path: Path) -> None:
    brain = tmp_path / "brain"
    brain.mkdir()
    inside_db = REPO_ROOT / "data" / "forbidden_test_vault.db"
    with pytest.raises(ValueError, match="outside repository root"):
        consolidate_conversations(brain_root=brain, db_path=inside_db, dry_run=True)
    assert not inside_db.exists()


def test_sanitization_drops_thinking_secrets_and_mechanical_artifacts(tmp_path: Path) -> None:
    brain = tmp_path / "brain"
    sess_id = "22222222-2222-4222-8222-222222222222"
    sess = brain / sess_id
    sess.mkdir(parents=True)
    synthetic_openai_key = "sk-" + "AbCdEf1234567890GhIjKlMnOp"
    _write_transcript(
        sess,
        [
            {
                "type": "USER_INPUT",
                "created_at": "2026-11-10T09:00:00Z",
                "content": (
                    f"<USER_REQUEST>\nAudita BFT con {synthetic_openai_key}\n</USER_REQUEST>\n"
                    "<ADDITIONAL_METADATA>NOISY_SYSTEM_WRAPPER</ADDITIONAL_METADATA>"
                ),
            },
            {
                "type": "PLANNER_RESPONSE",
                "created_at": "2026-11-10T09:01:00Z",
                "thinking": "INTERNAL_CHAIN_OF_THOUGHT_MUST_NEVER_LEAK",
                "tool_calls": [{"name": "read_file"}, {"name": "run_command"}],
            },
        ],
    )
    # Mechanical artifacts to ignore
    (sess / "walkthrough.md").write_text("# Mechanical walkthrough", encoding="utf-8")
    (sess / "implementation_plan.md").write_text("# Mechanical plan", encoding="utf-8")
    (sess / "task.md").write_text("# Mechanical task", encoding="utf-8")
    (sess / "learning_proposal_01.md").write_text("# Learning", encoding="utf-8")
    (sess / "implementation_plan.md.resolved.0").write_text("# Backup", encoding="utf-8")
    (sess / "scratch").mkdir()
    (sess / "scratch" / "ephemeral.md").write_text("# Scratch", encoding="utf-8")

    # High-exergy crystal artifacts to index
    crystal_a = sess / "bft_theorem_crystal.md"
    crystal_a.write_text("# BFT Theorem Crystal\nProof notes.\n", encoding="utf-8")
    nested = sess / "notes"
    nested.mkdir()
    crystal_b = nested / "larsa_matrix.md"
    crystal_b.write_text("# LARSA Matrix\n", encoding="utf-8")

    db_path = tmp_path / "out" / "vault.db"
    catalog_out = tmp_path / "out" / "CATALOG.md"
    report = consolidate_conversations(
        brain_root=brain,
        db_path=db_path,
        catalog_out=catalog_out,
        dry_run=True,
        logical_tick=120,
    )
    assert report.dry_run is True
    assert not db_path.exists()
    assert not catalog_out.exists()
    assert report.sessions_scanned == 1
    assert report.crystal_md_count == 2
    assert report.new_crystal_candidates == 2

    rec = report.sessions[0]
    assert rec.user_turn_count == 1
    assert rec.tool_call_count == 2
    assert "REDACTED_SECRET" in rec.topic_summary
    assert synthetic_openai_key not in rec.topic_summary
    assert "NOISY_SYSTEM_WRAPPER" not in rec.topic_summary
    assert "INTERNAL_CHAIN_OF_THOUGHT_MUST_NEVER_LEAK" not in json.dumps(report.to_dict())

    md_preview = render_markdown_catalog(report)
    assert "bft_theorem_crystal.md" in md_preview
    assert "notes/larsa_matrix.md" in md_preview
    assert "walkthrough.md" not in md_preview
    assert "INTERNAL_CHAIN_OF_THOUGHT_MUST_NEVER_LEAK" not in md_preview


def test_execute_wal_full_dedup_conflict_and_source_preservation(tmp_path: Path) -> None:
    brain = tmp_path / "brain"
    sess_id = "33333333-3333-4333-8333-333333333333"
    sess = brain / sess_id
    sess.mkdir(parents=True)
    log_path = _write_transcript(
        sess,
        [
            {
                "type": "USER_INPUT",
                "created_at": "2026-11-12T12:00:00Z",
                "content": "<USER_REQUEST>Kudurru Seqlock</USER_REQUEST>",
            }
        ],
    )
    crystal = sess / "kudurru_crystal.md"
    original_bytes = b"# Kudurru Seqlock\nInvariant v1.\n"
    crystal.write_bytes(original_bytes)
    original_log_bytes = log_path.read_bytes()

    db_path = tmp_path / "vault" / "conversation_vault.db"
    catalog_out = tmp_path / "vault" / "CATALOG.md"

    first = consolidate_conversations(
        brain_root=brain,
        db_path=db_path,
        catalog_out=catalog_out,
        dry_run=False,
        logical_tick=60,
    )
    assert first.db_written is True
    assert first.catalog_written is True
    assert first.new_crystal_candidates == 1
    recorded_b3 = first.sessions[0].artifacts[0].content_b3

    with closing(sqlite3.connect(db_path)) as conn:
        _configure_wal_connection(conn)
        assert conn.execute("PRAGMA journal_mode").fetchone()[0].lower() == "wal"
        assert conn.execute("PRAGMA synchronous").fetchone()[0] == 2  # FULL
        assert conn.execute("PRAGMA integrity_check").fetchone() == ("ok",)
        assert conn.execute("SELECT COUNT(*) FROM consolidated_sessions").fetchone()[0] == 1
        assert conn.execute("SELECT content_b3 FROM consolidated_artifacts").fetchone()[0] == recorded_b3

    # Second run against generated catalog_out as catalog_ref -> ALREADY_INDEXED
    second = consolidate_conversations(
        brain_root=brain,
        db_path=db_path,
        catalog_ref=catalog_out,
        dry_run=True,
        logical_tick=61,
    )
    assert second.already_indexed_crystals == 1
    assert second.new_crystal_candidates == 0
    assert second.conflicts_count == 0

    # Mutate crystal on disk -> CONFLICT_DIGEST detected and original DB digest preserved
    crystal.write_bytes(b"# Kudurru Seqlock\nInvariant v2 mutated.\n")
    third = consolidate_conversations(
        brain_root=brain,
        db_path=db_path,
        catalog_ref=catalog_out,
        dry_run=False,
        logical_tick=62,
    )
    assert third.conflicts_count >= 1
    assert third.sessions[0].artifacts[0].catalog_status == "CONFLICT_DIGEST"
    with closing(sqlite3.connect(db_path)) as conn:
        row = conn.execute("SELECT content_b3, catalog_status FROM consolidated_artifacts").fetchone()
        assert row == (recorded_b3, "CONFLICT_DIGEST")

    # Source log untouched
    assert log_path.read_bytes() == original_log_bytes
    assert crystal.read_bytes() == b"# Kudurru Seqlock\nInvariant v2 mutated.\n"


def test_symlink_rejection_and_logical_tick_determinism(tmp_path: Path) -> None:
    brain = tmp_path / "brain"
    sess = brain / "44444444-4444-4444-8444-444444444444"
    sess.mkdir(parents=True)
    outside = tmp_path / "outside_secret.md"
    outside.write_text("SECRET_OUTSIDE", encoding="utf-8")

    # Symlink dir and symlink artifact are skipped safely without reading targets
    outside_dir = tmp_path / "outside_dir"
    outside_dir.mkdir()
    (brain / "symlinked-session").symlink_to(outside_dir, target_is_directory=True)
    (sess / "leak.md").symlink_to(outside)

    skipped = consolidate_conversations(brain_root=brain, db_path=tmp_path / "vault.db", dry_run=True)
    assert skipped.sessions_scanned == 1
    assert skipped.artifacts_indexed == 0
    assert "SECRET_OUTSIDE" not in json.dumps(skipped.to_dict())

    # Symlinked catalog_ref or transcript.jsonl fails closed via O_NOFOLLOW
    sym_catalog = tmp_path / "sym_catalog.md"
    sym_catalog.symlink_to(outside)
    with pytest.raises(OSError):
        consolidate_conversations(
            brain_root=brain, db_path=tmp_path / "vault.db", catalog_ref=sym_catalog, dry_run=True
        )

    sym_transcript = sess / ".system_generated" / "logs" / "transcript.jsonl"
    sym_transcript.parent.mkdir(parents=True, exist_ok=True)
    sym_transcript.symlink_to(outside)
    with pytest.raises(OSError):
        consolidate_conversations(brain_root=brain, db_path=tmp_path / "vault.db", dry_run=True)

    d1 = canonical_manifest_digest(77, [("s1", "b3:" + "a" * 64), ("s2", "b3:" + "b" * 64)])
    d2 = canonical_manifest_digest(77, [("s2", "b3:" + "b" * 64), ("s1", "b3:" + "a" * 64)])
    d3 = canonical_manifest_digest(78, [("s1", "b3:" + "a" * 64), ("s2", "b3:" + "b" * 64)])
    assert d1 == d2
    assert d1 != d3


def test_cli_consolidate_conversations_and_sharur_openai_regex(tmp_path: Path, isolated_env: Path) -> None:
    brain = tmp_path / "brain"
    sess = brain / "55555555-5555-4555-8555-555555555555"
    sess.mkdir(parents=True)
    synthetic_openai_key = "sk-" + "AbCdEf1234567890GhIjKlMnOp"
    _write_transcript(
        sess,
        [{"type": "USER_INPUT", "created_at": "2026-11-15T08:00:00Z", "content": synthetic_openai_key}],
    )
    (sess / "summary.md").write_text("# Summary\n", encoding="utf-8")

    proc = subprocess.run(
        [
            sys.executable,
            "-m",
            "babylon60.cli.main_dispatcher",
            "consolidate-conversations",
            "--brain-root",
            str(brain),
            "--dry-run",
            "--json",
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
        timeout=10,
        env={
            **os.environ,
            "PYTHONPATH": str(ENGINE_ROOT),
            "HOME": str(isolated_env),
            "BABYLON_HOME": str(isolated_env / ".babylon60"),
        },
    )
    assert proc.returncode == 0
    data = json.loads(proc.stdout)
    assert data["status"] == "CONSOLIDATION_DRY_RUN"
    assert data["crystal_md_count"] == 1

    auditor = _load_script("scripts/c5_sharur/sharur_100_conversation_auditor.py", "test_sharur_auditor")
    corpus = auditor.BrainCorpusIndex(brain_dir=brain)
    corpus.index()
    assert corpus.secret_matches["openai"] == 1


def test_classify_domains_uses_crystal_filenames_when_prompt_is_terse(tmp_path: Path) -> None:
    assert _classify_domains(["audit"]) == ("general_ops",)
    assert _classify_domains(["que es esto"], artifact_names=["eu_ai_act_report.md"]) == ("legaltech_governance",)

    brain = tmp_path / "brain"
    sess_audio = brain / "66666666-6666-4666-8666-666666666666"
    sess_audio.mkdir(parents=True)
    _write_transcript(
        sess_audio,
        [
            {
                "type": "USER_INPUT",
                "created_at": "2026-11-16T08:00:00Z",
                "content": "<USER_REQUEST>auditoria</USER_REQUEST>",
            }
        ],
    )
    (sess_audio / "auditoria_espectral_caribou_herndon_vs_bounces.md").write_text("# Audio\n", encoding="utf-8")

    sess_no_log = brain / "77777777-7777-4777-8777-777777777777"
    sess_no_log.mkdir(parents=True)
    (sess_no_log / "nemesis_verifier_isolation_audit.md").write_text("# Nemesis\n", encoding="utf-8")
    (sess_no_log / "fl_aiact_iter2_vs_silicon_audit.md").write_text("# AI Act\n", encoding="utf-8")

    db_path = tmp_path / "vault" / "conversation_vault.db"
    catalog_out = tmp_path / "vault" / "README.md"
    report = consolidate_conversations(
        brain_root=brain,
        db_path=db_path,
        catalog_out=catalog_out,
        dry_run=False,
        logical_tick=70,
    )
    by_id = {s.session_id: s for s in report.sessions}
    assert by_id["66666666-6666-4666-8666-666666666666"].domains == ("audio_dsp_flstudio",)
    assert set(by_id["77777777-7777-4777-8777-777777777777"].domains) == {"babylon60", "legaltech_governance"}

    with closing(sqlite3.connect(db_path)) as conn:
        raw_audio = conn.execute(
            "SELECT domains_json FROM consolidated_sessions WHERE session_id = ?",
            ("66666666-6666-4666-8666-666666666666",),
        ).fetchone()[0]
    assert json.loads(raw_audio) == ["audio_dsp_flstudio"]
