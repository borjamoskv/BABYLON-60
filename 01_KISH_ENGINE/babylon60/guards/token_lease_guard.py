"""
TokenLease & Cost Circuit Breaker Guard (V1: Paperclip/Skills Assimilation) - C5-REAL Ring-0.
Gobernanza atómica de presupuesto por subagente en enjambres SHARUR / CORTEX.
Implementa contabilidad diferencial (5x output/thinking weight, 95% implicit cache discount)
y disyuntor fail-closed ante bucles de exploración anérgica.
"""

from __future__ import annotations

import hashlib
import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional


class TokenLeaseViolationError(RuntimeError):
    """Disparado en modo fail-closed cuando un subagente viola su contrato de presupuesto."""


@dataclass
class TokenUsageStep:
    step_index: int
    input_tokens: int
    cached_tokens: int
    output_tokens: int
    verified_outcome: bool = False
    timestamp_ns: int = field(default_factory=time.monotonic_ns)

    @property
    def effective_cost_units(self) -> float:
        """
        Calcula unidades de coste ponderadas según INV_C5_ARGON_GOVERNANCE:
        - Tokens no cacheados de entrada: 1.0x
        - Tokens cacheados (Implicit Caching 95% off): 0.05x
        - Tokens de salida + thinking: 5.0x
        """
        uncached_in = max(0, self.input_tokens - self.cached_tokens)
        return (uncached_in * 1.0) + (self.cached_tokens * 0.05) + (self.output_tokens * 5.0)


@dataclass
class TokenLease:
    agent_id: str
    role: str
    max_effective_units: float = 150_000.0
    max_unverified_steps: int = 4
    steps: List[TokenUsageStep] = field(default_factory=list)
    tripped: bool = False
    trip_reason: Optional[str] = None

    @property
    def consumed_units(self) -> float:
        return sum(s.effective_cost_units for s in self.steps)

    @property
    def remaining_units(self) -> float:
        return max(0.0, self.max_effective_units - self.consumed_units)

    @property
    def consecutive_unverified_steps(self) -> int:
        count = 0
        for s in reversed(self.steps):
            if s.verified_outcome:
                break
            count += 1
        return count

    def record_step(
        self,
        input_tokens: int,
        output_tokens: int,
        cached_tokens: int = 0,
        verified_outcome: bool = False,
    ) -> TokenUsageStep:
        """Registra un turno de inferencia y evalúa el disyuntor termodinámico."""
        if self.tripped:
            raise TokenLeaseViolationError(f"[FAIL-CLOSED] Lease de {self.agent_id} ya disparado: {self.trip_reason}")

        step = TokenUsageStep(
            step_index=len(self.steps),
            input_tokens=input_tokens,
            cached_tokens=cached_tokens,
            output_tokens=output_tokens,
            verified_outcome=verified_outcome,
        )
        self.steps.append(step)

        if self.consumed_units > self.max_effective_units:
            self.tripped = True
            self.trip_reason = (
                f"Presupuesto agotado: {self.consumed_units:.1f} > {self.max_effective_units:.1f} unidades"
            )
            raise TokenLeaseViolationError(f"[FAIL-CLOSED] {self.agent_id}: {self.trip_reason}")

        if self.consecutive_unverified_steps > self.max_unverified_steps:
            self.tripped = True
            self.trip_reason = f"Bucle de exploración sin salida verificada ({self.consecutive_unverified_steps} pasos)"
            raise TokenLeaseViolationError(f"[FAIL-CLOSED] {self.agent_id}: {self.trip_reason}")

        return step

    def seal_receipt_sha256(self) -> str:
        """Genera un recibo determinista SHA-256 de la ejecución del subagente."""
        payload = f"{self.agent_id}:{self.role}:{len(self.steps)}:{self.consumed_units:.2f}:{self.tripped}"
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()


class SwarmLeaseRegistry:
    """Registro centralizado O(1) de presupuestos de subagentes para SHARUR / CORTEX."""

    def __init__(self) -> None:
        self._leases: Dict[str, TokenLease] = {}

    def issue_lease(
        self,
        agent_id: str,
        role: str,
        max_effective_units: float = 150_000.0,
        max_unverified_steps: int = 4,
    ) -> TokenLease:
        if role not in ("arquitecto", "ejecutor", "auditor"):
            raise ValueError(f"Rol no canónico en CORTEX: {role}")
        lease = TokenLease(
            agent_id=agent_id,
            role=role,
            max_effective_units=max_effective_units,
            max_unverified_steps=max_unverified_steps,
        )
        self._leases[agent_id] = lease
        return lease

    def get_lease(self, agent_id: str) -> TokenLease:
        if agent_id not in self._leases:
            raise KeyError(f"Subagente sin TokenLease registrado: {agent_id}")
        return self._leases[agent_id]
