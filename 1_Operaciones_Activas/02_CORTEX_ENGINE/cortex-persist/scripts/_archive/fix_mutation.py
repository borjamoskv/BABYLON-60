f2 = "~/30_BABYLON60/babylon60/engine/mutation_engine.py"
with open(f2) as f:
    c2 = f.read()

import_stmt = "from babylon60.crypto.aes import get_default_encrypter\n"
if "get_default_encrypter" not in c2[:500]:
    c2 = c2.replace("import logging", "import logging\n" + import_stmt)

with open(f2, "w") as f:
    f.write(c2)
