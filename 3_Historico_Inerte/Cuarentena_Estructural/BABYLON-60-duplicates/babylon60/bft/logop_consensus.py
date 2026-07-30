# C5-REAL EXERGY CERTIFIED
# [C5-REAL] Exergy-Maximized
"""Logarithmic Opinion Pooling (LogOP) Consensus Engine.

Enforces INV_BFT_LOGOP:
When aggregating heuristic probabilities from a Bayesian Swarm (multiple BFT agents),
the system MUST use Logarithmic Opinion Pooling (geometric weighted mean) rather than
Linear Pooling.

Mathematical Invariant:
If any expert assigns a strict P=0 to a hypothesis (an Absolute Veto based on falsification),
the aggregate pool mathematically collapses to 0, overriding any Byzantine 'tyranny of the masses'
attempting to force a hallucinated consensus.
"""

from __future__ import annotations

import math
from typing import Sequence


class LogOPConsensusEngine:
    """Logarithmic Opinion Pooling (LogOP) Aggregator."""

    @staticmethod
    def aggregate(probabilities: Sequence[float], weights: Sequence[float] | None = None) -> float:
        """
        Calculates the Logarithmic Opinion Pool (geometric weighted mean) of probabilities.
        
        Args:
            probabilities: List of probabilities p_i in [0.0, 1.0].
            weights: List of weights w_i >= 0. Defaults to equal weights.
            
        Returns:
            Aggregated probability in [0.0, 1.0]. Returns 0.0 if any p_i == 0.0 (Absolute Veto).
        """
        if not probabilities:
            return 0.0

        n = len(probabilities)
        if weights is None:
            weights = [1.0 / n] * n
        else:
            total_w = sum(weights)
            if total_w <= 0:
                raise ValueError("Total weights must be strictly positive.")
            weights = [w / total_w for w in weights]

        assert len(probabilities) == len(weights), "Probabilities and weights must have equal length."

        # Absolute Veto Check: Any p_i == 0.0 mathematical collapse to 0.0 in O(1)
        for p in probabilities:
            if p <= 0.0:
                return 0.0

        # LogOP Calculation: exp(sum(w_i * ln(p_i)))
        log_sum = sum(w * math.log(p) for p, w in zip(probabilities, weights))
        
        # Exponential un-log
        aggregated_p = math.exp(log_sum)
        
        # Clamp bounds [0.0, 1.0] for floating point precision safety
        return max(0.0, min(1.0, aggregated_p))
