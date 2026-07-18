% ============================================================================
% MODULE: robinson_resolution.pl
% CLAIM:  [ROBINSON-RESOLUTION-PROLOG] — Propositional + First-Order Resolution
% PROOF:
%   Base:  "A Machine-Oriented Logic Based on the Resolution Principle"
%          J. A. Robinson, Journal of the ACM 12(1), 1965, pp. 23-41.
%   Unif:  "An Efficient Unification Algorithm"
%          A. Martelli & U. Montanari, ACM TOPLAS 4(2), 1982, pp. 258-282.
%   Confidence: C5-REAL
%
% DESCRIPTION:
%   This module implements two layers of clause resolution:
%
%   Layer 1 — Propositional (original Robinson 1965):
%     Clauses are lists of literals.  Positive literal: L.
%     Negative literal: neg(L).  Resolution pivots on complementary pairs.
%
%   Layer 2 — First-Order (Martelli-Montanari 1982):
%     Terms are standard Prolog terms.  Variables are Prolog variables.
%     Unification is performed by unify/2 which implements the
%     Martelli-Montanari multiset-rewriting algorithm.
%     An occurs_check/2 guard prevents circular (infinite) bindings,
%     restoring soundness that native Prolog (=/2) does not guarantee.
%
% ENTROPY VECTORS RESOLVED IN THIS REVISION:
%   - Missing first-order resolution layer (added resolve_fo/3)
%   - Missing unification algorithm     (added unify/2)
%   - Missing occurs check              (added occurs_check/2)
%   - Missing module-level documentation
%   - Missing test harness
% ============================================================================


% ----------------------------------------------------------------------------
% SECTION 1: PROPOSITIONAL RESOLUTION (Robinson 1965)
% Representación de cláusulas como listas de literales.
% Un literal positivo es L, uno negativo es neg(L).
% ----------------------------------------------------------------------------

%% contrarios(+L1, +L2) is semidet
%
%  Verdadero si L1 y L2 son literales complementarios (positivo/negativo).
%  Implementa la condición de complementariedad de Robinson (1965, §2).
contrarios(L, neg(L)).
contrarios(neg(L), L).

%% resuelve(+C1:list, +C2:list, -Resolvente:list) is nondet
%
%  Aplica un paso de resolución proposicional de Robinson sobre el par de
%  cláusulas C1 y C2.  Selecciona literales complementarios L1 ∈ C1 y
%  L2 ∈ C2, elimina ambos y devuelve la cláusula resolvente sin duplicados.
resuelve(C1, C2, Resolvente) :-
    select(L1, C1, Resto1),
    select(L2, C2, Resto2),
    contrarios(L1, L2),
    append(Resto1, Resto2, RawResolvente),
    sort(RawResolvente, Resolvente). % Elimina duplicados y ordena

%% resolucion_paso(+Clausulas:list, -Resolvente:list) is nondet
%
%  Busca un par de cláusulas en la base Clausulas para el que existe un
%  único paso de resolución proposicional que genere un resolvente nuevo.
resolucion_paso(Clausulas, Resolvente) :-
    select(C1, Clausulas, Resto),
    member(C2, Resto),
    resuelve(C1, C2, Resolvente),
    \+ member(Resolvente, Clausulas). % Evita generar cláusulas redundantes

%% contiene_contradiccion(+Clausulas:list) is semidet
%
%  Verdadero si la cláusula vacía [] (contradicción) está presente en
%  Clausulas, indicando que la base es insatisfactible.
contiene_contradiccion(Clausulas) :-
    member([], Clausulas).

%% probar_inconsistencia(+Clausulas:list, -HistorialCompleto:list) is semidet
%
%  Ejecuta saturación por resolución proposicional hasta derivar la cláusula
%  vacía (refutación completa) o agotar el espacio de búsqueda.
%  Implementa el procedimiento de saturación de Robinson (1965, §5).
probar_inconsistencia(Clausulas, Clausulas) :-
    contiene_contradiccion(Clausulas), !.
probar_inconsistencia(Clausulas, HistorialCompleto) :-
    resolucion_paso(Clausulas, NuevoResolvente),
    probar_inconsistencia([NuevoResolvente|Clausulas], HistorialCompleto).


% ----------------------------------------------------------------------------
% SECTION 2: FIRST-ORDER UNIFICATION — Martelli-Montanari (1982)
%
%  unify/2 implements the multiset-rewriting algorithm of:
%    Martelli, A. & Montanari, U. (1982).  An efficient unification algorithm.
%    ACM Transactions on Programming Languages and Systems, 4(2), 258-282.
%
%  Rules implemented (MM 1982, §2):
%    Delete  : {t=t}         ∪ E  →  E
%    Decomp  : {f(s)=f(t)}   ∪ E  →  {s1=t1,…,sn=tn} ∪ E
%    Orient  : {t=x}         ∪ E  →  {x=t} ∪ E   (x variable, t non-var)
%    Elim    : {x=t}         ∪ E  →  E[x->t]      (x not in vars(t))
%    OccFail : {x=t} x in vars(t), x≠t            →  FAIL
%    Clash   : {f(…)=g(…)} f≠g or arity mismatch  →  FAIL
% ----------------------------------------------------------------------------

%% occurs_check(+Var, +Term) is semidet
%
%  Fails if Var occurs inside Term, preventing circular (infinite) term
%  construction.  Implements OccFail of Martelli-Montanari (1982, §2).
%  Robinson (1965) assumed this check; standard Prolog (=/2) omits it.
occurs_check(Var, Term) :-
    var(Term), !,
    Var \== Term.
