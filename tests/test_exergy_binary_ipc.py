# =============================================================================
# BABYLON-60 C5-REAL: TEST SUITE FOR EXERGY BINARY IPC & SEQLOCK SPMC (64B)
# =============================================================================
"""Test suite for binary inter-agent IPC, C-ABI dynamic linking to libbabylon60,
strict 64-byte alignment, Seqlock SPMC protocol, and fail-stop handling.
"""

from concurrent.futures import ThreadPoolExecutor
import hashlib
import os
import struct
import time
from typing import Dict

import pytest

from babylon60.bft.exergy_binary_ipc import (
    MAGIC_HEADER,
    POISONED,
    RUNNING,
    SharedManifestFFIWriter,
    find_babylon60_dylib,
    pack_agent_message,
    unpack_agent_message,
)


def test_pack_unpack_roundtrip() -> None:
    """Verifica empaquetado y desempaquetado binario sin pérdida causal."""
    sender = "AGENT-SENTINEL-01"
    recipient = "ORCHESTRATOR-RING0"
    payload: Dict[str, object] = {
        "event": "BOUNTY_INGEST",
        "bounty_id": "GH-VULN-2026-9912",
        "severity": 9.8,
        "tags": ["evm", "reentrancy", "zero-day"],
    }
    lamport_t = 1337

    frame = pack_agent_message(sender, recipient, payload, lamport_t)
    assert isinstance(frame, bytes)
    assert frame.startswith(MAGIC_HEADER)

    dec_sender, dec_recip, dec_payload, dec_lamport = unpack_agent_message(frame)
    assert dec_sender == sender
    assert dec_recip == recipient
    assert dec_payload == payload
    assert dec_lamport == lamport_t


def test_unpack_corruption_handling() -> None:
    """Certifica rechazo en tiempo O(1) de tramas corruptas sin pánico incontrolado."""
    # 1. Trama demasiado corta
    with pytest.raises(ValueError, match="Longitud binaria insuficiente"):
        unpack_agent_message(b"SHORT")

    # 2. Cabecera mágica inválida
    valid_frame = pack_agent_message("A", "B", {"k": "v"}, 1)
    bad_magic = b"X60IPC" + valid_frame[6:]
    with pytest.raises(ValueError, match="Cabecera magica invalida"):
        unpack_agent_message(bad_magic)

    # 3. Payload recortado
    truncated = valid_frame[:-2]
    with pytest.raises(ValueError, match="Integridad de payload"):
        unpack_agent_message(truncated)

    # 4. Checksum alterado (alterando un byte del payload manteniendo longitud)
    corrupted_body = bytearray(valid_frame)
    corrupted_body[25] ^= 0xFF
    with pytest.raises(ValueError, match="Checksum SHA3-256 invalido"):
        unpack_agent_message(bytes(corrupted_body))


def test_find_babylon60_dylib() -> None:
    """Verifica la resolución determinista de libbabylon60 compilada por Cargo."""
    dylib_path = find_babylon60_dylib()
    if dylib_path is None:
        pytest.skip("libbabylon60 no encontrada en target/debug o target/release (requiere cargo build previo)")
    assert os.path.exists(dylib_path)

    # Test con variable de entorno explícita
    old_env = os.environ.get("BABYLON60_DYLIB_PATH")
    try:
        os.environ["BABYLON60_DYLIB_PATH"] = dylib_path
        assert find_babylon60_dylib() == dylib_path
    finally:
        if old_env is not None:
            os.environ["BABYLON60_DYLIB_PATH"] = old_env
        else:
            os.environ.pop("BABYLON60_DYLIB_PATH", None)


