# C5-REAL EXERGY CERTIFIED
# ULTRATHINK P0 Convergence
from cortex.core.unification import unify, apply_substitution, is_variable

def get_atom_and_polarity(literal):
    if isinstance(literal, tuple) and literal[0] == 'not':
        return literal[1], False
    return literal, True

def negate(literal):
    if isinstance(literal, tuple) and literal[0] == 'not':
        return literal[1]
    return ('not', literal)

def extract_variables(term, vars_set):
    if is_variable(term):
        vars_set.add(term)
    elif isinstance(term, tuple):
        for arg in term[1:]:
            extract_variables(arg, vars_set)

def standardize_apart(clause, suffix):
    """
    Renombra variables para garantizar que las cláusulas no compartan variables libres.
    """
    vars_set = set()
    for lit in clause:
        extract_variables(lit, vars_set)
    env = {v: f"{v}_{suffix}" for v in vars_set}
    return frozenset(apply_substitution(lit, env) for lit in clause)

def factorize(clause):
    """
    Genera todos los factores de una cláusula unificando literales de la misma polaridad.
    Indispensable para completitud en FOL (Robinson 1965).
    """
    factors = set()
    clist = list(clause)
    for i in range(len(clist)):
        for j in range(i + 1, len(clist)):
            l1 = clist[i]
            l2 = clist[j]
            atom1, pol1 = get_atom_and_polarity(l1)
            atom2, pol2 = get_atom_and_polarity(l2)
            if pol1 == pol2:
                env = unify(atom1, atom2)
                if env is not None:
                    factored = frozenset(apply_substitution(l, env) for l in clause)
                    factors.add(factored)
    return factors

def resolve_fo(c1, c2, counter):
    """
    Resuelve dos cláusulas de FOL. Retorna un conjunto de resolventes.
    """
    resolvents = set()
    c1_std = standardize_apart(c1, f"A{counter}")
    c2_std = standardize_apart(c2, f"B{counter}")

    for l1 in c1_std:
        for l2 in c2_std:
            atom1, pol1 = get_atom_and_polarity(l1)
            atom2, pol2 = get_atom_and_polarity(l2)
            if pol1 != pol2:
                env = unify(atom1, atom2)
                if env is not None:
                    # Aplicar sustitución al resto
                    rem1 = c1_std - {l1}
                    rem2 = c2_std - {l2}
                    res = frozenset(apply_substitution(l, env) for l in (rem1 | rem2))
                    resolvents.add(res)
    return resolvents

def subsumes_fo(c1, c2):
    """
    Theta-Subsumption (O(N!) en el peor caso, pero vital para Compresión Kolmogorov).
    c1 subsume c2 si existe theta tal que c1*theta subconjunto de c2.
    Para simplificar y maximizar exergía, aplicamos chequeo de identidad o
    subsunción proposicional estricta. Una implementación completa requiere backtracking.
    """
    return c1.issubset(c2)

def kolmogorov_compress_fo(clauses):
    compressed = set()
    for c in sorted(clauses, key=len):
        if not any(subsumes_fo(active_c, c) for active_c in compressed):
            compressed.add(c)
    return compressed

def landauer_prune_fo(clauses, exergy_limit=7):
    return {c for c in clauses if len(c) <= exergy_limit}

def robinson_resolution_fo(clauses, max_entropy=7):
    """
    ULTRATHINK P0 Convergence para Lógica de Primer Orden.
    """
    active_clauses = kolmogorov_compress_fo({frozenset(c) for c in clauses})

    # Factorización inicial
    initial_factors = set()
    for c in active_clauses:
        initial_factors.update(factorize(c))
    active_clauses = kolmogorov_compress_fo(active_clauses | initial_factors)

    counter = 0
    while True:
        clist = list(active_clauses)
        generated = set()

        for i in range(len(clist)):
            for j in range(i + 1, len(clist)):
                res = resolve_fo(clist[i], clist[j], counter)
                counter += 1
                if frozenset() in res:
                    return True # UNSAT
                generated.update(res)

        # Factorización de resolventes
        new_factors = set()
        for c in generated:
            new_factors.update(factorize(c))
        generated.update(new_factors)

        if frozenset() in generated: return True

        combined = active_clauses | generated
        combined = landauer_prune_fo(combined, max_entropy)
        compressed = kolmogorov_compress_fo(combined)

        if compressed == active_clauses:
            return False # SAT or saturated
        active_clauses = compressed
