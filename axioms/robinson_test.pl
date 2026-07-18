:- consult('../axioms/robinson_resolution.pl').

:- initialization(run_all, main).

run_all :-
    writeln('=== C5-REAL ROBINSON RESOLUTION TESTS ==='),

    % Test 1: Refutación proposicional {p,q},{¬p,q},{p,¬q},{¬p,¬q}
    % Representación nativa: literal positivo = átomo, negativo = neg(átomo)
    (probar_inconsistencia(
        [[p,q],[neg(p),q],[p,neg(q)],[neg(p),neg(q)]],
        _)
    ->  writeln('[T1 PASS] Propositional refutation: contradiction reached')
    ;   writeln('[T1 FAIL] Propositional refutation: no contradiction')),

    % Test 2: Un solo par resolvente
    (resuelve([a, b], [neg(a), c], R),
     writeln('[T2 PASS] Single resolve:'), writeln(R)
    ; writeln('[T2 FAIL] Single resolve failed')),

    % Test 3: Unificación FO — Decomposición f(X) = f(a) => X = a
    (unify(f(X1), f(a)), X1 == a
    ->  writeln('[T3 PASS] FO Decomp: f(X)=f(a) => X=a')
    ;   writeln('[T3 FAIL] FO Decomp failed')),

    % Test 4: Unificación FO — Orient: variable lhs
    (unify(Y1, hello), Y1 == hello
    ->  writeln('[T4 PASS] FO Orient: Y=hello')
    ;   writeln('[T4 FAIL] FO Orient failed')),

    % Test 5: occurs_check bloquea X = f(X) — evita binding circular
    (occurs_check(Z1, f(Z1))
    ->  writeln('[T5 FAIL] occurs_check should block circular binding')
    ;   writeln('[T5 PASS] occurs_check: circular binding blocked correctly')),

    % Test 6: Clash — f(a) != f(b)
    (unify(f(a), f(b))
    ->  writeln('[T6 FAIL] Clash should fail')
    ;   writeln('[T6 PASS] Clash: f(a)!=f(b) correctly fails')),

    writeln('=== SUITE COMPLETE ==='),
    halt(0).
