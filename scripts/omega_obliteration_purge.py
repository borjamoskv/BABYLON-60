# C5-REAL EXERGY CERTIFIED
import os
import sys

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from cortex.core.cortex_purge import obliterate_zero_operators

if __name__ == "__main__":
    target = os.environ.get("CORTEX_TARGET_DIR", PROJECT_ROOT)
    obliterate_zero_operators(target)

