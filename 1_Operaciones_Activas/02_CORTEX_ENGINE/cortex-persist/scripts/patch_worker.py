# [C5-REAL] Exergy-Maximized
"""
cat_id: patch-worker
cat_type: script
version: 1.0.0
reality_level: C5-REAL
owner: borjamoskv
exergy_tier: P2
"""

import logging
import re
from pathlib import Path


def main():
    dist_dir = Path("dist/server/chunks")
    if not dist_dir.exists():
        logging.getLogger(__name__).info("dist/server/chunks not found, skipping patch")
        return

    for path in dist_dir.glob("*.mjs"):
        content = path.read_text(encoding="utf-8")
        if "deserializeManifest" in content and "rootDir: new URL" in content:
            logging.getLogger(__name__).info(f"Patching {path.name}...")
            pattern = r"(rootDir|srcDir|publicDir|outDir|cacheDir|buildClientDir|buildServerDir):\s*new\s*URL\(serializedManifest\.\1\)"
            replacement = (
                '\\1: new URL(serializedManifest.\\1.replace(/^file:\\/\\/\\/?/, "http://local/"))'
            )
            new_content = re.sub(pattern, replacement, content)
            if new_content != content:
                path.write_text(new_content, encoding="utf-8")
                logging.getLogger(__name__).info("Patch successfully applied.")
            else:
                logging.getLogger(__name__).info("No replacements matched, check pattern.")


if __name__ == "__main__":
    main()
