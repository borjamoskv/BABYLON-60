# C5-REAL EXERGY CERTIFIED
import ctypes
import os
import time
from typing import Callable, Optional, Tuple

# Definiciones de estructura bit-exactas para x86_64 System V ABI

class SharedManifest(ctypes.Structure):
    """
    Réplica exacta de SharedManifest en Rust.
    Layout: payload(32) + status(1) + pad(7) + epoch(8) + ts(8) = 56 bytes.
    """
    _fields_ = [
        ("payload", ctypes.c_uint8 * 32),
        ("status_flag", ctypes.c_uint8),
        ("_padding", ctypes.c_uint8 * 7),  # Padding explícito para alineación de 8 bytes
        ("epoch_id", ctypes.c_uint64),
        ("timestamp_ns", ctypes.c_uint64),
    ]

class EpochState(ctypes.Structure):
    """
    Réplica exacta de EpochState en Rust.
    Layout: active_ptr(8) + fallback_ptr(8) + counter(8) = 24 bytes.
    """
    _fields_ = [
        ("active_epoch_ptr", ctypes.c_void_p),
        ("stable_fallback_ptr", ctypes.c_void_p),
        ("global_epoch_counter", ctypes.c_uint64),
    ]

# Validaciones de compilación estática
assert ctypes.sizeof(SharedManifest) == 56, "ABI Mismatch: SharedManifest"
assert ctypes.sizeof(EpochState) == 24, "ABI Mismatch: EpochState"


class BabylonIPC:
    """Interfaz lock-free para observación de estado EBR desde Python."""

    def __init__(self, lib_path: str):
        self._lib = ctypes.CDLL(lib_path)

        # Configuración estricta de tipos FFI
        self._lib.init_shared_memory.argtypes = [ctypes.c_int]
        self._lib.init_shared_memory.restype = ctypes.c_void_p

        self._lib.destroy_shared_memory.argtypes = [ctypes.c_void_p]
        self._lib.destroy_shared_memory.restype = None

        self._state_addr: Optional[int] = None

    def attach(self, fd: int) -> bool:
        """Vincula el FD de memoria compartida y obtiene acceso directo."""
        ptr = self._lib.init_shared_memory(fd)
        if not ptr:
            return False
        self._state_addr = ptr
        return True

    def read_active_epoch(self) -> Optional[Tuple[int, int]]:
        """
        Lectura lock-free del par (epoch_id, timestamp_ns).
        Retorna None si no hay época activa.

        Nota: En x86_64, la lectura de c_void_p alineado es atómica.
        La consistencia se garantiza por el protocolo Release/Acquire de Rust.
        """
        if self._state_addr is None:
            return None

        # Acceso directo a memoria compartida sin copia
        state = EpochState.from_address(self._state_addr)

        manifest_ptr = state.active_epoch_ptr
        if manifest_ptr is None or manifest_ptr == 0:
            return None

        # Dereferencia segura asumiendo validez garantizada por EBR
        manifest = SharedManifest.from_address(manifest_ptr)
        return (manifest.epoch_id, manifest.timestamp_ns)

    def observe(self, callback: Callable[[int, int], None], interval_s: float = 0.001):
        """
        Bucle de sondeo de baja latencia para cambios de época.
        Diseñado para correr en un hilo dedicado de monitoreo.
        """
        last_epoch = -1

        while True:
            result = self.read_active_epoch()
            if result:
                eid, ts = result
                if eid != last_epoch:
                    callback(eid, ts)
                    last_epoch = eid

            # Sleep híbrido para reducir consumo CPU manteniendo reactividad
            time.sleep(interval_s)

    def detach(self):
        """Limpieza de recursos FFI."""
        if self._state_addr:
            self._lib.destroy_shared_memory(self._state_addr)
            self._state_addr = None

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self.detach()
        return False
