"""Isolated regressions for SW100-C0378/C0360/C0385."""

from __future__ import annotations

import importlib.util
import json
import os
import shutil
import sqlite3
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from types import ModuleType, SimpleNamespace

import pytest

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts/c5_destiladora"


def load_script(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def make_db(path: Path, *, precondition: str = "False", status: str = "EXTRACTED") -> None:
    with sqlite3.connect(path) as conn:
        conn.executescript((SCRIPTS / "destiladora_schema.sql").read_text())
        conn.execute(
            "INSERT INTO cortex_invariant_clusters "
            "(cluster_id, ast_signature, sample_count, z3_precondition, status, "
            "lean4_proof_status, crystallized_fn_name) VALUES (?, ?, 3, ?, ?, ?, ?)",
            ("abcdef1234567890", "ab" * 32, precondition, status,
             "PROVED" if status == "PROVED" else "UNTESTED", "resolve_fixture"),
        )


@pytest.mark.parametrize("precondition", ["False", "", "EXIT_CODE==123 && UNKNOWN_INPUT"])
def test_c0378_compiler_success_cannot_certify_unrepresented_preconditions(tmp_path, monkeypatch, precondition):
    emitter = load_script(SCRIPTS / "proof_emitter_lean4.py", "lot12_proof_emitter")
    db = tmp_path / "fixture.db"
    make_db(db, precondition=precondition)
    # The original promotes on this compiler result regardless of the precondition.
    monkeypatch.setattr(shutil, "which", lambda _name: "/fixture/lean")
    monkeypatch.setattr(subprocess, "run", lambda *_a, **_k: SimpleNamespace(returncode=0, stdout="", stderr=""))
    report = emitter.Lean4ProofEmitter(db_path=db, lean_dir=tmp_path / "lean").prove_extracted_clusters()
    with sqlite3.connect(db) as conn:
        status, proof_status = conn.execute(
            "SELECT status, lean4_proof_status FROM cortex_invariant_clusters"
        ).fetchone()
    assert status != "PROVED"
    assert proof_status != "PROVED"
    assert report["results"][0]["status"] != "PROVED"


def primitives():
    return [{"id": f"ONC-{i:03d}", "name": "fixture", "category": "test", "layer": "meta",
             "role": "", "mechanism": "", "reference": ""} for i in range(1, 301)]


def lean_run(path: Path):
    lean = os.environ.get("BABYLON60_TEST_LEAN_BIN") or shutil.which("lean")
    if not lean:
        pytest.skip("Lean compiler is not installed")
    return subprocess.run([lean, str(path)], cwd=path.parent, capture_output=True, text=True, timeout=60)


def test_c0360_generated_catalog_cannot_prove_false_with_301_elements(tmp_path):
    generator = load_script(ROOT / "scripts/babylon60/gen_oncology_primitives.py", "lot12_oncology")
    output = tmp_path / "Oncology.lean"
    generator.export_lean4(primitives(), output)
    # Close an optional namespace so the exploit is evaluated in both versions.
    source = output.read_text()
    assert "axiom anergy_purge_limit" not in source
    # A toolchain/configuration failure must never count as a logical rejection.
    base = lean_run(output)
    assert base.returncode == 0, base.stdout + base.stderr
    if source.rstrip().endswith("end Babylon60.Oncology"):
        source += "\nopen Babylon60.Oncology\n"
    source += '''
theorem swarm100_false : False := by
  let p : OncologyPrimitive := ⟨"", "", "", .«meta», "", "", ""⟩
  exact anergy_purge_limit (List.replicate 301 p) (by decide)
'''
    if "end Babylon60.Oncology" not in source:
        source += "\nend Babylon60.Oncology\n"
    output.write_text(source)
    proc = lean_run(output)
    assert proc.returncode != 0, "Generated axiom derives False for a freely constructible list"


def test_c0385_demo_does_not_modify_existing_workspace_database(tmp_path, monkeypatch):
    project = tmp_path / "fixture-project"
    script = project / "scripts/c5_destiladora/test_destiladora_e2e.py"
    script.parent.mkdir(parents=True)
    shutil.copyfile(SCRIPTS / "test_destiladora_e2e.py", script)
    operator_db = project / "data/cortex_memory.db"
    operator_db.parent.mkdir()
    make_db(operator_db, status="PROVED")
    before = operator_db.read_bytes()
    ingestor = ModuleType("goal_trace_ingestor")
    ingestor.ingest_goal_trace = lambda **_kwargs: "synthetic-fixture-trace"  # type: ignore[attr-defined]
    ingestor.ensure_schema = lambda _conn: None  # type: ignore[attr-defined]
    extractor = ModuleType("invariant_extractor_z3")
    extractor.Z3InvariantExtractor = lambda **_kwargs: SimpleNamespace(  # type: ignore[attr-defined]
        inspect_and_extract=lambda **_kw: {"processed": 0, "clusters": []})
    emitter = ModuleType("proof_emitter_lean4")
    emitter.Lean4ProofEmitter = lambda **_kwargs: SimpleNamespace(  # type: ignore[attr-defined]
        prove_extracted_clusters=lambda: {"total_evaluated": 0, "results": []})
    codegen = ModuleType("codegen_rust_b60")
    codegen.generate_rust_fastpath = lambda **_kwargs: 0  # type: ignore[attr-defined]
    for module in [ingestor, extractor, emitter, codegen]:
        monkeypatch.setitem(sys.modules, module.__name__, module)
    monkeypatch.setattr(subprocess, "run", lambda *_a, **_k: SimpleNamespace(returncode=1, stdout="", stderr=""))
    monkeypatch.setenv("HOME", str(tmp_path / "external-home"))
    old_path = list(sys.path)
    try:
        demo = load_script(script, "lot12_e2e_fixture")
        demo.run_end_to_end_test()
    finally:
        sys.path[:] = old_path
    assert operator_db.read_bytes() == before
    with sqlite3.connect(operator_db) as conn:
        assert conn.execute("SELECT status FROM cortex_invariant_clusters").fetchone()[0] == "PROVED"


def test_c0378_unverified_rows_are_excluded_by_unmodified_rust_consumer(tmp_path):
    emitter = load_script(SCRIPTS / "proof_emitter_lean4.py", "lot12_consumer_emitter")
    consumer = load_script(SCRIPTS / "codegen_rust_b60.py", "lot12_consumer")
    db = tmp_path / "consumer.db"
    make_db(db)
    report = emitter.Lean4ProofEmitter(db_path=db, lean_dir=tmp_path / "proof").prove_extracted_clusters()
    assert report["certified"] == 0
    output = tmp_path / "crystallized.rs"
    assert consumer.generate_rust_fastpath(db_path=db, output_file=output) == 0
    assert "EXPECTED_SIG_" not in output.read_text()


@pytest.mark.parametrize("state", ["PROVED", "COMPILED", "DEPLOYED"])
def test_c0378_stale_proof_eligibility_is_withdrawn(tmp_path, state):
    emitter = load_script(SCRIPTS / "proof_emitter_lean4.py", "lot12_stale_emitter")
    db = tmp_path / "stale.db"
    make_db(db, status="PROVED")
    with sqlite3.connect(db) as conn:
        conn.execute("UPDATE cortex_invariant_clusters SET status = ?", (state,))
    report = emitter.Lean4ProofEmitter(db_path=db).prove_extracted_clusters()
    assert report["results"][0]["status"] == "NOT_VERIFIED"
    assert report["results"][0]["model_check_status"] == "NOT_EXECUTED"
    with sqlite3.connect(db) as conn:
        assert conn.execute("SELECT status, lean4_proof_status, lean4_proof_path FROM cortex_invariant_clusters").fetchone() == ("EXTRACTED", "NOT_VERIFIED", None)


def test_c0378_missing_database_fails_without_creating_files(tmp_path):
    emitter = load_script(SCRIPTS / "proof_emitter_lean4.py", "lot12_missing_emitter")
    db = tmp_path / "missing.db"
    proof = tmp_path / "proof"
    with pytest.raises(sqlite3.OperationalError):
        emitter.Lean4ProofEmitter(db_path=db, lean_dir=proof).prove_extracted_clusters()
    assert not db.exists()
    assert not proof.exists()


def test_c0378_unextracted_rows_are_not_promoted_or_reset(tmp_path):
    emitter = load_script(SCRIPTS / "proof_emitter_lean4.py", "lot12_pending_emitter")
    db = tmp_path / "pending.db"
    make_db(db, status="ACCUMULATING")
    report = emitter.Lean4ProofEmitter(db_path=db).prove_extracted_clusters()
    assert report["total_evaluated"] == 0
    with sqlite3.connect(db) as conn:
        assert conn.execute("SELECT status, lean4_proof_status FROM cortex_invariant_clusters").fetchone() == ("ACCUMULATING", "UNTESTED")


def test_c0360_real_lean_checks_catalog_and_bounded_theorem(tmp_path):
    generator = load_script(ROOT / "scripts/babylon60/gen_oncology_primitives.py", "lot12_valid_oncology")
    output = tmp_path / "Catalog.lean"
    data = primitives()
    data[0]["name"] = 'quote " and backslash \\ and newline\nfixture'
    data[0]["category"] = 'escaped " category'
    data[0]["role"] = 'escaped \\ role'
    generator.export_lean4(data, output)
    output.write_text(output.read_text() + '''
open Babylon60.Oncology
example : ontologyCatalog.length = 300 := ontology_count_invariant
example (p : OncologyPrimitive) : ¬ ((List.replicate 301 p).length ≤ 300) := by simp
example : ¬ ([] : List OncologyPrimitive).length > 300 := anergy_purge_limit [] (by decide)
''')
    proc = lean_run(output)
    assert proc.returncode == 0, proc.stdout + proc.stderr


@pytest.mark.parametrize("count", [0, 1, 299, 301])
def test_c0360_wrong_cardinality_preserves_output(tmp_path, count):
    generator = load_script(ROOT / "scripts/babylon60/gen_oncology_primitives.py", "lot12_count_oncology")
    output = tmp_path / "Catalog.lean"
    output.write_text("existing output")
    data = (primitives() + [primitives()[0]])[:count]
    with pytest.raises(ValueError):
        generator.export_lean4(data, output)
    assert output.read_text() == "existing output"


def test_c0385_real_demo_uses_disposable_home_database_and_no_native_generation(tmp_path):
    external_home = tmp_path / "operator-home"
    external_home.mkdir()
    canary = external_home / "cortex_memory.db"
    canary.write_bytes(b"operator fixture must remain untouched")
    environment = dict(os.environ)
    environment["HOME"] = str(external_home)
    environment["CORTEX_MEMORY_DB"] = str(canary)
    environment["CORTEX_VAULT_KEY"] = "fixture-key-must-not-load"
    proc = subprocess.run([sys.executable, str(SCRIPTS / "test_destiladora_e2e.py"), "--isolated-demo"],
                          cwd=tmp_path, env=environment, capture_output=True, text=True, timeout=60)
    assert proc.returncode == 2, proc.stdout + proc.stderr
    report = json.loads(proc.stdout)
    assert report["status"] == "NOT_VERIFIED"
    assert report["trace_count"] == 3
    assert report["synthetic"] is True
    assert report["temporary_files_removed"] is True
    assert not Path(report["temporary_root"]).exists()
    assert Path(report["database"]).parent == Path(report["temporary_root"])
    assert Path(report["home"]).parent == Path(report["temporary_root"])
    assert report["proofs"]["certified"] == 0
    assert report["rust_generation"] == "NOT_EXECUTED"
    assert report["native_compilation"] == "NOT_EXECUTED"
    assert report["benchmark"] == "NOT_EXECUTED"
    assert canary.read_bytes() == b"operator fixture must remain untouched"


def test_c0385_cli_rejects_external_database_arguments(tmp_path):
    canary = tmp_path / "operator.db"
    canary.write_bytes(b"untouched")
    proc = subprocess.run([sys.executable, str(SCRIPTS / "test_destiladora_e2e.py"), "--db-path", str(canary)],
                          cwd=tmp_path, capture_output=True, text=True, timeout=10)
    assert proc.returncode != 0
    assert canary.read_bytes() == b"untouched"


def test_c0378_warmup_and_concurrent_instances_preserve_rejection(tmp_path):
    emitter = load_script(SCRIPTS / "proof_emitter_lean4.py", "lot12_burst_emitter")
    db = tmp_path / "burst.db"
    make_db(db)
    with sqlite3.connect(db) as conn:
        for i in range(31):
            conn.execute("INSERT INTO cortex_invariant_clusters (cluster_id, ast_signature, z3_precondition, status) VALUES (?, ?, ?, 'EXTRACTED')",
                         (f"fixture-{i}", "cd" * 32, f"UNVERIFIED-{i}"))
    def reject(_index):
        return emitter.Lean4ProofEmitter(db_path=db).prove_extracted_clusters()
    for i in range(2):
        assert reject(i)["total_evaluated"] == 32
    with ThreadPoolExecutor(max_workers=8) as executor:
        reports = list(executor.map(reject, range(24)))
    assert all(report["certified"] == 0 for report in reports)
    with sqlite3.connect(db) as conn:
        assert conn.execute("SELECT COUNT(*) FROM cortex_invariant_clusters").fetchone()[0] == 32
        assert conn.execute("SELECT COUNT(*) FROM cortex_invariant_clusters WHERE lean4_proof_status = 'NOT_VERIFIED' AND status = 'EXTRACTED'").fetchone()[0] == 32


def test_c0385_warmup_and_concurrent_demo_roots_are_distinct(tmp_path):
    environment = dict(os.environ)
    environment["HOME"] = str(tmp_path)
    def run(_index):
        proc = subprocess.run([sys.executable, str(SCRIPTS / "test_destiladora_e2e.py"), "--isolated-demo"],
                              cwd=tmp_path, env=environment, capture_output=True, text=True, timeout=60)
        assert proc.returncode == 2, proc.stdout + proc.stderr
        return json.loads(proc.stdout)
    run(0)
    with ThreadPoolExecutor(max_workers=3) as executor:
        reports = list(executor.map(run, range(6)))
    roots = [report["temporary_root"] for report in reports]
    assert len(set(roots)) == 6
    assert all(not Path(root).exists() for root in roots)
    assert all(report["trace_count"] == 3 and report["proofs"]["certified"] == 0 for report in reports)


@pytest.mark.parametrize("phase", ["ingest", "extract", "prove"])
def test_c0385_exception_removes_private_database_and_home(tmp_path, phase):
    child = '''
import importlib.util,json,sys,types
from pathlib import Path
s=importlib.util.spec_from_file_location('demo',sys.argv[1])
m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
roots=[]
def ingest(**kw):
    roots.append(Path(kw['db_path']).parent)
    if sys.argv[2]=='ingest':raise RuntimeError('fixture')
    return 'synthetic'
def extract(**kw):
    if sys.argv[2]=='extract':raise RuntimeError('fixture')
    return {'processed':0,'clusters':[]}
def prove():raise RuntimeError('fixture')
i=types.ModuleType('goal_trace_ingestor');i.ingest_goal_trace=ingest
x=types.ModuleType('invariant_extractor_z3');x.Z3InvariantExtractor=lambda **kw:types.SimpleNamespace(inspect_and_extract=extract)
p=types.ModuleType('proof_emitter_lean4');p.Lean4ProofEmitter=lambda **kw:types.SimpleNamespace(prove_extracted_clusters=prove)
sys.modules.update({a.__name__:a for a in [i,x,p]})
try:m._run_isolated_demo()
except RuntimeError:pass
print(json.dumps({'count':len(roots),'removed':bool(roots) and all(not root.exists() for root in roots)}))
'''
    proc = subprocess.run([sys.executable, "-c", child, str(SCRIPTS / "test_destiladora_e2e.py"), phase],
                          cwd=tmp_path, capture_output=True, text=True, timeout=30)
    assert proc.returncode == 0, proc.stderr
    assert json.loads(proc.stdout)["removed"] is True
