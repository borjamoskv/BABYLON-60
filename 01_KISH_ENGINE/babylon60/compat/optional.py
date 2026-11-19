#!/usr/bin/env python3
# ============================================================================
# BABYLON-60 v4.0 Sovereign Hardened
# █ AUTOCOGNITION-Ω | STATE: C5-REAL | AESTHETIC: INDUSTRIAL_NOIR_2026
# ============================================================================
"""
optional.py - Graceful Degradation & Optional Dependency Bridge

Módulo materializado vía Autopoiesis (Sello L0).
Resuelve el hueco de existencia de `np` (NumPy) importado por 9 módulos
de cómputo pesado. Si NumPy no está disponible, provee un mock estricto
que lanza una excepción clara indicando el paquete faltante en lugar de
romper el tiempo de importación global.
"""

import logging
import types
from typing import cast

logger = logging.getLogger("BABYLON-60.COMPAT")


class MissingOptionalDependency:
    """Mock object that raises an error only when accessed/called."""

    def __init__(self, name: str, pip_package: str) -> None:
        self._name = name
        self._pip_package = pip_package

    def __getattr__(self, item: str) -> object:
        raise ImportError(
            f"❌ Dependencia Opcional Faltante: El ecosistema requiere '{self._name}' "
            f"para colapsar esta función matemática. Ejecuta: pip install {self._pip_package}"
        )

    def __call__(self, *args: object, **kwargs: object) -> None:
        self.__getattr__("__call__")


try:
    import numpy as _real_np

    np: types.ModuleType = _real_np
except ImportError:
    np = cast(types.ModuleType, MissingOptionalDependency("numpy", "numpy"))

__all__ = ["np", "MissingOptionalDependency"]
