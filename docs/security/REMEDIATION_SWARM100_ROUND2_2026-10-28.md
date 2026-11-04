# Corrección de los P1 de la segunda ronda — 28/10/2026

## Contrato de tarea

Resultado esperado: rechazar las entradas inseguras de V01–V06 y V08–V11,
conservar datos ante errores y mantener los controles válidos. V07 (P2) y los
582 candidatos sin estado final quedan fuera de esta corrección.

Rutas: módulos señalados en la [segunda ronda](AUDIT_SWARM100_ROUND2_2026-10-28.md),
el ledger utilizado por gobernanza, pruebas dirigidas y este registro. Preservar
los informes y reproducciones originales, así como los cambios ajenos.

Restricciones: transacciones SQLite con `synchronous=FULL`, ausencia de efectos
productivos, pruebas con claves sintéticas y directorios temporales, sin cambios
de dependencias, commits ni despliegues. Aplican los contratos de persistencia,
concurrencia, integridad y confinamiento de rutas de
[agent_contracts.md](../03_guides/agent_contracts.md).

Aceptación fijada antes de editar código:

| ID | Criterio | Estado inicial |
| --- | --- | --- |
| R01 | No inventar campañas ejecutadas ni promover evidencia ausente | pending |
| R02 | Conservar salidas existentes ante entradas o compilación fallidas | pending |
| R03 | Rechazar CRL ilegible, malformada o de esquema inválido | pending |
| R04 | Verificar contenido JSON, diferenciándolo de listas de hashes | pending |
| R05 | Serializar alta, revocación, cierre transitivo y recibos | pending |
| R06 | Recalcular el hash del contenido del cristal | pending |
| R08 | No declarar borrado criptográfico ni éxito sin destruir claves | pending |
| R09 | Conservar bases divergentes y archivos no identificados | pending |
| R10 | Copiar una instantánea SQLite que incluya WAL confirmado | pending |
| R11 | Rechazar IDs y rutas que escapen del perfil de extensión | pending |

La API de shredding heredada no tiene claves independientes por hecho. La
corrección rechaza esa operación; no promete borrado físico ni introduce una
migración criptográfica implícita. La consolidación crea copias y conserva los
orígenes: no puede demostrar que ningún escritor continúe utilizando una base.

## Resultado y aceptación

Nueve P1 corregidos dentro de los casos probados. V08 queda **mitigado por rechazo
explícito**, con la funcionalidad de destrucción criptográfica no disponible.
Los informes y datos originales de la auditoría permanecen intactos.

| ID | Estado final del criterio | Evidencia y comportamiento |
| --- | --- | --- |
| R01 | passed | Campañas vacías por defecto, claims sin observaciones en UNTESTED y ledger de demostración marcado sintético. |
| R02 | passed | Salidas existentes rechazadas incluso con entradas válidas; ningún borrado previo de directorios. |
| R03 | passed | CRL corrupta o inválida rechazada por API y CLI; certificado Ed25519 de fixture revocado sigue rechazado. |
| R04 | passed | Hash del contenido del evento recalculado; mutación rechazada también mediante certificado firmado. |
| R05 | passed | Intercalaciones en ambos órdenes y con bases compartidas/separadas; rollback conjunto probado para base compartida. |
| R06 | passed | Contenido, modalidad y obligaciones se recalculan; una raíz escrita en Markdown no se acepta como prueba. |
| R08 | passed | API síncrona/asíncrona devuelve CRYPTO_ERASURE_UNSUPPORTED, sin nuevos marcadores ni carga de claves del operador. |
| R09 | passed | Bases divergentes y desconocidas preservadas; no hay barrido destructivo de archivos SQLite. |
| R10 | passed | Backup SQLite con WAL confirmado, origen conservado y publicación que no sustituye destinos concurrentes. |
| R11 | passed | IDs Chromium estrictos; operaciones relativas a descriptores abiertos, sin seguir symlinks; preferencias con copia previa. |

Las [47 regresiones nuevas](../../tests/test_swarm100_round2_regressions.py)
incluyen cinco rondas de calentamiento y veinte rondas de seis derivaciones
concurrentes más una revocación, usando SQLite real y datos desechables. Se
comprueban ausencia de registros ACTIVE tras revocar, eliminación de blobs
consultables e integridad del ledger. Esto no mide rendimiento ni prueba
aislamiento del sistema operativo.

