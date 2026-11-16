"""Independent confined checks for S6 reports, proof gating, Lean and demo."""

from __future__ import annotations

import asyncio
import importlib.util
import json
import math
import os
import shutil
import sqlite3
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

ROOT = Path(__file__).absolute().parents[5]


def load(relative: str):
    path = ROOT / relative
    name = "review_s6_" + path.stem
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture(autouse=True)
def private_home(tmp_path, monkeypatch):
    monkeypatch.setenv("HOME", str(tmp_path / "home"))
    (tmp_path / "home").mkdir()


def corpus():
    return SimpleNamespace(
        artifacts=[],
        artifacts_by_ext={},
        scripts_in_brain=[],
        target_files_mutated={},
        large_files=[],
        conv_dirs=[],
        secret_matches={},
        touch_id_invocations=0,
        learned_preferences=[],
        learned_workspace_facts=[],
        transcripts=[],
        total_lines=0,
        user_messages=[],
        planner_messages=[],
        tool_calls_counter={},
        total_brain_bytes=0,
        entropy_samples=[],
    )


def test_c0328_repeated_reporter_matrix_and_real_thresholds(tmp_path):
    mod = load("scripts/c5_sharur/sharur_100_conversation_reporters.py")
    c = corpus()
    for i in range(30):
        d = tmp_path / f"session-{i}"
        d.mkdir()
        c.conv_dirs.append(d)
    c.scripts_in_brain = [str(i) for i in range(6)]
    c.large_files = [{"size": 1500 * 1024 * 1024}]
    c.touch_id_invocations = 10**9

    async def run():
        return await asyncio.gather(
            *[(mod.run_cohort_4 if i < 80 else mod.run_cohort_5)(i, c, asyncio.Semaphore(4)) for i in range(60, 100)]
        )

    for _ in range(3):
        rs = asyncio.run(run())
        byid = {r.agent_id: r for r in rs}
        assert all(byid[i].verdict == "WARN" for i in [62, 71, 75])
        assert byid[87].verdict == "OBSERVED"
        assert byid[87].metrics["hardware_verified"] is False
        assert byid[99].verdict == "NOT_EXECUTED"
        sitrep = mod.compile_swarm_sitrep(c, rs, 0.0)
        assert sitrep.certification == "NOT_ATTESTED"
        assert sitrep.exergy_score is None
        assert sitrep.total_agents == 40
        assert (
            sum(
                getattr(sitrep, k)
                for k in [
                    "passed_agents",
                    "warned_agents",
                    "failed_agents",
                    "observed_agents",
                    "not_executed_agents",
                    "info_agents",
                    "unknown_agents",
                ]
            )
            == 40
        )
        assert all(r.entropy_bits is None for r in rs)


def test_c0328_unrecognized_reported_verdict_is_counted_unknown():
    mod = load("scripts/c5_sharur/sharur_100_conversation_reporters.py")
    r = mod.AgentResult(400, 1, "fixture", "fixture", "CERTIFIED", 0.0, None, "untrusted fixture")
    s = mod.compile_swarm_sitrep(corpus(), [r], 0.0)
    assert s.unknown_agents == 1 and s.passed_agents == 0
    assert s.certification == "NOT_ATTESTED"


def test_c0343_predicates_change_with_actual_fixture_files(tmp_path):
    m = load("scripts/c5_sharur/sharur_100_full_spectrum_auditor.py")
    m.REPO_ROOT = tmp_path
    m.SKILLS_DIR_GLOBAL = tmp_path / "skills"
    m.SKILLS_JSON_REPO = tmp_path / "a.json"
    m.SKILLS_JSON_GLOBAL = tmp_path / "b.json"
    sem = asyncio.Semaphore(1)
    def run(fn, i):
        return asyncio.run(fn(i, sem))
    assert run(m.audit_cohort_ring0, 10).verdict == "WARN"
    (tmp_path / "Cargo.toml").write_text("fixture")
    assert run(m.audit_cohort_ring0, 10).verdict == "PASS"
    for data, expected in [('{"entries":["a"]}', "WARN"), ("[]", "FAIL"), ('{"entries":["b"]}', "PASS")]:
        m.SKILLS_JSON_REPO.write_text('{"entries":["b"]}')
        m.SKILLS_JSON_GLOBAL.write_text(data)
        assert run(m.audit_cohort_topology, 67).verdict == expected
    (tmp_path / ".git").mkdir()
    assert run(m.audit_cohort_devsecops, 81).verdict == "PASS"
    (tmp_path / ".git/a.lock").write_text("owned fixture")
    assert run(m.audit_cohort_devsecops, 81).verdict == "WARN"
    (tmp_path / "transcript.vtt").write_text("fixture")
    assert run(m.audit_cohort_devsecops, 85).verdict == "WARN"
    for text in ["", "雪" * 100, "雪a🔥" * 100]:
        r = asyncio.run(m.audit_cohort_linguistics(41, sem, text=text))
        assert r.verdict == "OBSERVED"
        assert math.isclose(r.entropy_bits, 0.0 if len(set(text)) <= 1 else math.log2(3), abs_tol=1e-9)


