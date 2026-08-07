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
            # Búsqueda ascendente determinista hacia la raíz del repositorio (donde reside Cargo.toml o .git)
            curr = os.path.abspath(__file__)
            workspace_dir = None
            for _ in range(6):
                curr = os.path.dirname(curr)
                if os.path.exists(os.path.join(curr, "Cargo.toml")) or os.path.exists(os.path.join(curr, ".git")):
                    workspace_dir = curr
                    break

            search_paths = []
            if workspace_dir:
                search_paths.append(os.path.join(workspace_dir, "target", "debug"))
                search_paths.append(os.path.join(workspace_dir, "target", "release"))

            # Paths de fallback
            search_paths.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "cortex-persist", "kernel_rs", "target", "debug")))

            found = False
            for path in search_paths:
                if os.path.exists(path):
                    for f in os.listdir(path):
                        if f.startswith("libcortex_kernel") and (f.endswith(".dylib") or f.endswith(".so") or f.endswith(".dll")):
                            lib_path = os.path.join(path, f)
                            found = True
                            break
                if found:
                    break

            if not found:
                raise FileNotFoundError(f"[C5-REAL] Kernel BFT no encontrado en workspace. Rutas buscadas: {search_paths}")

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
