import pytest
import os
import sys
from hypothesis import given, settings, strategies as st

sys.path.insert(0, os.path.abspath("."))
from cortex.categorical_896_engine import Categorical896Engine


_engine_instance = None

def get_engine():
    global _engine_instance
    if _engine_instance is None:
        yaml_file = "primitives/896_categorical_logic_primitives.yml"
        _engine_instance = Categorical896Engine(yaml_path=yaml_file)
    return _engine_instance


def test_engine_initialization():
    engine = get_engine()
    assert len(engine.primitives) == 896
    assert len(engine.domain_index) == 8
    for dom_id, prims in engine.domain_index.items():
        assert len(prims) == 112


@settings(deadline=None)
@given(st.lists(st.integers(min_value=1, max_value=896), min_size=1, max_size=50))
def test_property_morphism_cost_monotonicity(primitive_seq):
    engine = get_engine()
    cost = engine.evaluate_morphism_cost(primitive_seq)
    assert cost >= len(primitive_seq)
    assert cost != float('inf')


@settings(deadline=None)
@given(st.integers(min_value=561, max_value=672), st.integers(min_value=673, max_value=784))
def test_property_collision_detection_exhaustion(d6_id, d7_id):
    engine = get_engine()
    collisions = engine.detect_diagrammatic_collisions({d6_id, d7_id})
    assert len(collisions) == 1
    assert collisions[0]["risk_level"] == "CRITICAL_C5_VIOLATION"

