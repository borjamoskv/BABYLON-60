# C5-REAL EXERGY CERTIFIED
import os
import ctypes
import sys

# Deterministic Path Resolution
_BASE_DIR = os.path.dirname(os.path.abspath(__file__))
_LIB_PATH = os.path.join(_BASE_DIR, "libcortex_guard.dylib")

try:
    _guard = ctypes.CDLL(_LIB_PATH)
    _guard.bft_assert.argtypes = [ctypes.c_int, ctypes.c_char_p]
    _guard.bft_assert.restype = None
except OSError:
    print(f"[FATAL] No se pudo cargar libcortex_guard.dylib. ¿Ejecutó 'make build' en {_BASE_DIR}?")
    sys.exit(1)

def enforce_invariant(condition: bool, constraint_name: str):
    """
    DOMAIN PRIMITIVE: Enforces a boolean invariant at the OS POSIX level.
    If condition is False, the entire Python interpreter is killed via SIGABRT (abort).
    No try/except can catch this. Absolute Determinism.
    """
    c_name = constraint_name.encode('utf-8')
    # Will never return if condition == False
    _guard.bft_assert(int(condition), c_name)
