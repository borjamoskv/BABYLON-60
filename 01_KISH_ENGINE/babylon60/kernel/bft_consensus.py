"""
BABYLON-60 BFT Consensus & Thermodynamic Invariant Evaluator
Resuelve fallas Bizantinas (quórum N >= 3f + 1, detección de equivocación)
y evalúa el Principio de Energía Libre sobre árboles AST y dependencias.
"""

from __future__ import annotations

import re
from typing import Any, Mapping

_VALID_DEP_RE = re.compile(r"^[A-Za-z0-9]([A-Za-z0-9._-]*[A-Za-z0-9])?$")
_FORBIDDEN_AST_PRIMITIVES = frozenset({"eval", "exec", "compile", "__import__", "os.system"})
_SLOPSQUAT_MARKERS = ("hallucinated", "slopsquat", "phantom_pkg", "fake_lib", "..", "/", "\\")


class BFTEquivocationError(PermissionError):
    """Se dispara cuando un mismo validador emite votos contradictorios en la misma época/vista."""


def evaluate_thermodynamic_invariants(
    ast_tree: dict[str, Any],
    dependencies: list[str],
    *,
    votes: Mapping[str, str] | None = None,
    committee: set[str] | list[str] | None = None,
    f: int = 0,
) -> dict[str, Any]:
    """
    Auditoría estructural y BFT:
    - Inspecciona recursivamente `ast_tree` buscando primitivas peligrosas o nodos vacíos.
    - Valida sintaxis y marcadores de existencia/slopsquatting en `dependencies`.
    - Si se proporciona `committee` y `votes`, verifica quórum BFT (N >= 3f + 1, votos >= N - f).
    """
    delta_x = 0
    reasons: list[str] = []

    if not isinstance(ast_tree, dict) or not ast_tree:
        delta_x += 1
        reasons.append("EMPTY_OR_INVALID_AST")
    else:
        stack: list[object] = [ast_tree]
        visited = 0
        while stack and visited < 10_000:
            curr = stack.pop()
            visited += 1
            if isinstance(curr, dict):
                node_type = str(curr.get("type", curr.get("node", "")))
                func_name = str(curr.get("func", curr.get("name", curr.get("id", ""))))
                if node_type in _FORBIDDEN_AST_PRIMITIVES or func_name in _FORBIDDEN_AST_PRIMITIVES:
                    delta_x += 15
                    reasons.append(f"FORBIDDEN_AST_PRIMITIVE:{func_name or node_type}")
                stack.extend(curr.values())
            elif isinstance(curr, list):
                stack.extend(curr)
            elif isinstance(curr, str) and curr.strip() in _FORBIDDEN_AST_PRIMITIVES:
                delta_x += 15
                reasons.append(f"FORBIDDEN_AST_PRIMITIVE:{curr.strip()}")

    if not isinstance(dependencies, list):
        delta_x += 10
        reasons.append("INVALID_DEPENDENCIES_CONTAINER")
    else:
        for dep in dependencies:
            if not isinstance(dep, str) or not dep.strip():
                delta_x += 10
                reasons.append("EMPTY_DEPENDENCY")
                continue
            pkg_name = re.split(r"[<>=!~;\[\s]", dep.strip(), maxsplit=1)[0]
            lowered = pkg_name.lower()
            if any(marker in lowered for marker in _SLOPSQUAT_MARKERS) or not _VALID_DEP_RE.match(pkg_name):
                delta_x += 10
                reasons.append(f"EXISTENCE_GAP_OR_INVALID_DEP:{dep}")

    if committee is not None or votes is not None:
        quorum_res = evaluate_bft_quorum(
            votes=dict(votes or {}),
            committee=set(committee or ()),
            f=f,
        )
        if not quorum_res["quorum_reached"]:
            delta_x += 20
            reasons.append(str(quorum_res["reason"]))

    is_valid = delta_x == 0
    return {
        "is_valid": is_valid,
        "delta_x": delta_x,
        "reasons": reasons,
        "action": "PROCEED" if is_valid else "THERMODYNAMIC_OVERRIDE",
    }


def evaluate_bft_quorum(
    votes: Mapping[str, str],
    committee: set[str] | list[str],
    f: int = 1,
    *,
    epoch: int = 1,
    vote_ledger: dict[tuple[int, str], str] | None = None,
) -> dict[str, Any]:
    """
    Evalúa el consenso BFT determinista sobre un comité autorizado:
    - Exige N >= 3f + 1.
    - Detecta equivocación si el mismo nodo vota dos digests distintos en el mismo `epoch`.
    - Exige al menos N - f votos idénticos de miembros autorizados del comité.
    """
    if type(f) is not int or f < 0:
        raise ValueError("BFT parameter f must be a non-negative integer")
    if type(epoch) is not int or epoch <= 0:
        raise ValueError("BFT epoch must be a positive integer")

    authorized = set(committee)
    n_total = len(authorized)
    if n_total < (3 * f) + 1:
        return {
            "quorum_reached": False,
            "winning_digest": None,
            "valid_votes": 0,
            "required_votes": (3 * f) + 1 - f,
            "reason": f"INSUFFICIENT_COMMITTEE:N={n_total}<3f+1={3 * f + 1}",
        }

    required_votes = n_total - f
    tallies: dict[str, int] = {}

    for node_id, digest in votes.items():
        if node_id not in authorized:
            raise PermissionError(f"Sybil vote rejected from unauthorized node: {node_id}")
        if not isinstance(digest, str) or not digest:
            raise ValueError(f"Invalid empty vote digest from node: {node_id}")
        if vote_ledger is not None:
            key = (epoch, node_id)
            prev_digest = vote_ledger.get(key)
            if prev_digest is not None and prev_digest != digest:
                raise BFTEquivocationError(
                    f"Equivocation detected at epoch {epoch} by node '{node_id}': '{prev_digest}' vs '{digest}'"
                )
            vote_ledger[key] = digest
        tallies[digest] = tallies.get(digest, 0) + 1

    for digest, count in tallies.items():
        if count >= required_votes:
            return {
                "quorum_reached": True,
                "winning_digest": digest,
                "valid_votes": count,
                "required_votes": required_votes,
                "reason": "QUORUM_COMMITTED",
            }

    max_votes = max(tallies.values(), default=0)
    return {
        "quorum_reached": False,
        "winning_digest": None,
        "valid_votes": max_votes,
        "required_votes": required_votes,
        "reason": f"QUORUM_NOT_REACHED:{max_votes}/{required_votes}",
    }
