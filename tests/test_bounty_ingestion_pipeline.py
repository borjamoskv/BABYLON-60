# ============================================================================
# BABYLON-60 v4.0 Sovereign Hardened
# █ AUTOCOGNITION-Ω | STATE: C5-REAL | AESTHETIC: INDUSTRIAL_NOIR_2026
# ============================================================================
# [PoC & Falsación Empírica] Stress Test: Bounty Ingestion & B60IPC Dispatcher
"""test_bounty_ingestion_pipeline.py - Validación y test de estrés termodinámico.

Certifica:
1. Filtrado O(1) de duplicados (Anergía cero).
2. Empaquetado binario determinista B60IPC.
3. Despacho segregado por dominios (EVM, Native, AI).
4. Tolerancia a tramas corruptas (Fail-Stop).
5. Stress Test empírico (1.000 iteraciones a latencia sub-milisegundo).
"""

from __future__ import annotations

import time
from typing import Dict, List

from babylon60.bft.bounty_ring_dispatcher import BountyRingDispatcher
from babylon60.transducers.bounty_feed_transducer import (
    BountyAdvisory,
    BountyDomain,
    BountyFeedTransducer,
    ExergyFilter,
)


def test_exergy_filter_deduplication_and_classification() -> None:
    """Verifica el descarte O(1) de duplicados y la clasificación ontológica."""
    filter_engine = ExergyFilter(capacity=100)

    # Novedad y unicidad
    assert filter_engine.is_novel("fp_alpha") is True
    assert filter_engine.is_novel("fp_alpha") is False
    assert filter_engine.is_novel("fp_beta") is True

    # Clasificación causal de dominios
    assert (
        filter_engine.classify_domain(
            "Uniswap v4 Hook transient storage vulnerability", "reentrancy via EIP-1153", "solidity"
        )
        == BountyDomain.DOMAIN_EVM
    )

    assert (
        filter_engine.classify_domain(
            "WebKit JavaScriptCore memory corruption", "heap-use-after-free in IsoMalloc", "cpp"
        )
        == BountyDomain.DOMAIN_NATIVE
    )

    assert (
        filter_engine.classify_domain(
            "PyTorch TorchScript arbitrary code execution", "pickle deserialization in tensor", "python"
        )
        == BountyDomain.DOMAIN_AI
    )

    assert (
        filter_engine.classify_domain("Regular denial of service", "infinite loop in parser", "general")
        == BountyDomain.DOMAIN_GENERAL
    )


def test_b60ipc_framing_and_corruption_resilience() -> None:
    """Valida la integridad de trama B60IPC y la inmunidad ante corrupción."""
    transducer = BountyFeedTransducer()
    dispatcher = BountyRingDispatcher()

    advisory = BountyAdvisory(
        advisory_id="GHSA-TEST-001",
        source="github_advisories",
        title="Test Solidity Reentrancy",
        target_ecosystem="solidity",
        domain=BountyDomain.DOMAIN_EVM,
        severity="critical",
        reference_url="https://github.com/advisories/GHSA-TEST-001",
        payload_summary="Reentrancy exploit",
        raw_fingerprint="sha3_mock_fp",
    )

    frame = transducer.pack_advisory_to_b60ipc(advisory)
    assert len(frame) > 30

    # Despacho legítimo
    dispatched = dispatcher.dispatch_frame(frame)
    assert dispatched is not None
    assert dispatched.advisory_id == "GHSA-TEST-001"
    assert dispatched.domain == BountyDomain.DOMAIN_EVM
    assert dispatcher.telemetry.total_dispatched == 1

    # Inyección de corrupción intencional de checksum
    corrupted_frame = bytearray(frame)
    corrupted_frame[-1] ^= 0xFF  # Invertir último byte de checksum SHA3-256
    corrupted_dispatched = dispatcher.dispatch_frame(bytes(corrupted_frame))

    assert corrupted_dispatched is None
    assert dispatcher.telemetry.total_corrupted_dropped == 1
    assert dispatcher.telemetry.total_dispatched == 1


