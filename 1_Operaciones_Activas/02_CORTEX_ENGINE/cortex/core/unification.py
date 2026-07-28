# C5-REAL EXERGY CERTIFIED
# Martelli-Montanari (1982) Unification Algorithm with Occurs Check
# Extends Robinson's Propositional Resolution to First-Order Logic (FOL)

def is_variable(term):
    """
    Las variables se denotan como cadenas que comienzan con '?'.
    Cualquier otra cadena (ej. 'a', 'x') se trata como constante (Skolem).
    """
    return isinstance(term, str) and term.startswith('?')

def occurs_check(var, term):
    """
    Previene la construcción de términos infinitos / bindings circulares.
    Implementación rigurosa requerida por C5-REAL para garantizar terminación.
    """
    if term == var:
        return True
    if isinstance(term, tuple):
        return any(occurs_check(var, arg) for arg in term[1:])
    return False

def unify(t1, t2, env=None):
    """
    Unifica dos términos de Lógica de Primer Orden (FOL).
    Devuelve un diccionario con las sustituciones (Most General Unifier - MGU),
    o None si los términos no unifican.
    Los términos complejos se representan como tuplas: ('f', '?x', 'a') -> f(?x, a).
    """
    if env is None:
        env = {}

    # 1. Elim (Resolución de bindings previos)
    while is_variable(t1) and t1 in env:
        t1 = env[t1]
    while is_variable(t2) and t2 in env:
        t2 = env[t2]

    # 2. Delete (Identidad estricta)
    if t1 == t2:
        return env

    # 3. Orient / Elim (Binding de Variable 1)
    if is_variable(t1):
        if occurs_check(t1, t2):
            return None # OccFail
        env[t1] = t2
        return env

    # 4. Orient / Elim (Binding de Variable 2)
    if is_variable(t2):
        if occurs_check(t2, t1):
            return None # OccFail
        env[t2] = t1
        return env

    # 5. Decomp (Descomposición recursiva de functores/predicados)
    if isinstance(t1, tuple) and isinstance(t2, tuple):
        # Clash (Fallo por colisión de functor o aridad)
        if t1[0] != t2[0] or len(t1) != len(t2):
            return None

        for arg1, arg2 in zip(t1[1:], t2[1:]):
            env = unify(arg1, arg2, env)
            if env is None:
                return None
        return env

    # Clash (Constantes o tipos primitivos discordantes)
    return None

def apply_substitution(term, env):
    """
    Aplica el entorno (MGU) al término de forma recursiva (sustitución).
    """
    if is_variable(term):
        if term in env:
            return apply_substitution(env[term], env)
        return term
    if isinstance(term, tuple):
        return tuple([term[0]] + [apply_substitution(arg, env) for arg in term[1:]])
    return term
