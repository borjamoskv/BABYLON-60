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
    Implements Robinson's Resolution Principle augmented with Subsumption
    and Tautology Deletion for optimal exergy and minimal state explosion.
    Returns True if unsatisfiable (derives empty clause), False if satisfiable.
    """
    # 1. Tautology Deletion on initial clauses
    clauses = {frozenset(c) for c in clauses if not is_tautology(c)}

    # 2. Forward Subsumption on initial clauses
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

        # 3. Forward Subsumption on new clauses
        filtered_new = set()
        for new_c in generated_in_step:
            if any(subsumes(active_c, new_c) for active_c in active_clauses):
                continue
            filtered_new.add(new_c)

        if not filtered_new or filtered_new.issubset(active_clauses):
            return False # Satisfiable, saturation reached

        # 4. Backward Subsumption: remove active clauses subsumed by new ones
        active_clauses = {c for c in active_clauses if not any(subsumes(new_c, c) for new_c in filtered_new)}
        active_clauses.update(filtered_new)