def test_c0354_repeated_simulation_never_attests(tmp_path):
    m = load("scripts/c5_sharur/sharur_100_swarm_execution.py")
    m.REPO_ROOT = tmp_path
    for _ in range(3):
        report, _ = asyncio.run(m.execute_sharur_100())
        assert report["simulation"] is True and report["certification"] == "NOT_ATTESTED"
        assert report["critical_fixes_attested"] == []
        assert report["passed_agents"] == 0 and report["not_executed_agents"] == 100
        assert {r["status"] for r in report["results"]} == {"NOT_EXECUTED"}
        assert all(r["exergy_score"] is None and r["simulation"] for r in report["results"])
        assert json.loads((tmp_path / "scripts/c5_legion/legion_100_audit_sitrep.json").read_text()) == report


def test_c0378_real_db_withdraws_stale_proofs_and_consumer_sees_no_rule(tmp_path):
    m = load("scripts/c5_destiladora/proof_emitter_lean4.py")
    db = tmp_path / "invariants.db"
    with sqlite3.connect(db) as conn:
        conn.executescript((ROOT / "scripts/c5_destiladora/destiladora_schema.sql").read_text())
        for i, (status, proof) in enumerate([("PROVED", "PROVED"), ("COMPILED", "PROVED"), ("EXTRACTED", "UNTESTED")]):
            conn.execute(
                "INSERT INTO cortex_invariant_clusters (cluster_id,ast_signature,sample_count,z3_precondition,status,lean4_proof_status,crystallized_fn_name) VALUES (?,?,3,?,?,?,?)",
                (str(i), "ab" * 32, "False", status, proof, f"fixture_rule_{i}"),
            )
    r = m.Lean4ProofEmitter(db, tmp_path / "proofs").prove_extracted_clusters()
    assert r["certified"] == 0 and r["total_evaluated"] == 3
    assert all(x["status"] == "NOT_VERIFIED" for x in r["results"])
    with sqlite3.connect(db) as conn:
        assert (
            conn.execute("SELECT COUNT(*) FROM cortex_invariant_clusters WHERE lean4_proof_status='PROVED'").fetchone()[
                0
            ]
            == 0
        )
        assert (
            conn.execute(
                "SELECT COUNT(*) FROM cortex_invariant_clusters WHERE (status='PROVED' OR status='COMPILED') AND lean4_proof_status='PROVED'"
            ).fetchone()[0]
            == 0
        )
    codegen = load("scripts/c5_destiladora/codegen_rust_b60.py")
    out = tmp_path / "rules.rs"
    assert codegen.generate_rust_fastpath(db, out) == 0
    text = out.read_text()
    assert "return FastPathVerdict::Hit" not in text
    assert not (tmp_path / "proofs").exists()


