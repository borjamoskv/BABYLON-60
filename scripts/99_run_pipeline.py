"""Pipeline Orquestador Unificado (C5-REAL Cascade)."""
import os
import sys
import subprocess
import time

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(PROJECT_ROOT)
os.chdir(PROJECT_ROOT)

def run_step(name: str, cmd: list[str]) -> bool:
    print(f"\n⚡ [PIPELINE] Ejecutando: {name} ...")
    start = time.perf_counter()
    env_vars = dict(os.environ)
    env_vars["PYO3_PYTHON"] = os.path.join(PROJECT_ROOT, ".venv", "bin", "python")
    try:
        res = subprocess.run(cmd, env=env_vars, check=True, capture_output=True, text=True)
        elapsed = time.perf_counter() - start
        print(f"✅ {name} completado con éxito en {elapsed:.4f}s.")
        if res.stdout.strip():
            print(f"--- Output ---\n{res.stdout.strip()}")
        return True
    except subprocess.CalledProcessError as e:
        elapsed = time.perf_counter() - start
        print(f"❌ {name} FALLÓ en {elapsed:.4f}s con código de salida {e.returncode}.")
        if e.stdout:
            print(f"--- Stdout ---\n{e.stdout.strip()}")
        if e.stderr:
            print(f"--- Stderr ---\n{e.stderr.strip()}")
        return False

def main():
    print("=== PIPELINE ORQUESTADOR UNIFICADO C5-REAL ===")
    start_global = time.perf_counter()
    
    steps = [
        ("00_init_ledger", [".venv/bin/python", "scripts/00_init_ledger.py"]),
        ("10_codegen_constants", [".venv/bin/python", "scripts/10_codegen_constants.py"]),
        ("11_codegen_noether", [".venv/bin/python", "scripts/11_codegen_noether.py"]),
        ("12_codegen_observer", [".venv/bin/python", "scripts/12_codegen_observer.py"]),
        ("13_codegen_haskell", [".venv/bin/python", "scripts/13_codegen_haskell.py"]),
        ("14_codegen_neuro", [".venv/bin/python", "scripts/14_codegen_neuro.py"]),
        ("15_codegen_tts", [".venv/bin/python", "scripts/15_codegen_tts.py"]),
        ("16_codegen_primitives", [".venv/bin/python", "scripts/16_codegen_primitives.py"]),
        ("17_codegen_github", [".venv/bin/python", "scripts/17_codegen_github.py"]),
        ("20_stress_db", [".venv/bin/python", "scripts/20_stress_db.py"]),
        ("Pytest Suite", [".venv/bin/pytest"]),
        ("Go Test Suite", ["go", "test", "./primitives/..."]),
        ("Tauri Rust Tests", ["cargo", "test", "--manifest-path", "src-tauri/Cargo.toml"]),
        ("Strike-RS Rust Tests", ["cargo", "test", "--manifest-path", "strike-rs/Cargo.toml"]),
        ("31_autoconsolidate", [".venv/bin/python", "scripts/31_autoconsolidate.py"]),
        ("32_legion_purge", [".venv/bin/python", "scripts/32_legion_purge.py"]),
    ]
    
    failed = False
    for name, cmd in steps:
        if not run_step(name, cmd):
            failed = True
            break
            
    elapsed_global = time.perf_counter() - start_global
    print("\n==============================================")
    if failed:
        print(f"❌ PIPELINE ABORTADO debido a fallos. Tiempo: {elapsed_global:.4f}s")
        sys.exit(1)
    else:
        print(f"✅ PIPELINE COMPLETADO EXITOSAMENTE. Tiempo total: {elapsed_global:.4f}s")
        sys.exit(0)

if __name__ == "__main__":
    main()
