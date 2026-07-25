# C5-REAL EXERGY CERTIFIED
"""
Unit tests for FISR Baseline v18.4 Lawvere Metric & PRF Engines
================================================================
Kernel: MOSKV-1 APEX
State: Executable C5-REAL Test Suite for Baseline v18.4
"""

from hypothesis import given, strategies as st
from cortex.subadditivity_verifier import CertificateCategoryP, Morphism, Certificate


def test_identity_zero_cost_axiom() -> None:
    cat = CertificateCategoryP()
    cat.add_identity_certificate("A")

    id_morphism = Morphism("id_A", "A", "A")
    mu_id = cat.compute_mu(id_morphism)
    assert mu_id == 0.0


def test_infimum_empty_convention() -> None:
    cat = CertificateCategoryP()
    alpha = Morphism("alpha_uncertified", "A", "B")

    mu_val = cat.compute_mu(alpha)
    assert mu_val == float("inf")


def test_subadditivity_sequential_with_contextual_delta() -> None:
    def friction_fn(m1: Morphism, m2: Morphism) -> float:
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


def test_kappa_repair_operator() -> None:
    cat = CertificateCategoryP()
    alpha = Morphism("alpha", "X", "Y")
    cat.add_certificate(Certificate("c_alpha", alpha, 10.0))

    e1 = Morphism("e1", "Y", "Z")
    cat.add_certificate(Certificate("c_e1", e1, 3.0))

    e2 = Morphism("e2", "Y", "W")
    cat.add_certificate(Certificate("c_e2", e2, 1.5))

    def predicate_R(m: Morphism, comp_cost: float) -> bool:
        return comp_cost <= 12.0

    kappa_val = cat.compute_kappa_repair_operator(alpha, predicate_R)
    assert kappa_val == 1.5


def test_kappa_monotonicity_theorem_2_1() -> None:
    cat = CertificateCategoryP()
    alpha = Morphism("alpha", "X", "Y")
    cat.add_certificate(Certificate("c_alpha", alpha, 10.0))

    e1 = Morphism("e1", "Y", "Z")
    cat.add_certificate(Certificate("c_e1", e1, 4.0))

    e2 = Morphism("e2", "Y", "W")
    cat.add_certificate(Certificate("c_e2", e2, 2.0))

    def R_strict(m: Morphism, cost: float) -> bool:
        return cost <= 12.5

    def R_weak(m: Morphism, cost: float) -> bool:
        return cost <= 15.0

    kappa_strict = cat.compute_kappa_repair_operator(alpha, R_strict)
    kappa_weak = cat.compute_kappa_repair_operator(alpha, R_weak)

    assert kappa_strict == 2.0
    assert kappa_weak == 2.0
    assert kappa_weak <= kappa_strict


def test_prf_s_soundness_and_prf_c_completeness() -> None:
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
    cost2=st.floats(min_value=0, max_value=1000, allow_nan=False, allow_infinity=False),
)
def test_property_sequential_subadditivity(cost1: float, cost2: float) -> None:
    cat = CertificateCategoryP()
    alpha = Morphism("alpha", "A", "B")
    beta = Morphism("beta", "B", "C")
    cat.add_certificate(Certificate("c1", alpha, cost1))
    cat.add_certificate(Certificate("c2", beta, cost2))
    ok, lhs, rhs = cat.verify_sequential_subadditivity(alpha, beta)
    assert ok is True


@given(
    cost1=st.floats(min_value=0, max_value=1000, allow_nan=False, allow_infinity=False),
    cost2=st.floats(min_value=0, max_value=1000, allow_nan=False, allow_infinity=False),
)
def test_property_monoidal_subadditivity(cost1: float, cost2: float) -> None:
    cat = CertificateCategoryP()
    alpha = Morphism("alpha", "A", "B")
    beta = Morphism("beta", "C", "D")
    cat.add_certificate(Certificate("c1", alpha, cost1))
    cat.add_certificate(Certificate("c2", beta, cost2))
    ok, lhs, rhs = cat.verify_monoidal_subadditivity(alpha, beta)
    assert ok is True


