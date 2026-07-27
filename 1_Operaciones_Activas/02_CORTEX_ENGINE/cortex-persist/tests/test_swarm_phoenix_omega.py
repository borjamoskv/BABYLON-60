import ast
import pytest
from pathlib import Path
from babylon60.swarm.phoenix_omega import (
    StructuralAtom,
    PhoenixState,
    PhaseStatus,
    AtomicPhase,
    AnalysisEngine
)

def test_structural_atom_compute_signature():
    code = "def foo():\n    return 42"
    node = ast.parse(code)
    atom = StructuralAtom(
        id="foo",
        source_path=Path("test.py"),
        ast_node=node,
        complexity_score=1.0,
        dependencies=set(),
        dependents=set(),
        semantic_signature=""
    )
    sig = atom.compute_signature()
    assert isinstance(sig, str)
    assert len(sig) == 16

def test_phoenix_state_transition():
    state = PhoenixState(
        phase=AtomicPhase.ANALYSIS,
        status=PhaseStatus.COMPLETED,
        atoms={},
        artifacts={},
        metrics={"test": 1.0}
    )
    new_state = state.transition_to(AtomicPhase.EXTRACTION)

    assert new_state.phase == AtomicPhase.EXTRACTION
    assert new_state.status == PhaseStatus.PENDING
    assert new_state.metrics == {"test": 1.0}
    assert new_state.rollback_snapshot is not None
    assert new_state.rollback_snapshot["phase"] == "analysis"

@pytest.mark.asyncio
async def test_analysis_engine_execute(tmp_path):
    target = tmp_path / "target.py"
    target.write_text("def my_func():\n    pass")

    state = PhoenixState(
        phase=AtomicPhase.ANALYSIS,
        status=PhaseStatus.PENDING,
        atoms={},
        artifacts={},
        metrics={}
    )

    engine = AnalysisEngine()
    new_state = await engine.execute(state, [target])

    # AnalysisEngine should parse target.py and populate atoms
    assert len(new_state.atoms) > 0
    # There should be an atom for my_func (depends on parser logic, but atoms shouldn't be empty)
