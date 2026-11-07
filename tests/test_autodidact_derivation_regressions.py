"""V07: a natural-language goal is not a checked proof."""

import copy

import pytest

from babylon60.autodidact.engine import AutodidactOmegaEngine
from babylon60.autodidact.epistemology import derive, hash_statement, verify
from babylon60.autodidact.types import (
    Justification,
    JustifiedStatement,
    Modality,
    Obligation,
    Statement,
    StatementStatus,
)


def premise():
    return JustifiedStatement(
        Statement(
            "All fixture triangles have three sides.",
            Modality.EPISTEMIC,
            [Obligation.PROVENANCE, Obligation.REPRODUCIBILITY],
        ),
        Justification("Observation", {"source": "fixture"}, 0.8),
        status=StatementStatus.STABILIZED,
    )


@pytest.mark.parametrize("goal", ["All fixture triangles have five sides.", "An unrelated assertion is true."])
@pytest.mark.parametrize("obligations", [[], [Obligation.PROVENANCE]])
def test_unrelated_conclusion_is_rejected(goal, obligations):
    with pytest.raises(ValueError, match="UNPROVEN_DERIVATION"):
        derive([premise()], Statement(goal, Modality.EPISTEMIC, obligations))


def test_engine_rejection_leaves_registry_unchanged():
    engine = AutodidactOmegaEngine(db_path=None)
    before = (
        copy.deepcopy(engine.statements),
        copy.deepcopy(engine.statement_registry),
        copy.deepcopy(engine.dependencies_dag),
    )
    with pytest.raises(ValueError, match="UNPROVEN_DERIVATION"):
        engine.derive_theorem([premise()], "All fixture triangles have five sides.")
    assert (engine.statements, engine.statement_registry, engine.dependencies_dag) == before


def test_identity_preserves_evidence_and_confidence():
    p = premise()
    result = derive([p], Statement(p.statement.content, p.statement.modality, [Obligation.PROVENANCE]))
    assert result.justification.kind == "Observation"
    assert result.justification.confidence == 0.8
    assert result.justification.parameters == p.justification.parameters
    assert result.status != StatementStatus.CANONICAL
    assert verify(result)
    result.justification.parameters["source"] = "changed copy"
    assert p.justification.parameters["source"] == "fixture"


def test_identity_does_not_add_obligations():
    p = premise()
    with pytest.raises(ValueError, match="UNPROVEN_DERIVATION"):
        derive([p], Statement(p.statement.content, p.statement.modality, [Obligation.CONFIDENCE]))


def test_stale_premise_hash_is_rejected():
    p = premise()
    p.statement_hash = hash_statement(p.statement)
    p.statement.content = "tampered"
    with pytest.raises(ValueError):
        derive([p], Statement(p.statement.content, p.statement.modality))


def test_identity_does_not_create_self_dependency():
    engine = AutodidactOmegaEngine(db_path=None)
    p = engine.assert_hypothesis("fixture", obligations=[Obligation.PROVENANCE])
    result = engine.derive_theorem([p], "fixture", goal_obligations=[Obligation.PROVENANCE])
    assert result is p
    assert result.status == StatementStatus.STABILIZED
    assert engine.dependencies_dag == {}
    assert engine.statements == [p]


def test_falsified_premise_is_rejected_without_explicit_contradiction_obligation():
    p = premise()
    with pytest.raises(ValueError):
        derive([p], Statement(p.statement.content, p.statement.modality), nogoods={hash_statement(p.statement)})


@pytest.mark.parametrize("corruption", ["evidence", "content", "status"])
def test_registry_collision_cannot_replace_validated_identity(corruption):
    engine = AutodidactOmegaEngine(db_path=None)
    p = premise()
    cached = copy.deepcopy(p)
    cached.statement_hash = hash_statement(cached.statement)
    if corruption == "evidence":
        cached.justification = Justification("FormalProof", {}, 1.0)
        cached.status = StatementStatus.CANONICAL
    elif corruption == "content":
        cached.statement.content = "An unrelated stale registry entry."
    else:
        cached.status = StatementStatus.FALSIFIED
    engine.statement_registry[cached.statement_hash] = cached
    engine.statements.append(cached)
    before = copy.deepcopy((engine.statements, engine.statement_registry, engine.dependencies_dag))
    with pytest.raises(ValueError):
        engine.derive_theorem([p], p.statement.content, goal_obligations=p.statement.obligations)
    assert (engine.statements, engine.statement_registry, engine.dependencies_dag) == before


def test_imported_identity_retains_ancestry_and_falsification_cascade():
    engine = AutodidactOmegaEngine(db_path=None)
    ancestor = premise()
    ancestor_hash = hash_statement(ancestor.statement)
    imported = derive([ancestor], Statement(ancestor.statement.content, Modality.EPISTEMIC, []))
    result = engine.derive_theorem([imported], imported.statement.content, goal_obligations=[])
    assert result.dependencies == [ancestor_hash]
    assert engine.dependencies_dag[ancestor_hash] == {result.statement_hash}
    engine.propagate_contradiction(ancestor_hash)
    assert result.status == StatementStatus.DISCREDITED
    assert result.statement_hash in engine.falsifier.nogoods


def test_identity_rejects_a_known_falsified_ancestor():
    ancestor = premise()
    imported = derive([ancestor], Statement(ancestor.statement.content, Modality.EPISTEMIC, []))
    with pytest.raises(ValueError):
        derive([imported], imported.statement, nogoods={hash_statement(ancestor.statement)})
