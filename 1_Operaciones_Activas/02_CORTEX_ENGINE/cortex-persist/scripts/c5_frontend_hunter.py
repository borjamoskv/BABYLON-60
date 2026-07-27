# [C5-REAL] Exergy-Maximized
"""
cat_id: c5-frontend-hunter
cat_type: script
version: 1.0.0
reality_level: C5-REAL
owner: borjamoskv
exergy_tier: P2
"""

import logging
import os
import subprocess

dead_files = []
for root, _, files in os.walk("src"):
    for file in files:
        if file.endswith((".tsx", ".astro")):
            filepath = os.path.join(root, file)
            basename = file.split(".")[0]

            # Astro pages are automatically routed, so index.astro, etc are used by the framework.
            if "/pages/" in root:
                continue

            cmd = f"grep -rw '{basename}' src/ || true"
            out = subprocess.check_output(cmd, shell=True, text=True).strip().split("\n")

            # Exclude matches in the file itself
            out = [line for line in out if line and not line.startswith(filepath)]

            if len(out) == 0:
                dead_files.append(filepath)

logging.getLogger(__name__).info("DEAD_FRONTEND:", dead_files)
