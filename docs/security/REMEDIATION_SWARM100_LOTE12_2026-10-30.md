# Lote 12 ejecutado: 30 hallazgos — 30/10/2026

Estado de cierre: código, pruebas y revisiones por ID aprobados. La validación
global final del registro está pendiente de estabilizar las ediciones ajenas
concurrentes; no se ha omitido su comprobación estricta de hashes.

Resultado: **28 FIXED y 2 MITIGATED** sobre los 30 hallazgos únicos del
[plan autorizado](PLAN_SWARM100_LOTE12_2026-10-29.md). Se modificaron las
29 fuentes productivas previstas y sus pruebas. El
[Lote 13](PLAN_SWARM100_LOTE13_2026-10-30.md) queda preparado con otros
30 hallazgos (25 P1 y 5 P2, 23 fuentes principales) más la copia C0461
pendiente del mismo fallo: 24 fuentes previstas en total, **sin aplicarlo**.

## Contrato y alcance

Reproducir cada ID antes de su parche, aplicar correcciones en las rutas
seleccionadas, ejecutar regresiones y revisión independiente, reconciliar
el inventario conservando historia y preparar el siguiente lote. Aplican los
[contratos de persistencia, concurrencia, confianza y verificación](../03_guides/agent_contracts.md).
La [selección original](evidence/swarm100-lot12-plan-20261029/selection-30.json)
coincidía con los hashes de las 29 fuentes al iniciar. El
[contrato ejecutado](evidence/swarm100-lot12-20261030/execution-contract.json)
y el [control de alcance](evidence/swarm100-lot12-20261030/scope-check.json)
registran rutas, restricciones y hashes finales.

Solo HOME/directorios/repositorios/SQLite temporales, procesos hijos propios y
claves software sintéticas; sin datos del operador, proveedores, iCloud/mail
reales, hardware, despliegue ni commit/push del repositorio. El grafo MCP
`babylon-60` se usó para símbolos y consumidores; los vacíos/rangos anteriores
se contrastaron con lectura dirigida. Context7 se consultó donde el contrato
externo lo requería. No se ejecutó telemetría global.

## Resultado por grupo

| Grupo | IDs | Estado y comportamiento comprobado |
| --- | --- | --- |
| Snapshots | C0528, C0529 | FIXED: raíz lógica correcta; origen ausente/corrupto rechazado; apertura SQLite de solo lectura; DB y manifiesto exclusivos, sincronizados y coherentes bajo reloj fijo/concurrencia. |
| Identidad | C0337, C0345, C0533 | FIXED: no sustituir identidad existente, metadatos recargados bajo exclusión y errores de carga antes de quote/TSA o forja. |
| Confianza | C0271, C0276, C0432 | FIXED: ancla externa para el manifiesto completo, software identificado sin falso hardware y autoridad de licencia obligatoria. |
| Entrega | C0434, C0358, C0208, C0509, C0422 | FIXED: drenar/fallar de forma observable, propagar rechazo de admisión, predecesor vigente al commit, esperar cancelaciones bajo exclusión y error al agotar entrega. |
| Archivos/Git | C0435, C0298, C0437, C0448, C0490 | FIXED: cola privada exclusiva, preservar módulos activos, backup Git comprobado antes de reescribir, DNS del dominio exacto e instrucciones previas conservadas. |
| Entrada | C0103, C0221, C0486, C0113 | FIXED: argumentos literales sin shell, bytes completos o rechazo, política también sobre destino explícito y matriz PSD comprobada con límites numéricos. |
| Recursos | C0294 | MITIGATED: proceso hijo exige límites de memoria; Darwin los rechaza y la ejecución no se admite. El positivo Linux queda omitido en este host. |
| Verificación/reportes | C0175, C0328, C0343, C0354 | FIXED: 11 contenidos M0 cubiertos por digests firmados; observaciones, comprobaciones no ejecutadas y simulaciones quedan diferenciadas. |
| Formal/E2E | C0360, C0385 | FIXED: elimina el axioma contradictorio; catálogo Lean acotado y demo con HOME/DB desechables antes de importar. |
| Correspondencia formal | C0378 | MITIGATED: no se promueve a PROVED sin puente comprobado entre precondición e implementación; elegibilidad heredada retirada de la tabla, sin revocar binarios existentes. |

Los dictámenes, rangos actuales y límites por ID están en la
[revisión agregada](evidence/swarm100-lot12-20261030/independent-review.json).
Los [30 cambios de estado](evidence/swarm100-lot12-20261030/candidate-status-updates.json)
remiten a esa evidencia. FIXED no certifica propiedades ajenas al fallo concreto.

## Reproducción, pruebas y revisión

Se conservaron rojos por ID antes de editar, hashes originales y reproducciones
aisladas en los resultados de cada grupo. S1 recibió cambios concurrentes antes
de la reserva exclusiva confirmada por el operador; se guardaron las versiones
intermedias y el parche incremental, sin restaurar ni descartar las mejoras.
Los fallos de montaje o invocación de herramientas se identifican separados
de los defectos productivos; no se cuentan como prueba de un hallazgo.

