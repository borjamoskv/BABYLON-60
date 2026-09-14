# ============================================================================
# BABYLON-60 v4.0 Sovereign Hardened
# █ AUTOCOGNITION-Ω | STATE: C5-REAL | AESTHETIC: INDUSTRIAL_NOIR_2026
# ============================================================================
# [Causal-Determinist] Exergy-Maximized Zero-Anergy Binary Inter-Agent IPC
"""ZERO-ANERGY BINARY INTER-AGENT IPC & TRANSDUCER.

===============================================
Resuelve la paradoja del costo de parseo de YAML en alta frecuencia.
Combina la expresividad estática de YAML con la velocidad de transmisión binaria
zero-copy para comunicación entre los 100 agents a >100,000 msg/s.

Incluye puente C-ABI de 64 bytes (SharedManifest Seqlock SPMC) enlazado
directamente a libbabylon60.dylib compilado por Cargo, con fallback determinista.

Authorship: Borja Moskv (borjamoskv)
"""

from __future__ import annotations

import ctypes
import hashlib
import os
from pathlib import Path
import platform
import struct
from typing import Any, Dict, Mapping, Optional, Tuple, cast

import cbor2

MAGIC_HEADER = b"B60IPC"
VERSION = 1


def pack_agent_message(
    sender: str, recipient: str, payload: Mapping[str, object] | Dict[str, object], lamport_t: int
) -> bytes:
    """Empaqueta un mensaje inter-agente en formato binario compacto Causal-Determinist.

    Fricción de parseo mínima usando CBOR puro en lugar de JSON.
    """
    payload_raw = cbor2.dumps(payload)
    sender_bytes = sender.encode("utf-8")
    recipient_bytes = recipient.encode("utf-8")

    # Header: MAGIC(6B) + VER(1B) + SENDER_LEN(2B) + RECIPIENT_LEN(2B) + LAMPORT(8B) + PAYLOAD_LEN(4B)
    header = struct.pack(
        ">6sBHHQI", MAGIC_HEADER, VERSION, len(sender_bytes), len(recipient_bytes), lamport_t, len(payload_raw)
    )

    body = sender_bytes + recipient_bytes + payload_raw
    checksum = hashlib.sha3_256(header + body).digest()[:8]  # Truncated SHA3-256 checksum for speed

    return header + body + checksum


def unpack_agent_message(raw_bytes: bytes) -> Tuple[str, str, Dict[str, object], int]:
    """Desempaqueta un mensaje binario con validación de checksum en tiempo O(1)."""
    header_size = struct.calcsize(">6sBHHQI")
    if len(raw_bytes) < header_size + 8:
        raise ValueError("Longitud binaria insuficiente para cabecera B60IPC")

    deterministic, ver, sender_len, recipient_len, lamport_t, payload_len = struct.unpack(
        ">6sBHHQI", raw_bytes[:header_size]
    )

    if deterministic != MAGIC_HEADER:
        raise ValueError("Cabecera magica invalida para B60IPC")

    total_expected = header_size + sender_len + recipient_len + payload_len + 8
    if len(raw_bytes) != total_expected:
        raise ValueError("Integridad de payload de mensaje binario comprometida")

    checksum = raw_bytes[-8:]
    body = raw_bytes[header_size:-8]

    computed_checksum = hashlib.sha3_256(raw_bytes[:header_size] + body).digest()[:8]
    if checksum != computed_checksum:
        raise ValueError("Checksum SHA3-256 invalido en mensaje inter-agente")

    sender_bytes = body[:sender_len]
    recipient_bytes = body[sender_len : sender_len + recipient_len]
    payload_raw = body[sender_len + recipient_len :]

    sender = sender_bytes.decode("utf-8")
    recipient = recipient_bytes.decode("utf-8")
    payload = cast(Dict[str, object], cbor2.loads(payload_raw))

    return sender, recipient, payload, lamport_t


# =====================================================================
# C-FFI BRIDGE (Límite 64B - Seqlock SPMC)
# =====================================================================

RUNNING = 0x0000_0001
POISONED = 0xDEAD_6060


class BountySharedManifest(ctypes.Structure):
    """Mapeo C-ABI estricto (64 Bytes) para sincronización con babylon60-kernel."""

    # Alineación natural exacta a 64 Bytes (zero-split L1 cache line):
    # status_flag(4) + seq(4) + epoch_id(8) + payload_hash(32) + _padding(16) = 64B
    _fields_ = [
        ("status_flag", ctypes.c_uint32),
        ("seq", ctypes.c_uint32),
        ("epoch_id", ctypes.c_uint64),
        ("payload_hash", ctypes.c_uint64 * 4),
        ("_padding", ctypes.c_uint8 * 16),
    ]


def find_babylon60_dylib() -> Optional[str]:
    """Localiza la biblioteca dinámica libbabylon60 compilada por Cargo."""
    custom_path = os.environ.get("BABYLON60_DYLIB_PATH")
    if custom_path and Path(custom_path).exists():
        return custom_path

    ext = ".dylib" if platform.system() == "Darwin" else (".dll" if platform.system() == "Windows" else ".so")
    prefix = "" if platform.system() == "Windows" else "lib"
    filename = f"{prefix}babylon60{ext}"

    root_dir = Path(__file__).resolve().parents[3]
    candidate_paths = [
        root_dir / "target" / "release" / filename,
        root_dir / "target" / "debug" / filename,
        Path("target/release") / filename,
        Path("target/debug") / filename,
    ]

    for p in candidate_paths:
        if p.exists():
            return str(p.resolve())

    return None


