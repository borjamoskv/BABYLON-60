% Claim: [ROBINSON-RESOLUTION-PROLOG] Resolver de Cláusulas por Resolución de Robinson
% Proof:
%   Base: "Principio de Resolución de J. Alan Robinson (1965)"
%         "Unification Algorithm de Martelli-Montanari (1982)"
%   Confidence: C5-REAL

% Representación de cláusulas como listas de literales.
% Un literal positivo es L, uno negativo es neg(L).

% contrarios(L1, L2) es verdadero si son literales complementarios
contrarios(L, neg(L)).
contrarios(neg(L), L).

% resuelve(C1, C2, Resolvente) aplica resolución de Robinson sobre una pareja de cláusulas
resuelve(C1, C2, Resolvente) :-
    select(L1, C1, Resto1),
    select(L2, C2, Resto2),
    contrarios(L1, L2),
    append(Resto1, Resto2, RawResolvente),
    sort(RawResolvente, Resolvente). % Elimina duplicados y ordena

% resolucion_paso(Clausulas, NuevaClausula) busca una resolución en un solo paso
resolucion_paso(Clausulas, Resolvente) :-
    select(C1, Clausulas, Resto),
    member(C2, Resto),
    resuelve(C1, C2, Resolvente),
    \+ member(Resolvente, Clausulas). % Evita generar cláusulas redundantes

% clausula_vacia comprueba si la cláusula vacía (contradicción []) está presente
contiene_contradiccion(Clausulas) :-
    member([], Clausulas).

% probar_inconsistencia(Clausulas, Pasos) ejecuta saturación por resolución
probar_inconsistencia(Clausulas, Clausulas) :-
    contiene_contradiccion(Clausulas), !.
probar_inconsistencia(Clausulas, HistorialCompleto) :-
    resolucion_paso(Clausulas, NuevoResolvente),
    probar_inconsistencia([NuevoResolvente|Clausulas], HistorialCompleto).

% --- FIRST-ORDER LOGIC EXPANSION ---

% occurs_check(Var, Term): true if Var occurs in Term
occurs_check(Var, Term) :-
    var(Term), !, Var == Term.
occurs_check(Var, Term) :-
    compound(Term),
    Term =.. [_|Args],
    member(Arg, Args),
    occurs_check(Var, Arg), !.

% unify(T1, T2): Martelli-Montanari Unification with Occurs Check
unify(T1, T2) :-
    var(T1), var(T2), T1 == T2, !.
unify(T1, T2) :-
    var(T1), !,
    \+ occurs_check(T1, T2),
    T1 = T2.
unify(T1, T2) :-
    var(T2), !,
    \+ occurs_check(T2, T1),
    T2 = T1.
unify(T1, T2) :-
    atomic(T1), atomic(T2), !, T1 = T2.
unify(T1, T2) :-
    compound(T1), compound(T2),
    T1 =.. [F|Args1], T2 =.. [F|Args2],
    length(Args1, L), length(Args2, L),
    unify_args(Args1, Args2).

unify_args([], []).
unify_args([H1|T1], [H2|T2]) :-
    unify(H1, H2),
    unify_args(T1, T2).

% contrarios_fo(L1, L2): FO complementary literals
contrarios_fo(L1, neg(L2)) :- unify(L1, L2).
contrarios_fo(neg(L1), L2) :- unify(L1, L2).

% resolve_fo(C1, C2, Resolvente): First-order resolution
resolve_fo(C1, C2, Resolvente) :-
    copy_term(C1-C2, C1Copy-C2Copy),
    select(L1, C1Copy, Resto1),
    select(L2, C2Copy, Resto2),
    contrarios_fo(L1, L2),
    append(Resto1, Resto2, RawResolvente),
    sort(RawResolvente, Resolvente).

:- if(false).
% Test Harness for First-Order Resolution
test_fo_resolution :-
    % C1: P(x) | Q(f(x))
    % C2: ~P(a) | R(y)
    % Expected Resolvent: Q(f(a)) | R(y)
    C1 = [p(X), q(f(X))],
    C2 = [neg(p(a)), r(Y)],
    resolve_fo(C1, C2, Res),
    write('C1: '), write(C1), nl,
    write('C2: '), write(C2), nl,
    write('Resolvent: '), write(Res), nl.
:- endif.
