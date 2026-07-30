# [C5-REAL] Exergy-Maximized
"""
cat_id: c5-exec
cat_type: script
version: 1.0.0
reality_level: C5-REAL
owner: borjamoskv
exergy_tier: P2
"""


from __future__ import annotations

import logging
import os
import subprocess
import sys


def main() -> int:
    if len(sys.argv) < 2:
        logging.getLogger(__name__).info("Usage: c5_exec.py <command>", file=sys.stderr)
        return 1

    cmd = " ".join(sys.argv[1:])

    shell = "/bin/zsh" if os.path.exists("/bin/zsh") else "/bin/sh"

    proc = subprocess.run(
        [shell, "-c", cmd],
        text=True,
        env=os.environ.copy(),
    )
    return proc.returncode


if __name__ == "__main__":
    sys.exit(main())
