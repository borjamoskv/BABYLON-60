#!/usr/bin/env python3
# ============================================================================
# BABYLON-60 v4.0 Sovereign Hardened
# █ AGENTS.ARCHI SUITE | TESTS | STATE: C5-REAL
# ============================================================================
"""
Unit and Invariant Test Suite for Chamber 3: agents.archi.
"""

from datetime import date
from pathlib import Path
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
    EdinTopology,
    Modality,
    Proposition,
    AOFValidator,
    AttestationEnvelope,
    KimiClient,
    OpenRouterClient,
    OpenRouterRoleTier,
    QuotaBudgetTracker,
    SensitivePathGuard,
    TokenBucketRateLimiter,
    RobustLLMClient,
    BabylonTrustGateway,
    CortexWalStore,
    ProposedToolAction,
    ResumableTaskExecutor,
    annihilate_wal_triplet,
    run_royal_rumble_endurance_benchmark,
    BlackboardArbiter,
    BlackboardStatus,
    BlackboardTopic,
    ColdPathCurator,
    MAX_CLAIM_CHARS,
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
    assert getattr(agent, "current_state") == SubagentState.PLANNING

    agent.transition_to(SubagentState.EXECUTING, reason="Running subtask")
    assert getattr(agent, "current_state") == SubagentState.EXECUTING

    # Forbidden transition: EXECUTING cannot jump directly to IDLE without VERIFYING/DEADLOCKED/POISONED
    with pytest.raises(ValueError):
        agent.transition_to(SubagentState.IDLE)

    # Watchdog deadlock detection
    time.sleep(0.06)
    deadlocked = mgr.scan_deadlocks()
    assert "worker_01" in deadlocked
    assert getattr(agent, "current_state") == SubagentState.DEADLOCKED


def test_swarm_router_typo_tolerance() -> None:
    """Validates Levenshtein fuzzy matching and typo tolerance for user triggers."""
    # Exact triggers
    target, conf = SwarmRouter.route_query("por favor ejecutar edin audit")
    assert target == TopologyTarget.EDIN_SWARM
    assert conf == 1.0

    target, _ = SwarmRouter.route_query("desplegar sharur-3600")
    assert target == TopologyTarget.SHARUR_3600

    target, _ = SwarmRouter.route_query("vamos a grill-me con este diseño")
    assert target == TopologyTarget.SOCRATIC_GRILL

    # Typo tolerance: "enjmabres" -> EDIN_SWARM
    target, conf = SwarmRouter.route_query("lanza los enjmabres")
    assert target == TopologyTarget.EDIN_SWARM
    assert conf >= 0.5

    # Typo tolerance: "axiomatizacion" -> AXIOMATIC_PROTOCOL
    target, conf = SwarmRouter.route_query("vamos a axiomatizacion formal")
    assert target == TopologyTarget.AXIOMATIC_PROTOCOL


@pytest.mark.asyncio
async def test_edin_parallel_verification_topology() -> None:
    """Validates Edin 100-worker batch execution and barrier aggregation."""
    edin = EdinTopology(worker_count=50, max_batch_concurrency=10)
    items = [f"item_{i}" for i in range(25)]

    def _sync_verify(item: str) -> bool:
        return item != "item_13"

    report = await edin.execute_parallel_verification(items, _sync_verify)
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


def test_circuit_breaker_subordination() -> None:
    """Validates INV_C5_CB_SUBORDINATION: Subordinating CB to Ring-0 eliminates false trips."""
    # Standard non-delegated client
    cfg_std = SwarmConfig(circuit_breaker_threshold=2, delegate_circuit_breaker=False)
    client_std = RobustLLMClient(cfg_std)
    client_std._consecutive_failures = 2
    assert client_std.is_circuit_breaker_tripped is True

    # Delegated client (subordinated to Ring-0)
    cfg_del = SwarmConfig(circuit_breaker_threshold=2, delegate_circuit_breaker=True)
    client_del = RobustLLMClient(cfg_del)
    client_del._consecutive_failures = 10
    assert client_del.is_circuit_breaker_tripped is False


