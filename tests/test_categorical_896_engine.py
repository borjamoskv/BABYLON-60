import pytest
import os
import sys

sys.path.insert(0, os.path.abspath("."))
from cortex.categorical_896_engine import Categorical896Engine, CategoricalPrimitive


def test_engine_initialization():
    yaml_file = "primitives/896_categorical_logic_primitives.yml"
    engine = Categorical896Engine(yaml_path=yaml_file)
    
    assert len(engine.primitives) == 896
    assert len(engine.domain_index) == 8
    
    # Verify each domain has exactly 112 primitives
    for dom_id, prims in engine.domain_index.items():
        assert len(prims) == 112, f"Domain {dom_id} count mismatch: expected 112, got {len(prims)}"


def test_morphism_cost_subadditivity():
    yaml_file = "primitives/896_categorical_logic_primitives.yml"
    engine = Categorical896Engine(yaml_path=yaml_file)
    
    cost_a = engine.evaluate_morphism_cost([1, 2])
    cost_b = engine.evaluate_morphism_cost([3, 4, 5])
    cost_ab = engine.evaluate_morphism_cost([1, 2, 3, 4, 5])
    
    # Verify subadditivity law: mu(b o a) <= mu(a) + mu(b)
    assert cost_ab <= cost_a + cost_b


def test_collision_detection():
    yaml_file = "primitives/896_categorical_logic_primitives.yml"
    engine = Categorical896Engine(yaml_path=yaml_file)
    
    collisions = engine.detect_diagrammatic_collisions({561, 673})
    assert len(collisions) == 1
    assert collisions[0]["collision_type"] == "NON_COMMUTATIVE_STRUCTURAL_COLLISION"
