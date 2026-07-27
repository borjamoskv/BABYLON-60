import logging
import os
import shutil
from pathlib import Path

# 1. Mover facts a engine/core
if os.path.exists("babylon60/facts"):
    shutil.move("babylon60/facts", "babylon60/engine/core/facts")
# 2. Mover llm a engine/cognitive
if os.path.exists("babylon60/llm"):
    shutil.move("babylon60/llm", "babylon60/engine/cognitive/llm")

# 3. Eliminar código especulativo de Keter en reflex.py
reflex_path = Path("babylon60/engine/cognitive/reflex.py")
if reflex_path.exists():
    txt = reflex_path.read_text()
    if "KeterEngine" in txt:
        # Borrar la clase ReflexAgent completa o el método que lo usa
        import re
        txt = re.sub(r'from babylon60\.extensions\.speculative\.keter import KeterEngine', '', txt)
        reflex_path.write_text(txt)

# 4. Actualizar referencias
c = 0
for d in ["babylon60", "tests", "scripts"]:
    for root, _dirs, files in os.walk(d):
        for file in files:
            if file.endswith(".py"):
                p = Path(root) / file
                txt = p.read_text()
                changed = False
                if "babylon60.facts" in txt:
                    txt = txt.replace("babylon60.facts", "babylon60.engine.core.facts")
                    changed = True
                if "babylon60.llm" in txt:
                    txt = txt.replace("babylon60.llm", "babylon60.engine.cognitive.llm")
                    changed = True
                if changed:
                    p.write_text(txt)
                    c += 1
logging.getLogger(__name__).info(f"Updated {c} files.")