def test_openrouter_royal_rumble_v2_roles_and_poolside_sunset() -> None:
    """Validates Inkling planner, Poolside Oct 31 sunset gate, and JSON Schema auto-routing."""
    client = OpenRouterClient(api_key="test")

    # 1. Planner uses Thinking Machines Inkling primary + Inkling-Small + Nemotron-3-Super
    planner_models = client.resolve_role_models(OpenRouterRoleTier.PLANNER, reference_date=date(2026, 10, 16))
    assert planner_models[0] == "thinkingmachines/inkling:free"
    assert "thinkingmachines/inkling-small:free" in planner_models
    assert "nvidia/nemotron-3-super-120b-a12b:free" in planner_models

    # 2. Coder uses Poolside Laguna S 2.1 on or before 2026-10-31, switches to Cohere North Mini Code on 2026-11-01
    coder_oct = client.resolve_role_models(OpenRouterRoleTier.CODER_ACT, reference_date=date(2026, 10, 31))
    assert coder_oct[0] == "poolside/laguna-s-2.1:free"
    assert "cohere/north-mini-code:free" in coder_oct

    coder_nov = client.resolve_role_models(OpenRouterRoleTier.CODER_ACT, reference_date=date(2026, 11, 1))
    assert coder_nov[0] == "cohere/north-mini-code:free"
    assert all("poolside" not in m for m in coder_nov)

    # 3. Requesting response_format (JSON Schema) on PLANNER automatically shifts away from Inkling to Nemotron-3-Super
    schema_payload = client.build_chat_payload(
        prompt="Generate structured DAG",
        role=OpenRouterRoleTier.PLANNER,
        response_format={"type": "json_object"},
        tool_choice="auto",
        reference_date=date(2026, 10, 16),
    )
    assert schema_payload["model"] == "nvidia/nemotron-3-super-120b-a12b:free"
    assert schema_payload["response_format"] == {"type": "json_object"}
    assert schema_payload["provider"]["allow_fallbacks"] is True


def test_openrouter_sensitive_path_guard_blocks_free_endpoints() -> None:
    """Validates Zero-Trust IP Guardrail blocks Ring-0/Rust/Lean4 files from :free endpoints."""
    client = OpenRouterClient(api_key="test")

    # Sensitive Rust path triggers guard on :free role
    res_path = client.query(
        prompt="Refactor this module",
        role=OpenRouterRoleTier.CODER_ACT,
        context_paths=["src/manifest.rs"],
    )
    assert res_path["success"] is False
    assert "SOVEREIGN_IP_GUARD_TRIPPED" in res_path["error"]
    assert res_path["route_override"] == "local_mlx"

    # Sensitive content marker triggers guard on :free role
    res_marker = client.query(
        prompt="Verify SharedManifest and KUDURRU-64 layout invariants",
        role=OpenRouterRoleTier.PLANNER,
    )
    assert res_marker["success"] is False
    assert "SOVEREIGN_IP_GUARD_TRIPPED" in res_marker["error"]

    # Non-sensitive scaffolding query passes guard check
    assert (
        SensitivePathGuard.is_sensitive(prompt="Write a generic SQLite task runner", context_paths=["app/runner.py"])
        is False
    )


def test_openrouter_quota_80_20_partition_and_token_bucket() -> None:
    """Validates 80% WORK / 20% RECOVERY RPD quota split and 15 RPM TokenBucketRateLimiter."""
    quota = QuotaBudgetTracker(daily_limit=50, work_ratio=0.80)
    assert quota.work_budget == 40
    assert quota.recovery_budget == 10

    for _ in range(40):
        assert quota.can_spend("work") is True
        quota.record_attempt("work")

    # Work budget exhausted at 40, but recovery budget (10 calls) remains available
    assert quota.can_spend("work") is False
    assert quota.can_spend("recovery") is True

    for _ in range(10):
        assert quota.can_spend("recovery") is True
        quota.record_attempt("recovery")

    assert quota.can_spend("recovery") is False
    assert quota.total_used == 50

    # Deterministic TokenBucketRateLimiter (15 RPM = 1 token every 4.0s, burst=2)
    fake_now = [100.0]
    bucket = TokenBucketRateLimiter(rpm=15.0, burst=2, clock=lambda: fake_now[0])
    assert bucket.acquire_wait_seconds() == 0.0
    assert bucket.acquire_wait_seconds() == 0.0
    wait_s = bucket.acquire_wait_seconds()
    assert abs(wait_s - 4.0) < 1e-6


