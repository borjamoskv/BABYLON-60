# ============================================================================
# BABYLON-60 v4.0 Sovereign Hardened
# █ AUTOCOGNITION-Ω | STATE: C5-REAL | AESTHETIC: INDUSTRIAL_NOIR_2026
# ============================================================================
import warnings

warnings.warn(
    "Módulo deprecado (INV_C5_NOMINAL_DENSITY). Usar babylon60.transducers.cache en su lugar.",
    DeprecationWarning,
    stacklevel=2,
)
from babylon60.transducers.cache import *  # noqa: E402, F403, F401