La prueba existente de cardinalidad M0 se actualizó para esperar tres claims
UNTESTED cuando sólo hay etiquetas del registro y no observaciones aportadas.

## Evidencia ejecutada

- [Batería final](evidence/swarm100-remediation-20261028/related-tests.log): **143 passed, 1 skipped** en diez archivos de pruebas. La omisión es una prueba existente que requiere la extensión Rust `strike_rs`, no construida en este entorno.
- [Ruff](evidence/swarm100-remediation-20261028/ruff.log): sin errores en los nueve módulos y las dos suites modificadas.
- [MyPy](evidence/swarm100-remediation-20261028/mypy.log): sin errores en nueve fuentes, con `--follow-imports=silent`; no certifica tipos de dependencias transitivas.
- [Diff](evidence/swarm100-remediation-20261028/diff-check.log): sin errores de whitespace.
- [Comandos, entorno y hashes](evidence/swarm100-remediation-20261028/validation.json): comandos exactos, versiones Python/SQLite, códigos de salida y SHA-256 de fuentes y logs.
- [Controles documentales](evidence/swarm100-remediation-20261028/document-checks.json): auditoría semántica, presupuesto, topología y enlaces del presente documento.

La [primera ejecución](evidence/swarm100-remediation-20261028/baseline-tests.log)
dio 34 fallos y dos controles aprobados. Dos fallos iniciales de V08 correspondían
al montaje de la fixture: se añadió el encrypter sintético al singleton antes de
editar la API, y la repetición de esos dos casos detectó el éxito incorrecto del
shredding. El [primer ensayo de compatibilidad](evidence/swarm100-remediation-20261028/related-tests-initial.log)
detectó 14 errores por ledgers separados y una expectativa M0 obsoleta; quedaron
resueltos en la batería final. Se conservan los logs fallidos para trazabilidad.

## Límites y cambios de contrato

- V08 no destruye claves ni hace irrecuperable el ciphertext; impide comunicar
  éxito o cumplimiento inexistentes. Los marcadores históricos siguen siendo
  consultables y no se convierten en evidencia de borrado.
- Con memoria y ledger en archivos distintos, el bloqueo de escritura de memoria
  cubre la validación y la mutación. No se promete commit atómico entre dos bases
  WAL frente a un fallo de proceso o alimentación; ese caso requeriría un
  protocolo adicional de recuperación. El rollback conjunto probado corresponde
  al almacenamiento compartido.
- Los eventos JSON con payload y digest se verifican contra SHA-256 del JSON
  canónico sin `entry_hash`/`hash`, conservando el formato histórico. Las listas
  de hashes y manifiestos de raíz declaran alcance de compromisos, sin acreditar
  contenido ausente. Los formatos ambiguos se rechazan.
- El formato heredado de cristal compromete las proposiciones, su modalidad y
  obligaciones, y los compromisos de falsación. No autentica tesis, autoría,
  justificación o Markdown ni acredita verdad lógica. V07 sigue pendiente.
- El paquete M0 verifica bytes aportados; no ejecuta ni autentica por sí mismo
  las campañas suministradas por el llamante. Una firma software de fixture no
  constituye atestación hardware.
- `compile_pack` requiere una ruta de salida nueva. La consolidación conserva
  todos los orígenes; no fusiona bases divergentes. La purga de navegador requiere
  Python 3.11 o superior con `rmtree` resistente a ataques por symlink y modifica
  únicamente la copia del script en este repositorio.
- Sin cambios de dependencias o lockfiles, despliegue, commit ni push. No se
  tocó configuración global. La telemetría de ghost listeners se omitió
  explícitamente. Los 582 candidatos y V07 no reciben un cierre por inferencia.

El MCP de grafo no estaba expuesto en esta sesión; se utilizaron búsquedas
acotadas. Se consultó Context7 para los contratos de
[backup SQLite](https://github.com/python/cpython/blob/main/Doc/library/sqlite3.rst)
y [borrado relativo a descriptores](https://github.com/python/cpython/blob/main/Doc/library/shutil.rst).
