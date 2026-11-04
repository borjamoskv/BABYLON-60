# Auditoría de cambios locales y consolidación — 30/10/2026

## Resultado y límite de la consolidación

Se capturaron **143 rutas pendientes** (34 modificadas y 109 nuevas) sobre
`c47293e03f0b957794ec1ca917e1cf835027bd1b`, conservando bytes, hashes, modos y diff
fuera del repositorio antes de intervenir. El
[inventario](evidence/pending-local-audit-20261030/manifest.json) identifica cada ruta.

Durante la auditoría otra sesión incorporó las 143 rutas en la cadena que incluye
`77eb00ecdc`; la base actualizada de validación fue
`15eeb1788ceb3f62d51fdb1a6c702cfd4996ac3d`. Se conservan esos commits sin reescribirlos.
El hecho de estar incorporado no implica haber superado esta auditoría: quedan dos
contraejemplos abiertos y varias garantías sin comprobación suficiente.

La [comparación de consolidación externa](evidence/pending-local-audit-20261030/concurrent-consolidation.json)
confirma que las 143 rutas están versionadas. Solo los dos manifiestos de skills
difieren de la captura inicial; su regeneración actual coincide exactamente con el
árbol de recursos. La captura original permanece disponible fuera de Git.

## Commits atómicos de esta auditoría

| Commit | Cambio verificado |
| --- | --- |
| `5efff02a13` | Elimina cuatro residuos de lint del modelo doxástico y sus pruebas; comportamiento conservado. |
| `14c6931cae` | Asigna identificadores diferentes a las consultas independientes de la prueba del parser Z3. El control de replay permanece activo. |
| Commit de este informe | Versiona hallazgos, criterios, comandos y evidencia; no certifica los grupos con incidencias. |

No se modificaron controles productivos para hacer pasar las pruebas. En la
prueba del parser, reutilizar el ID 50 disparaba correctamente la reserva durable
anti-replay a partir de la segunda consulta; el caso ahora comprueba las cuatro
entradas con IDs distintos.

## Verificación realizada

| Unidad | Observación reproducida |
| --- | --- |
| Python integrado | [304 pruebas correctas, sin omisiones](evidence/pending-local-audit-20261030/live-python.json): firmas/Merkle, Markov, grafos, modelo doxástico, aprobación experimental, Work y alineación Lean. |
| Calidad Python | [Ruff y MyPy finales](evidence/pending-local-audit-20261030/final-quality.json) correctos para los grupos consolidados. El fallo inicial de lint doxástico motivó el primer commit. |
| Kernel semántico | 4 pruebas unitarias y 16 regresiones/resultados del solver correctos; las 16 se repiten en release. La alineación Lean real comprueba umbrales y códigos, sin demostrar equivalencia total Rust–Lean. |
| Adaptador y confianza Z3 | [15 pruebas de parser y 15 de confianza correctas](evidence/pending-local-audit-20261030/solver-serial.json), con binario de prueba fijado y ejecución serial. El worker ignorado por defecto se invoca explícitamente desde los tests de proceso. |
| Confinamiento de skills | [18 pruebas correctas](evidence/pending-local-audit-20261030/live-rust-results.json): catálogo real, rutas, sustituciones y protocolo stdio. |
| Lockfile Cargo | [19 cambios de versión de paquetes internos](evidence/pending-local-audit-20261030/lockfile-audit.json), sin cambios de dependencias externas; metadata y compilación con `--locked` correctas. |
| Manifiestos de skills | [Ambas copias coinciden con la derivación del árbol actual](evidence/pending-local-audit-20261030/live-skills-lock-audit.json). |
| Babylon Work | 39 pruebas HTTP/runtime/nativas correctas y [recorrido Playwright](evidence/pending-local-audit-20261030/ui-audit.json): crear, preparar extractos, editar, guardar y recargar. Base desechable; proveedores desactivados y ninguna autenticación hardware. |
| Artefacto de comparación | [SHA-256 y CRC del ZIP correctos](evidence/pending-local-audit-20261030/comparison-artifact-integrity.json); esto no evalúa calidad de modelos ni acredita una campaña externa. |

Los conteos se solapan y no se suman. Las pruebas de firmas del prototipo usan
credenciales software aisladas; no son nuevos ensayos Touch ID. Las pruebas
experimentales no incluyen participantes humanos reales.

El primer ensayo del adaptador rechazó el pin histórico de Z3; se fijó de forma
explícita el ejecutable de prueba instalado desde `uv.lock`, con
[versión y hash registrados](evidence/pending-local-audit-20261030/solver-test-anchor.json).
No se cambió ninguna ancla productiva/global. Tras resolver el ID duplicado,
una ejecución paralela sufrió timeouts. La ejecución serial pasa sin ampliar
plazos ni cambiar autenticación. La robustez bajo mayor contención queda pendiente.

## Hallazgos abiertos

### PA-01 — P2: digest no hexadecimal aceptado

`Finding` y `ReproductionRun` admiten `"z" * 64` y `is_verified` devuelve `True`
cuando ambas declaraciones coinciden. `_validate_digest` comprueba longitud y
valor vacío, pero no el alfabeto hexadecimal. Esto contradice el rechazo de
digests mal formados del contrato propuesto. Las 15 pruebas existentes pasan y
no detectan este caso. No se ha corregido ni marcado como contrato verificado.

### PA-02 — P1: exportación mal formada alcanza ATTESTED

Un `ProvenanceEnvelope` con `native_export_digest_b3="b3:not-a-digest"` supera
`verify_integrity` y alcanza `ATTESTED` para `NATIVE_MESSAGE_TRANSCRIPT`.
Se verifica el prefijo, sin validar un digest completo ni una exportación.
Las nueve pruebas existentes pasan; este contraejemplo limita su cobertura.
La observación se refiere al evaluador de procedencia, sin ejecutar efectos.

[Reproducción y hashes de las fuentes](evidence/pending-local-audit-20261030/negative-probe-result.json).
Para repetir los dos controles sin efectos:

```sh
uv run --locked --no-sync python -I docs/security/evidence/pending-local-audit-20261030/reproduce_negative_probes.py
```

El script devuelve **1** mientras persista cualquiera de los dos falsos positivos;
no interpretar ese fallo esperado como una certificación exitosa.

## Pendiente y conservación

No se certifican migración de identificadores Rust persistidos tras cambiar el
prefijo SHA3/SHA-256, garantías físicas/regulatorias de las nuevas especificaciones,
eficacia de ensayos humanos ni comparación real de modelos. Pasar los controles
estructurales de documentos no prueba esas propiedades.

Los [grupos auditados](evidence/pending-local-audit-20261030/audited-units.json) y el
[resumen](evidence/pending-local-audit-20261030/summary.json) separan pruebas correctas,
contraejemplos y ámbitos pendientes. Los logs originales se conservan, sin quitar
espacios ni modificar su contenido, en `raw-validation-logs.tar.gz`, con
[hashes por miembro](evidence/pending-local-audit-20261030/raw-log-hashes.json).
No se versionan bases de prueba, binarios, material privado de claves ni entornos.
No se ha hecho push ni se han reescrito commits ajenos. Los artefactos locales
nuevos de otras sesiones permanecen sin incorporar.
