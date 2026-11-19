---
title: "Modelo de seguridad BABYLON-60: controles y límites"
status: Modelo-condicional-con-inspeccion-estatica
version: 5.0.0
---

# Modelo de seguridad — cortex-persist

Revisión científica: 2026-10-26. Esta página distingue requisitos de seguridad, mecanismos observados en fuentes y propiedades pendientes de evidencia. Se retira el sello genérico «Verified»: ni un nombre de régimen ni una declaración de [CLAIMS.toml](../../CLAIMS.toml) certifican una ejecución. No se ejecutaron aquí tests del ledger, campañas de fallo ni efectos de producción.

## 1. Propiedades y condiciones del ledger

| Propiedad | Mecanismo observado o previsto | Alcance y evidencia pendiente |
| --- | --- | --- |
| Integridad de registros | En el ledger Python inspeccionado, `_compute_entry_hash` usa el hash SHA3-256 del sobre serializado; `verify_chain` recalcula hashes y enlaces. | Detecta inconsistencias de la instantánea leída. Para detectar sustitución o rollback coherente de toda la cadena hace falta un checkpoint auténtico conservado aparte. No prueba inmutabilidad del soporte ni verdad del contenido. |
| Procedencia declarada | Se exige `cortex_taint` no vacío; `agent_id` tiene valor por defecto vacío en `LedgerEvent`. | Son metadatos aportados por el llamante. No autentican al autor ni su autorización. El sobre de hash de este actor no incluye `agent_id`; no se presume una identidad criptográficamente ligada por ese campo. |
| Orden lógico | El actor inserta `lamport_t = max + 1`; el verificador exige secuencia contigua y reloj creciente. | Describe el orden almacenado de ese ledger. No demuestra causalidad física, orden global de varios nodos ni reproducción determinista de efectos externos. |
| Idempotencia local | UUID v5 derivado de campos del evento, restricción `UNIQUE(event_id)` y transacción de inserción. | La protección se refiere a esa clave y a las comparaciones implementadas. No identifica por sí sola toda escritura semánticamente equivalente ni garantiza ejecución exactamente una vez de un efecto externo. |
| Registro temporal | Un commit Git puede conservar un objeto y fechas declaradas. | Las fechas del commit son configurables; sin testigo independiente no prueban una cota de existencia en tiempo real. La integración de cada mutación con Git requiere evidencia propia. |

Fuentes locales: [BFTLedgerActor](../../01_KISH_ENGINE/babylon60/bft/ledger_actor.py), [funciones de hash Python](../../01_KISH_ENGINE/babylon60/bft/cortex_crypto_kernel.py) y [conexiones SQLite](../../01_KISH_ENGINE/babylon60/database/core.py). La inspección estática identifica código y condiciones; no acredita que se ejecuten en todos los caminos de producción.

