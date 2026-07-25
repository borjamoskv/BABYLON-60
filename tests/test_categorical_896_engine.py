# C5-REAL EXERGY CERTIFIED
import os
import sys
from hypothesis import given, settings, strategies as st

sys.path.insert(0, os.path.abspath("."))
from cortex.categorical_896_engine import Categorical896Engine

_engine_instance = None

def get_engine() -> Categorical896Engine:
    global _engine_instance
    if _engine_instance is None:
        yaml_file = "primitives/896_categorical_logic_primitives.yml"
        _engine_instance = Categorical896Engine(yaml_path=yaml_file)
    return _engine_instance

def test_engine_initialization() -> None:
    engine = get_engine()
    assert len(engine.primitives) == 896
    assert len(engine.domain_index) == 8
    for dom_id, prims in engine.domain_index.items():
        assert len(prims) == 112

@settings(deadline=None)
@given(st.lists(st.integers(min_value=1, max_value=896), min_size=1, max_size=50))
def test_property_morphism_cost_monotonicity(primitive_seq: list[int]) -> None:
    engine = get_engine()
    cost = engine.evaluate_morphism_cost(primitive_seq)
    assert cost >= len(primitive_seq)
    assert cost != float("inf")

@settings(deadline=None)
@given(st.integers(min_value=561, max_value=672), st.integers(min_value=673, max_value=784))
def test_property_collision_detection_exhaustion(d6_id: int, d7_id: int) -> None:
    engine = get_engine()
    collisions = engine.detect_diagrammatic_collisions({d6_id, d7_id})
    assert len(collisions) == 1
    assert collisions[0]["risk_level"] == "CRITICAL_C5_VIOLATION"

@settings(deadline=None)
@given(
    st.lists(st.integers(min_value=1, max_value=896), min_size=1, max_size=20),
    st.lists(st.integers(min_value=1, max_value=896), min_size=1, max_size=20),
    st.floats(min_value=0.0, max_value=10.0),
)
def test_theorem_1_1_subadditivity_sequential(seq_a: list[int], seq_b: list[int], delta: float) -> None:
    engine = get_engine()
    res = engine.evaluate_sequential_composition(seq_a, seq_b, delta_circ=delta)
    assert res["theorem_1_1_sequential_holds"] is True
    assert res["mu_composed"] <= res["upper_bound"] + 1e-12

@settings(deadline=None)
@given(
    st.lists(st.integers(min_value=1, max_value=896), min_size=1, max_size=20),
    st.lists(st.integers(min_value=1, max_value=896), min_size=1, max_size=20),
    st.floats(min_value=0.0, max_value=10.0),
)
def test_theorem_1_1_subadditivity_monoidal(seq_a: list[int], seq_b: list[int], delta: float) -> None:
    engine = get_engine()
    res = engine.evaluate_monoidal_composition(seq_a, seq_b, delta_otimes=delta)
    assert res["theorem_1_1_monoidal_holds"] is True
    assert res["mu_tensor"] <= res["upper_bound"] + 1e-12

@settings(deadline=None)
@given(
    st.lists(st.integers(min_value=1, max_value=896), min_size=1, max_size=10),
    st.floats(min_value=1.0, max_value=10.0),
    st.floats(min_value=10.1, max_value=20.0),
)
def test_theorem_2_1_kappa_monotonicity(morphism: list[int], k_strong: float, k_weak: float) -> None:
    engine = get_engine()
    extensions = [[1, 2], [3, 4, 5], [6]]
    res = engine.verify_kappa_monotonicity(morphism, k_strong, k_weak, extensions)
    assert res["theorem_2_1_holds"] is True

def test_simplicial_complex_compat_omega() -> None:
    engine = get_engine()
    audit = engine.get_structural_audit()
    compat = audit["compat_complex"]
    assert compat["downset_invariant_verified"] is True
    assert compat["total_faces"] > 0
    assert compat["maximal_dimension"] == 3

def test_multi_domain_collision_audit() -> None:
    engine = get_engine()
    # D4 (337..448), D5 (449..560), D6 (561..672), D7 (673..784)
    active_set = {340, 450, 570, 680}
    collisions = engine.detect_diagrammatic_collisions(active_set)
    # Expect 1 D6xD7, 1 D4xD6, 1 D5xD7 = 3 collisions
    assert len(collisions) == 3
