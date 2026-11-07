# Lote 8 propuesto: commits de objetivos — 29/10/2026

Estado: ejecutado por instrucción del operador; véase el
[informe de cierre](REMEDIATION_SWARM100_LOTE8_2026-10-29.md).
La planificación inicial agrupaba dos P1 CONFIRMED_STATIC/OPEN en una
fuente productiva prevista: `scripts/c5_cortex/cortex_objectives_transducer.py`.
La [selección con hash](evidence/swarm100-lot7-20261029/lot8-selection.json)
conserva el dictamen vigente y fija la versión anterior al futuro parche.
No quedan P1 OPEN previamente reproducidos; se agrupan estos dos por compartir
`run_git_sentinel` y sus cuatro consumidores de mutación de objetivos.

| ID | Fallo que reproducir primero | Resultado exigido |
| --- | --- | --- |
| C0499 | Un hook rechaza el commit y el helper reintenta con --no-verify | Propagar el rechazo sin desactivar hooks ni crear un commit alternativo. |
| C0500 | git add . y el commit de todo el índice capturan trabajo ajeno | Limitar staging/commit a los dos resultados declarados y preservar archivos e índice ajenos. |

Reproducción exclusivamente en repositorios temporales con HOME/configuración
Git propia, hooks locales inocuos y autor sintético. Nunca ejecutar el helper
contra el checkout del operador, importar configuración global, publicar o
hacer push. Un hook temporal que devuelve error y otro que registra sus
invocaciones permiten observar commits, códigos y número de intentos reales.
Conservar evidencia red/green por ID y hashes de fuentes.

Diseño propuesto: retirar el reintento --no-verify; ante rechazo informar error
sin afirmar éxito. Usar una lista explícita de rutas relativa a WORKSPACE_DIR:
`cortex/ontology/babylon60_objectives.yaml` y `PROJECT.md`. Verificar que son
los resultados esperados antes de cualquier staging. No basta sustituir
`git add .`: un commit ordinario aún incluiría entradas previamente preparadas.
Como política inicial, rechazar un índice con entradas previas antes de
mutarlo, preservándolo byte a byte. Con índice inicialmente limpio, preparar
solo los resultados declarados; ante fallo restaurar únicamente la preparación
introducida por esta operación y conservar los cambios del árbol de trabajo.
No reset --hard, clean, stash global, hooksPath alternativo ni bypass equivalente.

Cubrir éxito en fixture limpio; rechazo de pre-commit/commit-msg; error de Git
que no sea hook; falta de cambios; archivo ajeno tracked y untracked; índice
ajeno preparado; preparación parcial de un resultado; rutas con espacios y
rechazo sin efecto sobre staging/HEAD ajenos. Validar consumidores con dobles o
repositorios temporales: un fallo no puede convertirse en éxito ni hash de un
commit inexistente. No cerrar otros defectos de persistencia/rollback por
inferencia a partir de este helper.

Aceptación antes de cerrar: regresiones, suite relacionada, Ruff/MyPy, revisión
independiente, registro reconciliado, controles documentales y plan del Lote 9.
Sin modificar dependencias/lockfiles ni otros archivos productivos. La ejecución posterior emplea commit --only sin staging manual, outputs
tracked y subconjunto por consumidor; el informe documenta compatibilidad y
límites de concurrencia/hooks. El Lote 9 se prepara sin aplicar.
