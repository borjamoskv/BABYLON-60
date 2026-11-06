# FL-019 — Integridad de transformaciones geométricas

## Alcance y contrato de aceptación

FL-019 comprueba un artefacto geométrico contra una transformación afín declarada
y una cadena de procedencia activa. Reutiliza
[`CompositeSafetyGate` de FL-018](../../src/larsa.rs) y el
[DAG de gobernanza de memoria](../../01_KISH_ENGINE/babylon60/memory/governance.py).
Es una API de biblioteca; no añade un despacho de efectos protegidos.

| Criterio | Comprobación reproducible |
| --- | --- |
| GEO-01: ambas implementaciones corroboran el resultado | Casos válidos de identidad, rotación, traslación, escala, cizalla y reflexión declarada |
| GEO-02: ninguna comprobación acepta una transformación alterada | Espejo no declarado, traslación incorrecta, permutación y corrupción de coordenadas |
| GEO-03: la procedencia necesaria es íntegra y vigente | Etapa omitida, cambio de aristas, contenido alterado y revocación de antecesores |
| GEO-04: no se acepta evidencia repetida o retirada | Replay tras reapertura y revocación de la política persistente |
| GEO-05: la falta de cobertura produce rechazo | Tetraedro degenerado, matriz singular, tipos/rangos/tamaño fuera del dominio y ausencia de biblioteca nativa |

Rutas de implementación: [`geometry_integrity.rs`](../../src/geometry_integrity.rs),
[`geometry_python.rs`](../../src/geometry_python.rs) y
[`geometry_workflow.py`](../../01_KISH_ENGINE/babylon60/memory/geometry_workflow.py).
El núcleo reutiliza dependencias existentes. El saneamiento de CI actualiza
P-256 y Tokio para resolver avisos de seguridad bloqueantes. Aplican los contratos de hashes causales,
persistencia existente, aritmética comprobada y delimitación de evidencia; no se
añaden garantías de aislamiento, rendimiento ni validación científica universal.

## Dominio exacto

La entrada contiene entre 4 y 256 puntos tridimensionales enteros y una matriz
afín de 3 × 4. Las primeras cuatro posiciones deben ser afínmente independientes.
Cada coordenada de entrada y coeficiente está entre −10.000 y 10.000; las
coordenadas de salida están entre −1.000.000.000 y 1.000.000.000. La parte lineal
de la matriz debe ser invertible. El orden y la cardinalidad de los puntos se
conservan. No se admiten booleanos, flotantes, NaN ni tolerancias aproximadas.

El núcleo usa aritmética `i128` comprobada. El esquema rechaza campos desconocidos,
campos duplicados y solicitudes JSON de más de 65.536 bytes. Un caso degenerado
es falta de cobertura, no una aprobación por ausencia de contraejemplos.

## Dos comprobaciones independientes

1. **Ecuaciones de coordenadas:** para cada punto verifica directamente
   `salida = A × entrada + b`.
2. **Determinantes:** reconstruye los coeficientes afines de las cuatro anclas
   mediante la regla de Cramer y los compara con la matriz declarada. Comprueba
   los demás puntos con coordenadas baricéntricas exactas y contrasta el volumen
   orientado con el determinante de la parte lineal.

El segundo comprobador no utiliza las coordenadas esperadas calculadas por el
primero. Se ejecutan ambos y sus resultados alimentan los dos controles críticos
de FL-018. Una reflexión declarada es válida; una reflexión adicional falla.
No se aceptan indicadores `passed` ni informes proporcionados por el solicitante.

La independencia es algorítmica. Ambas implementaciones comparten compilador,
proceso y representación de entrada. No constituyen aislamiento frente a una
biblioteca nativa maliciosa ni tolerancia a fallos del anfitrión.
El digest identifica el archivo configurado, no atesta por sí solo la imagen
cargada por el sistema operativo. Cambiar el binario exige un proceso nuevo;
usar rutas versionadas evita reutilizar una biblioteca ya cargada.

