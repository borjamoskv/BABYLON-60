# C5-REAL EXERGY CERTIFIED
def is_tautology(clause):
    """A clause is a tautology if it contains both a literal and its negation."""
    for literal in clause:
        neg_literal = literal[1:] if literal.startswith('~') else '~' + literal
        if neg_literal in clause:
            return True
    return False

def subsumes(clause1, clause2):
    """Returns True if clause1 subsumes clause2 (i.e., clause1 is a subset of clause2)."""
    return clause1.issubset(clause2)

def pure_literal_elimination(clauses):
    """
    Removes clauses containing pure literals (literals whose negation doesn't appear).
    """
    while True:
        all_literals = set()
        for clause in clauses:
            all_literals.update(clause)

        pure_literals = set()
        for lit in all_literals:
            neg_lit = lit[1:] if lit.startswith('~') else '~' + lit
            if neg_lit not in all_literals:
                pure_literals.add(lit)

        if not pure_literals:
            break

        new_clauses = {c for c in clauses if not any(p in c for p in pure_literals)}
        if len(new_clauses) == len(clauses):
            break
        clauses = new_clauses
    return clauses

def unit_propagation(clauses):
    """
    Applies Unit Propagation (Boolean Constraint Propagation).
    Returns the new set of clauses, and a boolean indicating if UNSAT was derived.
    """
    clauses = set(clauses)
    while True:
        units = [c for c in clauses if len(c) == 1]
        if not units:
            break

        unit = units[0]
        l = list(unit)[0]
        neg_l = l[1:] if l.startswith('~') else '~' + l

        new_clauses = set()
        for c in clauses:
            if l in c:
                continue # Clause is subsumed by the unit
            if neg_l in c:
                new_c = set(c)
                new_c.remove(neg_l)
                if not new_c:
                    return set(), True # Derives empty clause -> UNSAT
                new_clauses.add(frozenset(new_c))
            else:
                new_clauses.add(c)

        if clauses == new_clauses:
            break
        clauses = new_clauses
    return clauses, False

def resolve(clause1, clause2):
    """
    Returns a set of all possible clauses obtained by resolving clause1 and clause2.
    """
    resolvents = set()
    for literal in clause1:
        neg_literal = literal[1:] if literal.startswith('~') else '~' + literal
        if neg_literal in clause2:
            new_clause = set(clause1) | set(clause2)
            new_clause.remove(literal)
            new_clause.remove(neg_literal)

            # Avoid generating tautologies
            if not is_tautology(new_clause):
                resolvents.add(frozenset(new_clause))
    return resolvents

def robinson_resolution(clauses):
    """
    Implements Robinson's Resolution Principle augmented with DPLL techniques:
    Unit Propagation, Pure Literal Elimination, Tautology Deletion, and Subsumption
    for maximum thermodynamic exergy and minimal state explosion.
    Returns True if unsatisfiable (derives empty clause), False if satisfiable.
    """
    # 1. Tautology Deletion on initial clauses
    clauses = {frozenset(c) for c in clauses if not is_tautology(c)}

    # 2. DPLL Pre-processing: Unit Propagation and Pure Literal Elimination
    clauses, unsat = unit_propagation(clauses)
    if unsat:
        return True
    clauses = pure_literal_elimination(clauses)
    if not clauses:
        return False

    # 3. Forward Subsumption on initial clauses
    active_clauses = set()
    for c in sorted(clauses, key=len):
        if not any(subsumes(active_c, c) for active_c in active_clauses):
            active_clauses.add(c)

    while True:
        clauses_list = list(active_clauses)
        n = len(clauses_list)
        generated_in_step = set()

        for i in range(n):
            for j in range(i + 1, n):
                resolvents = resolve(clauses_list[i], clauses_list[j])
                if frozenset() in resolvents:
                    return True # Unsatisfiable
                generated_in_step.update(resolvents)

        # Combine active and newly generated clauses
        combined = active_clauses | generated_in_step

        # Apply intense DPLL pruning on the combined state space
        combined, unsat = unit_propagation(combined)
        if unsat:
            return True
        combined = pure_literal_elimination(combined)

        if not combined:
            return False # Fully satisfied by pure literals

        # Cross-subsumption (Forward + Backward simultaneously via rebuilding)
        filtered_combined = set()
        for c in sorted(combined, key=len):
            if not any(subsumes(active_c, c) for active_c in filtered_combined):
                filtered_combined.add(c)

        if filtered_combined == active_clauses:
            return False # Satisfiable, saturation reached

        active_clauses = filtered_combined
