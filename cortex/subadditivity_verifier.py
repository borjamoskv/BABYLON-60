"""
C5-REAL FISR Subadditivity Theorem Verifier & Certificate Algebra Transducer
=============================================================================
Kernel: MOSKV-1 APEX
State: Executable C5-REAL Proof Verification Engine for Baseline v18.1
"""

from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple, Set, Any
import math


@dataclass(frozen=True)
class Morphism:
    name: str
    src: str
    tgt: str


@dataclass(frozen=True)
class Certificate:
    cert_id: str
    target_morphism: Morphism
    cost: float  # In N_bar (float('inf') for non-certifiable)

    def __post_init__(self):
        if self.cost < 0:
            raise ValueError(f"Cost valuation must be non-negative, got {self.cost}")


class CertificateCategoryP:
    """
    Implementation of Category P and Functor pi: P -> C (Identity on Objects).
    Morphs in P are certificates projecting to morphs in C via pi.
    """

    def __init__(self, delta_circ: float = 0.0, delta_tensor: float = 0.0):
        self.delta_circ = delta_circ
        self.delta_tensor = delta_tensor
        self.certificates: Dict[Morphism, List[Certificate]] = {}

    def add_certificate(self, cert: Certificate) -> None:
        self.certificates.setdefault(cert.target_morphism, []).append(cert)

    def get_cert_fiber(self, alpha: Morphism) -> List[Certificate]:
        return self.certificates.get(alpha, [])

    def compute_mu(self, alpha: Morphism) -> float:
        fiber = self.get_cert_fiber(alpha)
        if not fiber:
            return float('inf')
        return min(c.cost for c in fiber)

    def compose_sequential(self, c1: Certificate, c2: Certificate) -> Certificate:
        """
        c1: cert for alpha: X -> Y
        c2: cert for beta: Y -> Z
        c2 (circ) c1: cert for beta o alpha: X -> Z
        """
        if c1.target_morphism.tgt != c2.target_morphism.src:
            raise ValueError(f"Composition mismatch: {c1.target_morphism.tgt} != {c2.target_morphism.src}")

        composed_morphism = Morphism(
            name=f"({c2.target_morphism.name} o {c1.target_morphism.name})",
            src=c1.target_morphism.src,
            tgt=c2.target_morphism.tgt
        )
        composed_cost = c1.cost + c2.cost + self.delta_circ
        composed_cert = Certificate(
            cert_id=f"({c2.cert_id} * {c1.cert_id})",
            target_morphism=composed_morphism,
            cost=composed_cost
        )
        self.add_certificate(composed_cert)
        return composed_cert

    def compose_monoidal(self, c1: Certificate, c2: Certificate) -> Certificate:
        """
        c1: cert for alpha: X -> Y
        c2: cert for beta: A -> B
        c1 (tensor) c2: cert for alpha tensor beta: (X x A) -> (Y x B)
        """
        tensor_morphism = Morphism(
            name=f"({c1.target_morphism.name} (x) {c2.target_morphism.name})",
            src=f"({c1.target_morphism.src} x {c2.target_morphism.src})",
            tgt=f"({c1.target_morphism.tgt} x {c2.target_morphism.tgt})"
        )
        tensor_cost = c1.cost + c2.cost + self.delta_tensor
        tensor_cert = Certificate(
            cert_id=f"({c1.cert_id} (x) {c2.cert_id})",
            target_morphism=tensor_morphism,
            cost=tensor_cost
        )
        self.add_certificate(tensor_cert)
        return tensor_cert

    def verify_sequential_subadditivity(self, alpha: Morphism, beta: Morphism) -> Tuple[bool, float, float]:
        """
        Verifies: mu(beta o alpha) <= mu(alpha) + mu(beta) + delta_circ
        Returns (is_satisfied, left_hand_side, right_hand_side)
        """
        mu_alpha = self.compute_mu(alpha)
        mu_beta = self.compute_mu(beta)
        rhs = mu_alpha + mu_beta + self.delta_circ

        comp_morphism = Morphism(
            name=f"({beta.name} o {alpha.name})",
            src=alpha.src,
            tgt=beta.tgt
        )
        mu_comp = self.compute_mu(comp_morphism)

        # If comp_morphism isn't explicitly in fiber, simulate best composition
        if mu_comp == float('inf') and mu_alpha < float('inf') and mu_beta < float('inf'):
            # Find optimal c1 and c2
            c1_opt = min(self.get_cert_fiber(alpha), key=lambda c: c.cost)
            c2_opt = min(self.get_cert_fiber(beta), key=lambda c: c.cost)
            self.compose_sequential(c1_opt, c2_opt)
            mu_comp = self.compute_mu(comp_morphism)

        satisfied = mu_comp <= rhs
        return satisfied, mu_comp, rhs

    def verify_monoidal_subadditivity(self, alpha: Morphism, beta: Morphism) -> Tuple[bool, float, float]:
        """
        Verifies: mu(alpha (x) beta) <= mu(alpha) + mu(beta) + delta_tensor
        Returns (is_satisfied, left_hand_side, right_hand_side)
        """
        mu_alpha = self.compute_mu(alpha)
        mu_beta = self.compute_mu(beta)
        rhs = mu_alpha + mu_beta + self.delta_tensor

        tensor_morphism = Morphism(
            name=f"({alpha.name} (x) {beta.name})",
            src=f"({alpha.src} x {beta.src})",
            tgt=f"({alpha.tgt} x {beta.tgt})"
        )
        mu_tensor = self.compute_mu(tensor_morphism)

        if mu_tensor == float('inf') and mu_alpha < float('inf') and mu_beta < float('inf'):
            c1_opt = min(self.get_cert_fiber(alpha), key=lambda c: c.cost)
            c2_opt = min(self.get_cert_fiber(beta), key=lambda c: c.cost)
            self.compose_monoidal(c1_opt, c2_opt)
            mu_tensor = self.compute_mu(tensor_morphism)

        satisfied = mu_tensor <= rhs
        return satisfied, mu_tensor, rhs
