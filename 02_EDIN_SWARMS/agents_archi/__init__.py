#!/usr/bin/env python3
# ============================================================================
# BABYLON-60 v4.0 Sovereign Hardened
# █ AGENTS.ARCHI ROOT PACKAGE | DOMAIN: agents.archi | STATE: C5-REAL
# ============================================================================
"""
agents_archi: Sovereign Swarm Topologies, Agentic Lifecycles, and Protocols.

Chamber 3 of BABYLON-60 Tripartite Architecture.
"""

from .orchestrator import (
    InferenceBackend,
    SwarmConfig,
    AgentPager,
    KernelTelemetry,
    RobustLLMClient,
    SwarmOrchestrator,
    SubagentState,
    SubagentHandle,
    DynamicLifecycleManager,
    BabylonTrustGateway,
    CortexWalStore,
    ProposedToolAction,
    ResumableTaskExecutor,
    RoyalRumbleBenchmarkReport,
    TrustGatewayVerdict,
    annihilate_wal_triplet,
    compute_idempotency_key,
    run_royal_rumble_endurance_benchmark,
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
from .topologies import (
    SwarmRouter,
    TopologyTarget,
    EdinTopology,
    DistributionDesignTeam,
    AgentRole,
    AgentSpecification,
    SocialMediaTeam,
    SocialAgentRole,
    SocialAgentSpecification,
)
from .protocols import (
    Modality,
    Proposition,
    AOFValidator,
    AttestationEnvelope,
)
from .clients import (
    KimiClient,
    OpenRouterClient,
    OpenRouterRoleTier,
    QuotaBudgetTracker,
    SensitivePathGuard,
    TokenBucketRateLimiter,
)

__all__ = [
    # Orchestrator
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
    # Topologies
    "SwarmRouter",
    "TopologyTarget",
    "EdinTopology",
    "DistributionDesignTeam",
    "AgentRole",
    "AgentSpecification",
    "SocialMediaTeam",
    "SocialAgentRole",
    "SocialAgentSpecification",
    # Protocols
    "Modality",
    "Proposition",
    "AOFValidator",
    "AttestationEnvelope",
    # Clients
    "KimiClient",
    "OpenRouterClient",
    "OpenRouterRoleTier",
    "QuotaBudgetTracker",
    "SensitivePathGuard",
    "TokenBucketRateLimiter",
]
