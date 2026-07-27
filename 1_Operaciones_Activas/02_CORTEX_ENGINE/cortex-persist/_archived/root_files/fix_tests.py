import logging
import os
from pathlib import Path

replace_map = {
    "babylon60.engine.cognitive.models": "babylon60.types.core_models",
    "babylon60.engine.flow.causality_models": "babylon60.types.core_models"
}

c = 0
for root, _dirs, files in os.walk("tests"):
    for file in files:
        if file.endswith(".py"):
            p = Path(root) / file
            txt = p.read_text()
            changed = False
            for old, new in replace_map.items():
                if old in txt:
                    txt = txt.replace(old, new)
                    changed = True
            if changed:
                p.write_text(txt)
                c += 1
logging.getLogger(__name__).info(f"Migrated imports in {c} test files.")
