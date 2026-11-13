---
title: "Arquitectura de cortex-persist: diseño y evidencia delimitada"
status: Diseno-con-inspeccion-estatica-parcial
version: 5.0.0
---

# BABYLON-60: arquitectura de cortex-persist

Revisión científica: 2026-10-26. El diagrama describe el diseño y las fuentes que se han inspeccionado; no acredita despliegue, rendimiento, aislamiento ni ejecución de cada enlace. Se retira el sello genérico «Verified». Los requisitos conservan carácter normativo y su cumplimiento debe comprobarse por componente, versión y modelo de amenaza. Véase el [modelo de seguridad](spec_security_model.md).

## 1. Pipeline del ledger Python observado

```text
LedgerEvent declarado por el llamante
    │
    ▼
Cola de una instancia BFTLedgerActor
    │
    ▼
Validación de campos / clave de idempotencia
    │
    ▼
BEGIN IMMEDIATE + INSERT / consulta de fila existente
    │                   │
    ▼                   ▼
SQLite WAL + FULL       V1 SHA3-256 / nuevas entradas V2 BLAKE3
    │
    ▼
Resultado de inserción: seq, event_id, entry_hash
```

En [ledger_actor.py](../../01_KISH_ENGINE/babylon60/bft/ledger_actor.py) se observan la cola, la transacción de inserción y los pragmas. El reloj lógico se asigna en la transacción. Los metadatos de taint y tiempo son datos declarados/derivados, no pruebas de verdad o autoría. El actor puede publicar una notificación IPC tras insertar; esa publicación no forma parte de la transacción SQLite y su fallo no se convierte aquí en atomicidad del sistema completo.

No se identifica en ese recorrido una llamada que haga commit Git por cada mutación. Git Sentinel se conserva como integración de diseño pendiente de comprobar en el camino de ejecución correspondiente.

## 2. Subsistemas y alcance de la descripción

### 2.1 Capa Python

Las fuentes inspeccionadas incluyen [BFTLedgerActor](../../01_KISH_ENGINE/babylon60/bft/ledger_actor.py), [CortexPersistLedger](../../01_KISH_ENGINE/babylon60/bft/cortex_persist_ledger.py) y [funciones de conexión SQLite](../../01_KISH_ENGINE/babylon60/database/core.py). La cola pertenece a una instancia; no serializa automáticamente todas las escrituras de cualquier proceso o implementación. SQLite y sus transacciones proporcionan otra capa de coordinación dentro de sus condiciones.

Las antiguas referencias `babylon60.api.client.CortexClient` y `babylon60.api.server` no se usan como API vigente: no se localizaron esos módulos/clase en las búsquedas acotadas de esta revisión. `database.core` contiene helpers de conexión, por lo que no se presenta como un pool certificado. Esto no afirma ausencia de otras interfaces en el repositorio.

### 2.2 Núcleo Rust

[El crate strike-rs](../../00_ABZU_KERNEL/crates/strike-rs/Cargo.toml) y sus enlaces opcionales son componentes distintos de la implementación Python L0. Un enlace PyO3 o compilar código Rust no demuestra que todas las funciones liberen el GIL, que no bloqueen ni que alcancen una latencia concreta. Esas propiedades requieren inspección por función y pruebas de la integración. No se presenta una medición nueva en esta página.

### 2.3 Interfaz e inferencia local: propuesta de integración

La descripción histórica de `babylon60-ide/`, Tauri, FastAPI, Vite y `inference/` se conserva como propuesta de responsabilidades, sin certificar que esas rutas y tecnologías formen un despliegue integrado en esta versión. La existencia de otros componentes de interfaz no demuestra esta composición exacta.

