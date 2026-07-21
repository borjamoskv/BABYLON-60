"""
Unit tests for FISR Baseline v18.3 Lawvere Metric & Kappa Repair Operator
==========================================================================
Kernel: MOSKV-1 APEX
State: Executable C5-REAL Test Suite for Baseline v18.3
"""

import pytest
from cortex.subadditivity_verifier import CertificateCategoryP, Morphism, Certificate


def test_identity_zero_cost_axiom():
    cat = CertificateCategoryP()
    cat.add_identity_certificate("A")

    id_morphism = Morphism("id_A", "A", "A")
    mu_id = cat.compute_mu(id_morphism)
    assert mu_id == 0.0


def test_infimum_empty_convention():
    cat = CertificateCategoryP()
    alpha = Morphism("alpha_uncertified", "A", "B")

    # Empty fiber -> inf \emptyset = \infty
    mu_val = cat.compute_mu(alpha)
    assert mu_val == float('inf')


def test_subadditivity_sequential_with_contextual_delta():
    # Contextual friction function
    def friction_fn(m1, m2):
        if m1.src == "A" and m2.tgt == "C":
            return 0.5
        return 0.0

    cat = CertificateCategoryP(delta_circ_fn=friction_fn)
    alpha = Morphism("alpha", "A", "B")
    beta = Morphism("beta", "B", "C")

    cat.add_certificate(Certificate("c1", alpha, 2.0))
    cat.add_certificate(Certificate("c2", beta, 4.0))

    ok, lhs, rhs = cat.verify_sequential_subadditivity(alpha, beta)
    assert ok is True
    assert lhs == 6.5
    assert rhs == 6.5


def test_kappa_repair_operator():
    cat = CertificateCategoryP()
    alpha = Morphism("alpha", "X", "Y")
    cat.add_certificate(Certificate("c_alpha", alpha, 10.0))  # mu(alpha) = 10.0

    # Extension e1: Y -> Z, cost = 3.0
    e1 = Morphism("e1", "Y", "Z")
    cat.add_certificate(Certificate("c_e1", e1, 3.0))

    # Extension e2: Y -> W, cost = 1.5
    e2 = Morphism("e2", "Y", "W")
    cat.add_certificate(Certificate("c_e2", e2, 1.5))

    # Budget predicate R_k^A: composed cost <= 12.0
    def predicate_R(comp_morphism, comp_cost):
        return comp_cost <= 12.0

    # Compute kappa(alpha, R):
    # e1 o alpha cost = 3.0 + 10.0 = 13.0 > 12.0 (Fails R)
    # e2 o alpha cost = 1.5 + 10.0 = 11.5 <= 12.0 (Satisfies R)
    # Optimal repair cost mu(e2) = 1.5
    kappa_val = cat.compute_kappa_repair_operator(alpha, predicate_R)
    assert kappa_val == 1.5
