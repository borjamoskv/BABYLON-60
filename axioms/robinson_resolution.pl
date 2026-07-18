% Claim: [ROBINSON-RESOLUTION-PROLOG] Resolver de Cláusulas por Resolución de Robinson
% Proof:
%   Base: "Principio de Resolución de J. Alan Robinson (1965)"
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
