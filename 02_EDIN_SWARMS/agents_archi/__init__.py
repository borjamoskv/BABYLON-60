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
)
from .topologies import (
    SwarmRouter,
    TopologyTarget,
    EdinTopology,
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
    # Topologies
    "SwarmRouter",
    "TopologyTarget",
    "EdinTopology",
    # Protocols
    "Modality",
    "Proposition",
    "AOFValidator",
    "AttestationEnvelope",
    # Clients
    "KimiClient",
    "OpenRouterClient",
]
