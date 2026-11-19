#!/usr/bin/env python3
# ============================================================================
# BABYLON-60 v4.0 Sovereign Hardened
# █ TOPOLOGIES PACKAGE | DOMAIN: agents.archi | STATE: C5-REAL
# ============================================================================
"""Topologies package for agents.archi."""

from .router import SwarmRouter, TopologyTarget
from .edin import EdinTopology
from .babylon21_consolidation import (
    ArchitecturalRing,
    AgentGateOutcome,
    BABYLON21_AGENTS,
    Babylon21ConsolidationTopology,
    ConsolidationAgentId,
    ConsolidationAgentSpec,
    ConsolidationSealReceipt,
    ConsolidationSquad,
)
from .distribution_design import DistributionDesignTeam, AgentRole, AgentSpecification
from .social_media_team import SocialMediaTeam, SocialAgentRole, SocialAgentSpecification
from .autodidact_topology import AutodidactSwarmTopology
from .rea_harness_topology import (
    ReaHarnessSwarmTopology,
    ReaSubagentClawCode,
    ReaSubagentDeepSeekHarness,
    ReaSubagentOpenClaw,
    ReaSwarmConsolidationReceipt,
)

__all__ = [
    "SwarmRouter",
    "TopologyTarget",
    "EdinTopology",
    "ArchitecturalRing",
    "AgentGateOutcome",
    "BABYLON21_AGENTS",
    "Babylon21ConsolidationTopology",
    "ConsolidationAgentId",
    "ConsolidationAgentSpec",
    "ConsolidationSealReceipt",
    "ConsolidationSquad",
    "DistributionDesignTeam",
    "AgentRole",
    "AgentSpecification",
    "SocialMediaTeam",
    "SocialAgentRole",
    "SocialAgentSpecification",
    "AutodidactSwarmTopology",
    "ReaHarnessSwarmTopology",
    "ReaSubagentClawCode",
    "ReaSubagentOpenClaw",
    "ReaSubagentDeepSeekHarness",
    "ReaSwarmConsolidationReceipt",
]