def test_cortex_wal_pragmas_and_idempotent_compaction(tmp_path: Path) -> None:
    """Validates INV_C5_WAL_SYNCHRONOUS_FULL, idempotent replay, error-preserving compaction, and WAL triplet annihilation."""
    db_file = tmp_path / "cortex_test.db"
    wal = CortexWalStore(db_file)
    try:
        mode, sync_flag = wal.verify_wal_pragmas()
        assert mode == "wal"
        assert sync_flag == 2  # SQLite FULL == 2

        executor = ResumableTaskExecutor(wal)
        prop = ProposedToolAction(
            step_index=0,
            logical_tick=1,
            tool_name="write_module",
            target_path="app/service.py",
            args={"lines": 42},
        )
        res1 = executor.execute_step("task_alpha", prop, lambda _p: (True, "a" * 64, ""))
        assert res1["status"] == "PASS"

        # Replaying the exact same step after a simulated crash skips execution in O(1) without spending quota
        work_before = executor.quota.work_used
        res2 = executor.execute_step("task_alpha", prop, lambda _p: (True, "a" * 64, ""))
        assert res2["status"] == "IDEMPOTENT_SKIP"
        assert executor.quota.work_used == work_before

        # Verify repeat failed call is blocked by BabylonTrustGateway
        bad_prop = ProposedToolAction(
            step_index=1,
            logical_tick=2,
            tool_name="run_migration",
            target_path="app/db.py",
            args={"sql": "DROP"},
        )
        fail_res = executor.execute_step("task_alpha", bad_prop, lambda _p: (False, "f" * 64, "Migration syntax error"))
        assert fail_res["status"] == "FAIL"

        # Repeating the exact same failed action is deterministically DENIED by the Trust Gateway
        repeat_verdict = BabylonTrustGateway.evaluate(
            bad_prop,
            task_id="task_alpha",
            consecutive_failures=1,
            failed_signatures=wal.get_failed_action_signatures("task_alpha"),
        )
        assert repeat_verdict.admitted is False
        assert repeat_verdict.reason == "DENY_REPEATED_FAILED_CALL"
        assert repeat_verdict.requires_structured_review is True

        # Context compaction preserves prefix and error summary
        msgs = [
            {"role": "system", "content": "Immutable system prompt"},
            {"role": "user", "content": "Initial objective"},
        ] + [{"role": "assistant", "content": f"msg {i}"} for i in range(10)]
        compacted = wal.compact_context_preserving_errors("task_alpha", msgs, max_tail=2)
        assert compacted[0]["content"] == "Immutable system prompt"
        assert compacted[1]["content"] == "Initial objective"
        assert "Migration syntax error" in compacted[2]["content"]
    finally:
        wal.close()
        annihilate_wal_triplet(db_file)

    assert not db_file.exists()
    assert not Path(f"{db_file}-wal").exists()
    assert not Path(f"{db_file}-shm").exists()


def test_royal_rumble_100_iterations_3_interrupts_model_switch(tmp_path: Path) -> None:
    """Validates the full 100-iteration ROYAL-RUMBLE v2 endurance benchmark with 3 WAL restarts and 1 model switch."""
    db_file = tmp_path / "royal_rumble_100.db"
    try:
        report = run_royal_rumble_endurance_benchmark(
            db_file,
            total_steps=100,
            interrupt_steps=(25, 60, 85),
            model_switch_step=50,
            transient_fail_steps=(15, 42, 73),
            sensitive_probe_step=33,
        )
        metrics = report.to_metrics_dict()
        assert metrics["finalizacion_completed"] is True
        assert report.completed_steps == 100
        assert metrics["continuidad_interruptions_recovered"] == 3
        assert report.model_switches_survived == 1
        assert metrics["correccion_zero_regressions"] is True
        assert metrics["seguridad_zero_unauthorized_effects"] is True
        # "Iterar sin redundar": ~1.06 calls/step (far below 3.0x swarm-per-step overhead)
        assert metrics["eficiencia_calls_per_step"] <= 1.15
        assert metrics["memoria_errors_preserved"] >= 4  # 3 transient fails + 1 denied sensitive probe
        assert metrics["robustez_429_timeout_recoveries"] == 3
    finally:
        annihilate_wal_triplet(db_file)

    assert not db_file.exists()


