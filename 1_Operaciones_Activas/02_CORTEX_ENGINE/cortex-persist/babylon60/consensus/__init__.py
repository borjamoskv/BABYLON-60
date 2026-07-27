# [C5-REAL] Exergy-Maximized
"""Consensus.

Neural Swarm Consensus and Reputation-Weighted validation.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from babylon60.consensus.manager import ConsensusManager as ConsensusManager

if TYPE_CHECKING:
    from babylon60.consensus.reputation import (
        ReputationManager,  # pyright: ignore[reportMissingImports]
    )
    from babylon60.consensus.trust import TrustGraph  # pyright: ignore[reportMissingImports]
else:
    # Runtime optional loading
    ReputationManager: Any = None
    TrustGraph: Any = None
    try:
        from babylon60.consensus.reputation import ReputationManager as _RM

        ReputationManager = _RM
    except ImportError:
        pass

    try:
        from babylon60.consensus.trust import TrustGraph as _TG

        TrustGraph = _TG
    except ImportError:
        pass


__all__ = ["ConsensusManager", "ReputationManager", "TrustGraph"]
