import pytest
from babylon60.core.manifold import (
    EpistemicField,
    _hash_to_vector,
    epistemic_projection,
    update_metric,
    compute_geodesic,
    apply_mutation,
    autodidact_step,
)
from babylon60.core.membrane import EpistemicEvent, EpistemicState


def test_hash_to_vector():
    # Sin traza
    assert _hash_to_vector(None, dim=2) == [0.0, 0.0]

    # Con traza
    trace = {"result": "unsat", "core": ["x > 5"]}
    vec = _hash_to_vector(trace, dim=4)
    assert len(vec) == 4
    # Validar que los valores estén en el rango [-0.5, 0.5]
    for val in vec:
        assert -0.5 <= val <= 0.5


def test_epistemic_projection_confirmed():
    event = EpistemicEvent(
        payload={"k": "v"},
        state=EpistemicState.CONFIRMED,
        confidence=0.9,
        z3_trace={"result": "sat"},
        entropy_signature=1.5,
        reality_level="C5-REAL",
    )
    field = epistemic_projection(event)
    assert field.curvature == 0.1 * 1.5
    assert field.uncertainty_density == pytest.approx(1.0 - 0.9)


def test_epistemic_projection_undecidable():
    event = EpistemicEvent(
        payload={"k": "v"},
        state=EpistemicState.UNDECIDABLE,
        confidence=0.3,
        z3_trace={"result": "unknown"},
        entropy_signature=2.0,
        reality_level="C5-REAL",
    )
    field = epistemic_projection(event)
    assert field.curvature == 1.5 * 2.0


def test_update_metric():
    g = [[1.0, 0.0], [0.0, 1.0]]
    field = EpistemicField(curvature=0.5, direction=[0.2, -0.2], uncertainty_density=0.1)
    new_g = update_metric(g, field)

    # 1.0 + 0.5 * 0.2 * 0.2
    assert new_g[0][0] == pytest.approx(1.0 + 0.5 * 0.04)
    # 0.0 + 0.5 * 0.2 * -0.2
    assert new_g[0][1] == pytest.approx(-0.02)


def test_compute_geodesic():
    g_static = [[1.0, 0.0], [0.0, 1.0]]
    g_dynamic = [[1.5, 0.1], [0.2, 1.2]]

    shift = compute_geodesic(g_static, g_dynamic)
    assert shift == pytest.approx([0.5, 0.2])


def test_apply_mutation_no_event():
    assert apply_mutation("my_ast", [1.0, 2.0]) == "my_ast"


def test_apply_mutation_with_confirmed_event():
    event = EpistemicEvent(
        payload={},
        state=EpistemicState.CONFIRMED,
        confidence=0.9,
        z3_trace=None,
        entropy_signature=1.0,
        reality_level="C4-SIM",
    )
    assert apply_mutation("my_ast", [1.0, 2.0], event) == "my_ast"


def test_apply_mutation_with_unknown_event(monkeypatch):
    # Mockear las importaciones internas para probar UAO
    class MockGhostManifold:
        def absorb_uop_ast(self, ast):
            pass

    import babylon60.core.manifold as manifold_module
    import sys
    import types

    # Fabricar un mock para babylon60.core.ghost
    ghost_mod = types.ModuleType("babylon60.core.ghost")
    ghost_mod.ghost_manifold_engine = MockGhostManifold()
    sys.modules["babylon60.core.ghost"] = ghost_mod

    # Fabricar un mock para babylon60.core.uop
    uop_mod = types.ModuleType("babylon60.core.uop")
    uop_mod.unknown_as_operator = lambda e: "mutated_ast_by_uao"
    sys.modules["babylon60.core.uop"] = uop_mod

    event = EpistemicEvent(
        payload={},
        state=EpistemicState.UNKNOWN,
        confidence=0.1,
        z3_trace=None,
        entropy_signature=1.0,
        reality_level="C4-SIM",
    )

    result = apply_mutation("my_ast", [1.0, 2.0], event)
    assert result == "mutated_ast_by_uao"

    # Limpieza
    del sys.modules["babylon60.core.ghost"]
    del sys.modules["babylon60.core.uop"]


def test_autodidact_step():
    class MockGhostManifold:
        def propagate(self, g):
            return [[v * 1.1 for v in row] for row in g]

        def absorb_uop_ast(self, ast):
            pass

    import sys
    import types

    ghost_mod = types.ModuleType("babylon60.core.ghost")
    ghost_mod.ghost_manifold_engine = MockGhostManifold()
    sys.modules["babylon60.core.ghost"] = ghost_mod

    uop_mod = types.ModuleType("babylon60.core.uop")
    uop_mod.unknown_as_operator = lambda e: "uao_result"
    sys.modules["babylon60.core.uop"] = uop_mod

    g_static = [[1.0, 0.0], [0.0, 1.0]]
    g_dynamic = [[1.0, 0.0], [0.0, 1.0]]
    events = [
        EpistemicEvent(
            payload={},
            state=EpistemicState.UNKNOWN,
            confidence=0.3,
            z3_trace={"res": "unk"},
            entropy_signature=2.0,
            reality_level="C4",
        )
    ]

    res = autodidact_step("ast", g_static, g_dynamic, events)
    assert res == "uao_result"

    del sys.modules["babylon60.core.ghost"]
    del sys.modules["babylon60.core.uop"]