def test_openrouter_embed_sensitive_guard() -> None:
    """Validates OpenRouterClient.embed() blocks Ring-0 content on :free embedding models."""
    client = OpenRouterClient(api_key="test")
    res = client.embed(
        inputs=["#[repr(C, align(64))] struct SharedManifest"],
        model="nvidia/nemotron-3-embed-1b:free",
        context_paths=["src/manifest.rs"],
    )
    assert res["success"] is False
    assert "SOVEREIGN_IP_GUARD_TRIPPED" in res["error"]
    assert res["route_override"] == "local_mlx"

    # With enable_local_failover=True, sensitive embedding transparently routes to local (or BLAKE3 64D fallback)
    client_failover = OpenRouterClient(api_key="test", enable_local_failover=True, local_base_url="http://127.0.0.1:9")
    res_local = client_failover.embed(
        inputs=["#[repr(C, align(64))] struct SharedManifest"],
        model="nvidia/nemotron-3-embed-1b:free",
        context_paths=["src/manifest.rs"],
    )
    assert res_local["success"] is True
    assert res_local["route_override"] == "local_mlx"
    assert len(res_local["embeddings"][0]) == 64


def test_blackboard_arbiter_admission_and_anti_cheap_talk(tmp_path: Path) -> None:
    """Validates deterministic schema enforcement, anti-cheap-talk bound, sensitive guard, and O(1) dedup."""
    db_file = tmp_path / "blackboard_admission.db"
    wal = CortexWalStore(db_file)
    try:
        arbiter = BlackboardArbiter(wal)

        # 1. Reject prose exceeding MAX_CLAIM_CHARS (280 chars)
        long_res = arbiter.publish(
            task_id="task_bb",
            logical_tick=1,
            topic=BlackboardTopic.HYPOTHESIS,
            author_agent_id="agent_coder_1",
            target_path="app/router.py",
            claim="x" * (MAX_CLAIM_CHARS + 1),
        )
        assert long_res.admitted is False
        assert long_res.reason == "DENY_CHEAP_TALK_LENGTH"

        # 2. Reject sensitive Ring-0 / Lean 4 paths on :free endpoints
        sens_res = arbiter.publish(
            task_id="task_bb",
            logical_tick=2,
            topic=BlackboardTopic.PATCH_PROPOSAL,
            author_agent_id="agent_coder_1",
            target_path="src/manifest.rs",
            claim="Mutate SharedManifest alignment",
            author_model="poolside/laguna-s-2.1:free",
        )
        assert sens_res.admitted is False
        assert sens_res.reason == "DENY_SENSITIVE_PATH_ON_FREE_ENDPOINT"

        # 3. Admit valid typed tuple and deduplicate identical publish in O(1)
        ok_res = arbiter.publish(
            task_id="task_bb",
            logical_tick=3,
            topic=BlackboardTopic.HYPOTHESIS,
            author_agent_id="agent_coder_1",
            target_path="app/router.py",
            claim="Null check missing on line 42",
            payload={"line": 42},
        )
        assert ok_res.admitted is True
        assert ok_res.reason == "ADMITTED_OPEN"
        assert ok_res.tuple_record is not None

        dup_res = arbiter.publish(
            task_id="task_bb",
            logical_tick=3,
            topic=BlackboardTopic.HYPOTHESIS,
            author_agent_id="agent_coder_2",
            target_path="app/router.py",
            claim="Null check missing on line 42",
            payload={"line": 42},
        )
        assert dup_res.admitted is True
        assert dup_res.reason == "IDEMPOTENT_DUPLICATE"
        assert dup_res.tuple_id == ok_res.tuple_id
        assert len(arbiter.poll_subscription("task_bb")) == 1
    finally:
        wal.close()
        annihilate_wal_triplet(db_file)


