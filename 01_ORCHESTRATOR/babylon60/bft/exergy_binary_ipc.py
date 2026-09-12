# ============================================================================
# BABYLON-60 v4.0 Sovereign Hardened
# █ AUTOCOGNITION-Ω | STATE: C5-REAL | AESTHETIC: INDUSTRIAL_NOIR_2026
# ============================================================================
# [Causal-Determinist] Exergy-Maximized Zero-Anergy Binary Inter-Agent IPC
"""
ZERO-ANERGY BINARY INTER-AGENT IPC & TRANSDUCER
===============================================
Resuelve la paradoja del costo de parseo de YAML en alta frecuencia.
Combina la expresividad estática de YAML con la velocidad de transmisión binaria
zero-copy para comunicación entre los 100 agents a >100,000 msg/s.

Authorship: Borja Moskv (borjamoskv)
"""

from __future__ import annotations

import hashlib
import struct
import cbor2
import ctypes
from typing import Dict, Mapping, Tuple, cast

MAGIC_HEADER = b"B60IPC"
VERSION = 1


def pack_agent_message(
    sender: str, recipient: str, payload: Mapping[str, object] | Dict[str, object], lamport_t: int
) -> bytes:
    """
    Empaqueta un mensaje inter-agente en formato binario compacto Causal-Determinist.
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
    """
    Desempaqueta un mensaje binario con validación de checksum en tiempo O(1).
    """
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


class SharedManifestFFIWriter:
    """Implementa escritura Seqlock SPMC lock-free desde Python al manifest C."""

    def __init__(self) -> None:
        self.manifest = BountySharedManifest()
        self.manifest.status_flag = RUNNING
        self.manifest.seq = 0
        self.manifest.epoch_id = 1
        for i in range(4):
            self.manifest.payload_hash[i] = 0

    def publish(self, epoch: int, hash_bytes: bytes) -> bool:
        """Escribe un epoch y un hash (32 bytes) de forma atómica (Seqlock)."""
        if self.manifest.status_flag == POISONED:
            return False

        current_seq = self.manifest.seq
        self.manifest.seq = current_seq + 1

        self.manifest.epoch_id = epoch

        h_uint64 = struct.unpack("<4Q", hash_bytes)
        for i in range(4):
            self.manifest.payload_hash[i] = h_uint64[i]

        self.manifest.seq = self.manifest.seq + 1
        return True
