# [C5-REAL] Exergy-Maximized
"""
ψSAP (Symbolic Action Principle) - Lagrangian Formalism for CORTEX.

Phase 2 (v3): Operationalizes the Recursive Identity Field (RIF) by
measuring the 'effort' it takes to maintain coherence.

The symbolic Lagrangian is defined as:
    L_ψ = K_ψ(t) - S_ψentropy(t) + G_grace(t) - F_collapse(t)
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from typing import Any

from babylon60.extensions.evolution.agents import AgentDomain, EnneagramSovereign
from babylon60.extensions.evolution.cortex_metrics import DomainMetrics

logger = logging.getLogger(__name__)


@dataclass
class SymbolicActionState:
    """The current state of a domain in the ψ-action landscape."""

    domain: AgentDomain
    timestamp: float = field(default_factory=time.time)

    momentum: float = 0.0

    entropy_resistance: float = 0.0

    grace: float = 0.0

    collapse_potential: float = 0.0

    lagrangian: float = 0.0

    cumulative_action: float = 0.0


class SymbolicActionEngine:
    """Calculates and monitors ψSAP metrics across domains."""

    def __init__(self):
        self._history: dict[AgentDomain, list[SymbolicActionState]] = {d: [] for d in AgentDomain}

    def compute_state(
        self, agent: EnneagramSovereign, metrics: DomainMetrics, grace_injection: float = 0.0
    ) -> SymbolicActionState:
        """Compute the current L_ψ for an agent domain."""

        momentum = max(0.0, metrics.fitness_delta)

        entropy_res = (metrics.ghost_density * 5.0) + (metrics.error_rate * 3.0)

        collapse_pot = (1.0 - metrics.health_score) * 10.0

        grace = grace_injection

        lagrangian = momentum - entropy_res + grace - collapse_pot

        state = SymbolicActionState(
            domain=agent.domain,
            momentum=momentum,
            entropy_resistance=entropy_res,
            grace=grace,
            collapse_potential=collapse_pot,
            lagrangian=lagrangian,
        )

        history = self._history[agent.domain]
        if history:
            prev = history[-1]
            dt = state.timestamp - prev.timestamp
            state.cumulative_action = prev.cumulative_action + (lagrangian * dt)
        else:
            state.cumulative_action = lagrangian

        history.append(state)
        if len(history) > 100:
            history.pop(0)

        return state

    def get_report(self) -> dict[str, Any]:
        """Aggregate report of action states across all domains."""
        report = {}
        for domain, history in self._history.items():
            if history:
                curr = history[-1]
                report[domain.name] = {
                    "lagrangian": round(curr.lagrangian, 2),
                    "momentum": round(curr.momentum, 2),
                    "entropy": round(curr.entropy_resistance, 2),
                    "grace": round(curr.grace, 2),
                    "collapse": round(curr.collapse_potential, 2),
                    "action": round(curr.cumulative_action, 2),
                }
        return report
