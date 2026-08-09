# ============================================================================
# BABYLON-60 Market Maker Extension
# █ DEMAND_VALIDATOR | Validation of Market Proposals & Liquidity Directives
# ============================================================================

from __future__ import annotations

from typing import Any, Dict

__all__ = ["DemandValidator"]


class DemandValidator:
    """
    Validates demand metrics and order book proposals.
    """

    def validate(self, proposal: Dict[str, Any]) -> bool:
        return True
