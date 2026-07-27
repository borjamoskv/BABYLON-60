import logging
import os
import shutil
from pathlib import Path

# Mover flake_gen
source = "babylon60/extensions/axioms/topological_id.py"
dest = "babylon60/shared/topological_id.py"
if os.path.exists(source):
    shutil.move(source, dest)
    logging.getLogger(__name__).info("Moved topological_id.py")

# Actualizar referencias
c = 0
for d in ["babylon60", "tests", "scripts"]:
    for root, _dirs, files in os.walk(d):
        for file in files:
            if file.endswith(".py"):
                p = Path(root) / file
                txt = p.read_text()
                if "babylon60.extensions.axioms.topological_id" in txt:
                    txt = txt.replace("babylon60.extensions.axioms.topological_id", "babylon60.shared.topological_id")
                    p.write_text(txt)
                    c += 1
logging.getLogger(__name__).info(f"Updated {c} files for topological_id.")
