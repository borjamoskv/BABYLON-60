# C5_IGNORE_NESTING
# C5-REAL EXERGY CERTIFIED
import ctypes
import os
import hashlib
import time

class ManifestStatus:
    IDLE = 0
    READY = 1
    VALIDATING = 2
    ACTIVE = 3
    RETIRED = 4
    QUARANTINE = 5

class HaltReason:
    DIGEST_MISMATCH = 0
    CAS_CONTENTION = 1
    NULL_POINTER = 2
    FALLBACK_UNAVAILABLE = 3
    GEOMETRIC_CAP_EXCEEDED = 4
    TRACE_CHAIN_VIOLATION = 5
    ACTIVE_READERS_NOT_DRAINED = 6
    VARENTROPY_LIMIT_EXCEEDED = 7
    RLHF_BREAKTHROUGH = 8

# Definir la estructura SharedManifest (layout en C, alineado a 8 bytes)
class SharedManifest(ctypes.Structure):
    _pack_ = 8
    _fields_ = [
        ("payload", ctypes.c_uint8 * 32),
        ("status_flag", ctypes.c_uint8),
        # 3 bytes de padding automático del compilador C para alinear el u32 a 4 bytes
        ("varentropy_bps", ctypes.c_uint32),
        ("active_readers", ctypes.c_size_t),
        ("epoch_id", ctypes.c_uint64),
        ("timestamp_ns", ctypes.c_uint64),
    ]

# Estructura opaca del Kernel State (EpochState)
class EpochState(ctypes.Structure):
    pass

class C5RealFFIBridge:
    def __init__(self, workspace_root: str):
        # Resolver la ruta de la librería compilada dinámica (.dylib en mac / .so en linux)
        release_path = os.path.join(workspace_root, "target", "release", "libcortex_kernel.dylib")
        debug_path = os.path.join(workspace_root, "target", "debug", "libcortex_kernel.dylib")

        candidates = []
        if os.path.exists(release_path):
            candidates.append((os.path.getmtime(release_path), release_path))
        if os.path.exists(debug_path):
            candidates.append((os.path.getmtime(debug_path), debug_path))

        if not candidates:
            raise FileNotFoundError(
                "No se encuentra libcortex_kernel.dylib. \n"
                "Por favor, compila el kernel de Rust antes de iniciar el puente FFI."
            )

        candidates.sort(key=lambda x: x[0], reverse=True)
        lib_path = candidates[0][1]

        self.lib = ctypes.CDLL(lib_path)

        # Configurar firmas de funciones (AXIOMA FFI)

        # init_shared_memory(fd: c_int) -> *mut EpochState
        self.lib.init_shared_memory.argtypes = [ctypes.c_int]
        self.lib.init_shared_memory.restype = ctypes.POINTER(EpochState)

        # initialize_epoch_state(ptr: *mut EpochState)
        self.lib.initialize_epoch_state.argtypes = [ctypes.POINTER(EpochState)]
        self.lib.initialize_epoch_state.restype = None

        # commit_epoch_transition(state, manifest, digest, raw_text, text_len) -> i64
        self.lib.commit_epoch_transition.argtypes = [
            ctypes.POINTER(EpochState),
            ctypes.POINTER(SharedManifest),
            ctypes.POINTER(ctypes.c_uint8 * 32),
            ctypes.POINTER(ctypes.c_uint8),
            ctypes.c_size_t
        ]
        self.lib.commit_epoch_transition.restype = ctypes.c_int64

        # Simular asignación de memoria compartida anónima (fd = -1) para testing local
        self.state_ptr = self.lib.init_shared_memory(-1)
        if not self.state_ptr:
            raise RuntimeError("Fallo al inicializar la memoria compartida (mmap failed).")

        self.lib.initialize_epoch_state(self.state_ptr)
        self.epoch_counter = 1

    def inject_to_ring0(self, generated_text: str, varentropy_bps: int = 0) -> bool:
        """
        Inyecta el texto generado en la memoria compartida y fuerza la transición atómica.
        Retorna True si el Kernel lo acepta (Active), False si lo guillotina (Quarantine).
        """
        text_bytes = generated_text.encode('utf-8')
        text_len = len(text_bytes)

        # 1. Crear el array C con el texto crudo
        raw_text_c = (ctypes.c_uint8 * text_len)(*text_bytes)

        # 2. Calcular el Digest SHA-256
        sha256 = hashlib.sha256(text_bytes).digest()
        digest_c = (ctypes.c_uint8 * 32)(*sha256)

        # 3. Preparar el SharedManifest candidato alineado estrictamente a 64 bytes
        buf = bytearray(ctypes.sizeof(SharedManifest) + 64)
        addr = ctypes.addressof((ctypes.c_char * len(buf)).from_buffer(buf))
        offset = (64 - (addr % 64)) % 64
        aligned_addr = addr + offset

        manifest = SharedManifest.from_address(aligned_addr)
        for i in range(32):
            manifest.payload[i] = sha256[i]

        manifest.status_flag = ManifestStatus.READY
        manifest.varentropy_bps = varentropy_bps
        manifest.active_readers = 0
        manifest.epoch_id = self.epoch_counter
        manifest.timestamp_ns = int(time.monotonic() * 1e9)

        self.epoch_counter += 1

        # 4. Invocar el CAS Rollback (Commit Transition) en Rust
        result = self.lib.commit_epoch_transition(
            self.state_ptr,
            ctypes.byref(manifest),
            ctypes.byref(digest_c),
            raw_text_c,
            text_len
        )

        if result > 0:
            print(f"✅ [KERNEL RING-0] Época {result} ACTIVA. (Transición Exitosa).")
            return True
        else:
            halt_reason = -result
            reason_str = "Desconocida"
            if halt_reason == HaltReason.DIGEST_MISMATCH: reason_str = "Digest Mismatch (Corrupción criptográfica)"
            elif halt_reason == HaltReason.VARENTROPY_LIMIT_EXCEEDED: reason_str = "Límite de Varentropía CUSUM excedido (Colapso Termodinámico)"
            elif halt_reason == HaltReason.RLHF_BREAKTHROUGH: reason_str = "Anergía Detectada / Fricción Léxica (RLHF Breakthrough)"
            elif halt_reason == HaltReason.GEOMETRIC_CAP_EXCEEDED: reason_str = "Vector Geométrico fuera del Cap Contractual"
            elif halt_reason == HaltReason.CAS_CONTENTION: reason_str = "Contención CAS concurrente"

            print(f"❌ [KERNEL RING-0] EPISTEMIC HALT (Cuarentena). Razón: {reason_str}")
            return False