def test_blackboard_two_man_rule_and_cold_path_curator(tmp_path: Path) -> None:
    """Validates Two-Man Rule (verifier != author), SHA-256 evidence_hash, and ColdPathCurator compaction."""
    db_file = tmp_path / "blackboard_curator.db"
    wal = CortexWalStore(db_file)
    try:
        arbiter = BlackboardArbiter(wal)
        curator = ColdPathCurator(arbiter)

        pub1 = arbiter.publish(
            task_id="task_curate",
            logical_tick=10,
            topic=BlackboardTopic.HYPOTHESIS,
            author_agent_id="agent_alpha",
            target_path="app/auth.py",
            claim="Token expiry off by 1s",
        )
        pub2 = arbiter.publish(
            task_id="task_curate",
            logical_tick=11,
            topic=BlackboardTopic.PATCH_PROPOSAL,
            author_agent_id="agent_alpha",
            target_path="app/cache.py",
            claim="Drop lock before flush",
        )

        # Self-verification must fail (Two-Man Rule)
        with pytest.raises(ValueError, match="Two-Man Rule"):
            arbiter.resolve(
                tuple_id=pub1.tuple_id,
                verifier_agent_id="agent_alpha",
                new_status=BlackboardStatus.VERIFIED,
                evidence_hash="a" * 64,
                logical_tick=12,
            )

        # Invalid evidence_hash must fail
        with pytest.raises(ValueError, match="Invalid evidence_hash"):
            arbiter.resolve(
                tuple_id=pub1.tuple_id,
                verifier_agent_id="agent_verifier",
                new_status=BlackboardStatus.VERIFIED,
                evidence_hash="not-a-sha256",
                logical_tick=12,
            )

        # Valid independent resolution (1 VERIFIED, 1 FALSIFIED)
        arbiter.resolve(
            tuple_id=pub1.tuple_id,
            verifier_agent_id="agent_verifier",
            new_status=BlackboardStatus.VERIFIED,
            evidence_hash="a" * 64,
            logical_tick=12,
        )
        arbiter.resolve(
            tuple_id=pub2.tuple_id,
            verifier_agent_id="agent_verifier",
            new_status=BlackboardStatus.FALSIFIED,
            evidence_hash="b" * 64,
            logical_tick=13,
        )

        # 100% deterministic ColdPathCurator compaction
        digest = curator.compact_resolved_tuples("task_curate", logical_tick=20)
        assert len(digest.verified_claims) == 1
        assert len(digest.falsified_claims) == 1
        assert "deterministic_compaction: 1 verified, 1 falsified at tick=20" == digest.executive_summary
        assert "[BLACKBOARD-DIGEST tick=20]" in digest.to_system_note()["content"]

        # Resolved tuples are now COMPACTED (zero clutter in VERIFIED/FALSIFIED/OPEN queues)
        assert arbiter.poll_subscription("task_curate", status=BlackboardStatus.OPEN) == []
        assert arbiter.poll_subscription("task_curate", status=BlackboardStatus.VERIFIED) == []
        assert len(arbiter.poll_subscription("task_curate", status=BlackboardStatus.COMPACTED)) == 2

        # Context compaction injects BlackboardDigest system note alongside WAL checkpoint
        msgs = [
            {"role": "system", "content": "System prompt"},
            {"role": "user", "content": "Goal"},
            {"role": "assistant", "content": "Step 1"},
        ]
        compacted_msgs = wal.compact_context_preserving_errors(
            "task_curate",
            msgs,
            max_tail=1,
            blackboard_digest=digest,
        )
        assert any("[BLACKBOARD-DIGEST tick=20]" in m["content"] for m in compacted_msgs)
    finally:
        wal.close()
        annihilate_wal_triplet(db_file)


