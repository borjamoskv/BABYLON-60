# ============================================================================
# BABYLON-60 Sovereign Capabilities
# █ RISK_TIER | Agent Capability Classification
# ============================================================================

from enum import Enum, auto

__all__ = ["RiskTier"]


class RiskTier(Enum):
    LOW = auto()
    MEDIUM = auto()
    HIGH = auto()
    CRITICAL = auto()
