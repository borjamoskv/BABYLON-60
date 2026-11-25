"""
seqlock_swarm_ring0.py — Seqlock SPMC Bare-Metal de 64 Bytes para Enjambres
===========================================================================
Implementación C-ABI alineada a 64 bytes (Línea de Caché L1) para enjambres
masivos (02_EDIN_SWARMS / Anillo-0/1). Erradica contención RFO y torn reads.
"""

import ctypes
import mmap
import time
from typing import Optional, Tuple

MANIFEST_SIZE = 64


class SwarmTransitionManifest(ctypes.Structure):
    """Estructura C-ABI de 64 bytes indivisible (KUDURRU-64).
    Alineada rígidamente para evitar colisiones de línea de caché en ARM64.
    """

    sequence: int
    timestamp_ns: int
    cluster_id: int
    agent_id: int
    payload_hash: bytes
    flags: int
    _padding: bytes

    _fields_ = [
        ("sequence", ctypes.c_uint64),  # 8 bytes: Par = Reposo, Impar = Mutación
        ("timestamp_ns", ctypes.c_uint64),  # 8 bytes: Monotonic hardware nanoseconds
        ("cluster_id", ctypes.c_uint32),  # 4 bytes: ID del cluster ejecutor
        ("agent_id", ctypes.c_uint32),  # 4 bytes: ID del agente / transición
        ("payload_hash", ctypes.c_char * 16),  # 16 bytes: Hash truncado BLAKE3 / SHA-256
        ("flags", ctypes.c_uint32),  # 4 bytes: Bitflags de control y terminación
        ("_padding", ctypes.c_char * 20),  # 20 bytes: Relleno para cerrar exactamente a 64B
    ]


# Verificación de invariante de silicio en tiempo de carga
assert ctypes.sizeof(SwarmTransitionManifest) == MANIFEST_SIZE, (
    f"FRACTURA L1: SwarmTransitionManifest debe medir 64 bytes, mide {ctypes.sizeof(SwarmTransitionManifest)}"
)


class SeqlockSwarmChannel:
    """Canal de comunicación en memoria compartida Zero-Copy con protocolo Seqlock SPMC."""

    def __init__(self, buffer: Optional[bytearray] = None):
        self._raw: bytearray | mmap.mmap
        if buffer is None:
            self._raw = bytearray(MANIFEST_SIZE)
        else:
            assert len(buffer) >= MANIFEST_SIZE, "El buffer debe tener al menos 64 bytes"
            self._raw = buffer

        self.manifest = SwarmTransitionManifest.from_buffer(self._raw)

    @classmethod
    def from_mmap(cls, mm: mmap.mmap, offset: int = 0) -> "SeqlockSwarmChannel":
        """Instancia el canal directamente sobre una región mmap compartida entre procesos."""
        manifest = SwarmTransitionManifest.from_buffer(mm, offset)
        instance = cls.__new__(cls)
        instance._raw = mm
        instance.manifest = manifest
        return instance

    def write(self, cluster_id: int, agent_id: int, payload_hash: bytes, flags: int = 0) -> int:
        """Escritor único (Producer): Transiciona de secuencia Par -> Impar -> Par."""
        seq = self.manifest.sequence
        # 1. Bloqueo de mutación (secuencia impar)
        self.manifest.sequence = seq + 1

        # 2. Mutación de campos en reposo
        self.manifest.timestamp_ns = time.time_ns()
        self.manifest.cluster_id = cluster_id
        self.manifest.agent_id = agent_id

        # Copia acotada de 16 bytes
        truncated_hash = (payload_hash[:16]).ljust(16, b"\x00")
        self.manifest.payload_hash = truncated_hash
        self.manifest.flags = flags

        # 3. Cierre de mutación (secuencia par)
        new_seq = seq + 2
        self.manifest.sequence = new_seq
        return new_seq

    def read(self, max_retries: int = 1000) -> Optional[Tuple[int, int, int, bytes, int]]:
        """Lectores múltiples concurrentes (Consumers): Lectura lock-free sin RFO."""
        for _ in range(max_retries):
            seq0 = self.manifest.sequence
            # Si la secuencia es impar, hay una mutación activa en curso
            if seq0 % 2 != 0:
                continue

            # Lectura especulativa de los 64 bytes
            _ = self.manifest.timestamp_ns
            cid = self.manifest.cluster_id
            aid = self.manifest.agent_id
            phash = bytes(self.manifest.payload_hash)
            flags = self.manifest.flags

            # Verificación de invariante causal: el contador no debe haber mutado
            seq1 = self.manifest.sequence
            if seq0 == seq1:
                return (seq0, cid, aid, phash, flags)

        return None  # Retorna None si hubo contención persistente

    def is_locked(self) -> bool:
        """Indica si el Seqlock se encuentra actualmente en estado de mutación activa."""
        return (self.manifest.sequence % 2) != 0

    def close(self) -> None:
        """Aniquilación afín explícita de la vista C-ABI para permitir cierre limpio de mmap."""
        self.manifest = SwarmTransitionManifest()
        if isinstance(self._raw, mmap.mmap) and not self._raw.closed:
            self._raw.close()

    def __enter__(self) -> "SeqlockSwarmChannel":
        return self

    def __exit__(self, exc_type: object, exc_val: object, exc_tb: object) -> None:
        self.close()
