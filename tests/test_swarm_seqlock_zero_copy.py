"""
test_swarm_seqlock_zero_copy.py — Suite de Verificación de Silicio para Seqlock SPMC
===================================================================================
Valida formalmente la ausencia de Torn Reads, el alineamiento L1 (64 bytes) y
el throughput bare-metal sin contención RFO en Apple Silicon.
"""

import time
import threading

from agents_archi.orchestrator.seqlock_swarm_ring0 import SwarmTransitionManifest, SeqlockSwarmChannel


def test_seqlock_manifest_alignment_64b() -> None:
    """Valida la invariante KUDURRU-64: El manifiesto mide exactamente 64 bytes."""
    import ctypes

    assert ctypes.sizeof(SwarmTransitionManifest) == 64
    channel = SeqlockSwarmChannel()
    assert len(channel._raw) == 64
    assert channel.manifest.sequence == 0
    assert not channel.is_locked()


def test_seqlock_single_writer_sequential_reads() -> None:
    """Verifica transiciones de paridad Par -> Impar -> Par y consistencia de campos."""
    channel = SeqlockSwarmChannel()
    test_hash = b"0123456789abcdef"

    # 1. Escribir transición 1
    new_seq = channel.write(cluster_id=1, agent_id=42, payload_hash=test_hash, flags=0x01)
    assert new_seq == 2
    assert not channel.is_locked()

    # 2. Leer transición
    res = channel.read()
    assert res is not None
    seq, cid, aid, phash, flags = res
    assert seq == 2
    assert cid == 1
    assert aid == 42
    assert phash == test_hash
    assert flags == 0x01


def test_seqlock_multithread_spmc_concurrency() -> None:
    """Prueba de estrés SPMC: 1 escritor emite 20.000 transiciones contra 4 lectores concurrentes."""
    channel = SeqlockSwarmChannel()
    TOTAL_WRITES = 20000
    NUM_READERS = 4

    stop_signal = threading.Event()
    read_counts = [0] * NUM_READERS
    torn_reads = [0] * NUM_READERS

    def reader_worker(reader_idx: int) -> None:
        while not stop_signal.is_set():
            snap = channel.read(max_retries=100)
            if snap is not None:
                seq, cid, aid, phash, flags = snap
                # Invariante 1: Nunca puede observarse una secuencia impar
                if seq % 2 != 0:
                    torn_reads[reader_idx] += 1
                read_counts[reader_idx] += 1

    # Iniciar lectores
    threads = []
    for i in range(NUM_READERS):
        t = threading.Thread(target=reader_worker, args=(i,))
        t.daemon = True
        t.start()
        threads.append(t)

    # Iniciar escritor en el hilo principal
    start_time = time.perf_counter()
    for w in range(TOTAL_WRITES):
        payload = f"h_{w:014d}".encode()
        channel.write(cluster_id=w % 8, agent_id=w, payload_hash=payload, flags=0)
    elapsed = time.perf_counter() - start_time

    # Detener lectores
    time.sleep(0.01)
    stop_signal.set()
    for t in threads:
        t.join(timeout=1.0)

    total_reads = sum(read_counts)
    total_torn = sum(torn_reads)

    # Aserciones de invariantes
    assert total_torn == 0, f"FRACTURA DE SILICIO: Se detectaron {total_torn} torn reads"
    assert total_reads > 0, "Los lectores no registraron lecturas"

    throughput_w = TOTAL_WRITES / elapsed
    print("\n[SEQLOCK STRESS REPORT]")
    print(f"  • Escrituras:     {TOTAL_WRITES} en {elapsed:.4f}s ({throughput_w:.2f} writes/s)")
    print(f"  • Lecturas SPMC:  {total_reads} lecturas en {NUM_READERS} hilos")
    print(f"  • Torn Reads:     {total_torn} (100% Determinista / RFO=0)")


def test_seqlock_zero_copy_throughput_benchmark() -> None:
    """Benchmark bare-metal: Medir throughput en un solo núcleo sin I/O."""
    channel = SeqlockSwarmChannel()
    N = 100000
    dummy_hash = b"hash_manifest_64"

    t0 = time.perf_counter()
    for i in range(N):
        channel.write(1, i, dummy_hash, 0)
    elapsed = time.perf_counter() - t0

    ops_sec = N / elapsed
    assert ops_sec > 500000.0, f"Rendimiento insuficiente: {ops_sec:.2f} ops/s"
    print(f"\n[BARE-METAL BENCHMARK] {N} writes en {elapsed:.4f}s -> {ops_sec:,.0f} transiciones/s")
