#!/usr/bin/env python3
# ============================================================================
# BABYLON-60 v4.0 Sovereign Hardened
# █ AGENTS.ARCHI SUITE | TESTS | STATE: C5-REAL
# ============================================================================
"""
Unit and Invariant Test Suite for Chamber 3: agents.archi.
"""

import pytest
import asyncio
import time
from agents_archi import (
    SwarmConfig,
    InferenceBackend,
    AgentPager,
    DynamicLifecycleManager,
    SubagentState,
    SwarmRouter,
    TopologyTarget,
    CenturiaTopology,
    Modality,
    Proposition,
    AOFValidator,
    AttestationEnvelope,
    KimiClient,
    OpenRouterClient,
)


def test_swarm_config_pxs_and_routing() -> None:
    """Validates PxS ARM64 scaling and dynamic backend URLs."""
    cfg = SwarmConfig(p_cores=8, s_threads=2, backend=InferenceBackend.MOONSHOT_REMOTE)
    assert cfg.max_concurrent == 16
    assert "moonshot.cn" in cfg.api_url

    cfg_local = SwarmConfig(p_cores=4, s_threads=1, backend=InferenceBackend.LOCAL_VLLM)
    assert cfg_local.max_concurrent == 4
    assert "localhost:8000" in cfg_local.api_url
    assert cfg_local.api_key == ""


@pytest.mark.asyncio
async def test_agent_pager_futex_synchronization() -> None:
    """Validates zero-CPU O(1) awakening across parallel agents."""
    pager = AgentPager()
    awoken = []

    async def _worker(idx: int) -> None:
        await pager.wait_for_beep()
        awoken.append(idx)

    tasks = [asyncio.create_task(_worker(i)) for i in range(5)]
    await asyncio.sleep(0.01)
    assert len(awoken) == 0  # Still sleeping in futex

    pager.beep()
    await asyncio.gather(*tasks)
    assert len(awoken) == 5


def test_dynamic_lifecycle_transitions_and_deadlock() -> None:
    """Validates FSM invariants, forbidden transitions, and watchdog deadlock detection."""
    mgr = DynamicLifecycleManager(default_timeout_s=0.05)
    agent = mgr.spawn("worker_01", role="verifier", timeout_s=0.05)
    assert agent.current_state == SubagentState.IDLE

    # Valid transition: IDLE -> PLANNING -> EXECUTING
    agent.transition_to(SubagentState.PLANNING, reason="Decomposing task")
    assert agent.current_state == SubagentState.PLANNING

    agent.transition_to(SubagentState.EXECUTING, reason="Running subtask")
    assert agent.current_state == SubagentState.EXECUTING

    # Forbidden transition: EXECUTING cannot jump directly to IDLE without VERIFYING/DEADLOCKED/POISONED
    with pytest.raises(ValueError):
        agent.transition_to(SubagentState.IDLE)

    # Watchdog deadlock detection
    time.sleep(0.06)
    deadlocked = mgr.scan_deadlocks()
    assert "worker_01" in deadlocked
    assert agent.current_state == SubagentState.DEADLOCKED


def test_swarm_router_typo_tolerance() -> None:
    """Validates Levenshtein fuzzy matching and typo tolerance for user triggers."""
    # Exact triggers
    target, conf = SwarmRouter.route_query("por favor ejecutar legion audit")
    assert target == TopologyTarget.LEGION_SWARM
    assert conf == 1.0

    target, _ = SwarmRouter.route_query("desplegar centuria")
    assert target == TopologyTarget.CENTURIA_100

    target, _ = SwarmRouter.route_query("vamos a grill-me con este diseño")
    assert target == TopologyTarget.SOCRATIC_GRILL

    # Typo tolerance: "enjmabres" -> LEGION_SWARM
    target, conf = SwarmRouter.route_query("lanza los enjmabres")
    assert target == TopologyTarget.LEGION_SWARM
    assert conf >= 0.5

    # Typo tolerance: "axiomatizacion" -> AXIOMATIC_PROTOCOL
    target, conf = SwarmRouter.route_query("vamos a axiomatizacion formal")
    assert target == TopologyTarget.AXIOMATIC_PROTOCOL


@pytest.mark.asyncio
async def test_centuria_parallel_verification_topology() -> None:
    """Validates Centuria 100-worker batch execution and barrier aggregation."""
    centuria = CenturiaTopology(worker_count=50, max_batch_concurrency=10)
    items = [f"item_{i}" for i in range(25)]

    def _sync_verify(item: str) -> bool:
        return item != "item_13"

    report = await centuria.execute_parallel_verification(items, _sync_verify)
    assert report["total_items"] == 25
    assert report["passed"] == 24
    assert report["failed"] == 1
    assert report["throughput_items_per_sec"] > 0


def test_aof_humes_guillotine() -> None:
    """Enforces Hume's Guillotine: Deontic conclusions require deontic premises."""
    p_is1 = Proposition("CPU load is 98%", Modality.EPISTEMIC)
    p_is2 = Proposition("Thermodynamic dissipation limit reached", Modality.EPISTEMIC)
    c_ought = Proposition("You must halt worker 4", Modality.DEONTIC)

    # Attempting to derive ought from purely epistemic premises MUST raise ValueError
    with pytest.raises(ValueError, match="Hume's Guillotine Breach"):
        AOFValidator.enforce_humes_guillotine([p_is1, p_is2], c_ought)

    # Grounded with a deontic premise/axiom passes
    p_norm = Proposition("System must preserve entropy bounds", Modality.DEONTIC)
    assert AOFValidator.enforce_humes_guillotine([p_is1, p_norm], c_ought) is True


def test_attestation_envelope_integrity_and_tamper_detection() -> None:
    """Verifies SCITT cryptographic attestation and tamper resistance."""
    payload = {"task_id": "tx_99", "action": "bft_commit", "data": {"nonce": 42}}
    envelope = AttestationEnvelope.create(
        sender_id="agent_alpha",
        recipient_id="bft_gateway",
        payload=payload,
        signing_key="SecretKey123",
    )

    # Valid verification
    assert envelope.verify(expected_key="SecretKey123") is True

    # Wrong key verification failure
    assert envelope.verify(expected_key="WrongKey") is False

    # Tampering with payload fails verification
    envelope.payload["data"]["nonce"] = 999
    assert envelope.verify(expected_key="SecretKey123") is False


def test_client_adapters_safeguard() -> None:
    """Validates unconfigured air-gap safeguards for Kimi and OpenRouter clients."""
    kimi = KimiClient(api_key="")
    assert not kimi.is_configured()
    res = kimi.query("test query")
    assert res["success"] is False
    assert "Missing KIMI_API_KEY" in res["error"]

    openrouter = OpenRouterClient(api_key="")
    assert not openrouter.is_configured()
    res2 = openrouter.query("test query")
    assert res2["success"] is False
    assert "Missing OPENROUTER_API_KEY" in res2["error"]
