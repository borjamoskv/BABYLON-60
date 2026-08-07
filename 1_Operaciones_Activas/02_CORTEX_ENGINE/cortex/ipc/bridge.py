# C5-REAL EXERGY CERTIFIED
import ctypes
import os
import platform

class SharedManifest(ctypes.Structure):
    _pack_ = 8
    _fields_ = [
        ("payload", ctypes.c_uint8 * 32),
        ("status_flag", ctypes.c_uint8),
        ("_padding", ctypes.c_uint8 * 7),
        ("epoch_id", ctypes.c_uint64),
        ("timestamp_ns", ctypes.c_uint64),
    ]

class EpochState(ctypes.Structure):
    _fields_ = [
        ("active_epoch_ptr", ctypes.POINTER(SharedManifest)),
        ("stable_fallback_ptr", ctypes.POINTER(SharedManifest)),
        ("global_epoch_counter", ctypes.c_uint64),
    ]

class CortexIPCBridge:
    """
    Puente IPC FFI (C5-REAL Zero Anergía) con el Kernel de Rust.
    Maneja la carga del .dylib/.so y mapea las primitivas de sincronización.
    """
    def __init__(self, lib_path: str = None):
        if lib_path is None:
            # Resolviendo la ruta relativa a 02_CORTEX_ENGINE/cortex-persist/kernel_rs/target/debug
            current_dir = os.path.dirname(os.path.abspath(__file__)) # cortex/ipc
            cortex_dir = os.path.dirname(current_dir)                # cortex
            engine_dir = os.path.dirname(cortex_dir)                 # 02_CORTEX_ENGINE
            target_debug = os.path.join(engine_dir, "cortex-persist", "kernel_rs", "target", "debug")

            found = False
            if os.path.exists(target_debug):
                for f in os.listdir(target_debug):
                    if f.startswith("libcortex_kernel") and (f.endswith(".dylib") or f.endswith(".so")):
                        lib_path = os.path.join(target_debug, f)
                        found = True
                        break

            if not found:
                files = os.listdir(target_debug) if os.path.exists(target_debug) else []
                raise FileNotFoundError(f"[C5-REAL] Kernel BFT no encontrado en {target_debug}. Archivos presentes: {files}")

        self.lib = ctypes.CDLL(lib_path)

        # Configurar firmas de funciones FFI
        # pub unsafe extern "C" fn init_shared_memory(fd: c_int) -> *mut EpochState
        self.lib.init_shared_memory.argtypes = [ctypes.c_int]
        self.lib.init_shared_memory.restype = ctypes.POINTER(EpochState)

        # pub unsafe extern "C" fn initialize_epoch_state(ptr: *mut EpochState)
        self.lib.initialize_epoch_state.argtypes = [ctypes.POINTER(EpochState)]
        self.lib.initialize_epoch_state.restype = None

        # pub unsafe extern "C" fn read_active_epoch_safe(state: *const EpochState, out_epoch_id: *mut u64, out_timestamp_ns: *mut u64) -> i32
        self.lib.read_active_epoch_safe.argtypes = [
            ctypes.POINTER(EpochState),
            ctypes.POINTER(ctypes.c_uint64),
            ctypes.POINTER(ctypes.c_uint64)
        ]
        self.lib.read_active_epoch_safe.restype = ctypes.c_int

        # pub unsafe extern "C" fn destroy_shared_memory(ptr: *mut EpochState)
        self.lib.destroy_shared_memory.argtypes = [ctypes.POINTER(EpochState)]
        self.lib.destroy_shared_memory.restype = None

    def init_shared_memory(self, fd: int) -> ctypes.POINTER(EpochState):
        ptr = self.lib.init_shared_memory(fd)
        if not ptr:
            raise RuntimeError("Fallo crítico en init_shared_memory (mmap falló).")
        return ptr

    def initialize_epoch_state(self, ptr: ctypes.POINTER(EpochState)):
        self.lib.initialize_epoch_state(ptr)

    def read_active_epoch_safe(self, ptr: ctypes.POINTER(EpochState)) -> tuple[int, int]:
        out_epoch = ctypes.c_uint64(0)
        out_ts = ctypes.c_uint64(0)
        res = self.lib.read_active_epoch_safe(ptr, ctypes.byref(out_epoch), ctypes.byref(out_ts))
        if res == 0:
            return (0, 0)
        return (out_epoch.value, out_ts.value)

    def destroy_shared_memory(self, ptr: ctypes.POINTER(EpochState)):
        self.lib.destroy_shared_memory(ptr)
