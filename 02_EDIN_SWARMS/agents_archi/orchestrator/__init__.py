#!/usr/bin/env python3
# ============================================================================
# BABYLON-60 v4.0 Sovereign Hardened
# █ AGENTS.ARCHI ORCHESTRATOR PACKAGE | STATE: C5-REAL
# ============================================================================
"""Orchestrator package for agents.archi."""

from .swarm import (
    InferenceBackend,
    SwarmConfig,
    AgentPager,
    KernelTelemetry,
    RobustLLMClient,
    SwarmOrchestrator,
)
from .lifecycle import (
    SubagentState,
    SubagentHandle,
    DynamicLifecycleManager,
)
from .royal_rumble import (
    BabylonTrustGateway,
    CortexWalStore,
    ProposedToolAction,
    ResumableTaskExecutor,
    RoyalRumbleBenchmarkReport,
    TrustGatewayVerdict,
    annihilate_wal_triplet,
    compute_idempotency_key,
    run_royal_rumble_endurance_benchmark,
)
from .blackboard import (
    BlackboardAdmissionResult,
    BlackboardArbiter,
    BlackboardDigest,
    BlackboardStatus,
    BlackboardTopic,
    BlackboardTuple,
    ColdPathCurator,
    MAX_CLAIM_CHARS,
    compute_tuple_id,
)

__all__ = [
    "InferenceBackend",
    "SwarmConfig",
    "AgentPager",
    "KernelTelemetry",
    "RobustLLMClient",
    "SwarmOrchestrator",
    "SubagentState",
    "SubagentHandle",
    "DynamicLifecycleManager",
    "BabylonTrustGateway",
    "CortexWalStore",
    "ProposedToolAction",
    "ResumableTaskExecutor",
    "RoyalRumbleBenchmarkReport",
    "TrustGatewayVerdict",
    "annihilate_wal_triplet",
    "compute_idempotency_key",
    "run_royal_rumble_endurance_benchmark",
    "BlackboardAdmissionResult",
    "BlackboardArbiter",
    "BlackboardDigest",
    "BlackboardStatus",
    "BlackboardTopic",
    "BlackboardTuple",
    "ColdPathCurator",
    "MAX_CLAIM_CHARS",
    "compute_tuple_id",
]
