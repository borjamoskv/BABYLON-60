import logging
import os
import shutil
from pathlib import Path

# 1. Renombrar carpeta
if os.path.exists("babylon60/types"):
    shutil.move("babylon60/types", "babylon60/shared")

# 2. Reemplazar 'babylon60.types.' por 'babylon60.shared.' en todo el código
c = 0
for d in ["babylon60", "tests", "scripts"]:
    for root, _dirs, files in os.walk(d):
        for file in files:
            if file.endswith(".py"):
                p = Path(root) / file
                txt = p.read_text()
                if "babylon60.types." in txt:
                    txt = txt.replace("babylon60.types.", "babylon60.shared.")
                    p.write_text(txt)
                    c += 1
logging.getLogger(__name__).info(f"Migrated namespace in {c} files.")
