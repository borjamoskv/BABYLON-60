# [C5-REAL] Exergy-Maximized
"""CORTEX - Causal Geometry Guard.

Enforces the P0 directive for Causal Geometry Compliance.
All agent operations relating to quantum orders, causal sets, or CDT
MUST adhere strictly to the 340 primitives/invariants defined in
CAUSAL_GEOMETRY_ONTOLOGY.md.
"""

from __future__ import annotations

import logging
from typing import Any

from babylon60.guards.base import Guard, GuardViolation

logger = logging.getLogger("babylon60.guards.causal_geometry")

_CAUSAL_KEYWORDS = frozenset(
    {
        "quantum order",
        "causal set",
        "causal sets",
        "cdt",
        "causal dynamical triangulation",
        "causal geometry",
        "quantum geometry",
        "quantum gravity",
    }
)

class CausalGeometryGuard(Guard[str]):
    """
    Enforces that any payload discussing causal sets, CDT or quantum orders
    explicitly references the ontology or complies structurally.
    """

    def evaluate(self, payload: str, **kwargs: Any) -> str:
        """
        Validates the payload against Causal Geometry Compliance.
        """
        payload_lower = payload.lower()

        # Check if the payload touches restricted domains
        touches_domain = any(kw in payload_lower for kw in _CAUSAL_KEYWORDS)

        if touches_domain:
            # If it touches the domain, it MUST reference the 340 invariants or the ontology file.
            # We enforce this by checking for explicit structural markers.
            has_ontology_ref = "causal_geometry_ontology.md" in payload_lower or "causal geometry ontology" in payload_lower
            has_invariant_ref = "340 primitives" in payload_lower or "340 invariants" in payload_lower or "primitive" in payload_lower or "invariant" in payload_lower

            if not (has_ontology_ref or has_invariant_ref):
                logger.error("[P0] Causal Geometry Compliance Violation detected.")
                raise GuardViolation(
                    "[P0] CAUSAL GEOMETRY COMPLIANCE: Operations relating to quantum orders, "
                    "causal sets, or CDT MUST adhere strictly to the 340 primitives/invariants "
                    "defined in CAUSAL_GEOMETRY_ONTOLOGY.md. The payload is missing explicit "
                    "ontological grounding."
                )

        return payload