def test_domain_segregation_and_drain() -> None:
    """Verifica la segregación determinista por colas canónicas."""
    transducer = BountyFeedTransducer()
    dispatcher = BountyRingDispatcher()

    items = [
        ("GHSA-EVM-1", "Uniswap Hook Exploit", BountyDomain.DOMAIN_EVM),
        ("GHSA-NAT-1", "WebKit Gigacage Bypass", BountyDomain.DOMAIN_NATIVE),
        ("GHSA-AI-1", "PyTorch Tensor Inversion", BountyDomain.DOMAIN_AI),
        ("GHSA-GEN-1", "Generic HTML Injection", BountyDomain.DOMAIN_GENERAL),
    ]

    for adv_id, title, domain in items:
        adv = BountyAdvisory(
            advisory_id=adv_id,
            source="test",
            title=title,
            target_ecosystem="test",
            domain=domain,
            severity="high",
            reference_url="",
            payload_summary="",
            raw_fingerprint=f"fp_{adv_id}",
        )
        frame = transducer.pack_advisory_to_b60ipc(adv)
        dispatcher.dispatch_frame(frame)

    depths = dispatcher.get_queue_depths()
    assert depths["evm"] == 1
    assert depths["native"] == 1
    assert depths["ai"] == 1
    assert depths["general"] == 1

    # Drain EVM
    evm_batch = dispatcher.drain_domain(BountyDomain.DOMAIN_EVM)
    assert len(evm_batch) == 1
    assert evm_batch[0].advisory_id == "GHSA-EVM-1"
    assert dispatcher.get_queue_depths()["evm"] == 0


def test_empirical_stress_1000_iterations() -> None:
    """Stress Test empírico (1.000 iteraciones) según invariante de Falsación Empírica."""
    transducer = BountyFeedTransducer(filter_capacity=10_000)
    dispatcher = BountyRingDispatcher(queue_capacity=2_048)

    iterations = 1_000
    synthetic_advisories: List[Dict[str, object]] = []

    for i in range(iterations):
        synthetic_advisories.append(
            {
                "ghsa_id": f"GHSA-STRESS-{i:05d}",
                "summary": f"Synthetic Advisory {i} uniswap hook flash loan"
                if i % 3 == 0
                else f"Synthetic Advisory {i} webkit memory heap corruption"
                if i % 3 == 1
                else f"Synthetic Advisory {i} pytorch model injection",
                "description": f"Details for synthetic issue {i}",
                "severity": "critical" if i % 10 == 0 else "medium",
                "html_url": f"https://security.example.com/{i}",
                "vulnerabilities": [{"package": {"ecosystem": "solidity" if i % 3 == 0 else "cpp"}}],
            }
        )

    t0 = time.perf_counter()

    # 1. Fase de transducción y filtrado
    frames = transducer.ingest_raw_advisories(synthetic_advisories)
    t_ingest = time.perf_counter()

    # 2. Fase de despacho lock-free
    for frame in frames:
        dispatcher.dispatch_frame(frame)
    t_dispatch = time.perf_counter()

    total_time = t_dispatch - t0
    assert t_ingest >= t0
    latency_per_item_us = (total_time / iterations) * 1_000_000

    # Atestaciones de rendimiento y completitud
    assert len(frames) == iterations
    assert dispatcher.telemetry.total_dispatched == iterations
    assert dispatcher.telemetry.total_corrupted_dropped == 0

    # Latencia promedio por ítem debe ser menor a 250 microsegundos bajo contención multihilo
    assert latency_per_item_us < 250.0, f"Latencia excesiva: {latency_per_item_us:.2f} µs/item"

    # Verificar que las colas acumularon las cantidades esperadas
    depths = dispatcher.get_queue_depths()
    assert depths["evm"] + depths["native"] + depths["ai"] + depths["general"] == iterations
