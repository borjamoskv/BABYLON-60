# C5-REAL EXERGY CERTIFIED
from cortex.core.robinson_fo import robinson_resolution_fo, factorize, standardize_apart

def test_socrates():
    # 1. Man(Socrates)
    # 2. ~Man(x) v Mortal(x)
    # 3. ~Mortal(Socrates)
    clauses = [
        {('Man', 'Socrates')},
        {('not', ('Man', '?x')), ('Mortal', '?x')},
        {('not', ('Mortal', 'Socrates'))}
    ]
    # Should resolve to UNSAT (True)
    assert robinson_resolution_fo(clauses) == True

def test_factoring():
    # P(x) v P(a)
    clause = frozenset({('P', '?x'), ('P', 'a')})
    factors = factorize(clause)
    # Factoring unifies ?x with a, producing P(a)
    assert frozenset({('P', 'a')}) in factors

def test_standardize_apart():
    clause = frozenset({('P', '?x', '?y')})
    std = standardize_apart(clause, '1')
    assert std == frozenset({('P', '?x_1', '?y_1')})

def test_satisfiable_fo():
    # 1. P(a)
    # 2. ~P(b)
    clauses = [
        {('P', 'a')},
        {('not', ('P', 'b'))}
    ]
    # Cannot resolve -> SAT (False)
    assert robinson_resolution_fo(clauses) == False

def test_theta_subsumption():
    from cortex.core.robinson_fo import subsumes_fo
    # C1 = {P(?x)}, C2 = {P(a), Q(b)}
    # P(?x) theta-subsumes P(a) with ?x=a
    c1 = frozenset({('P', '?x')})
    c2 = frozenset({('P', 'a'), ('Q', 'b')})
    assert subsumes_fo(c1, c2) == True

    # C3 = {Q(b)}, C2 = {P(a), Q(b)} -> Q(b) is in C2!
    c3 = frozenset({('Q', 'b')})
    assert subsumes_fo(c3, c2) == True

    # C4 = {P(c)} -> P(c) does not subsume {P(a), Q(b)}
    c4 = frozenset({('P', 'c')})
    assert subsumes_fo(c4, c2) == False

