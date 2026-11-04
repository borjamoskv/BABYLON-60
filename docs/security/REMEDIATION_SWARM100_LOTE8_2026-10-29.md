# Lote 8 ejecutado: commits limitados a sus resultados — 29/10/2026

C0499 y C0500 pasan a FIXED para el reintento que omitía hooks y la inclusión
de trabajo ajeno mediante staging/commit global. La única fuente productiva
editada es `scripts/c5_cortex/cortex_objectives_transducer.py`, incluidos sus
cuatro consumidores internos. El
[registro reconciliado](evidence/swarm100-round3-20261028/registry.json)
y la [validación final](evidence/swarm100-lot8-20261029/validation.json)
conservan estados, comandos, hashes y límites.

## Reproducción y aceptación

Las [siete reproducciones previas](evidence/swarm100-lot8-20261029/before-tests.log)
fallaron contra el [hash del plan](evidence/swarm100-lot8-20261029/before-source-manifest.json):
rechazos de pre-commit/commit-msg que se eludían, archivos ajenos tracked y
untracked capturados, PROJECT.md ajeno en un comando de YAML y preparación
previa ajena/parcial consumida. Se usaron repositorios temporales, identidad
sintética y configuración Git propia; nunca el helper sobre el checkout real.

**782 pruebas pasan y 1 se omite** en la suite relacionada final. Incluye
**61 regresiones del lote**; la omisión requiere strike_rs no compilado, con
ese módulo bloqueado antes de recoger los tests. Pasan MyPy con
check-untyped-defs, Ruff y los controles documentales. Fuente y tests conservan
los mismos hashes antes y después de la suite.

La [revisión independiente](evidence/swarm100-lot8-20261029/independent-review.json)
aprueba **10 controles en 21 repositorios temporales**, repite las 61 regresiones
y Ruff y no deja hallazgos accionables abiertos dentro del alcance acordado.
También reproduce los dos límites descritos abajo; no los presenta como
propiedades resueltas.

| ID | Corrección | Aceptación observada |
| --- | --- | --- |
| C0499 | Un único commit con hooks normales, sin reintento --no-verify. Errores propagados. | Rechazos no mueven HEAD ni alteran índice en las fixtures normales; hooks positivos sí se ejecutan. Ningún consumidor imprime éxito después de un fallo. |
| C0500 | Selección explícita por consumidor, preflight del índice y commit --only, sin git add global. | Archivos/índice ajenos se preservan; comandos YAML excluyen PROJECT ajeno. Casos de ITA/flags/preparación parcial se rechazan byte a byte. |

## Diseño y compatibilidad

Se sustituye la preparación manual propuesta por `git commit --only`, sin
`git add`: Git prepara el índice temporal y lo descarta si un hook ordinario
rechaza el commit. No se modifica hooksPath, no se fuerza configuración de
firma y no se ejecuta reset, clean o stash. Es un refinamiento documentado
[antes del parche](evidence/swarm100-lot8-20261029/task-contract.md), que evita
restaurar ciegamente contenido preparado por otros actores.

El helper acepta solo los resultados declarados dentro de la raíz Git exacta.
add-objective, add-milestone y update-status seleccionan YAML; iter selecciona
YAML y/o PROJECT según el resultado de cada productor. No basta limitarse a
ambas rutas fijas: incluir siempre PROJECT capturaría cambios ajenos cuando
solo se produce YAML.

Se rechazan selectores ambientales de repo/índice/configuración, índices
preparados, intent-to-add, flags especiales, estados de merge/rebase/sequencer,
HEAD sin commit/rama, sparse y split index. Los resultados seleccionados deben
ser archivos regulares ya tracked, sin seguir enlaces en sus componentes.
Un resultado nuevo/untracked requiere revisión y preparación explícita previa
fuera del helper; no se incorpora automáticamente.

Las consultas de diff operan sobre bytes, sin external diff/textconv; los
prechecks evitan refrescar el índice mediante GIT_OPTIONAL_LOCKS=0. Un no-op
se determina por diff válido y estado estable; devuelve el HEAD existente sin
invocar hooks ni crear commit. Un error no se interpreta mediante frases
localizadas de stderr. Tras un commit se comprueban padre, rama y rutas; un
resultado inesperado produce error, sin deshacer historia ajena.

Se probaron nombres con espacios y Unicode, contenido binario, worktree
vinculado y una repetición de warmup más ocho commits secuenciales. Es una
comprobación de comportamiento y alcance, no un benchmark ni una certificación
de paralelismo. El
[control AST y de alcance](evidence/swarm100-lot8-20261029/scope-check.json)
confirma intactas las funciones ajenas al helper y que los consumidores solo
añaden la selección de resultados. El gate del Lote 7, dependencias y lockfiles
conservan sus hashes.

## Límites explícitos

- La selección es por archivo completo. Ediciones previas no preparadas dentro
  del mismo resultado seleccionado no se separan por fragmento. Un escritor
  concurrente que prepare parcialmente ese mismo output después del último
  precheck puede ver su preparación sustituida por --only. La revisión lo
  reprodujo: no existe una transacción global frente a esos escritores.
- Git, su configuración y los hooks son código de confianza. Un hook que añada
  otra ruta al índice del commit puede generar un commit ampliado antes de que
  la postvalidación lo rechace. Un hook también puede escribir archivos o mover
  referencias. Detectar después no previene ni revierte ese efecto; no se
  acredita sandbox de hooks. Este límite también está reproducido.
- La preparación ajena detectada en preflight se rechaza sin cambios; la
  preparación tardía de rutas ajenas al conjunto seleccionado queda fuera del
  commit y se conserva en las fixtures de intercalación. Esto no implica
  aislamiento de escritores arbitrarios del repositorio.
- Los productores de los comandos escriben YAML/PROJECT antes del helper. Si
  Git falla, esos archivos pueden quedar modificados para revisión, aunque no
  se imprima éxito. No se cierra por inferencia un rollback de persistencia.
- Todos los commits/hooks de prueba se ejecutaron en repositorios temporales
  con HOME/configuración propia, sin firma real ni remotos. TCP/DNS bloqueados;
  no helper/commit/amend en el checkout del operador, hardware, ATTESTED,
  publicación o cambios de dependencias. Se omite la telemetría global.

## Registro y siguiente lote

Los 598 IDs originales quedan en **545 OPEN, 45 FIXED, 4 MITIGATED y
4 NOT_APPLICABLE**. Entre los 582 pendientes iniciales: 540 OPEN, 35 FIXED,
3 MITIGATED y 4 NOT_APPLICABLE. Quedan **539 hallazgos únicos OPEN**:
57 P1, 472 P2 y 10 P3. Solo se cierran C0499/C0500, sin duplicados adicionales.
C0431 y C0135/C0136 siguen OPEN; C0460 sigue MITIGATED.
SW100-R3-0001 permanece FIXED fuera de los 598 IDs.

El [Lote 9 propuesto](PLAN_SWARM100_LOTE9_2026-10-29.md) aborda C0438 en el
monitor de estado. Solo se prepara; su fuente conserva el hash seleccionado.

El MCP de grafo está disponible: project babylon-60, raíz exacta contrastada,
cobertura metadata_match como señal best-effort. Identificó los cuatro callers;
los cambios y límites se comprobaron además por AST y ejecución aislada.
Mediante Context7 se consultó la
[documentación primaria de git commit](https://github.com/git/git/blob/master/Documentation/git-commit.adoc)
para pathspec/--only; las garantías declaradas se limitan a los casos ejecutados.
