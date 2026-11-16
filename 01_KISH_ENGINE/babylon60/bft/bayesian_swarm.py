# ============================================================================
# BABYLON-60 v4.0 Sovereign Hardened
# █ AUTOCOGNITION-Ω | STATE: C5-REAL | AESTHETIC: INDUSTRIAL_NOIR_2026
# ============================================================================
"""
INV_BFT_04 / Thermodynamic Valve Extension
Bayesian Swarm module with BFT-Resilient Logarithmic Opinion Pooling (LogOP).
Faithful to Gelfand & Dey with Byzantine fault tolerance (f < N/3),
Sybil admission gating, monotonic epoch enforcement, and equivocation detection.
"""

from __future__ import annotations

import asyncio
import math
from typing import Dict, List, Optional

EPISTEMIC_FLOOR: float = 1e-12


class BFTByzantineError(PermissionError):
    """Raised on Sybil injection, BFT equivocation, or stale epoch regression."""


class BayesianSwarm:
    def __init__(self, agents: List[str]) -> None:
        """
        agents: List of authorized BFT agent identifiers.
        """
        self.agents = list(agents)
        self._authorized_agents = set(agents)
        self._lock: Optional[asyncio.Lock] = None
        self._lock_loop: Optional[asyncio.AbstractEventLoop] = None
        self._current_beliefs: Dict[str, float] = {}
        self._current_epoch: int = 0
        self._epoch_history: Dict[int, Dict[str, Dict[str, float]]] = {}

    def _get_lock(self) -> asyncio.Lock:
        try:
            running_loop = asyncio.get_running_loop()
        except RuntimeError:
            running_loop = None
        if self._lock is None or (running_loop is not None and self._lock_loop is not running_loop):
            self._lock = asyncio.Lock()
            self._lock_loop = running_loop
        return self._lock

    @property
    def current_epoch(self) -> int:
        return self._current_epoch

    async def async_pool_and_update(
        self,
        opinions: Dict[str, Dict[str, float]],
        weights: Dict[str, float] | None = None,
        *,
        epoch: Optional[int] = None,
    ) -> Dict[str, float]:
        """
        [FRENTE-037 / BFT-5] Coroutine-safe asynchronous opinion pool update.
        Enforces monotonic epoch progression and detects same-epoch equivocation.
        """
        async with self._get_lock():
            if epoch is not None:
                if type(epoch) is not int or epoch <= 0:
                    raise ValueError("BFT epoch must be a positive integer")
                if epoch < self._current_epoch:
                    raise BFTByzantineError(
                        f"Stale BFT epoch rejected: incoming epoch {epoch} < current_epoch {self._current_epoch}"
                    )
                prior_votes = self._epoch_history.setdefault(epoch, {})
                for agent, dist in opinions.items():
                    canonical_dist = {k: float(v) for k, v in dist.items()}
                    if agent in prior_votes and prior_votes[agent] != canonical_dist:
                        raise BFTByzantineError(
                            f"BFT Equivocation detected: agent '{agent}' submitted conflicting beliefs in epoch {epoch}"
                        )
                for agent, dist in opinions.items():
                    prior_votes[agent] = {k: float(v) for k, v in dist.items()}

            result = self.logarithmic_opinion_pool(opinions, weights)
            if epoch is not None and epoch > self._current_epoch:
                self._current_epoch = epoch
            self._current_beliefs = result
            return result

    def get_beliefs(self) -> Dict[str, float]:
        """Returns the latest consolidated beliefs."""
        return dict(self._current_beliefs)

    @staticmethod
    def _validate_scalar_probability(value: object, label: str) -> float:
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise ValueError(f"Invalid {label}: expected real number, got {type(value).__name__}")
        fval = float(value)
        if math.isnan(fval) or math.isinf(fval):
            raise ValueError(f"Invalid {label}: NaN or Inf is forbidden in BFT opinion pooling")
        return fval

    def logarithmic_opinion_pool(
        self, opinions: Dict[str, Dict[str, float]], weights: Dict[str, float] | None = None
    ) -> Dict[str, float]:
        """
        Computes the BFT-Resilient Logarithmic Opinion Pool (LogOP) of categorical distributions.

        - Enforces membership against `self.agents` (when non-empty) to block Sybil injection.
        - Rejects NaN, Inf, negative probabilities, and negative weights.
        - Ignores agents with weight w <= 0.0 so zero-weight nodes cannot veto.
        - Applies BFT fault tolerance (f = (N_active - 1) // 3): for N_active >= 4, a hypothesis
          is only hard-vetoed to 0.0 if at least (f + 1) active agents assign p <= 0.0; isolated
          zero votes (<= f) are clamped to EPISTEMIC_FLOOR so f Byzantine nodes cannot veto 2f+1 honest nodes.
        """
        if not opinions:
            return {}

        if self._authorized_agents:
            unauthorized = [agent for agent in opinions if agent not in self._authorized_agents]
            if unauthorized:
                raise BFTByzantineError(f"Sybil agent(s) not in authorized BFT committee: {unauthorized}")

        if weights is None:
            raw_weights = {agent: 1.0 / len(opinions) for agent in opinions}
        else:
            raw_weights = {}
            for agent in opinions:
                w_raw = weights.get(agent, 0.0)
                w_val = self._validate_scalar_probability(w_raw, f"weight for {agent}")
                if w_val < 0.0:
                    raise ValueError(f"Negative weight for agent {agent}: {w_val}")
                raw_weights[agent] = w_val

        # Filter to active agents with strictly positive weight
        active_agents = [agent for agent, w in raw_weights.items() if w > 0.0]
        if not active_agents:
            return {}

        weight_sum = sum(raw_weights[a] for a in active_agents)
        norm_weights = {a: raw_weights[a] / weight_sum for a in active_agents}

        # Validate all probability entries upfront and collect hypothesis universe
        hypotheses: set[str] = set()
        for agent in active_agents:
            dist = opinions[agent]
            if not isinstance(dist, dict):
                raise ValueError(f"Opinion distribution for {agent} must be a dict")
            for hyp, prob in dist.items():
                p_val = self._validate_scalar_probability(prob, f"probability P({hyp}|{agent})")
                if p_val < 0.0 or p_val > 1.0:
                    raise ValueError(f"Probability out of [0, 1] range for {agent}.{hyp}: {p_val}")
                hypotheses.add(hyp)

        n_active = len(active_agents)
        # Maximum Byzantine faults tolerated in N >= 3f + 1 is f = (N - 1) // 3.
        # Hard veto requires at least f + 1 zero-votes (guaranteeing at least 1 honest veto).
        max_byzantine_faults = (n_active - 1) // 3 if n_active >= 4 else 0
        veto_quorum_threshold = max_byzantine_faults + 1

        aggregated_unnormalized: Dict[str, float] = {}

        for hyp in hypotheses:
            zero_vote_count = 0
            for agent in active_agents:
                if float(opinions[agent].get(hyp, 0.0)) <= 0.0:
                    zero_vote_count += 1

            if zero_vote_count >= veto_quorum_threshold:
                aggregated_unnormalized[hyp] = 0.0
                continue

            supporting_agents = [a for a in active_agents if float(opinions[a].get(hyp, 0.0)) > 0.0]
            support_weight_sum = sum(norm_weights[a] for a in supporting_agents)
            log_sum = 0.0
            for agent in supporting_agents:
                p = float(opinions[agent][hyp])
                w = norm_weights[agent] / support_weight_sum
                log_sum += w * math.log(max(p, EPISTEMIC_FLOOR))

            aggregated_unnormalized[hyp] = math.exp(log_sum)

        total_mass = sum(aggregated_unnormalized.values())
        if total_mass <= 0.0:
            return {hyp: 0.0 for hyp in hypotheses}

        return {hyp: val / total_mass for hyp, val in aggregated_unnormalized.items()}
