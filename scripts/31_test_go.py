# C5-REAL EXERGY CERTIFIED
#!/usr/bin/env python3
"""
CORTEX Go Test Runner (C5-REAL).
Ejecuta la suite de pruebas unitarias de Go en los componentes generados.
"""

import os
import subprocess
import sys
import time

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def main() -> None:
    start_time = time.perf_counter()
    print("🧪 Running Go Test Suite...")
    cmd = ["go", "test", "./primitives/..."]

    try:
        subprocess.run(cmd, cwd=PROJECT_ROOT, check=True)
        elapsed = time.perf_counter() - start_time
        print(f"✅ Go tests completados con éxito en {elapsed:.4f}s.")
        sys.exit(0)
    except subprocess.CalledProcessError as e:
        elapsed = time.perf_counter() - start_time
        print(f"❌ Go tests fallaron con código {e.returncode} después de {elapsed:.4f}s.")
        sys.exit(e.returncode)

if __name__ == "__main__":
    main()
