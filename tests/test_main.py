# C5-REAL EXERGY CERTIFIED
from cortex.core.robinson import robinson_resolution, resolve, is_tautology, subsumes, pure_literal_elimination, unit_propagation

def test_resolve():
    clause1 = frozenset({'P', 'Q'})
    clause2 = frozenset({'~P', 'R'})
    resolvents = resolve(clause1, clause2)
    assert frozenset({'Q', 'R'}) in resolvents

def test_resolve_tautology_elimination():
    clause1 = frozenset({'P', 'Q'})
    clause2 = frozenset({'~P', '~Q'})
    resolvents = resolve(clause1, clause2)
    assert len(resolvents) == 0

def test_is_tautology():
    assert is_tautology(frozenset({'A', '~A'})) == True
    assert is_tautology(frozenset({'A', 'B'})) == False

def test_subsumes():
    assert subsumes(frozenset({'P'}), frozenset({'P', 'Q'})) == True
    assert subsumes(frozenset({'P', 'Q'}), frozenset({'P'})) == False

def test_pure_literal_elimination():
    clauses = {frozenset({'P', 'Q'}), frozenset({'~P', 'R'})}
    # Q and R are pure literals. Their clauses should be eliminated.
    reduced = pure_literal_elimination(clauses)
    assert len(reduced) == 0

def test_unit_propagation():
    clauses = {frozenset({'P'}), frozenset({'~P', 'Q'}), frozenset({'~Q', 'R'})}
    # Unit {P} satisfies {P} and simplifies {~P, Q} to {Q}.
    # Unit {Q} satisfies {Q} and simplifies {~Q, R} to {R}.
    # Unit {R} satisfies {R}. Set becomes empty.
    reduced, unsat = unit_propagation(clauses)
    assert not unsat
    assert len(reduced) == 0

def test_unit_propagation_unsat():
    clauses = {frozenset({'P'}), frozenset({'~P'})}
    reduced, unsat = unit_propagation(clauses)
    assert unsat == True

def test_robinson_resolution_unsatisfiable():
    clauses = [
        {'P'},
        {'~P', 'Q'},
        {'~Q'}
    ]
    assert robinson_resolution(clauses) == True

def test_robinson_resolution_satisfiable():
    clauses = [
        {'P'},
        {'~P', 'Q'}
    ]
    assert robinson_resolution(clauses) == False

def test_robinson_resolution_with_tautologies():
    clauses = [
        {'P', '~P'},
        {'Q'},
        {'~Q'}
    ]
    assert robinson_resolution(clauses) == True