**1387 pruebas aprobadas y 2 omitidas** en la
[suite acumulada](evidence/swarm100-lot12-20261030/related-tests.log), con hashes
de las 29 fuentes idénticos antes y después. Se omiten `strike_rs` no compilado
y el positivo de límites reales de memoria que requiere Linux. Hay un aviso de
deprecación heredado del módulo hygiene. Pasan Ruff, MyPy en las 27 fuentes
Python, sintaxis Bash, sintaxis ESM y cuatro fixtures Worker Node.
Los [comandos, códigos y hashes](evidence/swarm100-lot12-20261030/validation.json)
delimitan lo ejecutado; el análisis de tipos silencia dependencias transitivas.

Seis revisiones independientes ejecutaron regresiones y controles propios con
barreras, ráfagas tras calentamiento, SQLite real, firmas software, subprocesses
propios y Lean 4.35 instalado. Detectaron y verificaron correcciones de un
booleano hardware representado como string, cancelación silenciada, reapertura
de cola durante cierre/inicialización, enlace `.github` fuera del workspace y
creación simultánea del lock en Darwin. La primera integración conservada
reprodujo ese último fallo; la suite final completa ya pasa. La prueba Lean
exige primero un positivo real para que un fallo del wrapper/toolchain no
produzca un negativo falsamente aprobado.

Una modificación posterior de S1 protegió las notas opcionales de excepción
durante la limpieza; se conservó el diff y se reprodujo el caso añadido contra
la versión anterior. También se revisaron cambios de tipado y restauración de
fixtures en S3. Las revisiones correspondientes se renovaron y la suite
acumulada completa se repitió sobre los hashes actuales. Los resultados previos
permanecen separados como historia. Se observaron commits ajenos concurrentes;
este equipo no ejecutó commit/push.

## Registro, duplicados y trabajo ajeno

El inventario conserva los 598 IDs: **509 OPEN, 79 FIXED, 6 MITIGATED y
4 NOT_APPLICABLE**. Hay **503 hallazgos únicos OPEN: 25 P1, 468 P2 y 10 P3**.
Se refrescaron rangos/hashes de 23 colaterales conservando sus estados y de
registros en fuentes cambiadas por trabajo ajeno, distinguiendo cambios previos
y concurrentes. El [registro de esa revisión](evidence/swarm100-lot12-20261030/outside-scope-source-refresh.json)
no declara nuevas correcciones. C0295/C0386/C0436, C0209 y C0516/C0517 requieren
readjudicación de sus disparadores históricos; no se afirma que persistan.

**C0461 permanece OPEN**: es la copia secundaria del fallo C0103 y no está entre
las 29 fuentes autorizadas. Compartir hallazgo no acredita compartir parche.
El Lote 13 incorpora su reparación sin contarla como otro hallazgo único.
El reconciliador respeta ahora el estado explícito de una superficie duplicada
revisada e independiente, la muestra en resumen/cola y no la cuenta como otro
hallazgo único del Lote 13. No se modifica esa copia ni se oculta la ruta insegura.
La excepción de hash histórico solo permite una remediación posterior con
un override íntegro validado; el registro original permanece en la historia.

`uv.lock` y `pyproject.toml` se conservaron. Un cambio concurrente de una línea
en `Cargo.lock` se registró y preservó fuera del parche; este lote no modifica
dependencias ni ejecuta Cargo. Los cambios del núcleo Rust pertenecen a trabajo
ajeno. No se revirtió ni publicó ese trabajo.

## Límites que permanecen

- Locks, hard links y fsync se comprobaron en POSIX local y entre escritores
  cooperantes; no se certifica corte eléctrico, filesystem remoto o exclusión
  contra un proceso hostil del mismo usuario. Pueden quedar temporales huérfanos.
- Keyring/metadatos y conjuntos DB/manifiesto no son transacciones indivisibles
  entre almacenes. Un error tras publicación puede dejar datos visibles con
  durabilidad no confirmada; no hay rollback ciego.
- Enqueue confirma admisión; los trabajos fallidos retenidos en RAM no tienen
  recuperación durable garantizada. Error del Worker no acredita reentrega SMTP.
- M0 verifica contenido firmado según la clave aportada en su metadata; C0175
  no establece identidad mediante un ancla externa. Aeon sí exige su pin explícito.
- Hardware/TSA/proveedores no fueron certificados. Los reportes y el enjambre
  simulado siguen sin sustituir verificaciones reales. La API hardware y las
  capacidades formal/memoria bloqueadas no se presentan como implementadas.
- El callback heredado de `rewrite_commits.py`, checkpoints/membership, la copia
  C0461 y la retirada de binarios formalmente promocionados antes del parche
  quedan fuera del cierre. La selección del Lote 13 conserva dictámenes
  históricos y exige reconfirmarlos antes de editar.
