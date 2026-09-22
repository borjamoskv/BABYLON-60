#!/usr/bin/env python3
# ============================================================================
# BABYLON-60 v4.0 Sovereign Hardened
# █ SHARUR-3600 & KUDURRU-64 TEST SUITE | TESTS | STATE: C5-REAL
# ============================================================================
"""
Unit and Integration Tests for SHARUR-3600, KUDURRU-64, and Unified Memory Profiler.
"""

import pytest
from edin.swarms import (
    SharurSwarmTopology,
    SexagesimalScale,
    KudurruGravityFilter,
)
from edin import (
    UnifiedMemoryProfiler,
    AttestationEnvelope,
    calculate_shannon_entropy,
)


def test_shannon_entropy_calculation() -> None:
    """Validates fast Shannon entropy calculation on byte sequences."""
    assert calculate_shannon_entropy(b"") == 0.0
    # Homogeneous byte sequence: zero entropy
    assert calculate_shannon_entropy(b"AAAAAAA") == 0.0
    # High-entropy random-like sequence
    high_ent = calculate_shannon_entropy(bytes(range(256)))
    assert high_ent == 8.0


def test_kudurru_gravity_filter_silent_drop_low_entropy() -> None:
    """Validates INV_C5_SILENT_ANERGY_DROP: Low-entropy or uniform slop is silently dropped."""
    kudurru = KudurruGravityFilter(min_exergy=0.618, auto_init_ring0=False)
    # Low-entropy payload
    res = kudurru.evaluate_and_promote(candidate="0000000000000000")
    assert not res.accepted
    assert res.silent_drop
    assert "Low entropy" in res.reason

    stats = kudurru.stats()
    assert stats["proposals_evaluated"] == 1
    assert stats["proposals_dropped"] == 1
    assert stats["proposals_promoted"] == 0


def test_kudurru_gravity_filter_silent_drop_low_exergy() -> None:
    """Validates rejection of payloads that fail the exergy threshold without raising exceptions."""
    kudurru = KudurruGravityFilter(min_exergy=0.90, auto_init_ring0=False)
    payload = {"data": "Normal information content with moderate entropy"}
    # Force exergy score below 0.90
    res = kudurru.evaluate_and_promote(candidate=payload, candidate_exergy=0.45)
    assert not res.accepted
    assert res.silent_drop
    assert "below threshold" in res.reason


def test_kudurru_gravity_filter_high_exergy_promotion() -> None:
    """Validates INV_C5_KUDURRU_64_MEMBRANE: High-exergy Black Swans are accepted and hashed."""
    kudurru = KudurruGravityFilter(min_exergy=0.618, auto_init_ring0=True)

    envelope = AttestationEnvelope.create(
        sender_id="sharur_agent_0042",
        recipient_id="ring0_ledger",
        payload={
            "hypothesis": "C5-REAL Sexagesimal Topological Fixed Point",
            "proof_digest": "0x6060_c5_terminal_convergence",
            "exergy_gain": 21000,
        },
    )

    res = kudurru.evaluate_and_promote(candidate=envelope, candidate_exergy=0.95, epoch=1700000060)
    assert res.accepted
    assert not res.silent_drop
    assert res.epoch == 1700000060
    assert res.digest_hex is not None
    assert len(res.digest_hex) == 64  # SHA3-256 hex
    assert "High-exergy Black Swan validated" in res.reason
    assert res.promoted_to_ring0

    stats = kudurru.stats()
    assert stats["proposals_promoted"] >= 1


def test_kudurru_anti_mocking_silicon_attestation() -> None:
    """Validates Rule 6 (Anti-Mocking): Kudurru uses real compiled binary for Ring-0 promotion."""
    kudurru = KudurruGravityFilter(min_exergy=0.5, auto_init_ring0=False)
    assert kudurru.is_ring0_available(), "Debe detectar el binario babylon-attest compilado"

    candidate = {
        "event": "BLACK_SWAN_PROMOTION",
        "axiom": "C5-REAL Zero-Mock Silicon Invariant",
        "value": 21000,
    }
    res = kudurru.evaluate_and_promote(candidate=candidate, candidate_exergy=0.99)
    assert res.accepted
    assert res.promoted_to_ring0
    assert "receipt" in res.telemetry
    receipt = res.telemetry["receipt"]
    assert "block_hash" in receipt
    assert "signature" in receipt
    assert receipt["block_hash"] == res.digest_hex


@pytest.mark.asyncio
async def test_sharur_swarm_async_sweep() -> None:
    """Validates SharurSwarmTopology asynchronous sweep across items."""
    sharur = SharurSwarmTopology(scale=SexagesimalScale.SOSS)
    items = [f"item_{i:03d}" for i in range(30)]

    async def _mock_worker(item: str, agent_id: int) -> str:
        return f"Verified {item} by Sharur-{agent_id:04d}"

    summary = await sharur.execute_async_sweep(items, _mock_worker, max_batch_concurrency=10)
    assert summary.total_items == 30
    assert summary.passed_items == 30
    assert summary.failed_items == 0
    assert summary.items_per_second > 0
    assert summary.telemetry.wall_time_s >= 0.0


def _sample_sync_worker(item: str, agent_id: int) -> int:
    return len(item) + agent_id


def test_sharur_swarm_cpu_sweep_zero_thrashing() -> None:
    """Validates high-throughput parallel CPU sweep across virtual subagent workers."""
    sharur = SharurSwarmTopology(scale=SexagesimalScale.SOSS, process_workers=2)
    items = [f"syntax_token_{i}" for i in range(40)]

    summary = sharur.execute_parallel_cpu_sweep(items, _sample_sync_worker)
    assert summary.total_items == 40
    assert summary.passed_items == 40
    assert summary.failed_items == 0
    assert len(summary.results) == 40


def test_unified_memory_profiler_host_detection() -> None:
    """Validates hardware detection of physical RAM and Apple Silicon architecture."""
    profiler = UnifiedMemoryProfiler()
    report = profiler.get_hardware_report()
    assert report.total_ram_gb > 0
    assert report.available_ram_gb > 0
    assert report.max_hostable_params_q4_billions > 0
    assert report.recommended_backend in ("local_mlx", "local_vllm")


def test_unified_memory_profiler_mac_studio_ultra_256gb() -> None:
    """Validates simulation of 256GB Unified Memory Mac Studio Ultra expansion."""
    profiler = UnifiedMemoryProfiler()
    sim = profiler.simulate_mac_studio_ultra_256gb()
    assert sim["total_ram_gb"] == 256.0
    assert sim["usable_ram_gb"] == 204.8

    projections = {p["model"]: p for p in sim["projections"]}
    # Llama 70B must fit with zero swap and host multiple concurrent agents
    assert projections["Llama-3.3-70B"]["fits_zero_swap"]
    assert projections["Llama-3.3-70B"]["max_swarm_agents"] > 10

    # 120B MoE model must fit cleanly in 256GB
    assert projections["Kimi-K3-MoE-120B"]["fits_zero_swap"]


def test_dual_package_facade_consistency() -> None:
    """Verifies complete isomorphism between edin and agents_archi packages."""
    import agents_archi
    import edin

    assert hasattr(edin, "SharurSwarmTopology")
    assert hasattr(agents_archi, "SharurSwarmTopology")
    assert hasattr(edin, "KudurruGravityFilter")
    assert hasattr(agents_archi, "KudurruGravityFilter")
    assert hasattr(edin, "UnifiedMemoryProfiler")
    assert hasattr(agents_archi, "UnifiedMemoryProfiler")