Un cliente configurado contra `127.0.0.1` o `localhost` se comunica con un endpoint local según su resolución/configuración. Eso no impide que el servicio local, una dependencia, un proxy o una ruta alternativa realicen conexiones externas. El requisito de confidencialidad exige revisar configuración efectiva, destinos, redirecciones, egress, credenciales y registros en una prueba identificada. La afirmación anterior de «cero fugas de datos» se retira por falta de esa evidencia. [RFC 1122, loopback](https://www.rfc-editor.org/rfc/rfc1122.html#section-3.2.1.3) define el alcance de las direcciones; no es un protocolo de prevención de exfiltración de aplicaciones.

## 3. Contrato de evento y correspondencia

Toda entrada DEBE satisfacer el esquema y las comprobaciones del ledger concreto, con clave de idempotencia inequívoca, enlace de hash, taint y reloj lógico válidos. No se presume un único formato intercambiable entre implementaciones.

En el actor inspeccionado, la entrada es `LedgerEvent(stream, entity_id, event_type, payload, cortex_taint, source_db, source_table, source_pk, created_at=None, agent_id="")`. El actor deriva `event_id`, `lamport_t`, `prev_hash` y `entry_hash`; no recibe el antiguo dict de esta página como su contrato completo.

- Para una clave ya presente se comprueba el contenido que implementa esa ruta y se devuelve la fila compatible; un conflicto no es una nueva inserción válida. UUID v5 por sí solo no demuestra equivalencia semántica de dos intents.
- El verificador comprueba enlaces, secuencia y hashes de una instantánea. Para rollback de una historia coherentemente reescrita necesita una referencia confiable separada.
- Los campos de identidad no sustituyen autenticación, autorización ni atestación del efecto.

El [perfil criptográfico](spec_cryptographic_profile.md) distingue BLAKE3 canónico y SHA3-256 heredado. Las entradas V1 del actor conservan el sobre anterior con `created_at` para verificar los ledgers existentes. Las nuevas entradas V2 comprometen campos semánticos y tick lógico con BLAKE3, sin fecha física ni aleatoriedad del cifrado. Una migración aditiva conserva las filas, hashes y raíces históricas. La verificación de una entrada V2 cifrada requiere su clave; una escritura cifrada con una clave incompatible se rechaza. Véase el [contrato de versiones y claves](../03_guides/guide_ledger_hash_versions.md). Esto no acredita un único formato canónico para todos los ledgers del repositorio.

## 4. Niveles del diseño y consenso

| Nivel histórico | Función propuesta | Estatus científico en esta página |
| --- | --- | --- |
| L1 — cachés/telemetría | Estado local | No acredita por su etiqueta propiedades CRDT/AP. |
| L2 — ledger local | SQLite WAL y escritura transaccional | Se observa código de cola/transacciones; no es consenso BFT de red. |
| L3 — testigo Git | Historial local de contenido | Una fecha Git declarada no es un anclaje temporal independiente; integración automática no verificada aquí. |
| L4 — quórum BFT | Coordinación distribuida | Propuesta/prototipos a evaluar por protocolo; la desigualdad N ≥ 3f + 1 no prueba que exista el protocolo ni que cumpla sus supuestos. |
| L5 — anclaje externo | Recibo OTS/Bitcoin u otro servicio | Requiere verificar el recibo, sus compromisos y el servicio concreto; no se acredita disponibilidad operativa aquí. |

Los niveles son categorías de arquitectura. No se declara estabilidad de producción de L1–L3 por excluir L4/L5 del uso local. [CLAIMS.toml](../../CLAIMS.toml) registra afirmaciones por componente; sus comandos declarados no sustituyen la evidencia de ejecución.

## 5. Persistencia, Git y recuperación

El contrato mantiene SQLite WAL y `synchronous=FULL` para el ledger. En WAL, un commit se representa en el log; el checkpoint transfiere páginas a la base. La recuperación del motor y el replay de una cola de aplicación son mecanismos distintos: SQLite no reejecuta automáticamente intents que no llegaron a confirmarse. Deben identificarse transacción, cola duradera, política de reintento y observación independiente del efecto antes de afirmar continuidad o ejecución exactamente una vez. [SQLite WAL](https://www.sqlite.org/wal.html#how_wal_works).

El nivel de sincronización y los supuestos de almacenamiento condicionan durabilidad. La prueba con muerte de proceso, si se ejecuta y documenta, no equivale a una prueba física de pérdida de alimentación. [SQLite synchronous](https://www.sqlite.org/pragma.html#pragma_synchronous).

Una integración Git Sentinel DEBE demostrar qué archivos y mutaciones cubre, qué errores propaga y cómo vincula el commit con la transacción. El resultado «toda mutación dispara un commit» queda NO_VERIFICADO en esta revisión. El verificador del actor lanza una excepción ante ciertas inconsistencias; no se infiere de ello un subsistema universal de cuarentena o recuperación.

## 6. Separación de tenants

Se conserva el requisito de un archivo y control de acceso inequívocos por tenant. Archivos distintos no bastan para aislamiento frente a un proceso con permisos sobre ambos. El helper inspeccionado reduce rutas relativas a su basename bajo un directorio común; la integración DEBE evitar colisiones y comprobar rutas, permisos y autorización. No se certifica aquí que todas las consultas multi-tenant requieran mediación explícita.

## 7. Dependencias y comprobaciones

`aiosqlite`, SQLite, serialización y funciones de hash se identifican en las fuentes enlazadas. La lista histórica de dependencias no constituye un inventario de módulos activos: disponibilidad, importación, conexión y uso deben comprobarse por separado. No se modifican dependencias ni lockfiles en esta revisión documental.

Los [tests de resiliencia](../../tests/test_ledger_resilience.py) y [pragmas de durabilidad](../../tests/test_ledger_cross_equivalence.py) localizados muestran casos previstos de aceptación y fallo. No se ejecutan en este seguimiento; por ello no se comunican como resultados recientes ni como una campaña de aislamiento, rendimiento o pérdida de alimentación.

## 8. Tiempo lógico: requisito de diseño

El motor DEBE usar el reloj lógico del protocolo en los compromisos canónicos de consenso, conforme al [contrato técnico](../03_guides/agent_contracts.md#ring-0). Esta es una obligación técnica, no un «teorema Robinson-Moskv» ni una ley termodinámica.

Para distinguir referencias directas y dependencia transitiva, puede especificarse:

\[
P(a,b) := \operatorname{parentRef}(b,a) \land L(a) < L(b),
\qquad a \prec b := P^+(a,b).
\]

Aquí `parentRef` exige el campo y formato de referencia definidos por el protocolo; que el digest aparezca en cualquier lugar de un payload no basta para establecer parentesco. `P⁺` es el cierre transitivo. Esta es una definición propuesta para un DAG, no una prueba de causalidad física ni una afirmación de que todos los ledgers actuales implementen ese esquema.

Los relojes de Lamport preservan el orden de los eventos causalmente relacionados bajo sus reglas; la desigualdad de marcas no proporciona la implicación inversa. Su definición original incluye orden de proceso, mensajes y transitividad. [Lamport, 1978](https://lamport.azurewebsites.net/pubs/time-clocks.pdf). Los términos «cono de luz» o «frontera de Markov» son analogías en esta arquitectura mientras no se definan y comprueben sus correspondientes modelos físicos/probabilísticos.
