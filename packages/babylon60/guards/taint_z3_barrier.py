# ============================================================================
# BABYLON-60 v4.0 Sovereign Hardened
# █ TAINT_Z3_BARRIER | Formal SMT Barrier for CORTEX-TAINT System
# ============================================================================
# STATE: C5-REAL (Zero-Anergy, Deterministic Taint-Aware State Transitions)
# ============================================================================
"""
Barrera SMT formal para el sistema CORTEX-TAINT de BABYLON-60.

Implementa la verificación determinista de transiciones de estado
considerando el bit de contaminación (taint) del contexto de ejecución:

    PermitirExec(Acción, x_ctx) ⟺ ¬(EsCritica(Acción) ∧ τ(x_ctx))

Si el contexto lleva la marca TAINT_UNTRUSTED, el solver Z3 devuelve
UNSAT y aborta la ejecución antes de que el comando toque el sistema.
"""

from __future__ import annotations

import logging
from typing import Any, Optional, Tuple

from babylon60.verification.z3_compiler import PydanticModelIR, Z3ConstraintEmitter

logger = logging.getLogger("babylon60.guards.taint_z3_barrier")

__all__ = ["TaintZ3Barrier", "TaintCheckResult"]


class TaintCheckResult:
    """Resultado de una verificación de barrera taint/SMT."""

    __slots__ = ("allowed", "reason", "solver_result")

    def __init__(
        self,
        allowed: bool,
        reason: str,
        solver_result: Optional[str] = None,
    ):
        self.allowed = allowed
        self.reason = reason
        self.solver_result = solver_result

    def __repr__(self) -> str:
        status = "PERMIT" if self.allowed else "DENY"
        return f"TaintCheckResult({status}: {self.reason})"

    def __bool__(self) -> bool:
        return self.allowed


