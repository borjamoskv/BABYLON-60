# C5-REAL EXERGY CERTIFIED
import os
import sys

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from cortex.core.cortex_purge import execute_landauer_purge, run_ruff_fix

def run_legion_purge() -> None:
    run_ruff_fix()
    execute_landauer_purge()

if __name__ == "__main__":
    run_legion_purge()

