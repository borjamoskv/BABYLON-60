# C5-REAL EXERGY CERTIFIED

import sys
from cortex_guard import verify_dependencies

try:
    print("[CHILD] Requesting dependencies...")
    # Injecting a dependency that doesn't exist to trigger a collapse
    verify_dependencies(["ls", "herramienta_fantasma_inexistente"])
    print("[CHILD] ERROR: I should not be alive right now. Green Theater detected.")
    sys.exit(0)
except Exception as e:
    print(f"[CHILD] ERROR: Caught exception {e}. This is a violation! It should have been a SIGABRT.")
    sys.exit(0)
