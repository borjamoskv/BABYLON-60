# C5-REAL EXERGY CERTIFIED
#!/usr/bin/env python3
"""
TDAH Orphan Thread Purge — C5-REAL (Intervención Isomórfica).
Delegates to unified Landauer Purge primitive (cortex/cortex_purge.py).
"""

import os
import sys

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from cortex.cortex_purge import audit_and_purge_orphans

if __name__ == "__main__":
    audit_and_purge_orphans()

