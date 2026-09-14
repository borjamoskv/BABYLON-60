# ============================================================================
# BABYLON-60 Test Harness Configuration
# █ AUTOCOGNITION-Ω | STATE: C5-REAL | AESTHETIC: INDUSTRIAL_NOIR_2026
# ============================================================================

import gc
import os
from pathlib import Path
import sys

from typing import Generator

import pytest

# Ensure required environment invariants are populated for test suite execution
_repo_root = Path(__file__).resolve().parent.parent
os.environ.setdefault("BABYLON_HOME", str(_repo_root))
os.environ.setdefault("GEMINI_HOME", os.path.expanduser("~/.gemini"))

# Register experiments domain directories in sys.path for test discovery
_experiments_dir = _repo_root / "experiments"
for _sub in [
    "2_COMPILERS",
    "3_SUBPROJECTS",
    "4_INTEGRATIONS",
    "5_AUDIO_DSP",
    "6_SCRATCH",
    "7_SECURITY_AUDIT",
    "1_Operaciones_Activas/scripts",
]:
    _p = str(_experiments_dir / _sub)
    if _p not in sys.path:
        sys.path.insert(0, _p)


@pytest.fixture(autouse=True)
def clean_sqlite_wal_invariants() -> Generator[None, None, None]:
    """
    [INV_C5_SHM] Aniquilación determinista de tripletas SQLite (.db, .db-wal, .db-shm)
    en el árbol raíz del monorepo tanto antes como después de cada test.
    """
    gc.collect()
    for ext in ("*.db", "*.db-wal", "*.db-shm"):
        for path in _repo_root.glob(ext):
            try:
                path.unlink(missing_ok=True)
            except OSError:
                pass
    yield
    gc.collect()
    for ext in ("*.db", "*.db-wal", "*.db-shm"):
        for path in _repo_root.glob(ext):
            try:
                path.unlink(missing_ok=True)
            except OSError:
                pass