def test_blackboard_mcp_dispatch_integration(tmp_path: Path) -> None:
    """Validates MCP blackboard_dispatch tool (publish -> resolve -> curate) over CortexWalStore."""
    import json
    from babylon60.mcp.cortex_mcp_server import CortexMCPServer

    db_file = tmp_path / "mcp_blackboard.db"
    server = CortexMCPServer(ledger_path=str(tmp_path / "ledger.db"))
    try:
        pub_resp = server._handle_tools_call(
            {
                "name": "cortex_blackboard_dispatch",
                "arguments": {
                    "operation": "publish",
                    "task_id": "mcp_task",
                    "logical_tick": 1,
                    "topic": "HYPOTHESIS",
                    "author_agent_id": "agent_1",
                    "target_path": "app/core.py",
                    "claim": "Race condition in handler",
                    "db_path": str(db_file),
                },
            }
        )
        assert pub_resp["isError"] is False
        pub_content = pub_resp["content"]
        assert isinstance(pub_content, list) and isinstance(pub_content[0], dict)
        pub_data = json.loads(str(pub_content[0]["text"]))
        tuple_id = pub_data["tuple_id"]

        res_resp = server._handle_tools_call(
            {
                "name": "blackboard_dispatch",
                "arguments": {
                    "operation": "resolve",
                    "task_id": "mcp_task",
                    "tuple_id": tuple_id,
                    "verifier_agent_id": "agent_2",
                    "new_status": "VERIFIED",
                    "evidence_hash": "c" * 64,
                    "logical_tick": 2,
                    "db_path": str(db_file),
                },
            }
        )
        assert res_resp["isError"] is False

        cur_resp = server._handle_tools_call(
            {
                "name": "blackboard_dispatch",
                "arguments": {
                    "operation": "curate",
                    "task_id": "mcp_task",
                    "logical_tick": 3,
                    "db_path": str(db_file),
                },
            }
        )
        assert cur_resp["isError"] is False
        cur_content = cur_resp["content"]
        assert isinstance(cur_content, list) and isinstance(cur_content[0], dict)
        cur_data = json.loads(str(cur_content[0]["text"]))
        assert len(cur_data["verified_claims"]) == 1
    finally:
        annihilate_wal_triplet(db_file)