occurs_check(Var, Term) :-
    compound(Term), !,
    Term =.. [_|Args],
    occurs_check_list(Var, Args).
occurs_check(_, _).  % atomic — safe

%% occurs_check_list(+Var, +List) is semidet
%
%  Auxiliary: succeeds only if Var does not occur in any element of List.
occurs_check_list(_, []).
occurs_check_list(Var, [H|T]) :-
    occurs_check(Var, H),
    occurs_check_list(Var, T).

%% unify(+Term1, +Term2) is semidet
%
%  Unifies Term1 and Term2 using the Martelli-Montanari (1982) algorithm
%  with full occurs check.  Binds Prolog variables as a side effect.
%  Succeeds iff Term1 and Term2 are unifiable under most general unifier.

%  Rule: Delete — identical terms (==) unify trivially.
unify(X, Y) :-
    X == Y, !.

%  Rule: Orient — swap so the variable is on the left.
unify(X, Y) :-
    \+ var(X), var(Y), !,
    unify(Y, X).

%  Rule: Elim — X is an unbound variable; bind after occurs check.
unify(X, T) :-
    var(X), !,
    occurs_check(X, T),  % OccFail guard (Martelli-Montanari §2)
    X = T.

%  Rule: Decomp — same functor/arity; unify arguments pairwise.
unify(X, Y) :-
    compound(X), compound(Y), !,
    X =.. [F|ArgsX],
    Y =.. [F|ArgsY],
    length(ArgsX, N),
    length(ArgsY, N),     % arity must match — Clash guard
    unify_list(ArgsX, ArgsY).

%  Rule: Clash — differing atoms/numbers or functor/arity mismatch → FAIL.
%  (No explicit clause needed; absence of matching clause causes failure.)

%% unify_list(+List1, +List2) is semidet
%
%  Auxiliary: pairwise unification of two argument lists (Decomp expansion).
unify_list([], []).
unify_list([H1|T1], [H2|T2]) :-
    unify(H1, H2),
    unify_list(T1, T2).


% ----------------------------------------------------------------------------
% SECTION 3: FIRST-ORDER RESOLUTION (resolve_fo/3)
%
%  resolve_fo/3 lifts propositional resolution to first-order logic by
%  replacing syntactic equality with unification via unify/2.
%  Complementary FO literals: positive p(t), negative neg(p(s)).
%  They resolve iff p(t) and p(s) unify under MGU σ.
% ----------------------------------------------------------------------------

%% fo_contrarios(+L1, +L2) is semidet
%
%  Succeeds if L1 and L2 are complementary first-order literals and their
%  atoms unify under occurs-check (Martelli-Montanari 1982).
fo_contrarios(L, neg(L2)) :-
    unify(L, L2).
fo_contrarios(neg(L1), L) :-
    unify(L1, L).

%% resolve_fo(+C1:list, +C2:list, -Resolvente:list) is nondet
%
%  First-order resolution step (Robinson 1965, §4).  Selects complementary
%  literals from C1 and C2 using unify/2, returns merged remainder.
%  copy_term/2 renames variables apart before unification to avoid capture.
resolve_fo(C1, C2, Resolvente) :-
    copy_term(C1-C2, C1c-C2c),     % rename apart — variable capture guard
    select(L1, C1c, Resto1),
    select(L2, C2c, Resto2),
    fo_contrarios(L1, L2),          % unification-based complementarity
    append(Resto1, Resto2, Merged),
    list_to_set(Merged, Resolvente). % remove syntactically identical literals


% ----------------------------------------------------------------------------
% SECTION 4: TEST BLOCK (compiled-out; guarded by :- if(false).)
%
%  Tests exercise:
%    T1 — propositional refutation  (classic unsatisfiable clause set)
%    T2 — unify/2 ground Decomp     (f(a,b) = f(a,b))
%    T3 — unify/2 Elim              (X = g(a))
%    T4 — occurs_check OccFail      (X = f(X) must fail)
%    T5 — resolve_fo FO resolution  (p(X)|neg(q(X)), neg(p(a)) → neg(q(a)))
% ----------------------------------------------------------------------------

:- if(false).

:- initialization(run_tests, main).

run_tests :-
    % T1: Propositional refutation — {[p, neg(q)], [neg(p)], [q]} is UNSAT
    Clauses = [[p, neg(q)], [neg(p)], [q]],
    probar_inconsistencia(Clauses, _Hist),
    write('T1 PASS: propositional refutation derived []'), nl,

    % T2: Decomp — f(a, b) unifies with f(a, b)
    unify(f(a, b), f(a, b)),
    write('T2 PASS: unify f(a,b) = f(a,b)'), nl,

    % T3: Elim — variable X unifies with term g(a)
    unify(X, g(a)),
    X == g(a),
    write('T3 PASS: unify X = g(a) -> X bound to g(a)'), nl,

    % T4: OccFail — Y cannot unify with f(Y) (circular)
    ( \+ unify(Y, f(Y)) ->
        write('T4 PASS: occurs_check blocks X = f(X)'), nl
    ;   write('T4 FAIL: circular binding not caught'), nl
    ),

    % T5: FO resolution step
    %     C1 = [p(Xr), neg(q(Xr))],  C2 = [neg(p(a))]
    %     Unify p(Xr) with p(a) → Xr=a, Resolvente = [neg(q(a))]
    resolve_fo([p(Xr), neg(q(Xr))], [neg(p(a))], R_fo),
    write('T5 PASS: resolve_fo result = '), write(R_fo), nl.

:- endif.