class TaintZ3Barrier:
    """Barrera SMT formal para CORTEX-TAINT.

    Evalúa la proposición:
        PermitirExec(Acción, x_ctx) ⟺ ¬(EsCritica(Acción) ∧ τ(x_ctx))

    Donde τ(x_ctx) es el bit de contaminación monótona del contexto
    y EsCritica(Acción) clasifica la acción según el RiskTier.
    """

    def __init__(
        self,
        rlimit: int = 512 * 1024 * 1024,
        timeout_ms: int = 5000,
    ):
        self._rlimit = rlimit
        self._timeout_ms = timeout_ms
        self._z3 = None
        self._emitter = Z3ConstraintEmitter(
            rlimit=rlimit, timeout_ms=timeout_ms
        )

    def _ensure_z3(self):
        """Lazy import de z3."""
        if self._z3 is None:
            try:
                import z3
                self._z3 = z3
            except ImportError:
                raise ImportError(
                    "z3-solver is required for taint barrier. "
                    "Install with: pip install 'babylon60[smt]'"
                )
        return self._z3

    def check_transition(
        self,
        action_name: str,
        is_critical: bool,
        taint_bit: bool,
        model_constraints: Any = None,
    ) -> TaintCheckResult:
        """Verifica si una transición de estado es permitida.

        Implementa la regla formal:
            DENY iff (is_critical ∧ taint_bit)

        Opcionalmente verifica restricciones adicionales del modelo
        si se proporciona un z3.Solver con constraints del payload.

        Args:
            action_name: Nombre de la acción a ejecutar.
            is_critical: True si la acción requiere privilegios elevados.
            taint_bit: True si el contexto contiene datos UNTRUSTED.
            model_constraints: Solver Z3 opcional con restricciones del modelo.

        Returns:
            TaintCheckResult con la decisión PERMIT/DENY.
        """
        z3 = self._ensure_z3()

        # Core taint check: ¬(is_critical ∧ taint_bit)
        if is_critical and taint_bit:
            logger.warning(
                "[CORTEX-TAINT] BLOCKED: Critical action '%s' with UNTRUSTED context",
                action_name,
            )
            return TaintCheckResult(
                allowed=False,
                reason=(
                    f"Critical action '{action_name}' denied: "
                    f"context carries TAINT_UNTRUSTED bit"
                ),
                solver_result="DETERMINISTIC_DENY",
            )

        # If non-critical or trusted, optionally verify model constraints
        if model_constraints is not None:
            try:
                result = model_constraints.check()
                if result == z3.sat:
                    return TaintCheckResult(
                        allowed=True,
                        reason=f"Action '{action_name}' permitted: model constraints satisfiable",
                        solver_result="sat",
                    )
                elif result == z3.unsat:
                    logger.warning(
                        "[CORTEX-TAINT] BLOCKED: Action '%s' model constraints UNSAT",
                        action_name,
                    )
                    return TaintCheckResult(
                        allowed=False,
                        reason=f"Action '{action_name}' denied: model constraints unsatisfiable",
                        solver_result="unsat",
                    )
                else:
                    logger.warning(
                        "[CORTEX-TAINT] UNKNOWN: Action '%s' solver timeout/rlimit",
                        action_name,
                    )
                    return TaintCheckResult(
                        allowed=False,
                        reason=f"Action '{action_name}' denied: solver returned UNKNOWN (timeout/rlimit)",
                        solver_result="unknown",
                    )
            except Exception as e:
                logger.error(
                    "[CORTEX-TAINT] Solver error for '%s': %s", action_name, e
                )
                return TaintCheckResult(
                    allowed=False,
                    reason=f"Action '{action_name}' denied: solver error ({e})",
                    solver_result="error",
                )

        # No model constraints and taint check passed
        return TaintCheckResult(
            allowed=True,
            reason=f"Action '{action_name}' permitted: no taint conflict",
            solver_result="PASS",
        )

    def validate_model_satisfiability(
        self, model_ir: PydanticModelIR
    ) -> Tuple[bool, str]:
        """Verifica que las restricciones generadas de un modelo son satisfacibles.

        Args:
            model_ir: Representación intermedia del modelo Pydantic.

        Returns:
            Tuple de (es_satisfacible, descripción).
        """
        result = self._emitter.check_satisfiability(model_ir)
        if result.error:
            return False, f"Compilation error: {result.error}"
        if result.is_satisfiable is True:
            return True, f"Model {result.model_name}: SAT ({result.num_constraints} constraints)"
        elif result.is_satisfiable is False:
            return False, f"Model {result.model_name}: UNSAT — contradictory constraints detected"
        else:
            return False, f"Model {result.model_name}: UNKNOWN — solver timeout/rlimit exceeded"

    def check_transition_with_z3_proof(
        self,
        action_name: str,
        is_critical: bool,
        taint_bit: bool,
    ) -> TaintCheckResult:
        """Verifica transición con prueba formal Z3 completa.

        Construye y resuelve la proposición SMT:
            ¬(is_critical ∧ taint_bit)

        Args:
            action_name: Nombre de la acción.
            is_critical: Si la acción es crítica.
            taint_bit: Si el contexto está contaminado.

        Returns:
            TaintCheckResult con prueba formal.
        """
        z3 = self._ensure_z3()

        solver = z3.Solver()
        solver.set("timeout", self._timeout_ms)

        # Declare boolean variables
        critical_var = z3.Bool("is_critical")
        taint_var = z3.Bool("taint_bit")
        permit_var = z3.Bool("permit")

        # Assert known values
        solver.add(critical_var == is_critical)
        solver.add(taint_var == taint_bit)

        # Core rule: permit ⟺ ¬(critical ∧ taint)
        solver.add(permit_var == z3.Not(z3.And(critical_var, taint_var)))

        # Check if permit is satisfiable when True
        solver.push()
        solver.add(permit_var)
        result = solver.check()
        solver.pop()

        if result == z3.sat:
            return TaintCheckResult(
                allowed=True,
                reason=f"Z3 proved: action '{action_name}' is SAFE",
                solver_result="sat",
            )
        else:
            return TaintCheckResult(
                allowed=False,
                reason=f"Z3 proved: action '{action_name}' is BLOCKED (critical={is_critical}, taint={taint_bit})",
                solver_result=str(result),
            )
