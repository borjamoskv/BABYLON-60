# [C5-REAL] Exergy-Maximized
#!/usr/bin/env python3
"""
cat_id: install-git-sentinel
cat_type: script
version: 1.0.0
reality_level: C5-REAL
owner: borjamoskv
exergy_tier: P2
"""

import logging
import os
import stat
from pathlib import Path


def install_hook():
    repo_root = Path(__file__).resolve().parent.parent
    hook_path = repo_root / ".git" / "hooks" / "pre-commit"
    script_path = repo_root / "scripts" / "sovereign_pre_commit.py"

    if not script_path.exists():
        logging.getLogger(__name__).info(f"Error: {script_path} does not exist.")
        return

    hook_dir = hook_path.parent
    if not hook_dir.exists():
        hook_dir.mkdir(parents=True)

    # Create wrapper
    with open(hook_path, "w") as f:
        f.write(f'#!/bin/bash\nexec {repo_root}/.venv/bin/python {script_path} "$@"\n')

    st = os.stat(hook_path)
    os.chmod(hook_path, st.st_mode | stat.S_IEXEC)
    logging.getLogger(__name__).info(f"[C5-REAL] Git Sentinel installed at {hook_path}")


if __name__ == "__main__":
    install_hook()