Un hash sin un valor de referencia confiable permite comprobar coherencia, no autenticar un hecho. Una firma verificada liga bytes a una clave pública bajo los supuestos del esquema; atribuirla a una persona y a un permiso exige una política de confianza adicional. Esto no certifica la semántica del mensaje. Véase [RFC 8032, verificación de Ed25519](https://www.rfc-editor.org/rfc/rfc8032.html#section-5.1.7).

El reloj de Lamport satisface la implicación de causalidad a orden lógico bajo su protocolo; la desigualdad entre dos marcas no implica por sí sola una relación causal. La propiedad original es condicional y no deriva de un hash o de una etiqueta «causal». [Lamport, 1978](https://lamport.azurewebsites.net/pubs/time-clocks.pdf).

## 2. Garantías que esta página no acredita

| Propiedad | Límite |
| --- | --- |
| Corrección semántica | Un registro coherente o firmado puede contener una afirmación falsa. |
| Autoría o autorización | Campos de identidad y taint son declaraciones hasta que una frontera autenticada los compruebe. El ledger no sustituye esa frontera. |
| Almacenamiento inmutable | Los triggers SQL observados bloquean ciertas operaciones SQL; no protegen el archivo contra un administrador capaz de sustituir la base, los triggers y los checkpoints locales. |
| Historial completo | Sin una referencia externa confiable, una cadena autoconsistente no demuestra ausencia de omisiones, truncamiento o reescritura coherente. |
| Consenso global | Una cola local y SQLite no constituyen un protocolo BFT distribuido. El estado de L4/L5 requiere evidencia del componente y versión concretos. |
| Durabilidad ante corte eléctrico | `synchronous=FULL` es un requisito del ledger; el comportamiento del sistema operativo y del almacenamiento sigue formando parte de los supuestos. Esta revisión no inyecta cortes físicos. |
| Cumplimiento regulatorio | Esta especificación no es una evaluación ni certificación de cumplimiento. |

## 3. Modelo de amenazas y controles requeridos

### 3.1 Amenazas tratadas por el diseño

| Amenaza | Control y condición de aceptación |
| --- | --- |
| Modificación accidental de una fila | Recalcular el hash sobre los bytes almacenados y comprobar sus enlaces en una instantánea consistente; comparar contra una referencia confiable cuando se evalúe rollback. |
| Inserción repetida | Clave de idempotencia definida, restricción de unicidad y comparación del contenido que la implementación liga a esa clave; probar conflictos y reintentos. |
| Escritores concurrentes | Cola por instancia de actor y `BEGIN IMMEDIATE` en la inserción inspeccionada. Otros procesos y conexiones siguen sujetos a las reglas de SQLite, errores `SQLITE_BUSY` y la política de reintento. |
| Muerte del proceso durante una transacción | Preservar SQLite WAL, `synchronous=FULL`, límites transaccionales y archivos auxiliares. Comprobar recuperación en el modelo de fallo que se pretenda declarar. |
| Escritura sin atribución confiable | Se conserva la obligación de atribución y autoridad en la frontera aplicable, además del taint obligatorio. El `agent_id` vacío permitido por el actor es una discrepancia que esta documentación no certifica como resuelta; un taint no vacío tampoco la resuelve. |
| Lectura entre tenants | Resolver rutas sin colisiones, aplicar permisos y autorización de acceso. Archivos separados son organización de datos; no demuestran aislamiento frente al mismo usuario del sistema operativo. |

En WAL puede haber un escritor activo a la vez y siguen siendo posibles respuestas de ocupado. La recuperación de SQLite conserva transacciones confirmadas conforme a su protocolo; no reejecuta por sí misma intents de aplicación sin confirmar. [SQLite WAL](https://www.sqlite.org/wal.html#concurrency). El contrato del proyecto mantiene `synchronous=FULL` para el ledger; la documentación de SQLite describe su sincronización y supuestos, no una certificación de este despliegue. [SQLite synchronous](https://www.sqlite.org/pragma.html#pragma_synchronous).

### 3.2 Supuestos y amenazas fuera de esta comprobación

Acceso privilegiado al host, compromiso de claves o primitivas, cadena de suministro, servicios externos y agentes distribuidos requieren modelos de amenaza y pruebas propios. Excluirlos del alcance limita la conclusión; no elimina el riesgo ni los convierte en controles implementados.

## 4. Perfiles criptográficos y estado observado

| Superficie | Estatus en esta revisión |
| --- | --- |
| Hash de filas Python L0 | Se observa SHA3-256 en `compute_envelope_hash`; no debe describirse como BLAKE3 universal. |
| BLAKE3 canónico y testigos SHA-256 | El [perfil criptográfico](spec_cryptographic_profile.md) y el manifiesto canónico fijan superficies y requisitos. Esta página no prueba su cobertura integral. |
| Firmas Ed25519 o atestación hardware P-256 | Propiedades distintas: firma de bytes, identidad de clave y presencia humana requieren verificaciones específicas. La mera disponibilidad de una librería no acredita su uso correcto. |
| Anclajes externos | OTS, Bitcoin u otro servicio deben identificarse mediante recibo y verificación del anclaje concreto; no se certifica aquí su disponibilidad ni una fecha de existencia. |

Las configuraciones históricas de dependencias opcionales no se usan como inventario de capacidades activas.

## 5. Verificación de integridad disponible

La API inspeccionada es el método asíncrono `BFTLedgerActor.verify_chain(*, expected_checkpoint=None)`: devuelve `True` si la instantánea satisface sus comprobaciones y lanza `BFTCausalInvariantError` ante las violaciones implementadas. No es una función libre `verify_chain(db_path=...)` ni devuelve un dict con un número de entradas prefijado.

En un contexto que ya dispone de un actor del ledger y de un checkpoint conservado por un canal confiable, la llamada es:

```python
await actor.verify_chain(expected_checkpoint=trusted_checkpoint)
```

Ese fragmento ilustra la API y presupone esas dos variables; no es un certificado ni un programa autónomo. La comparación del checkpoint debe usar el estado esperado para la instantánea que se pretende validar. Una discrepancia también puede deberse a nuevas entradas legítimas y exige una política de actualización de la referencia.

Se localizaron [tests de idempotencia y corrupción](../../tests/test_ledger_resilience.py), [verificación de filas cifradas](../../tests/test_ledger_vault_verify.py) y [comprobaciones de FULL](../../tests/test_ledger_cross_equivalence.py). Su existencia y lectura no equivalen a una ejecución reciente ni a cobertura universal.

## 6. Separación de datos y tiempo

Cada tenant DEBE disponer de autorización y selección de archivo inequívocas. Se mantiene la regla de no escribir `cortex.db` desde el SDK y de usar las bases sidecar previstas por el contrato aplicable; esta revisión no certifica la mediación de todas las rutas.

El helper `resolve_db_path` inspeccionado reduce una ruta relativa a su nombre bajo el directorio común de bases de datos. Por tanto, no basta afirmar que nombres de carpeta distintos proporcionan aislamiento: pueden compartir el mismo basename. La asignación de archivos y los permisos deben comprobarse en la integración concreta.

Git conserva fechas configurables mediante `GIT_AUTHOR_DATE` y `GIT_COMMITTER_DATE`; el commit local es una referencia de contenido e historia declarada, no una autoridad de tiempo independiente. [Documentación oficial de Git](https://git-scm.com/docs/git-commit-tree#_date_formats).
