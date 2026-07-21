"""
Unit tests for FISR Baseline v18.4 Lawvere Metric & Kappa Monotonicity Theorems
================================================================================
Kernel: MOSKV-1 APEX
State: Executable C5-REAL Test Suite for Baseline v18.4
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
    cat.add_certificate(Certificate("c_alpha", alpha, 10.0))

    e1 = Morphism("e1", "Y", "Z")
    cat.add_certificate(Certificate("c_e1", e1, 3.0))

    e2 = Morphism("e2", "Y", "W")
    cat.add_certificate(Certificate("c_e2", e2, 1.5))

    def predicate_R(comp_morphism, comp_cost):
        return comp_cost <= 12.0

    kappa_val = cat.compute_kappa_repair_operator(alpha, predicate_R)
    assert kappa_val == 1.5


def test_kappa_monotonicity_theorem_2_1():
    """
    Theorem 2.1: If R => R' then kappa(alpha, R') <= kappa(alpha, R).
    """
    cat = CertificateCategoryP()
    alpha = Morphism("alpha", "X", "Y")
    cat.add_certificate(Certificate("c_alpha", alpha, 10.0))

    e1 = Morphism("e1", "Y", "Z")
    cat.add_certificate(Certificate("c_e1", e1, 4.0))

    e2 = Morphism("e2", "Y", "W")
    cat.add_certificate(Certificate("c_e2", e2, 2.0))

    # Strict predicate R: comp_cost <= 12.5 (Only e2 satisfies: 10 + 2 = 12 <= 12.5)
    def R_strict(m, cost):
        return cost <= 12.5

    # Weaker predicate R': comp_cost <= 15.0 (e1 & e2 satisfy: 10 + 4 = 14 <= 15)
    def R_weak(m, cost):
        return cost <= 15.0

    kappa_strict = cat.compute_kappa_repair_operator(alpha, R_strict)
    kappa_weak = cat.compute_kappa_repair_operator(alpha, R_weak)

    assert kappa_strict == 2.0
    assert kappa_weak == 2.0
    assert kappa_weak <= kappa_strict