def test_legaltech_flash_mini_veto_and_allow_fallbacks_false(monkeypatch: pytest.MonkeyPatch) -> None:
    """
    Validates that LegalTech / strict_model_floor workloads:
      1. Purge `mini`, `flash`, `small`, `xs`, `lightning`, and `:free` models from fallback arrays.
      2. Enforce `provider.allow_fallbacks = False` and `data_collection = 'deny'` in both OpenRouterClient and SwarmConfig.
      3. Reject explicit Flash/Mini requests and silent post-flight gateway downgrades (e.g., server returning gemini-2.5-flash or gpt-4o-mini).
      4. Exclude lightweight `qwen3:1.7b` (`ollama_11434`) during local failover.
    """
    import json
    import urllib.request
    from agents_archi.clients.openrouter import (
        ModelFloorGuard,
        OpenRouterClient,
        OpenRouterRoleTier,
        SensitivePathGuard,
        SubThresholdModelVetoError,
    )
    from agents_archi.orchestrator.swarm import InferenceBackend, RobustLLMClient, SwarmConfig

    # 1. Deterministic sub-threshold classifier
    for forbidden in (
        "google/gemini-2.5-flash",
        "openai/gpt-4o-mini",
        "cohere/north-mini-code:free",
        "thinkingmachines/inkling-small:free",
        "poolside/laguna-xs-2.1:free",
        "nvidia/nemotron-3.5-lightning:free",
        "qwen3:1.7b",
        "openrouter/free",
        "openrouter/auto",
    ):
        assert ModelFloorGuard.is_sub_threshold(forbidden) is True
        with pytest.raises(SubThresholdModelVetoError):
            ModelFloorGuard.assert_model_allowed(forbidden)

    for allowed in (
        "deepseek/deepseek-r1",
        "qwen/qwen-2.5-72b-instruct",
        "meta-llama/llama-3.3-70b-instruct",
        "deepseek-r1-distill-qwen-32b",
    ):
        assert ModelFloorGuard.is_sub_threshold(allowed) is False
        ModelFloorGuard.assert_model_allowed(allowed)

    # 2. SensitivePathGuard detects EU AI Act / LegalTech markers
    assert (
        SensitivePathGuard.is_legaltech(prompt="Redactar dictamen jurídico bajo el Reglamento (UE) 2024/1689") is True
    )
    assert SensitivePathGuard.is_legaltech(context_paths=["docs/03_guides/guide_legaltech_eu_ai_act.md"]) is True

    # 3. OpenRouterClient purges mini/free models and sets allow_fallbacks=False on LegalTech / strict_model_floor
    client = OpenRouterClient(api_key="test_secret_key_12345")
    strict_payload = client.build_chat_payload(
        prompt="Analizar cláusula de responsabilidad civil EU AI Act",
        role=OpenRouterRoleTier.CODER_ACT,
        strict_model_floor=True,
    )
    assert strict_payload["provider"]["allow_fallbacks"] is False
    assert strict_payload["provider"]["data_collection"] == "deny"
    assert all(not ModelFloorGuard.is_sub_threshold(m) for m in strict_payload["models"])
    assert "cohere/north-mini-code:free" not in strict_payload["models"]

    # Explicit Flash model request in LegalTech query fails closed
    veto_explicit = client.query(
        prompt="Emitir dictamen legal vinculante sobre eIDAS",
        model="google/gemini-2.5-flash",
    )
    assert veto_explicit["success"] is False
    assert veto_explicit.get("veto_triggered") is True
    assert "SUB_THRESHOLD_MODEL_VETO" in veto_explicit["error"]

    # 4. Swarm RobustLLMClient purges `cohere/north-mini-code:free` and sets allow_fallbacks=False on LegalTech prompts
    swarm_cfg = SwarmConfig(
        backend=InferenceBackend.OPENROUTER_REMOTE,
        openrouter_key="test_secret_key_12345",
    )
    swarm_client = RobustLLMClient(swarm_cfg)
    legal_msgs = [{"role": "user", "content": "Auditar cumplimiento EU AI Act y cláusula RGPD"}]
    swarm_payload = swarm_client.build_request_payload(legal_msgs)
    assert swarm_payload["provider"]["allow_fallbacks"] is False
    assert swarm_payload["provider"]["data_collection"] == "deny"
    assert "cohere/north-mini-code:free" not in swarm_payload["models"]
    assert all(not ModelFloorGuard.is_sub_threshold(m) for m in swarm_payload["models"])

    # 5. Post-flight gateway silent downgrade detection (server pretends to answer with gpt-4o-mini)
    class _FakeHTTPResponse:
        def __init__(self, body: dict[str, object]) -> None:
            self._raw = json.dumps(body).encode("utf-8")

        def read(self) -> bytes:
            return self._raw

        def __enter__(self) -> "_FakeHTTPResponse":
            return self

        def __exit__(self, *args: object) -> None:
            pass

    monkeypatch.setattr(
        urllib.request,
        "urlopen",
        lambda req, timeout=45.0: _FakeHTTPResponse(
            {
                "model": "openai/gpt-4o-mini",
                "choices": [{"message": {"content": "Silent mini fallback output"}}],
            }
        ),
    )
    postflight_or = client.query(
        prompt="Dictamen jurídico sobre responsabilidad penal y EU AI Act",
    )
    assert postflight_or["success"] is False
    assert postflight_or.get("veto_triggered") is True
    assert "SUB_THRESHOLD_MODEL_VETO [postflight]" in postflight_or["error"]


