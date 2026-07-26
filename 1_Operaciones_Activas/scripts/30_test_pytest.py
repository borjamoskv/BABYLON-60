# C5-REAL EXERGY CERTIFIED
#!/usr/bin/env python3
"""
CORTEX Python Test Runner (C5-REAL).
Ejecuta la suite de pruebas unitarias de Python usando pytest.
"""

import os
import subprocess
import sys
import time

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def main() -> None:
    start_time = time.perf_counter()
    print("🧪 Running Pytest Suite...")

    # Intentar ejecutar con el intérprete de la .venv aislada (Ω29)
    # y asegurar sincronización JIT (uv sync --all-extras)
    venv_pytest = os.path.join(PROJECT_ROOT, ".venv", "bin", "pytest")
    cmd = [venv_pytest] if os.path.exists(venv_pytest) else ["pytest"]

    try:
        # Sincronización requerida por Ω29
        subprocess.run(["uv", "sync", "--all-extras"], cwd=PROJECT_ROOT, check=True)

        subprocess.run(cmd, cwd=PROJECT_ROOT, check=True)
        elapsed = time.perf_counter() - start_time
        print(f"✅ Pytest completado con éxito en {elapsed:.4f}s.")
        sys.exit(0)
    except subprocess.CalledProcessError as e:
        elapsed = time.perf_counter() - start_time
        print(f"❌ Pytest falló con código {e.returncode} después de {elapsed:.4f}s.")
        sys.exit(e.returncode)

if __name__ == "__main__":
    main()
