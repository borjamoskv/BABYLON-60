# [C5-REAL] Exergy-Maximized
"""
CORTEX - Compatibility Layer (Wave 1: Namespace Decoupling).
Allows importing 'cortex.*' modules by aliasing them to 'babylon60.*'.
"""

import importlib.abc
import importlib.util
import sys
from typing import Any


class AliasLoader(importlib.abc.Loader):
    def __init__(self, real_name: str) -> None:
        self.real_name = real_name

    def create_module(self, spec: importlib.machinery.ModuleSpec) -> Any:
        # Import the real module and return it
        return importlib.import_module(self.real_name)

    def exec_module(self, module: Any) -> None:
        # The module is already executed by import_module, so no-op
        pass


class CortexAliasFinder(importlib.abc.MetaPathFinder):
    def find_spec(self, fullname: str, path: Any, target: Any = None) -> Any:
        if fullname == "cortex" or fullname.startswith("cortex."):
            real_name = fullname.replace("cortex", "babylon60", 1)
            try:
                # Check if the real module spec exists
                spec = importlib.util.find_spec(real_name)
                if spec is not None:
                    # Return a spec pointing to our AliasLoader
                    return importlib.machinery.ModuleSpec(
                        name=fullname,
                        loader=AliasLoader(real_name),
                        is_package=spec.submodule_search_locations is not None,
                    )
            except (ImportError, AttributeError, ValueError):
                pass
        return None


def install_compat_hooks():
    if not any(isinstance(f, CortexAliasFinder) for f in sys.meta_path):
        sys.meta_path.insert(0, CortexAliasFinder())


# Automatically install when imported
install_compat_hooks()
