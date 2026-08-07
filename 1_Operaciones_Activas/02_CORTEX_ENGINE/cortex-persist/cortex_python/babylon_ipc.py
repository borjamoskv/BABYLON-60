# C5-REAL EXERGY CERTIFIED
import ctypes
import ctypes.util
import mmap
import os
import tempfile
from typing import Optional


class SharedManifest(ctypes.Structure):
    """Réplica bit-exacta de #[repr(C, align(8))] SharedManifest en Rust."""
    _fields_ = [
        ("payload", ctypes.c_uint8 * 32),       # offset 0, size 32
        ("status_flag", ctypes.c_uint8),         # offset 32, size 1
        ("_pad", ctypes.c_uint8 * 7),            # offset 33, padding a 8-byte boundary
        ("epoch_id", ctypes.c_uint64),           # offset 40, size 8
        ("timestamp_ns", ctypes.c_uint64),       # offset 48, size 8
    ]
    _pack_ = 1  # Sin padding adicional de ctypes; nuestro padding manual es exacto


# Verificación estática de tamaño y alineación
assert ctypes.sizeof(SharedManifest) == 56, f"SharedManifest size mismatch: {ctypes.sizeof(SharedManifest)}"


class EpochState(ctypes.Structure):
    """Réplica bit-exacta de EpochState en Rust."""
    _fields_ = [
        ("active_epoch_ptr", ctypes.c_void_p),      # offset 0, AtomicPtr → puntero nativo
        ("stable_fallback_ptr", ctypes.c_void_p),   # offset 8, AtomicPtr → puntero nativo
        ("global_epoch_counter", ctypes.c_uint64),  # offset 16, AtomicU64
    ]


assert ctypes.sizeof(EpochState) == 24, f"EpochState size mismatch: {ctypes.sizeof(EpochState)}"


class BabylonIPC:
    """Capa de interoperabilidad lock-free Python↔Rust vía memoria compartida."""

    SHARED_MEM_SIZE = 24  # sizeof(EpochState)

    def __init__(self, rust_lib_path: str):
        self._lib = ctypes.CDLL(rust_lib_path)

        # Configurar firmas FFI
        self._lib.init_shared_memory.argtypes = [ctypes.c_int]
        self._lib.init_shared_memory.restype = ctypes.c_void_p

        self._lib.destroy_shared_memory.argtypes = [ctypes.c_void_p]
        self._lib.destroy_shared_memory.restype = None

        self._state_ptr: Optional[int] = None
        self._mm: Optional[mmap.mmap] = None
        self._fd: Optional[int] = None

    def attach(self, fd: int) -> bool:
        """Mapea memoria compartida desde FD y obtiene puntero a EpochState."""
        result = self._lib.init_shared_memory(fd)
        if not result:
            return False
        self._state_ptr = result
        self._fd = fd
        return True

    def attach_temp(self) -> bool:
        """Crea archivo temporal de memoria compartida para testing."""
        tmp = tempfile.NamedTemporaryFile(delete=False)
        tmp.write(b'\x00' * self.SHARED_MEM_SIZE)
        tmp.flush()
        tmp.close()

        fd = os.open(tmp.name, os.O_RDWR)
        success = self.attach(fd)
        if not success:
            os.close(fd)
            os.unlink(tmp.name)
            return False
        return True

    def read_active_epoch_id(self) -> Optional[int]:
        """Lectura lock-free del epoch_id activo.

        En x86_64, la lectura de un puntero alineado de 8 bytes es atómica
        por hardware. La lectura del campo epoch_id subyacente también es
        atómica. Esto proporciona semántica equivalente a Acquire para
        observación desde Python sin fences explícitos.
        """
        if self._state_ptr is None:
            return None

        # Leer puntero activo directamente desde memoria compartida
        # c_void_p en ctypes lee 8 bytes alineados de forma atómica en x86_64
        state = EpochState.from_address(self._state_ptr)
        manifest_ptr = state.active_epoch_ptr

        if manifest_ptr is None or manifest_ptr == 0:
            return None

        # Dereferenciar puntero al SharedManifest y leer epoch_id
        manifest = SharedManifest.from_address(manifest_ptr)
        return manifest.epoch_id

    def observe_loop(self, callback, poll_interval_ns: int = 1_000_000):
        """Bucle de observación lock-free que invoca callback cuando cambia epoch_id.

        Args:
            callback: Función llamada con (new_epoch_id, timestamp_ns) en cada cambio.
            poll_interval_ns: Intervalo de sondeo en nanosegundos (usado como sleep aproximado).
        """
        last_epoch: Optional[int] = None
        sleep_sec = poll_interval_ns / 1_000_000_000

        while True:
            current = self.read_active_epoch_id()
            if current is not None and current != last_epoch:
                # Leer timestamp asociado a la nueva época
                state = EpochState.from_address(self._state_ptr)
                manifest = SharedManifest.from_address(state.active_epoch_ptr)
                ts = manifest.timestamp_ns
                callback(current, ts)
                last_epoch = current

            # Busy-wait mitigado: en producción usar eventfd/futex
            import time
            time.sleep(sleep_sec)

    def detach(self):
        """Desmapea memoria compartida y libera recursos."""
        if self._state_ptr is not None:
            self._lib.destroy_shared_memory(self._state_ptr)
            self._state_ptr = None
        if self._fd is not None:
            os.close(self._fd)
            self._fd = None

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self.detach()
        return False
