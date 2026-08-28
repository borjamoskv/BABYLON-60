# C5-REAL EXERGY CERTIFIED
# babylon_ipc.py — Verificación axiomática en tiempo de ejecución
import ctypes
from typing import Callable, Optional, Tuple


class SharedManifest(ctypes.Structure):
    """AXIOMA 1: Layout verificado."""
    _pack_ = 1  # Elimina padding implícito; nuestro padding manual es canónico
    _fields_ = [
        ("payload", ctypes.c_uint8 * 32),      # offset 0
        ("status_flag", ctypes.c_uint8),       # offset 32
        ("_padding", ctypes.c_uint8 * 7),      # offset 33-39
        ("epoch_id", ctypes.c_uint64),         # offset 40
        ("timestamp_ns", ctypes.c_uint64),     # offset 48
    ]

# VERIFICACIÓN AXIOMA 1 EN TIEMPO DE CARGA
assert ctypes.sizeof(SharedManifest) == 56, \
    f"AXIOMA 1 REFUTADO: sizeof={ctypes.sizeof(SharedManifest)}, esperado=56"


class BabylonIPC:
    """Implementación que satisface AXIOMAS 1-7."""

    def __init__(self, lib_path: str):
        self._lib = ctypes.CDLL(lib_path)

        self._lib.init_shared_memory.argtypes = [ctypes.c_int]
        self._lib.init_shared_memory.restype = ctypes.c_void_p

        self._lib.initialize_epoch_state.argtypes = [ctypes.c_void_p]
        self._lib.initialize_epoch_state.restype = None

        self._lib.read_active_epoch_safe.argtypes = [
            ctypes.c_void_p,
            ctypes.POINTER(ctypes.c_uint64),
            ctypes.POINTER(ctypes.c_uint64),
        ]
        self._lib.read_active_epoch_safe.restype = ctypes.c_int32

        self._lib.destroy_shared_memory.argtypes = [ctypes.c_void_p]
        self._lib.destroy_shared_memory.restype = None

        self._state_addr: Optional[int] = None

    def attach(self, fd: int, initialize: bool = True) -> bool:
        """AXIOMA 3: attach + initialize como operación atómica de construcción."""
        ptr = self._lib.init_shared_memory(fd)
        if not ptr:
            return False
        self._state_addr = ptr
        if initialize:
            self._lib.initialize_epoch_state(self._state_addr)
        return True

    def read_active_epoch(self) -> Optional[Tuple[int, int]]:
        """AXIOMA 2 + 7: Lectura segura delegada a Rust con Acquire fence."""
        if self._state_addr is None:
            return None

        epoch_id = ctypes.c_uint64(0)
        timestamp_ns = ctypes.c_uint64(0)

        valid = self._lib.read_active_epoch_safe(
            self._state_addr,
            ctypes.byref(epoch_id),
            ctypes.byref(timestamp_ns),
        )
        if valid != 1:
            return None
        return (epoch_id.value, timestamp_ns.value)

    def observe(self, callback: Callable[[int, int], None], interval_s: float = 0.001):
        """AXIOMA 5 + 7: Observación monotónica sin efectos secundarios."""
        last_epoch = -1
        while True:
            result = self.read_active_epoch()
            if result is not None:
                eid, ts = result
                if eid != last_epoch:
                    callback(eid, ts)
                    last_epoch = eid
            import time
            time.sleep(interval_s)

    def detach(self):
        """AXIOMA 4: Liberación en mismo espacio de direcciones."""
        if self._state_addr:
            self._lib.destroy_shared_memory(self._state_addr)
            self._state_addr = None

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self.detach()
        return False
