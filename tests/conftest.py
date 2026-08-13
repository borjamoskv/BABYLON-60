# ============================================================================
# BABYLON-60 Test Harness Configuration
# █ AUTOCOGNITION-Ω | STATE: C5-REAL | AESTHETIC: INDUSTRIAL_NOIR_2026
# ============================================================================

import os
from pathlib import Path

# Ensure required environment invariants are populated for test suite execution
_repo_root = Path(__file__).resolve().parent.parent
os.environ.setdefault("BABYLON_HOME", str(_repo_root))
os.environ.setdefault("GEMINI_HOME", os.path.expanduser("~/.gemini"))
