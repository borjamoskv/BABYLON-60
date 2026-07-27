# [C5-REAL] Exergy-Maximized
"""
cat_id: c5-css-hunter
cat_type: script
version: 1.0.0
reality_level: C5-REAL
owner: borjamoskv
exergy_tier: P2
"""

import logging
import os
import subprocess

dead_css = []
for root, _, files in os.walk("src"):
    for file in files:
        if file.endswith(".css"):
            filepath = os.path.join(root, file)
            basename = os.path.basename(file)

            # Global css might be imported in layout, but let's check if the basename is mentioned anywhere
            cmd = f"grep -rw '{basename}' src/ || true"
            out = subprocess.check_output(cmd, shell=True, text=True).strip().split("\n")

            out = [line for line in out if line and not line.startswith(filepath)]

            if len(out) == 0:
                dead_css.append(filepath)

logging.getLogger(__name__).info("DEAD_CSS:", dead_css)
