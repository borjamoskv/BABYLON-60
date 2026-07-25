# C5-REAL EXERGY CERTIFIED
#!/usr/bin/env python3
"""
CORTEX Rust Test Runner (C5-REAL).
Ejecuta la suite de pruebas unitarias de Rust en src-tauri y strike-rs.
"""

import os
import subprocess
import sys
import time

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def run_test(name: str, manifest_path: str) -> bool:
    print(f"🧪 Running cargo test on {name}...")
    cmd = ["cargo", "test", "--manifest-path", manifest_path]
    try:
        env_vars = dict(os.environ)
        env_vars["PYO3_PYTHON"] = os.path.join(PROJECT_ROOT, ".venv", "bin", "python")
        subprocess.run(cmd, cwd=PROJECT_ROOT, check=True, env=env_vars)
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ cargo test failed on {name} (exit code {e.returncode})")
        return False

def main() -> None:
    start_time = time.perf_counter()

    # 1. src-tauri tests
    tauri_ok = run_test("src-tauri", "src-tauri/Cargo.toml")

    # 2. strike-rs tests
    strike_ok = run_test("strike-rs", "strike-rs/Cargo.toml")

    elapsed = time.perf_counter() - start_time
    if tauri_ok and strike_ok:
        print(f"✅ Rust tests completados con éxito en {elapsed:.4f}s.")
        sys.exit(0)
    else:
        print(f"❌ Pruebas de Rust fallaron en {elapsed:.4f}s.")
        sys.exit(1)

if __name__ == "__main__":
    main()
