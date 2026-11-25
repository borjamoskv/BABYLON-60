# ============================================================================
# BABYLON-60 Test Harness Configuration
# █ AUTOCOGNITION-Ω | STATE: C5-REAL | AESTHETIC: INDUSTRIAL_NOIR_2026
# ============================================================================

import gc
import os
from pathlib import Path
import sys
import tempfile

from typing import Generator

import pytest

# Ensure required environment invariants are populated for test suite execution
_repo_root = Path(__file__).resolve().parent.parent
os.environ.setdefault("BABYLON_HOME", str(_repo_root))
os.environ.setdefault("GEMINI_HOME", os.path.expanduser("~/.gemini"))
os.environ.setdefault("BABYLON60_SIGNING_SEED", "00" * 32)

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
def collect_test_garbage() -> Generator[None, None, None]:
    """Release closed SQLite handles without deleting database files."""
    gc.collect()
    yield
    gc.collect()


@pytest.fixture
def isolate_sqlite_wal_invariants(tmp_path: Path) -> Generator[None, None, None]:
    """Keep relative database files and temporary files inside each test's directory."""
    runtime_dir = tmp_path / "runtime"
    runtime_dir.mkdir()
    with pytest.MonkeyPatch.context() as runtime:
        runtime.chdir(runtime_dir)
        runtime.setenv("TMPDIR", str(runtime_dir))
        runtime.setattr(tempfile, "tempdir", str(runtime_dir))
        yield