def test_moskv1_render_exergy_guard_cache_mutex_and_silicon_gate(tmp_path: Path) -> None:
    """
    Validates the 4 MOSKV-1 render exergy primitives:
      1. BLAKE3 content-addressed cache hit skips re-rendering (O(1)).
      2. SingleRenderQueueMutex prevents concurrent render contention across surfaces.
      3. SiliconMediaGate blocks unverified/silent/clipped renders (Phi = 0).
      4. Two-tier Draft (--scale=0.5) vs Final CLI builder.
    """
    from babylon60.transducers.render_exergy_guard import (
        MediaVerificationMetrics,
        RenderCacheStore,
        RenderExergyOrchestrator,
        RenderTier,
        SiliconMediaGate,
        SingleRenderQueueMutex,
        build_remotion_render_args,
    )

    cache = RenderCacheStore(cache_dir=tmp_path / "cache")
    mutex = SingleRenderQueueMutex(lock_path=tmp_path / "render.lock")
    gate = SiliconMediaGate()
    orchestrator = RenderExergyOrchestrator(cache=cache, mutex=mutex, gate=gate)

    render_calls = [0]

    def _mock_render(dest: Path, tier: RenderTier) -> None:
        render_calls[0] += 1
        dest.write_bytes(b"FAKE_PRO_RES_AND_AAC_STREAM_" + tier.value.encode("utf-8"))

    def _valid_verifier(dest: Path) -> MediaVerificationMetrics:
        return gate.evaluate_metrics(
            integrated_lufs=-14.2,
            true_peak_dbtp=-1.1,
            video_frames=360,
            width=1920,
            height=1080,
            codec_name="h264",
        )

    out1 = tmp_path / "out" / "master_1.mp4"
    props = {"title": "C5 Render Exergy", "scenes": [{"id": 1, "durationInFrames": 180}]}

    # First execution renders and stores in BLAKE3 cache
    r1 = orchestrator.execute_render(
        composition_code="export const BabylonMasterclass = () => null;",
        props=props,
        output_path=out1,
        render_fn=_mock_render,
        audio_bytes_or_hash=b"audio_master_pcm",
        tier=RenderTier.FINAL,
        verifier_fn=_valid_verifier,
    )
    assert r1.cache_hit is False
    assert r1.verified is True
    assert r1.exergy_phi > 15000.0
    assert render_calls[0] == 1
    assert out1.is_file()

    # Second execution with identical inputs hits BLAKE3 cache without invoking render_fn
    out2 = tmp_path / "out" / "master_2.mp4"
    r2 = orchestrator.execute_render(
        composition_code="export const BabylonMasterclass = () => null;",
        props=props,
        output_path=out2,
        render_fn=_mock_render,
        audio_bytes_or_hash=b"audio_master_pcm",
        tier=RenderTier.FINAL,
        verifier_fn=_valid_verifier,
    )
    assert r2.cache_hit is True
    assert r2.exergy_phi == 21000.0
    assert render_calls[0] == 1
    assert out2.read_bytes() == out1.read_bytes()

    # Unverified render (clipped True Peak > -0.1 dBTP) is vetoed (Phi = 0) and deleted
    def _clipped_verifier(dest: Path) -> MediaVerificationMetrics:
        return gate.evaluate_metrics(
            integrated_lufs=-14.0,
            true_peak_dbtp=0.8,  # Clipping!
            video_frames=360,
            width=1920,
            height=1080,
            codec_name="h264",
        )

    out_bad = tmp_path / "out" / "clipped.mp4"
    with pytest.raises(RuntimeError, match="SILICON_MEDIA_GATE_VETO"):
        orchestrator.execute_render(
            composition_code="export const Clipped = () => null;",
            props=props,
            output_path=out_bad,
            render_fn=_mock_render,
            tier=RenderTier.FINAL,
            verifier_fn=_clipped_verifier,
        )
    assert not out_bad.exists()

    # Draft vs Final CLI builder check
    draft_cmd = build_remotion_render_args("src/index.ts", "Comp", "out.mp4", "props.json", tier=RenderTier.DRAFT)
    assert "--scale=0.5" in draft_cmd
    final_cmd = build_remotion_render_args("src/index.ts", "Comp", "out.mp4", "props.json", tier=RenderTier.FINAL)
    assert "--scale=0.5" not in final_cmd

    # Mutex hardening: reject preexisting symlink at lock_path
    symlink_lock = tmp_path / "symlink_render.lock"
    target_dummy = tmp_path / "dummy_target.txt"
    target_dummy.write_text("victim", encoding="utf-8")
    symlink_lock.symlink_to(target_dummy)
    bad_mutex = SingleRenderQueueMutex(lock_path=symlink_lock)
    with pytest.raises(RuntimeError, match="MOSKV1_RENDER_LOCK_SYMLINK_REJECTED"):
        with bad_mutex.acquire(non_blocking=True):
            pass

    # Mutex hardening: real mutual exclusion across independent descriptors
    with mutex.acquire(non_blocking=True):
        contending_mutex = SingleRenderQueueMutex(lock_path=tmp_path / "render.lock")
        with pytest.raises(RuntimeError, match="MOSKV1_RENDER_QUEUE_BUSY"):
            with contending_mutex.acquire(non_blocking=True):
                pass
