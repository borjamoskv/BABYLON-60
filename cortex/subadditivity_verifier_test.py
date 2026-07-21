"""
Unit tests for FISR Baseline v18.4 Lawvere Metric & PRF Engines
================================================================
Kernel: MOSKV-1 APEX
State: Executable C5-REAL Test Suite for Baseline v18.4
"""

import pytest
from hypothesis import given, strategies as st
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
    cat = CertificateCategoryP()
    alpha = Morphism("alpha", "X", "Y")
    cat.add_certificate(Certificate("c_alpha", alpha, 10.0))

    e1 = Morphism("e1", "Y", "Z")
    cat.add_certificate(Certificate("c_e1", e1, 4.0))

    e2 = Morphism("e2", "Y", "W")
    cat.add_certificate(Certificate("c_e2", e2, 2.0))

    def R_strict(m, cost):
        return cost <= 12.5

    def R_weak(m, cost):
        return cost <= 15.0

    kappa_strict = cat.compute_kappa_repair_operator(alpha, R_strict)
    kappa_weak = cat.compute_kappa_repair_operator(alpha, R_weak)

    assert kappa_strict == 2.0
    assert kappa_weak == 2.0
    assert kappa_weak <= kappa_strict


def test_prf_s_soundness_and_prf_c_completeness():
    cat = CertificateCategoryP()
    alpha = Morphism("alpha", "A", "B")
    beta = Morphism("beta", "B", "C")

    # Certificates within budget k = 5.0
    cat.add_certificate(Certificate("c_alpha", alpha, 3.0))
    cat.add_certificate(Certificate("c_beta", beta, 4.5))

    basics = [alpha, beta]
    k = 5.0

    # PRF-S: Cert_k => M |= FISR_k^A
    soundness_ok = cat.verify_prf_s_soundness(basics, k)
    assert soundness_ok is True

    # PRF-C: M |= FISR_k^A => Cert_k
    completeness_ok = cat.verify_prf_c_relative_completeness(basics, k)
    assert completeness_ok is True


@given(
    cost1=st.floats(min_value=0, max_value=1000, allow_nan=False, allow_infinity=False),
    cost2=st.floats(min_value=0, max_value=1000, allow_nan=False, allow_infinity=False)
)
def test_property_sequential_subadditivity(cost1, cost2):
    cat = CertificateCategoryP()
    alpha = Morphism("alpha", "A", "B")
    beta = Morphism("beta", "B", "C")
    cat.add_certificate(Certificate("c1", alpha, cost1))
    cat.add_certificate(Certificate("c2", beta, cost2))
    ok, lhs, rhs = cat.verify_sequential_subadditivity(alpha, beta)
    assert ok is True


@given(
    cost1=st.floats(min_value=0, max_value=1000, allow_nan=False, allow_infinity=False),
    cost2=st.floats(min_value=0, max_value=1000, allow_nan=False, allow_infinity=False)
)
def test_property_monoidal_subadditivity(cost1, cost2):
    cat = CertificateCategoryP()
    alpha = Morphism("alpha", "A", "B")
    beta = Morphism("beta", "C", "D")
    cat.add_certificate(Certificate("c1", alpha, cost1))
    cat.add_certificate(Certificate("c2", beta, cost2))
    ok, lhs, rhs = cat.verify_monoidal_subadditivity(alpha, beta)
    assert ok is True


@given(
    cost1=st.floats(min_value=0, max_value=1000, allow_nan=False, allow_infinity=False),
    cost2=st.floats(min_value=0, max_value=1000, allow_nan=False, allow_infinity=False)
)
def test_property_lawvere_triangle_inequality(cost1, cost2):
    cat = CertificateCategoryP()
    alpha = Morphism("alpha", "A", "B")
    beta = Morphism("beta", "B", "C")
    cat.add_certificate(Certificate("c1", alpha, cost1))
    cat.add_certificate(Certificate("c2", beta, cost2))
    ok, lhs, rhs = cat.verify_lawvere_triangle_inequality(alpha, beta)
    assert ok is True


@given(dummy=st.integers(min_value=0, max_value=100))
def test_property_identity_cost(dummy):
    cat = CertificateCategoryP()
    cat.add_identity_certificate("A")
    id_morphism = Morphism("id_A", "A", "A")
    mu_id = cat.compute_mu(id_morphism)
    assert mu_id == 0.0