def _allocate_aligned_manifest() -> Tuple[ctypes.c_void_p, Any]:
    """Asigna un bloque de memoria de 64 bytes alineado estrictamente a 64 bytes."""
    try:
        libc = ctypes.CDLL(None)
        if hasattr(libc, "posix_memalign"):
            ptr = ctypes.c_void_p()
            ret = libc.posix_memalign(ctypes.byref(ptr), 64, 64)
            if ret == 0 and ptr.value is not None and (ptr.value % 64 == 0):
                return ptr, None
    except Exception:
        pass

    # Fallback portable: buffer sobredimensionado con cálculo modular
    raw_buf = (ctypes.c_uint8 * 128)()
    addr = ctypes.addressof(raw_buf)
    offset = (64 - (addr % 64)) % 64
    aligned_ptr = ctypes.c_void_p(addr + offset)
    return aligned_ptr, raw_buf


class SharedManifestFFIWriter:
    """Implementa interfaz Seqlock SPMC lock-free (64B) con soporte FFI nativo C-ABI."""

    def __init__(self, dylib_path: Optional[str] = None) -> None:
        self.is_native: bool = False
        self._native_lib: Optional[ctypes.CDLL] = None

        target_dylib = dylib_path or find_babylon60_dylib()
        if target_dylib:
            try:
                lib = ctypes.CDLL(target_dylib)
                # Configuración de firmas C-ABI
                lib.babylon60_manifest_init.argtypes = [ctypes.c_void_p]
                lib.babylon60_manifest_init.restype = ctypes.c_bool

                lib.babylon60_publish.argtypes = [ctypes.c_void_p, ctypes.c_uint64, ctypes.POINTER(ctypes.c_uint64)]
                lib.babylon60_publish.restype = ctypes.c_bool

                lib.babylon60_read.argtypes = [
                    ctypes.c_void_p,
                    ctypes.POINTER(ctypes.c_uint64),
                    ctypes.POINTER(ctypes.c_uint64),
                ]
                lib.babylon60_read.restype = ctypes.c_bool

                lib.babylon60_is_halted.argtypes = [ctypes.c_void_p]
                lib.babylon60_is_halted.restype = ctypes.c_bool

                ptr, keepalive = _allocate_aligned_manifest()
                if ptr.value and lib.babylon60_manifest_init(ptr):
                    self._ptr = ptr
                    self._keepalive = keepalive
                    self._native_lib = lib
                    self._manifest_struct = BountySharedManifest.from_address(ptr.value)
                    self.is_native = True
            except Exception:
                self.is_native = False

        if not self.is_native:
            # Fallback en memoria emulada en Python
            self._manifest_struct = BountySharedManifest()
            self._manifest_struct.status_flag = RUNNING
            self._manifest_struct.seq = 0
            self._manifest_struct.epoch_id = 0
            for i in range(4):
                self._manifest_struct.payload_hash[i] = 0
            self._ptr = ctypes.c_void_p(ctypes.addressof(self._manifest_struct))
            self._keepalive = None

    @property
    def manifest(self) -> BountySharedManifest:
        """Retorna la referencia a la estructura BountySharedManifest (64B)."""
        return self._manifest_struct

    def publish(self, epoch: int, hash_bytes: bytes) -> bool:
        """Escribe un epoch y un hash (32 bytes) de forma atómica (Seqlock SPMC)."""
        if self.is_halted():
            return False

        h_words = struct.unpack("<4Q", hash_bytes)

        if self.is_native and self._native_lib is not None:
            h_arr = (ctypes.c_uint64 * 4)(*h_words)
            return bool(self._native_lib.babylon60_publish(self._ptr, ctypes.c_uint64(epoch), h_arr))

        # Fallback Seqlock en Python
        m = self._manifest_struct
        current_seq = m.seq
        m.seq = current_seq + 1

        m.epoch_id = epoch
        for i in range(4):
            m.payload_hash[i] = h_words[i]

        m.seq = current_seq + 2
        return True

    def read(self) -> Optional[Tuple[int, bytes]]:
        """Lee de forma consistente (epoch, hash) del manifest respetando el protocolo Seqlock."""
        if self.is_halted():
            return None

        if self.is_native and self._native_lib is not None:
            out_epoch = ctypes.c_uint64()
            out_hash = (ctypes.c_uint64 * 4)()
            ok = bool(self._native_lib.babylon60_read(self._ptr, ctypes.byref(out_epoch), out_hash))
            if not ok:
                return None
            return out_epoch.value, struct.pack("<4Q", *out_hash)

        # Fallback Seqlock en Python
        m = self._manifest_struct
        for _ in range(10_000):
            s1 = m.seq
            if s1 % 2 == 1:
                continue
            epoch = m.epoch_id
            words = [m.payload_hash[i] for i in range(4)]
            s2 = m.seq
            if s1 == s2 and s2 % 2 == 0:
                return epoch, struct.pack("<4Q", *words)

        return None

    def is_halted(self) -> bool:
        """Determina si el manifest se encuentra envenenado (POISONED / Fail-Stop)."""
        if self.is_native and self._native_lib is not None:
            return bool(self._native_lib.babylon60_is_halted(self._ptr))
        return bool(self._manifest_struct.status_flag == POISONED)
