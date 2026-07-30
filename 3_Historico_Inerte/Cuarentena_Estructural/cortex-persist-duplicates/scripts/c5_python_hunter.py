# [C5-REAL] Exergy-Maximized
"""
cat_id: c5-python-hunter
cat_type: script
version: 1.0.0
reality_level: C5-REAL
owner: borjamoskv
exergy_tier: P2
"""

import logging
import os
import subprocess

dead_py = []
for root, _, files in os.walk("babylon60"):
    for file in files:
        if file.endswith(".py") and not file.startswith("__"):
            filepath = os.path.join(root, file)
            basename = file[:-3]  # remove .py

            # Search for the module name
            cmd = f"grep -rw '{basename}' babylon60/ tests/ extensions/ || true"
            out = subprocess.check_output(cmd, shell=True, text=True).strip().split("\n")

            out = [line for line in out if line and not line.startswith(filepath)]

            if len(out) == 0:
                dead_py.append(filepath)

logging.getLogger(__name__).info("DEAD_PY:", dead_py)
