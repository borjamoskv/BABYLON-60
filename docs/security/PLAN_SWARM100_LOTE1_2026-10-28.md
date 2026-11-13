# Lote 1 propuesto: P1 abiertos con reproducción — 28/10/2026

> Alcance de la distribución pública: las referencias marcadas como material no distribuido identifican evidencia o herramientas excluidas deliberadamente de este checkout. Se conservan sus rutas y los resultados históricos; esos soportes no pueden verificarse desde esta distribución.

Estado: ejecutado tras autorización; [resultado y evidencia](REMEDIATION_SWARM100_LOTE1_2026-10-28.md).
La corrección independiente de AgentPager se documenta
[aquí](REMEDIATION_AGENT_PAGER_2026-10-28.md).

## Selección reproducible

Filtrar la cola vigente (material no distribuido: `evidence/swarm100-round3-20261028/remediation-queue.json`)
por `severity == P1`, `remediation_state == OPEN` y `decision == REPRODUCED`
seleccionó inicialmente **tres P1**, agrupados en tres módulos. Se conservan sus
IDs, hashes y arnés previo en
lot1-selection.json (material no distribuido: `evidence/swarm100-pager-20261028/lot1-selection.json`).
La reproducción previa es aislada; no acredita ejecución nativa ni despliegue.
Tras el cierre no quedan P1 OPEN con dictamen REPRODUCED. El siguiente bloque
estático está preparado en el [Lote 2](PLAN_SWARM100_LOTE2_2026-10-28.md).

| Orden | P1 | Módulo y copias afectadas | Resultado exigido |
| --- | --- | --- | --- |
| 1 | C0373 | `01_KISH_ENGINE/babylon60/transducers/c5_mail_transducer.py` | Un fallo de transporte no devuelve credenciales ni el comando que las contiene. |
| 2 | C0501 | `tools/skill_library/global/c5-socint-extraction-suite/scripts/socint_extract.py` y su copia en `c5-secops-infra-devtools/references/modules/` | El sello vincula nombres, tipos y valores; renombrar/intercambiar campos cambia la raíz. |
| 3 | C0420 | `tools/tamkarum_attestation_engine.py` | El verificador contrasta artefactos actuales y distingue integridad de procedencia autenticada. |

## 1. C0373 — credenciales en errores de correo

Reutilizar el fallo `CalledProcessError` con token sintético del
arnés existente (material no distribuido: `evidence/swarm100-round3-20261028/03-isolated-fixtures.py`).
Convertirlo en regresión antes de corregir. Sustituir la serialización de
excepciones/comandos por errores estructurados con datos permitidos y aplicar
redacción de la credencial en cualquier detalle devuelto.

Aceptación: stderr vacío, stderr que repite el token y excepción genérica no
filtran el token, cabecera Authorization ni argv; el código de error sigue
siendo útil. Conservar casos sin clave, respuesta HTTP de rechazo y respuesta
válida. Subproceso y credencial serán fixtures: no consultar Keychain ni enviar
correo real.

## 2. C0501 — sello Merkle sin vinculación a campos

La copia empaquetada es byte a byte idéntica. C0264 describe el mismo defecto
en esa segunda ruta, con severidad P2; se corregirán ambas superficies como una
familia y se reconciliará su relación al cierre.

Introducir un esquema de sello versionado que comprometa cada nombre de campo,
tipo y valor canónico, con separación de dominios para hojas y nodos. Mantener
orden determinista de campos y definir la cobertura del cuerpo sellado. Los
sellos heredados no deben presentarse como si ya usaran el esquema nuevo.

Aceptación: intercambio de autor/texto, renombrado de claves y cambio de tipo
alteran la raíz; reordenar un diccionario no la altera. Probar estructuras
anidadas y casos vacío/impar, además del productor que guarda `merkle_seal`.
Ejecutar el mismo conjunto contra las dos copias. Sin consultar redes sociales
ni ejecutar la extracción completa.

## 3. C0420 — verificación de atestación autocontenida

El checksum del mismo JSON no es una fuente de confianza. Propuesta de
contrato: el verificador recibe referencias explícitas a evidencias y una
clave autorizada externa al documento. Recalcula los digests actuales y
contrasta el commit/topología pertinentes. Solo acredita procedencia si
verifica la firma con esa clave; sin firma o ancla válida devuelve
`NO_VERIFICADO`/rechazo.

Conservar un modo explícito de comprobación de integridad si resulta necesario,
pero no devolver un éxito autenticado por ese solo motivo. No crear una clave
de producción ni atribuir atestación hardware a una firma software de fixture.
Una mitigación que únicamente bloquee el verificador permanecerá MITIGATED,
no FIXED.

Aceptación: archivo modificado, archivo ausente, HEAD distinto, JSON editado
con checksum rehecho, clave no autorizada y firma ausente/inválida se rechazan;
una fixture coherente y firmada por una clave de prueba autorizada verifica
con su alcance explícito. Resolver en el mismo módulo C0421 (P2): la CLI
devuelve salida no cero ante rechazo. Usar únicamente evidencias temporales y
claves sintéticas; no leer campañas privadas ni ejecutar `--emit` sobre ellas.

## Cierre por módulo

Primero conservar el fallo, después aplicar el parche y comprobar que la
regresión falla sin él y pasa con él. Ejecutar pytest dirigido con `uv run
--locked`, Ruff, tipos configurados y controles documentales proporcionales.
Cada cierre requiere hash vigente y evidencia del efecto; una limitación
pendiente conserva OPEN o MITIGATED. Revisar las copias distribuidas y los
consumidores del formato antes de cerrar su familia.

No mezclar en este lote los 77 P1 originales restantes ni el P1 adicional
SW100-R3-0001, que aún tienen confirmación estática. La siguiente prioridad
será reproducir los caminos de pérdida de datos, autorización e integridad
antes de sus parches. No se estima duración sin medir estos tres trabajos.
