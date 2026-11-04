# Lote 9 ejecutado: Git del monitor de estado — 29/10/2026

C0438 pasa a FIXED para la inclusión de trabajo ajeno, omisión de controles y
falso éxito de las operaciones Git del monitor. La única fuente productiva
editada es `scripts/c5_thermo/c5_exergy_optimizer_monitor.py`. El
[registro reconciliado](evidence/swarm100-round3-20261028/registry.json)
y la [validación final](evidence/swarm100-lot9-20261029/validation.json)
conservan estados, comandos, hashes y límites.

## Reproducción y aceptación

Las [ocho reproducciones previas](evidence/swarm100-lot9-20261029/before-tests.log)
fallaron contra el [hash del plan](evidence/swarm100-lot9-20261029/before-source-manifest.json):
error de Git convertido en salida vacía, configuración de firma omitida,
índice preparado consumido, ruta obsoleta que ocultaba un commit fallido,
hook omitido, COMPLETE tras rechazo, doble commit con reemplazo histórico y
HEAD viejo presentado como resultado de un no-op.

**829 pruebas pasan y 1 se omite** en la suite relacionada final, incluidas
**47 regresiones del lote**. La omisión corresponde a strike_rs no compilado,
con el módulo bloqueado antes de recoger los tests. Pasan MyPy con
check-untyped-defs, Ruff y los controles documentales. Fuente y tests conservan
los mismos hashes antes/después de la ejecución.

La [revisión independiente](evidence/swarm100-lot9-20261029/independent-review.json)
aprueba **10 controles en 15 repositorios temporales**, repite las 47 regresiones
y Ruff y no deja hallazgos accionables abiertos dentro de C0438. Verifica firma
configurada mediante caller, tres hooks rechazados sin reintento, preflight
antes de productores, un único commit, conservación histórica y no-op explícito.

## Corrección

_git_bytes conserva stdout como bytes y usa check=True. _git decodifica solo
metadatos para presentación mediante filesystem decoding. Los errores no se
transforman en cadenas vacías, ceros ni hashes aparentes. Se retiran los
overrides commit.gpgsign=false y --no-verify; los hooks y la configuración de
firma permanecen activos. El firmante de prueba solo registra su invocación y
falla: no se usa ninguna clave ni se realiza firma real.

El preflight se ejecuta al comienzo del caller, antes de censo, auditorías,
cristalización o append; vuelve a comprobarse antes del commit. Exige la raíz
Git exacta, STATUS.md regular y ya tracked, índice sin preparación/intent-to-add
ni flags especiales, HEAD/rama válidos y estado soportado. Rechaza selectores
ambientales que puedan desviar repo/índice/configuración, sparse, split index y
operaciones Git en curso. Las consultas no refrescan el índice implícitamente.

El monitor genera STATUS.md: no prepara su fuente actual ni la ruta obsoleta.
Se usa un único git commit --only sobre STATUS.md; Git gestiona la preparación
temporal y su descarte ante rechazo ordinario. No hay add global, reset, clean,
stash ni retry de bypass. Se comprueban padre, rama y ruta del commit creado.
El enfoque del Lote 8 se aplica con un preflight específico de una sola salida,
sin copiar/importar su helper general ni ampliar archivos productivos.

El caller añade una fila con COMMIT_REFERENCE_IN_STDOUT, un marcador neutral.
No reemplaza pendientes históricos ni intenta incluir dentro del documento el
hash del mismo commit que lo contiene. Se elimina el amend automático. Solo
un commit nuevo comprobado permite imprimir COMPLETE y su OID completo. Si
no hay cambios, el helper devuelve None y el caller imprime NO_CHANGE sin
presentar el HEAD existente como un commit nuevo. Los fallos se propagan.

Se probaron rutas con espacios, contenido binario, un worktree vinculado,
intercalaciones de índice/HEAD y warmup más cuatro commits secuenciales. Estos
casos comprueban comportamiento, no rendimiento o aislamiento físico. El
[control AST y de alcance](evidence/swarm100-lot9-20261029/scope-check.json)
confirma intactas las funciones de censo, métricas, cálculo SHA3 y append, y las
fases de auditoría del caller. Los lotes 7/8, dependencias y lockfiles conservan
sus hashes.

## Límites

- Git, su configuración, filtros y hooks son código de confianza. Pueden producir
  efectos antes de la postvalidación. Detectar un commit ampliado o HEAD movido
  no contiene ni revierte el efecto; no se acredita sandbox de hooks.
- La selección es por archivo completo. Cambios previos dentro de STATUS.md se
  incluyen; escritores concurrentes del mismo archivo o preparación parcial
  tardía no están cubiertos por una transacción global. Staging de rutas ajenas
  se rechaza en preflight o se preserva/excluye en las intercalaciones probadas.
- Si un productor ya escribió STATUS.md y después falla Git, el archivo puede
  quedar modificado para revisión. No hay rollback de persistencia ni undo
  automático de trabajo ajeno. Hooks arbitrarios tampoco tienen plazo garantizado.
- crystallize_status sigue calculando SHA3 del contenido anterior al append e
  ignora report. Ese digest no liga el reporte ni la fila final. El censo,
  métricas, significado de BFT y contenido de los productores no se certifican
  mediante este cierre de Git; su implementación permanece intacta.
- Todos los commits/hooks de prueba se ejecutaron solo en repositorios temporales
  con identidad/HOME/configuración propios. El monitor usa productores controlados
  en las fixtures; SQLite/red están prohibidos allí. No se ejecutó el monitor sobre el checkout ni se lanzaron sus auditorías/tests
  desde él; tampoco se usaron bases del operador, firma real, hardware, ATTESTED,
  publicación o commit/amend del checkout real. Se omite la telemetría global.

## Registro y siguiente lote

Los 598 IDs originales quedan en **544 OPEN, 46 FIXED, 4 MITIGATED y
4 NOT_APPLICABLE**. Entre los 582 pendientes iniciales: 539 OPEN, 36 FIXED,
3 MITIGATED y 4 NOT_APPLICABLE. Quedan **538 hallazgos únicos OPEN**:
56 P1, 472 P2 y 10 P3. Solo se cierra C0438, sin duplicados adicionales.
C0431 y C0135/C0136 siguen OPEN; C0460 sigue MITIGATED.
SW100-R3-0001 permanece FIXED fuera de los 598 IDs.

El [Lote 10 propuesto](PLAN_SWARM100_LOTE10_2026-10-29.md) agrupa C0574/C0575
en purge_residuals.py. Solo se prepara: el código conserva su hash seleccionado.

El MCP de grafo está disponible: project babylon-60/raíz exacta contrastada,
cobertura metadata_match como señal best-effort. Se consultaron mediante
Context7 las fuentes primarias de
[git commit](https://github.com/git/git/blob/master/Documentation/git-commit.adoc)
y [git config](https://github.com/git/git/blob/master/Documentation/git-config.adoc).
Los comandos utilizados se comprobaron además con Git real en las fixtures.