def test_native_shared_manifest_write_read_cycle() -> None:
    """Verifica la vinculación C-ABI nativa, alineación a 64B y ciclo Seqlock SPMC."""
    if find_babylon60_dylib() is None:
        pytest.skip("libbabylon60 no compilada en target/ (requiere cargo build previo)")
    writer = SharedManifestFFIWriter()
    assert writer.is_native is True, "El writer no se vinculó a la librería nativa C-ABI"
    assert writer.is_halted() is False

    # Verificar alineación a 64 bytes
    assert writer._ptr.value is not None
    assert writer._ptr.value % 64 == 0, f"El puntero a SharedManifest {writer._ptr.value} no está alineado a 64 bytes"

    # Verificar ciclo de escritura y lectura atómica
    for epoch in range(1, 101):
        payload_hash = hashlib.sha3_256(f"epoch_hash_{epoch}".encode()).digest()
        ok = writer.publish(epoch, payload_hash)
        assert ok is True

        read_res = writer.read()
        assert read_res is not None
        read_epoch, read_hash = read_res
        assert read_epoch == epoch
        assert read_hash == payload_hash

    # Verificar estructura física (64B)
    assert writer.manifest.status_flag == RUNNING
    assert writer.manifest.epoch_id == 100
    assert writer.manifest.seq % 2 == 0  # Paridad Seqlock: seq debe ser par en reposo


def test_python_fallback_shared_manifest() -> None:
    """Verifica el fallback determinista en memoria cuando no hay dylib nativa."""
    writer = SharedManifestFFIWriter(dylib_path="/tmp/nonexistent_libbabylon60.dylib")
    assert writer.is_native is False
    assert writer.is_halted() is False

    for epoch in range(1, 25):
        payload_hash = hashlib.sha3_256(f"fallback_{epoch}".encode()).digest()
        ok = writer.publish(epoch, payload_hash)
        assert ok is True

        read_res = writer.read()
        assert read_res is not None
        read_epoch, read_hash = read_res
        assert read_epoch == epoch
        assert read_hash == payload_hash

    assert writer.manifest.epoch_id == 24
    assert writer.manifest.seq % 2 == 0


def test_fail_stop_poisoned_state() -> None:
    """Certifica el protocolo Fail-Stop / POISONED (INV-4) tanto en nativo como fallback."""
    # 1. Modo Nativo
    native_writer = SharedManifestFFIWriter()
    if native_writer.is_native:
        assert native_writer.is_halted() is False
        native_writer.manifest.status_flag = POISONED
        assert native_writer.is_halted() is True
        assert native_writer.publish(999, b"\x00" * 32) is False
        assert native_writer.read() is None

    # 2. Modo Fallback
    fallback_writer = SharedManifestFFIWriter(dylib_path="/tmp/nonexistent.dylib")
    assert fallback_writer.is_native is False
    assert fallback_writer.is_halted() is False
    fallback_writer.manifest.status_flag = POISONED
    assert fallback_writer.is_halted() is True
    assert fallback_writer.publish(999, b"\x00" * 32) is False
    assert fallback_writer.read() is None


def test_concurrent_spmc_seqlock_simulation() -> None:
    """Stress test concurrente: 1 escritor y 3 lectores simultáneos certificando cero lecturas corruptas."""
    writer = SharedManifestFFIWriter()
    num_updates = 500
    stop_flag = False

    hashes_published = {}
    for i in range(1, num_updates + 1):
        hashes_published[i] = hashlib.sha3_256(struct.pack(">Q", i)).digest()

    def reader_task(reader_id: int) -> int:
        valid_reads = 0
        while not stop_flag:
            res = writer.read()
            if res is not None:
                ep, h = res
                if ep in hashes_published:
                    # El hash debe corresponder exactamente al epoch leído (cero desgarros)
                    assert h == hashes_published[ep], f"Lectura desgarrada en lector {reader_id} para epoch {ep}"
                    valid_reads += 1
            time.sleep(0.0001)
        return valid_reads

    with ThreadPoolExecutor(max_workers=4) as executor:
        futures = [executor.submit(reader_task, r_id) for r_id in range(3)]

        for ep in range(1, num_updates + 1):
            writer.publish(ep, hashes_published[ep])
            time.sleep(0.0002)

        time.sleep(0.01)
        stop_flag = True

        for f in futures:
            reads = f.result()
            assert reads > 0, "Un lector concurrente no logró registrar lecturas válidas"
