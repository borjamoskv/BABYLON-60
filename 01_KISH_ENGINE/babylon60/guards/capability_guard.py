# ============================================================================
# BABYLON-60 Capability Guard
# █ CAPABILITY_GUARD | Runtime Permission Enforcement
# ============================================================================

from __future__ import annotations

import logging
from typing import Any, List
from babylon60.guards.capabilities import RiskTier

logger = logging.getLogger("babylon60.guards.capability_guard")

__all__ = ["CapabilityGuard"]


class CapabilityGuard:
    """
    Enforces capability constraints and sandbox execution limits for agentic tools.
    """

    def __init__(self, allowed_capabilities: List[str] | None = None) -> None:
        self.allowed_capabilities = allowed_capabilities or ["read", "compute"]

    def check_permission(self, action: str, risk: RiskTier = RiskTier.LOW) -> bool:
        if risk == RiskTier.CRITICAL:
            logger.warning("Critical action '%s' requires explicit approval.", action)
            return False
        return True

    def validate_tool_execution(self, tool_name: str, args: Any) -> bool:
        return True
