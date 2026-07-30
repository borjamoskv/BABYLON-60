# C5-REAL EXERGY CERTIFIED
from cortex.core.unification import unify, apply_substitution

def test_unify_identity():
    # f(a, b) = f(a, b)
    t1 = ('f', 'a', 'b')
    t2 = ('f', 'a', 'b')
    assert unify(t1, t2) == {}

def test_unify_variable():
    # ?X = g(a)
    t1 = '?X'
    t2 = ('g', 'a')
    env = unify(t1, t2)
    assert env == {'?X': ('g', 'a')}
    assert apply_substitution(t1, env) == ('g', 'a')

def test_unify_variable_variable():
    # ?X = ?Y
    t1 = '?X'
    t2 = '?Y'
    env = unify(t1, t2)
    assert env == {'?X': '?Y'}

def test_unify_occurs_check():
    # ?X = f(?X) -> should fail (circular binding)
    t1 = '?X'
    t2 = ('f', '?X')
    assert unify(t1, t2) is None

def test_unify_complex():
    # p(?X, f(?Y)) = p(a, f(b))
    t1 = ('p', '?X', ('f', '?Y'))
    t2 = ('p', 'a', ('f', 'b'))
    env = unify(t1, t2)
    assert env == {'?X': 'a', '?Y': 'b'}

def test_unify_clash():
    # p(a) = q(a) -> FAIL
    t1 = ('p', 'a')
    t2 = ('q', 'a')
    assert unify(t1, t2) is None

def test_unify_arity_mismatch():
    # f(a) = f(a, b) -> FAIL
    t1 = ('f', 'a')
    t2 = ('f', 'a', 'b')
    assert unify(t1, t2) is None

def test_unify_transitive():
    # ?X = ?Y, ?Y = a -> ?X should evaluate to 'a'
    t1 = ('f', '?X', '?Y')
    t2 = ('f', '?Y', 'a')
    env = unify(t1, t2)
    assert env is not None
    assert apply_substitution('?X', env) == 'a'
    assert apply_substitution('?Y', env) == 'a'
