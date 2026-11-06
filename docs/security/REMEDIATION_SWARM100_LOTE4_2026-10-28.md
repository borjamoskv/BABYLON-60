# Lote 4 ejecutado: integridad de bundles — 28/10/2026

Resultado: C0061, C0083, C0086 y C0087 pasan a FIXED. También C0060 y C0088,
colaterales reproducidos en las mismas tres fuentes. Se preservan los materiales
históricos firmados; el código del verificador v1 era una de las fuentes
autorizadas. El verificador histórico v2 permanece intacto y C0135/C0136 OPEN.

## Evidencia

Las [13 reproducciones previas](evidence/swarm100-lot4-20261028/before-tests.log)
fallaron contra los [hashes aprobados](evidence/swarm100-lot4-20261028/before-source-manifest.json).
Los generadores originales se ejecutaron únicamente copiados a roots temporales,
con Git inerte, plataforma sintética y claves de software de fixture. No se
importaron sus efectos sobre el repositorio real ni se consultaron claves reales.

La [validación final](evidence/swarm100-lot4-20261028/validation.json) contiene
comandos, logs y hashes antes/después: **496 pruebas aprobadas, 1 omitida**;
**88 regresiones nuevas**. La omitida requiere strike_rs compilado. Pasan Ruff,
MyPy con check-untyped-defs y análisis sintáctico de las tres fuentes. La
[revisión independiente](evidence/swarm100-lot4-20261028/independent-review.json)
confirma las 88 regresiones, 11 controles propios y los hashes finales.

| ID | Corrección ejecutable |
| --- | --- |
| C0061 | Contrato nuevo que liga todos los campos del manifest, componentes y selección de artefactos a la firma; bytes externos recalculados. Contratos antiguos insuficientes rechazados. |
| C0083 | Sin PASS/contadores inventados ni firma reutilizada. Importación sin efectos y salida nueva obligatoria. |
| C0086 | Sin clave privada automática ni firma de resultados constantes; siempre NOT_EXECUTED mientras no exista un contrato de evidencia ejecutada. |
| C0087 | Verificador portátil generado comprueba los archivos externos, no dos strings de digest almacenados. |
| C0060 | Fallos de formato/integridad/firma devuelven salida no cero; unsigned por defecto devuelve NOT_AUTHENTICATED y código 2. |
| C0088 | Plataforma observada o UNKNOWN; procedencia limitada a OBSERVED_PLATFORM_ONLY y hardware UNVERIFIED. |

La revisión encontró tres inconsistencias entre lo que el generador emitía y
lo que el verificador aceptaba: claims mayores de 4 MiB, plataforma vacía y
manifests mayores de 4 MiB. Se reprodujeron y corrigieron antes de congelar
las fuentes. Se conservan esas evidencias y un fallo intermedio de fixture
(stub incompleto de subprocess), corregido antes de la suite final completa.

## Contrato nuevo y compatibilidad

Los dos entrypoints comparten funciones importables del verificador canónico y
producen `babylon60.evidence.snapshot.v3`. Copian ese verificador en cada salida;
no necesita rutas de código del repositorio para verificar, pero requiere
Python, blake3 y cryptography disponibles. No modifica ni regenera bundles
históricos y rechaza cualquier directorio de salida ya existente.

El manifest declara SELECTED_FILES y OBSERVED_HEAD_ONLY: comprueba una lista
exacta de archivos regulares, no todo el repositorio ni su correspondencia con
el commit observado. Registra ruta, tipo, tamaño y BLAKE3. Claims se captura
una sola vez y debe coincidir con sus bytes en el artefacto. El verificador
exige un root externo, inventarios cerrados, JSON estricto y límites compatibles;
rechaza traversal, symlinks, FIFOs, ausencias, componentes extra y datos cambiados.

La firma es ECDSA P-256/SHA-256 sobre el dominio explícito v3 seguido del
manifest JSON canónico completo. La clave PEM indicada por el llamador en
`--trusted-public-key` es su ancla de confianza; no se deriva confianza de una
clave almacenada por el bundle. La consistencia de esa firma no acredita por
sí sola identidad del operador, Secure Enclave, ejecución de suites ni hardware.

Sin ancla, la comprobación normal devuelve código 2. El modo explícito
`--integrity-only` permite comprobar coherencia sin autenticar y lo etiqueta
UNAUTHENTICATED_INTEGRITY_ONLY. Si se aporta una firma, exige su ancla y la
valida incluso en ese modo. Ninguna firma promueve NOT_EXECUTED a PASS.

Las nuevas CLI exigen `--output <directorio-nuevo>` para generar y
`--artifact-root <root-de-los-archivos>` para verificar. La selección predeterminada
es la lista de 13 fuentes declaradas; `--artifact` permite otra selección
explícita que incluya CLAIMS.toml. La antigüedad máxima predeterminada es un día;
`--max-age-seconds` permite un plazo explícito entre un segundo y un año.
Las firmas históricas no se reinterpretan como firmas de este contrato nuevo.

## Alcance y pendientes

- No se generan ATTESTED ni se ejecutan hardware, despliegues, red o publicación.
  Los generadores no implementan un runner ni la ingestión de evidencia ejecutada:
  sus suites siempre son NOT_EXECUTED y su certificación NONE.
- Los controles usan descriptores y verificaciones de identidad. No se certifica
  un snapshot transaccional de un worktree vivo, atomicidad frente a SIGKILL o
  aislamiento frente a otro escritor con el mismo UID.
- Los [hashes históricos](evidence/swarm100-lot4-20261028/historical-components-before.json),
  el verificador v2, dependencias/lockfiles y la fuente del Lote 5 se comprobaron
  intactos. Configuración y telemetría global no inspeccionadas.
- C0135/C0136 siguen OPEN/P2 en la copia histórica v2. Se refrescó la referencia
  cruzada de C0135 al productor acortado, conservando su estado y evidencia.

El inventario de 598 IDs queda en 554 OPEN, 36 FIXED, 4 MITIGATED y
4 NOT_APPLICABLE. Entre los 582 pendientes iniciales: 549 OPEN, 26 FIXED,
3 MITIGATED y 4 NOT_APPLICABLE. Quedan **548 hallazgos únicos OPEN**:
66 P1, 472 P2 y 10 P3. El hallazgo adicional SW100-R3-0001 sigue FIXED,
fuera de esos 598 IDs.

El [Lote 5](PLAN_SWARM100_LOTE5_2026-10-28.md) agrupa C0428/C0429/C0430 en
ledger_actor.py. Está preparado con su hash y no aplicado.

Se consultaron mediante Context7 las fuentes primarias de
[verificación ECDSA](https://github.com/pyca/cryptography/blob/main/docs/hazmat/primitives/asymmetric/ec.rst)
y [serialización de claves](https://github.com/pyca/cryptography/blob/main/docs/hazmat/primitives/asymmetric/serialization.rst).
No había herramientas de grafo expuestas; el descubrimiento fue acotado.
