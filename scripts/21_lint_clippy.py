# C5-REAL EXERGY CERTIFIED
#!/usr/bin/env python3
"""
CORTEX Rust Clippy Linter (C5-REAL).
Ejecuta la auditoría estricta de advertencias en componentes de Rust.
"""

import os
import subprocess
import sys
import time

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def run_clippy(manifest_name: str, manifest_path: str) -> bool:
    print(f"🔎 Running cargo clippy on {manifest_name}...")
    cmd = ["cargo", "clippy", "--manifest-path", manifest_path, "--", "-D", "warnings"]
    try:
        # Heredamos variables de entorno (ej. PYO3_PYTHON si aplica)
        env_vars = dict(os.environ)
        env_vars["PYO3_PYTHON"] = os.path.join(PROJECT_ROOT, ".venv", "bin", "python")
        subprocess.run(cmd, cwd=PROJECT_ROOT, check=True, env=env_vars)
        return True
    except subprocess.CalledProcessError as e:
        print(
            f"❌ Clippy warnings or compilation errors detected in {manifest_name} (exit code {e.returncode})."
        )
        return False


def main() -> None:
    start_time = time.perf_counter()

    # 1. Tauri Rust Component clippy check
    tauri_ok = run_clippy("src-tauri", "src-tauri/Cargo.toml")

    # 2. Strike-RS component clippy check
    strike_ok = run_clippy("strike-rs", "strike-rs/Cargo.toml")

    elapsed = time.perf_counter() - start_time
    if tauri_ok and strike_ok:
        print(f"✅ Rust Clippy limpio en {elapsed:.4f}s.")
        sys.exit(0)
    else:
        print(f"❌ Falló auditoría de Rust Clippy en {elapsed:.4f}s.")
        sys.exit(1)


if __name__ == "__main__":
    main()
