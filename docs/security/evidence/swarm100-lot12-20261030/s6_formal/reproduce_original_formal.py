"""Replay captured original formal sources only against disposable fixtures."""

import importlib.util
import json
import os
import shutil
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[5]
EVIDENCE = Path(__file__).resolve().parent


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main():
    lean = os.environ.get("BABYLON60_TEST_LEAN_BIN")
    if not lean:
        lean = subprocess.check_output(["elan", "which", "lean"], text=True).strip()
    lean = Path(lean)
    if not lean.is_file():
        raise RuntimeError("An installed Lean toolchain binary is required")
    captured = json.loads((EVIDENCE.parent / "before-source-snapshots.json").read_text())
    tests = load(ROOT / "tests/test_swarm100_lot12_s6_formal_regressions.py", "fixture_helpers")
    with tempfile.TemporaryDirectory(prefix="b60-original-formal-") as directory:
        root = Path(directory)
        os.environ["HOME"] = str(root / "home")
        os.environ["PATH"] = str(lean.parent) + os.pathsep + os.environ.get("PATH", "")
        emitter_path = root / "proof_emitter_lean4.py"
        emitter_path.write_text(captured["scripts/c5_destiladora/proof_emitter_lean4.py"])
        emitter = load(emitter_path, "captured_emitter")
        db = root / "fixture.db"
        tests.make_db(db, precondition="False")
        result = emitter.Lean4ProofEmitter(db_path=db, lean_dir=root / "lean").prove_extracted_clusters()
        shutil.copyfile(next((root / "lean").glob("*.lean")), EVIDENCE / "original-fixed-model.lean")
        generator_path = root / "gen_oncology_primitives.py"
        generator_path.write_text(captured["scripts/babylon60/gen_oncology_primitives.py"])
        generator = load(generator_path, "captured_oncology_generator")
        proof = root / "OncologyFalse.lean"
        generator.export_lean4(tests.primitives(), proof)
        # Isolate the axiom's logic from preexisting parser/recursion issues.
        code = proof.read_text().replace("import Lean", "import Lean\nset_option maxRecDepth 10000")
        code = code.replace("  | meta\n", "  | «meta»\n").replace("PrimitiveLayer.meta", "PrimitiveLayer.«meta»")
        code += '''
theorem swarm100_false : False := by
  let p : OncologyPrimitive := ⟨"", "", "", .«meta», "", "", ""⟩
  exact anergy_purge_limit (List.replicate 301 p) (by decide)
end Babylon60.Oncology
'''
        proof.write_text(code)
        proc = subprocess.run([str(lean), str(proof)], cwd=root, capture_output=True, text=True, timeout=60)
        shutil.copyfile(proof, EVIDENCE / "original-axiom-counterexample-normalized.lean")
        (EVIDENCE / "original-axiom-counterexample-normalized.log").write_text(proc.stdout + proc.stderr)
        report = {"scope": "Captured original sources, temporary DB/HOME and explicit installed Lean binary",
                  "lean_binary": str(lean), "original_emitter_precondition": "False",
                  "original_emitter_report": result, "normalized_axiom_false_proof_exit": proc.returncode,
                  "normalizations": ["Escape reserved meta constructor", "Increase maxRecDepth", "Close namespace"],
                  "no_operator_database_or_identity_access": True}
        (EVIDENCE / "original-formal-reproduction.json").write_text(json.dumps(report, indent=2) + "\n")
        print(json.dumps(report))
        if result["results"][0]["status"] != "PROVED" or proc.returncode != 0:
            raise SystemExit("Original counterexamples did not reproduce")


if __name__ == "__main__":
    main()
