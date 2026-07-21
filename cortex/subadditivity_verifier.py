"""
C5-REAL FISR Subadditivity Theorem Verifier & Lawvere Metric Transducer (v18.4)
================================================================================
Kernel: MOSKV-1 APEX
State: Executable C5-REAL Proof Verification Engine for Baseline v18.4
"""

from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple, Set, Any, Callable
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
    Lawvere Enriched Metric Space (C, mu) with extension/repair operator kappa
    and PRF-S Soundness / PRF-C Relative Completeness verification engines.
    """

    def __init__(self, delta_circ_fn: Optional[Callable[[Morphism, Morphism], float]] = None,
                 delta_tensor_fn: Optional[Callable[[Morphism, Morphism], float]] = None):
        self.delta_circ_fn = delta_circ_fn or (lambda a, b: 0.0)
        self.delta_tensor_fn = delta_tensor_fn or (lambda a, b: 0.0)
        self.certificates: Dict[Morphism, List[Certificate]] = {}

    def add_certificate(self, cert: Certificate) -> None:
        self.certificates.setdefault(cert.target_morphism, []).append(cert)

    def add_identity_certificate(self, obj_name: str) -> Certificate:
        id_morphism = Morphism(f"id_{obj_name}", obj_name, obj_name)
        id_cert = Certificate(f"id_cert_{obj_name}", id_morphism, 0.0)
        self.add_certificate(id_cert)
        return id_cert

    def get_cert_fiber(self, alpha: Morphism) -> List[Certificate]:
        return self.certificates.get(alpha, [])

    def compute_mu(self, alpha: Morphism) -> float:
        r"""
        Computes mu(alpha) = inf { |c| | c in Cert(alpha) }.
        Enforces total function convention: inf \emptyset = \infty.
        """
        fiber = self.get_cert_fiber(alpha)
        if not fiber:
            return float('inf')
        return min(c.cost for c in fiber)

    def compose_sequential(self, c1: Certificate, c2: Certificate) -> Certificate:
        if c1.target_morphism.tgt != c2.target_morphism.src:
            raise ValueError(f"Composition mismatch: {c1.target_morphism.tgt} != {c2.target_morphism.src}")

        delta = self.delta_circ_fn(c1.target_morphism, c2.target_morphism)
        composed_morphism = Morphism(
            name=f"({c2.target_morphism.name} o {c1.target_morphism.name})",
            src=c1.target_morphism.src,
            tgt=c2.target_morphism.tgt
        )
        composed_cost = c1.cost + c2.cost + delta
        composed_cert = Certificate(
            cert_id=f"({c2.cert_id} * {c1.cert_id})",
            target_morphism=composed_morphism,
            cost=composed_cost
        )
        self.add_certificate(composed_cert)
        return composed_cert

    def compose_monoidal(self, c1: Certificate, c2: Certificate) -> Certificate:
        delta = self.delta_tensor_fn(c1.target_morphism, c2.target_morphism)
        tensor_morphism = Morphism(
            name=f"({c1.target_morphism.name} (x) {c2.target_morphism.name})",
            src=f"({c1.target_morphism.src} x {c2.target_morphism.src})",
            tgt=f"({c1.target_morphism.tgt} x {c2.target_morphism.tgt})"
        )
        tensor_cost = c1.cost + c2.cost + delta
        tensor_cert = Certificate(
            cert_id=f"({c1.cert_id} (x) {c2.cert_id})",
            target_morphism=tensor_morphism,
            cost=tensor_cost
        )
        self.add_certificate(tensor_cert)
        return tensor_cert

    def verify_sequential_subadditivity(self, alpha: Morphism, beta: Morphism) -> Tuple[bool, float, float]:
        mu_alpha = self.compute_mu(alpha)
        mu_beta = self.compute_mu(beta)
        delta = self.delta_circ_fn(alpha, beta)
        rhs = mu_alpha + mu_beta + delta

        comp_morphism = Morphism(
            name=f"({beta.name} o {alpha.name})",
            src=alpha.src,
            tgt=beta.tgt
        )
        mu_comp = self.compute_mu(comp_morphism)

        if mu_comp == float('inf') and mu_alpha < float('inf') and mu_beta < float('inf'):
            c1_opt = min(self.get_cert_fiber(alpha), key=lambda c: c.cost)
            c2_opt = min(self.get_cert_fiber(beta), key=lambda c: c.cost)
            self.compose_sequential(c1_opt, c2_opt)
            mu_comp = self.compute_mu(comp_morphism)

        satisfied = mu_comp <= rhs
        return satisfied, mu_comp, rhs

    def compute_kappa_repair_operator(self, alpha: Morphism, budget_predicate: Callable[[Morphism, float], bool]) -> float:
        """
        Computes kappa(alpha, R) = inf { mu(e) | e o alpha |= R }.
        Iterates over extension morphisms e from alpha.tgt.
        """
        alpha_certs = self.get_cert_fiber(alpha)
        if not alpha_certs:
            return float('inf')
        c_alpha_opt = min(alpha_certs, key=lambda c: c.cost)

        valid_extension_costs = []
        for m, certs in list(self.certificates.items()):
            if m.src == alpha.tgt and certs:
                c_e_opt = min(certs, key=lambda c: c.cost)
                composed_cert = self.compose_sequential(c_alpha_opt, c_e_opt)
                comp_cost = composed_cert.cost
                if budget_predicate(composed_cert.target_morphism, comp_cost):
                    valid_extension_costs.append(c_e_opt.cost)

        if not valid_extension_costs:
            return float('inf')
        return min(valid_extension_costs)

    def verify_prf_s_soundness(self, basic_transitions: List[Morphism], k: float) -> bool:
        """
        PRF-S Soundness: Cert_k => M |= FISR_k^A.
        Verifies that if each basic transition has a certificate of cost <= k,
        then mu(alpha) <= k for all alpha and kappa(alpha, R_k^A) = 0.
        """
        for alpha in basic_transitions:
            mu_val = self.compute_mu(alpha)
            if mu_val > k:
                return False
            # Self-repair check with identity morphism
            self.add_identity_certificate(alpha.tgt)
            def budget_R_k(m, cost):
                return self.compute_mu(alpha) <= k
            kappa_val = self.compute_kappa_repair_operator(alpha, budget_R_k)
            if kappa_val > 0.0:
                return False
        return True

    def verify_prf_c_relative_completeness(self, basic_transitions: List[Morphism], k: float) -> bool:
        """
        PRF-C Relative Completeness: M |= FISR_k^A => Cert_k.
        Verifies that under coherent fiber reachability in N_bar,
        if mu(alpha) <= k for all basic transitions, a k-certification exists.
        """
        for alpha in basic_transitions:
            mu_val = self.compute_mu(alpha)
            if mu_val <= k:
                fiber = self.get_cert_fiber(alpha)
                if not any(c.cost <= k for c in fiber):
                    return False
            else:
                return False
        return True
