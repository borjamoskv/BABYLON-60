# ============================================================================
# BABYLON-60 v5.0 Sovereign Hardened
# █ AUTODIDACT-Ω | HARROP LOGIC COMPILER & HUME GUILLOTINE | STATE: C5-REAL
# ============================================================================
"""
Compilador Epistemológico de Harrop y Validador de la Guillotina de Hume.
Implementación determinista equivalente a strike_rs::omega0.
"""

from __future__ import annotations

import hashlib
import json
from typing import List, Optional, Set

from babylon60.autodidact.types import (
    Justification,
    JustifiedStatement,
    Modality,
    Obligation,
    Statement,
)


class HumeViolationError(ValueError):
    """Violación de la Guillotina de Hume: Imposible derivar lo deóntico de lo puramente epistémico."""

    pass


class UnverifiedPremiseError(ValueError):
    """Una premisa necesaria para la deducción falló la verificación de sus obligaciones."""

    pass


def hash_statement(s: Statement) -> str:
    """Computa deterministamente el hash canónico de un Statement."""
    h = hashlib.sha256()
    h.update(s.content.strip().encode("utf-8"))
    h.update(f":{s.modality.value}".encode("utf-8"))
    for ob in sorted([o.value for o in s.obligations]):
        h.update(f":{ob}".encode("utf-8"))
    return f"STMT:{h.hexdigest()}"


def hash_justification(j: Justification) -> str:
    """Computa deterministamente el hash canónico de una Justification."""
    h = hashlib.sha256()
    h.update(j.kind.encode("utf-8"))
    h.update(f":{j.confidence:.4f}".encode("utf-8"))
    param_str = json.dumps(j.parameters, sort_keys=True)
    h.update(param_str.encode("utf-8"))
    return f"JUST:{h.hexdigest()}"


def verify(js: JustifiedStatement, nogoods: Optional[Set[str]] = None) -> bool:
    """
    Operador 1: verify : J x S -> {true, false}.
    Comprueba si una Justificación satisface todas las obligaciones de un Statement.
    """
    if nogoods is None:
        nogoods = set()

    s = js.statement
    j = js.justification

    # Proposición sin obligaciones es trivialmente verificada si no es conjetura pura sin confianza
    if not s.obligations:
        if j.kind == "Conjecture" and j.confidence <= 0.0:
            return False
        return True

    s_hash = js.statement_hash or hash_statement(s)

    for obligation in s.obligations:
        if obligation == Obligation.PROVENANCE:
            if j.kind == "Conjecture":
                return False
        elif obligation == Obligation.REPRODUCIBILITY:
            if j.kind not in ("FormalProof", "StatisticalInference", "Observation", "SiliconBenchmark"):
                return False
        elif obligation == Obligation.CONFIDENCE:
            if j.kind == "FormalProof":
                pass
            elif j.kind == "StatisticalInference" and j.confidence < 0.95:
                return False
            elif j.kind == "ExpertConsensus" and j.confidence < 0.67:
                return False
            elif j.kind == "Conjecture":
                return False
        elif obligation == Obligation.CONTRADICTION:
            if s_hash in nogoods:
                return False
        elif obligation == Obligation.FRESHNESS:
            if j.kind == "Conjecture":
                return False
        elif obligation == Obligation.COMPLETENESS:
            if j.kind == "Conjecture":
                return False

    return True


def derive(
    premises: List[JustifiedStatement],
    goal: Statement,
    nogoods: Optional[Set[str]] = None,
) -> JustifiedStatement:
    """
    Operador 2: derive : P(S x J) x S -> (S x J).
    Sintetiza una nueva prueba para un objetivo a partir de premisas verificadas.
    Aplica formalmente la regla de Hume:
    Gamma_Epistemic |/- S_Deontic
    """
    if not premises:
        raise ValueError("Premisas vacías: no se puede derivar sin premisas.")

    if nogoods is None:
        nogoods = set()

    # REGLA DE HUME: Metas deónticas exigen al menos una premisa deóntica.
    if goal.modality == Modality.DEONTIC:
        has_deontic_premise = any(p.statement.modality == Modality.DEONTIC for p in premises)
        try:
            import strike_rs

            if hasattr(strike_rs, "py_enforce_hume_guillotine"):
                strike_rs.py_enforce_hume_guillotine(has_deontic_premise, goal.modality.value)
        except RuntimeError as ex:
            raise HumeViolationError(str(ex))
        except (ImportError, Exception):
            pass

        if not has_deontic_premise:
            raise HumeViolationError(
                f"Hume's Guillotine Breach (INV_C5_HUME_GUILLOTINE): "
                f"No se puede derivar la conclusión deóntica '{goal.content}' a partir de premisas puramente epistémicas."
            )

    # Todas las premisas deben pasar verificación
    for p in premises:
        if not verify(p, nogoods=nogoods):
            raise UnverifiedPremiseError(f"Premisa no verificada: '{p.statement.content}' falló sus obligaciones.")

    premise_refs = [p.statement.content for p in premises]
    proof_term = f"derived[{' ∧ '.join(premise_refs)}]"

    justification = Justification(
        kind="FormalProof",
        parameters={
            "proof_term": proof_term,
            "premises": premise_refs,
        },
        confidence=1.0,
    )

    js = JustifiedStatement(statement=goal, justification=justification)
    js.statement_hash = hash_statement(goal)
    return js


def optimize(proof: List[JustifiedStatement], nogoods: Optional[Set[str]] = None) -> List[JustifiedStatement]:
    """
    Operador 3: optimize : List(S x J) -> List(S x J).
    Normalización de pruebas: elimina aserciones no verificadas y deduplica por contenido.
    Invariantes:
    - Conservatividad: optimize(P) |- s <==> P |- s
    - Idempotencia: optimize(optimize(P)) == optimize(P)
    """
    result: List[JustifiedStatement] = []
    seen: Set[tuple[str, str]] = set()

    for js in proof:
        if not verify(js, nogoods=nogoods):
            continue
        key = (js.statement.content.strip(), js.statement.modality.value)
        if key not in seen:
            seen.add(key)
            result.append(js)

    return result