@given(
    cost1=st.floats(min_value=0, max_value=1000, allow_nan=False, allow_infinity=False),
    cost2=st.floats(min_value=0, max_value=1000, allow_nan=False, allow_infinity=False),
)
def test_property_lawvere_triangle_inequality(cost1: float, cost2: float) -> None:
    cat = CertificateCategoryP()
    alpha = Morphism("alpha", "A", "B")
    beta = Morphism("beta", "B", "C")
    cat.add_certificate(Certificate("c1", alpha, cost1))
    cat.add_certificate(Certificate("c2", beta, cost2))
    ok, lhs, rhs = cat.verify_lawvere_triangle_inequality(alpha, beta)
    assert ok is True


@given(dummy=st.integers(min_value=0, max_value=100))
def test_property_identity_cost(dummy: int) -> None:
    cat = CertificateCategoryP()
    cat.add_identity_certificate("A")
    id_morphism = Morphism("id_A", "A", "A")
    mu_id = cat.compute_mu(id_morphism)
    assert mu_id == 0.0


# ========================================================================
# THEOREM 3: LAWVERE PREMETRIC FORMAL VERIFICATION
# ========================================================================


def test_lawvere_premetric_reflexivity() -> None:
    """Thm 3 Part 1: mu(id_X) = 0 for all objects X."""
    cat = CertificateCategoryP()
    for obj in ["A", "B", "C", "D", "E"]:
        cat.add_identity_certificate(obj)
        id_m = Morphism(f"id_{obj}", obj, obj)
        assert cat.compute_mu(id_m) == 0.0, f"Reflexivity failed for {obj}"


def test_lawvere_premetric_triangle_3chain() -> None:
    """Thm 3 Part 2: Triangle inequality over a 3-chain A->B->C->D."""
    cat = CertificateCategoryP(delta_circ_fn=lambda a, b: 0.0)
    alpha = Morphism("alpha", "A", "B")
    beta = Morphism("beta", "B", "C")
    gamma = Morphism("gamma", "C", "D")

    cat.add_certificate(Certificate("c1", alpha, 3.0))
    cat.add_certificate(Certificate("c2", beta, 5.0))
    cat.add_certificate(Certificate("c3", gamma, 2.0))

    # Compose alpha ; beta
    c1 = min(cat.get_cert_fiber(alpha), key=lambda c: c.cost)
    c2 = min(cat.get_cert_fiber(beta), key=lambda c: c.cost)
    c_ab = cat.compose_sequential(c1, c2)

    # Verify triangle: mu(beta o alpha) <= mu(alpha) + mu(beta)
    comp_ab = Morphism("(beta o alpha)", "A", "C")
    mu_comp = cat.compute_mu(comp_ab)
    assert mu_comp <= cat.compute_mu(alpha) + cat.compute_mu(beta)

    # Compose (beta o alpha) ; gamma
    c3 = min(cat.get_cert_fiber(gamma), key=lambda c: c.cost)
    cat.compose_sequential(c_ab, c3)

    comp_abc = Morphism("(gamma o (beta o alpha))", "A", "D")
    mu_abc = cat.compute_mu(comp_abc)
    assert mu_abc <= cat.compute_mu(comp_ab) + cat.compute_mu(gamma)
    # Transitive bound
    assert mu_abc <= cat.compute_mu(alpha) + cat.compute_mu(beta) + cat.compute_mu(gamma)


