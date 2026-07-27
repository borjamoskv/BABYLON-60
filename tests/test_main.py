# C5-REAL EXERGY CERTIFIED
from cortex.robinson import robinson_resolution, resolve, is_tautology, subsumes

def test_resolve():
    clause1 = frozenset({'P', 'Q'})
    clause2 = frozenset({'~P', 'R'})
    resolvents = resolve(clause1, clause2)
    assert frozenset({'Q', 'R'}) in resolvents

def test_resolve_tautology_elimination():
    clause1 = frozenset({'P', 'Q'})
    clause2 = frozenset({'~P', '~Q'})
    # Resolving on P gives {Q, ~Q}, which is a tautology and should be excluded.
    resolvents = resolve(clause1, clause2)
    assert len(resolvents) == 0

def test_is_tautology():
    assert is_tautology(frozenset({'A', '~A'})) == True
    assert is_tautology(frozenset({'A', 'B'})) == False

def test_subsumes():
    # {P} subsumes {P, Q}
    assert subsumes(frozenset({'P'}), frozenset({'P', 'Q'})) == True
    # {P, Q} does not subsume {P}
    assert subsumes(frozenset({'P', 'Q'}), frozenset({'P'})) == False

def test_robinson_resolution_unsatisfiable():
    # P, P -> Q, ~Q => Unsatisfiable
    clauses = [
        {'P'},
        {'~P', 'Q'},
        {'~Q'}
    ]
    assert robinson_resolution(clauses) == True

def test_robinson_resolution_satisfiable():
    # P, P -> Q => Satisfiable
    clauses = [
        {'P'},
        {'~P', 'Q'}
    ]
    assert robinson_resolution(clauses) == False

def test_robinson_resolution_with_tautologies():
    # {P, ~P}, {Q}, {~Q} => Unsatisfiable (tautology doesn't affect outcome, just tests handling)
    clauses = [
        {'P', '~P'},
        {'Q'},
        {'~Q'}
    ]
    assert robinson_resolution(clauses) == True
