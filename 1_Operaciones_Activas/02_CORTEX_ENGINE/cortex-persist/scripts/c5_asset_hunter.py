# [C5-REAL] Exergy-Maximized
"""
cat_id: c5-asset-hunter
cat_type: script
version: 1.0.0
reality_level: C5-REAL
owner: borjamoskv
exergy_tier: P2
"""

import logging
import os
import subprocess

dead_assets = []
for root, _, files in os.walk("public"):
    for file in files:
        if file.endswith((".png", ".jpg", ".jpeg", ".svg", ".webp", ".mp4")):
            filepath = os.path.join(root, file)
            # Remove "public/" from the start since in HTML they are referenced from root e.g. /images/foo.png
            ref_path = filepath[len("public") :]
            basename = os.path.basename(file)

            # Check if this asset name is used anywhere in src/
            cmd = f"grep -rw '{basename}' src/ || true"
            out = subprocess.check_output(cmd, shell=True, text=True).strip()

            if not out:
                dead_assets.append(filepath)

logging.getLogger(__name__).info("DEAD_ASSETS:", len(dead_assets))
for da in dead_assets:
    logging.getLogger(__name__).info(da)
