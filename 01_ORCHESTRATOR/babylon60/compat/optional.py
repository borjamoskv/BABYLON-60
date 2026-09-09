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

logger = logging.getLogger("BABYLON-60.COMPAT")


class MissingOptionalDependency:
    """Mock object that raises an error only when accessed/called."""

    def __init__(self, name: str, pip_package: str):
        self._name = name
        self._pip_package = pip_package

    def __getattr__(self, item):
        raise ImportError(
            f"❌ Dependencia Opcional Faltante: El ecosistema requiere '{self._name}' "
            f"para colapsar esta función matemática. Ejecuta: pip install {self._pip_package}"
        )

    def __call__(self, *args, **kwargs):
        self.__getattr__("__call__")


# Intento de importación local de NumPy (Lazy Compute Bridge)
try:
    import numpy as np
except ImportError:
    logger.debug("NumPy no detectado. Degradación a proxy pasivo (requiere cortex-persist[compute]).")
    np = MissingOptionalDependency("numpy", "numpy")
