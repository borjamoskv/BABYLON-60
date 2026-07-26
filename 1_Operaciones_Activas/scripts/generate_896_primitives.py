# C5-REAL EXERGY CERTIFIED
#!/usr/bin/env python3
"""
Delegation wrapper for unified primitive generator (scripts/16_codegen_primitives.py).
"""

import importlib.util
import os
import sys

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

spec = importlib.util.spec_from_file_location(
    "codegen_primitives", os.path.join(PROJECT_ROOT, "scripts", "16_codegen_primitives.py")
)
if spec and spec.loader:
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    generate_896_primitives_yaml = mod.generate_896_primitives_yaml
else:
    raise ImportError("Could not load scripts/16_codegen_primitives.py")

if __name__ == "__main__":
    generate_896_primitives_yaml()