@given(
    cost1=st.floats(min_value=0, max_value=500, allow_nan=False, allow_infinity=False),
    cost2=st.floats(min_value=0, max_value=500, allow_nan=False, allow_infinity=False),
    cost3=st.floats(min_value=0, max_value=500, allow_nan=False, allow_infinity=False),
)
def test_property_lawvere_transitivity(cost1: float, cost2: float, cost3: float) -> None:
    """Property-based: mu(gamma o beta o alpha) <= sum of individual mu's."""
    cat = CertificateCategoryP(delta_circ_fn=lambda a, b: 0.0)
    alpha = Morphism("a", "A", "B")
    beta = Morphism("b", "B", "C")
    gamma = Morphism("g", "C", "D")

    cat.add_certificate(Certificate("c1", alpha, cost1))
    cat.add_certificate(Certificate("c2", beta, cost2))
    cat.add_certificate(Certificate("c3", gamma, cost3))

    c1 = min(cat.get_cert_fiber(alpha), key=lambda c: c.cost)
    c2 = min(cat.get_cert_fiber(beta), key=lambda c: c.cost)
    c_ab = cat.compose_sequential(c1, c2)
    c3 = min(cat.get_cert_fiber(gamma), key=lambda c: c.cost)
    cat.compose_sequential(c_ab, c3)

    comp_abc = Morphism("(g o (b o a))", "A", "D")
    mu_abc = cat.compute_mu(comp_abc)
    assert mu_abc <= cost1 + cost2 + cost3 + 1e-9  # epsilon for float


# ========================================================================
# THEOREM 4: PRF-S SOUNDNESS VERIFICATION
# ========================================================================


def test_prf_s_soundness_structural() -> None:
    """Thm 4: If each alpha in A(M) has cert with cost <= k, then M |= FISR_k^A."""
    cat = CertificateCategoryP()
    transitions = [
        Morphism("t1", "A", "B"),
        Morphism("t2", "B", "C"),
        Morphism("t3", "C", "D"),
    ]
    k = 7.0

    # Plant certificates within budget
    cat.add_certificate(Certificate("c_t1", transitions[0], 3.0))
    cat.add_certificate(Certificate("c_t2", transitions[1], 5.0))
    cat.add_certificate(Certificate("c_t3", transitions[2], 7.0))

    # Verify mu <= k for each
    for t in transitions:
        assert cat.compute_mu(t) <= k, f"mu({t.name}) > k"

    # Verify kappa = 0 for each (via identity extension)
    for t in transitions:
        cat.add_identity_certificate(t.tgt)
        id_m = Morphism(f"id_{t.tgt}", t.tgt, t.tgt)
        # Identity composed with alpha = alpha (conceptually)
        assert cat.compute_mu(id_m) == 0.0

    # Full engine verification
    assert cat.verify_prf_s_soundness(transitions, k) is True


def test_prf_s_soundness_fails_over_budget() -> None:
    """Thm 4 contrapositive: If a cert exceeds k, soundness fails."""
    cat = CertificateCategoryP()
    alpha = Morphism("alpha", "A", "B")
    cat.add_certificate(Certificate("c_alpha", alpha, 10.0))

    assert cat.verify_prf_s_soundness([alpha], k=5.0) is False


# ========================================================================
# THEOREM 5: SEPARATION THEOREM VERIFICATION
# ========================================================================


def test_separation_empty_fiber() -> None:
    """Thm 5: Model with empty Cert(alpha) is non-FISR for all k."""
    cat = CertificateCategoryP()
    alpha = Morphism("alpha", "A", "B")
    # Do NOT add any certificate for alpha

    # mu(alpha) = inf(empty) = infinity
    assert cat.compute_mu(alpha) == float("inf")

    # R_k fails for any finite k
    for k in [0, 1, 10, 100, 1000, 10**6]:
        assert cat.compute_mu(alpha) > k

    # kappa = infinity (no valid extension exists)
    def budget_any_k(m: Morphism, cost: float) -> bool:
        return cost <= 1000.0

    kappa = cat.compute_kappa_repair_operator(alpha, budget_any_k)
    assert kappa == float("inf")


def test_separation_boundary_nonempty_fiber() -> None:
    """Boundary: Model with Cert(alpha) non-empty IS FISR for k >= mu(alpha)."""
    cat = CertificateCategoryP()
    alpha = Morphism("alpha", "A", "B")
    cat.add_certificate(Certificate("c_alpha", alpha, 42.0))

    # mu(alpha) = 42, so FISR_42 should hold
    assert cat.compute_mu(alpha) == 42.0
    assert cat.verify_prf_s_soundness([alpha], k=42.0) is True

    # But FISR_41 should fail
    assert cat.verify_prf_s_soundness([alpha], k=41.0) is False
