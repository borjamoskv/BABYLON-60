# C5-REAL EXERGY CERTIFIED
#!/usr/bin/env python3
"""
CORTEX Code Formatter (C5-REAL).
Orquestador de autoformateo de código multilunguaje (Python, Go, Rust).
"""

import os
import subprocess
import sys
import time

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def run_cmd(name: str, cmd: list[str]) -> bool:
    print(f"🧹 Running {name}...")
    try:
        subprocess.run(
            cmd,
            cwd=PROJECT_ROOT,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed: {name} (exit code {e.returncode})")
        if e.stdout:
            print(e.stdout.decode("utf-8"))
        if e.stderr:
            print(e.stderr.decode("utf-8"))
        return False


def main() -> None:
    start_time = time.perf_counter()
    success = True

    # 1. Python Formatting (Ruff)
    if not run_cmd("Ruff Format (Python)", ["uv", "run", "ruff", "format", "."]):
        if not run_cmd(
            "Ruff Format (Fallback)", [sys.executable, "-m", "ruff", "format", "."]
        ):
            success = False

    # 2. Go Formatting (gofmt)
    if not run_cmd("Go Format (gofmt)", ["gofmt", "-w", "./primitives"]):
        success = False

    # 3. Rust Formatting (Tauri & Strike-RS)
    if not run_cmd(
        "Rust Format (src-tauri)",
        ["cargo", "fmt", "--manifest-path", "src-tauri/Cargo.toml"],
    ):
        success = False
    if not run_cmd(
        "Rust Format (strike-rs)",
        ["cargo", "fmt", "--manifest-path", "strike-rs/Cargo.toml"],
    ):
        success = False

    elapsed = time.perf_counter() - start_time
    if success:
        print(f"✅ Formateo completado con éxito en {elapsed:.4f}s.")
        sys.exit(0)
    else:
        print(f"❌ Formateo falló después de {elapsed:.4f}s.")
        sys.exit(1)


if __name__ == "__main__":
    main()
