# C5-REAL EXERGY CERTIFIED
#!/usr/bin/env python3
"""
CLI wrapper for unified Landauer purger primitive (cortex/cortex_purge.py).
"""

import sys
import os

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from cortex.core.cortex_purge import execute_landauer_purge

def main() -> None:
    results = execute_landauer_purge()
    print(f"Landauer Purge Finished: {results}")

if __name__ == "__main__":
    main()