def test_c0360_lean_real_catalog_and_contradiction_rejected(tmp_path):
    m = load("scripts/babylon60/gen_oncology_primitives.py")
    lean = os.environ.get("B60_REVIEW_LEAN_BINARY") or shutil.which("lean")
    if lean is None:
        pytest.skip("Lean unavailable; no formal claim")
    records = [
        dict(id=f"TEST-{i}", name="fixture", category="test", layer="meta", role="", mechanism="", reference="")
        for i in range(300)
    ]
    out = tmp_path / "Ontology.lean"
    m.export_lean4(records, out)
    base = out.read_text()
    good = subprocess.run([lean, str(out)], cwd=tmp_path, capture_output=True, text=True, timeout=90)
    assert good.returncode == 0, good.stdout + good.stderr
    assert "axiom anergy_purge_limit" not in base
    # The actual bound theorem must not justify the contradictory 301-element case.
    bad = tmp_path / "Exploit.lean"
    bad.write_text(
        base
        + '\nopen Babylon60.Oncology\nexample : False := by\n  let p : OncologyPrimitive := ⟨"", "", "", .«meta», "", "", ""⟩\n  exact anergy_purge_limit (List.replicate 301 p) (by decide)\n'
    )
    probe = subprocess.run([lean, str(bad)], cwd=tmp_path, capture_output=True, text=True, timeout=90)
    assert probe.returncode != 0
    for count in [0, 299, 301]:
        with pytest.raises(ValueError):
            m.export_lean4(records[:count] if count <= 300 else records + [records[0]], tmp_path / f"bad-{count}.lean")


def test_c0385_import_and_real_cli_leave_fixture_operator_db_untouched(tmp_path):
    project = tmp_path / "project"
    scripts = project / "scripts/c5_destiladora"
    scripts.mkdir(parents=True)
    for name in [
        "test_destiladora_e2e.py",
        "goal_trace_ingestor.py",
        "invariant_extractor_z3.py",
        "proof_emitter_lean4.py",
        "destiladora_schema.sql",
    ]:
        shutil.copyfile(ROOT / "scripts/c5_destiladora" / name, scripts / name)
    db = project / "data/cortex_memory.db"
    db.parent.mkdir()
    db.write_bytes(b"OPERATOR_FIXTURE_UNTOUCHED")
    home = tmp_path / "operator-home"
    home.mkdir()
    marker = home / "sentinel"
    marker.write_bytes(b"KEEP")
    env = dict(os.environ)
    env["HOME"] = str(home)
    env["CORTEX_MEMORY_DB"] = str(db)
    result = subprocess.run(
        [sys.executable, str(scripts / "test_destiladora_e2e.py"), "--isolated-demo"],
        cwd=project,
        env=env,
        capture_output=True,
        text=True,
        timeout=90,
    )
    assert result.returncode == 2, result.stdout + result.stderr
    assert db.read_bytes() == b"OPERATOR_FIXTURE_UNTOUCHED" and marker.read_bytes() == b"KEEP"
    assert '"synthetic": true' in result.stdout and '"rust_generation": "NOT_EXECUTED"' in result.stdout
    report = json.JSONDecoder().raw_decode(result.stdout[result.stdout.index('{\n  "status"') :])[0]
    assert report["temporary_files_removed"] is True
    assert not Path(report["temporary_root"]).exists()
    assert Path(report["database"]).parent == Path(report["temporary_root"])
    assert Path(report["home"]).parent == Path(report["temporary_root"])


def test_c0385_import_has_no_pipeline_or_filesystem_effects(tmp_path, monkeypatch):
    project = tmp_path / "project"
    script = project / "scripts/c5_destiladora/test_destiladora_e2e.py"
    script.parent.mkdir(parents=True)
    shutil.copyfile(ROOT / "scripts/c5_destiladora/test_destiladora_e2e.py", script)
    data = project / "data"
    data.mkdir()
    sentinel = data / "cortex_memory.db"
    sentinel.write_bytes(b"KEEP-AT-IMPORT")
    before_files = sorted(str(p.relative_to(project)) for p in project.rglob("*") if p.is_file())
    before_path = list(sys.path)
    before_cwd = Path.cwd()

    def denied(*args, **kwargs):
        raise AssertionError("Import attempted a child process")

    monkeypatch.setattr(subprocess, "run", denied)
    spec = importlib.util.spec_from_file_location("review_s6_demo_import", script)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    assert sentinel.read_bytes() == b"KEEP-AT-IMPORT"
    assert Path.cwd() == before_cwd and sys.path == before_path
    after_files = sorted(
        str(p.relative_to(project)) for p in project.rglob("*") if p.is_file() and "__pycache__" not in p.parts
    )
    assert before_files == after_files