## Procedencia, política y vigencia

La API Python registra la ruta `INPUT → TRANSFORM_SPEC → TRANSFORM → OUTPUT`
en el DAG existente. El contenido firmado vincula los identificadores y
compromisos de padres y dependencias; al leer se comparan también las aristas
reales. Así se detecta una alteración de aristas que conservara intacto el texto.

Las etiquetas de procedimiento `matrix` y `decomposed` son alternativas admitidas.
Registrar una etapa conserva una declaración de procedencia; no demuestra por
sí mismo que un programa externo ejecutara ese procedimiento. La aceptación
depende de comprobar las coordenadas reales con ambos verificadores.

La política persistente vincula tenant, principal, versión del comprobador y
digest de la biblioteca nativa configurada. Su tick lógico alimenta la época de
FL-018. Todos los registros dependen de ella. La rotación de esta política se
realiza revocando su `policy_record_id`; reabrir la base no recrea una política
revocada. `advance_policy_epoch` de gobernanza, cuyo estado es local al proceso,
no sustituye esta revocación persistente.

La aceptación es una observación de vigencia. `get_acceptance` vuelve a comprobar
la cadena y el resultado nativo al consultar una aprobación. La revocación de
cualquier antecesor impide reutilizarla. Las aprobaciones se vinculan a la pareja
salida/nonce y el DAG rechaza su repetición incluso después de reabrir la base.
Los estados `EXECUTED` y `SEMANTICALLY_VERIFIED` no implican `REPRODUCED`.
FL-019 admite únicamente registros vigentes desde su commit lógico y sin fecha
de expiración explícita; la vigencia se retira por revocación o invalidación del
DAG. No acepta registros externos con intervalos futuros o vencidos.

## Uso y comprobación

Construir la biblioteca con `cargo build --locked --lib --features python`.
El constructor recibe una ruta explícita a esa biblioteca de confianza:

```python
from babylon60.memory.geometry_workflow import GeometryWorkflow

workflow = GeometryWorkflow(
    governance,
    tenant_id="laboratory",
    principal="checker-host",
    native_library=native_library_path,
)
source = workflow.register_input(points)
specification = workflow.register_transform(source, affine_matrix)
execution = workflow.register_execution(specification, method="matrix")
candidate = workflow.register_output(execution, output_points)
acceptance = workflow.accept(candidate, nonce=1)
current = workflow.get_acceptance(acceptance.record_id)
```

El principal debe estar registrado previamente en la gobernanza. La ausencia de
biblioteca o evidencia válida produce un error explícito, sin evaluador alternativo.
Un resultado geométrico incorrecto produce una decisión sin aceptación semántica.

```sh
cargo test --locked --test nemesis_fl019_geometry
cargo test --locked --test nemesis_wave6_forged_authority fl018
cargo build --locked --lib --features python
# Linux; en macOS el sufijo de la biblioteca es .dylib.
BABYLON60_TEST_GEOMETRY_LIBRARY="$PWD/target/debug/libbabylon60.so" \
  uv run --locked pytest tests/test_fl019_geometry_workflow.py -q
```

Las [pruebas Rust](../../tests/nemesis_fl019_geometry.rs) incluyen 500 casos
válidos y 500 corrupciones deterministas de coordenadas. Las
[pruebas Python](../../tests/test_fl019_geometry_workflow.py) ejercitan los
comprobadores nativos y el DAG persistente con bases desechables. CI construye la
biblioteca y ejecuta explícitamente la suite Python, que requiere dicha biblioteca.

Esta campaña no es el experimento comparativo A/B/C de 500 flujos propuesto en
el radar. Esa comparación, sus tasas y su latencia p99 siguen pendientes. La
aceptación se limita al dominio geométrico descrito; no certifica criomicroscopía
ni conclusiones clínicas.
