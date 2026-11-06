---
title: Evidencia, evaluación y autorización EU AI Act
status: Implementation-with-local-native-validation
version: 5.1.0
---

# Evidencia, evaluación y autorización EU AI Act

BABYLON-60 proporciona infraestructura para registrar evidencia, revisar requisitos y controlar aprobaciones y publicaciones. **No certifica automáticamente conformidad jurídica ni garantiza cumplimiento universal.** La evaluación depende de finalidad, clasificación, papeles efectivos y procedimiento aplicable. Véanse el [texto consolidado](https://eur-lex.europa.eu/eli/reg/2024/1689/2026-07-27/eng) y el [artículo 43](https://ai-act-service-desk.ec.europa.eu/en/ai-act/article-43).

## Alcance operativo

El [catálogo versionado](../01_KISH_ENGINE/babylon60/compliance_exporter/regulatory_catalogue.json) inventaría obligaciones por papel y fase, con fuente y fecha de revisión. Incluye clasificación, artículos 9–15, calidad, proveedores/desplegadores, conformidad, transparencia, GPAI y seguimiento. Es una base de evaluación; no decide por sí sola aplicabilidad ni suficiencia jurídica.

El bloqueo acordado se limita a aprobar expedientes y publicar bajo `eu_ai_act_high_risk` cuando falte evidencia obligatoria de los artículos **9–14**. Otros requisitos permanecen visibles y pendientes cuando corresponda. Superar esa barrera no afirma cumplimiento del Reglamento completo.

Desarrollo, diagnóstico y CI continúan disponibles. `PlatformAutonomous` y `test_mock_hardware` sirven a pruebas y flujos no regulados. Los binarios con esa feature rechazan aprobaciones productivas.

## Cuatro modos del CLI

El ejecutable instalado es `babylon60-compliance`; también puede utilizarse `uv run --locked python -m babylon60.compliance_exporter.eu_ai_act`.

| Modo | Resultado | Condición |
| --- | --- | --- |
| `report` | Informe diagnóstico, JSON/Markdown/HTML | Puede mostrar carencias; no autoriza publicación |
| `assess` | Evaluación del expediente | Código 2 si no reúne las condiciones de la barrera |
| `approve` | Recibo de aprobación del expediente | Revisión válida, hecho anclado y autorización hardware |
| `authorize-release` | Recibo para una publicación exacta | Mismas condiciones y vínculo a commit, archivo, destino y ejecución |

`--allow-unverified` solo se admite en `report`. Los modos protegidos emiten JSON y no escriben un resultado de aprobación tras un rechazo. El código cero de un informe significa que se generó; no significa conformidad.

`generate_certificate`, `certificate_id` y las exportaciones históricas conservan compatibilidad como informes técnicos. No se convierten en recibos de autorización. El artículo 13 aparece en los tres formatos y los cinco idiomas.

## Perfil y expediente

Un perfil contiene `schema: babylon60.euai.profile.v1`, `system_id`, `system_version`, `configuration_digest` SHA-256, `intended_purpose`, `context`, `responsible_entity`, `roles`, `classification` y `classification_reason`. Los papeles admitidos son `provider`, `deployer`, `importer`, `distributor`, `representative` y `gpai_provider`. La clasificación puede ser `high_risk`, `infrastructure` o `not_high_risk`; un valor desconocido no es una exención.

El expediente usa `schema: babylon60.euai.assessment.v1` y un objeto `requirements`, indexado por los identificadores del catálogo. Cada entrada registra `applicability`, `owner`, `decision` y `evidence`, una lista de objetos con `path` relativo al bundle y `sha256`. `decision: accepted` necesita revisión firmada para surtir efecto. La inaplicabilidad exige justificación y revisión; los requisitos nucleares 9–14 de un perfil de alto riesgo no pueden omitirse.

Los estados son `MISSING`, `INVALID`, `PENDING_REVIEW`, `ACCEPTED` y `NOT_APPLICABLE`. Los archivos se leen sin seguir enlaces simbólicos y con límite de 32 MiB por evidencia. Los metadatos firmados no admiten claves JSON duplicadas ni números de coma flotante; las métricas pueden conservarse en los archivos de evidencia.

```bash
uv run --locked python -m babylon60.compliance_exporter.eu_ai_act \
  --mode assess --profile profile.json --assessment assessment.json \
  --bundle evidence --trust-store operator-policy.json --output evaluation.json
```

Para preparar una revisión, introducir en `assessment.review.statement` el identificador `reviewer` y `expires_at` como segundos Unix. La evaluación devuelve `review_statement`: el revisor comprueba el expediente y firma exactamente su JSON canónico UTF-8 (claves ordenadas, sin espacios, sin escapes ASCII forzados) con Ed25519. Guardar en `assessment.review` ese `statement` y su `signature` Base64. El sistema no genera esa aceptación humana.

La política externa registra `reviewers.<id>.name`, `public_key_hex`, `system_ids` y `scopes: ["assessment"]`. Puede revocar revisores mediante `revoked: true`, revisiones mediante sus digests en `revoked_reviews` y autorizaciones mediante sus digests en `revoked_authorizations`. Nunca se toma una clave de confianza del expediente. Perfil, versiones, configuración, evidencias, decisiones y catálogo quedan vinculados; sus cambios invalidan la revisión.

## Anclaje y barrera nativa

Compilar sin habilitar mocks:

```bash
cargo build --release --locked --bin babylon60_regulatory_gate
```

El binario recibe JSON por stdin y exige `--policy operator-policy.json --ledger l0.sqlite`. Las operaciones auxiliares son explícitas:

- `{"mode":"init"}` crea el esquema o migra la restricción antigua de un hecho por tick, preservando los hechos y sus ticks. Realizar copia de seguridad antes de migrar una instalación existente.
- `{"mode":"anchor","source_record":<assessment.review>}` verifica la revisión y ancla su hash. No aprueba el expediente ni fabrica evidencia. Es idempotente para el mismo hecho.
- `approve` y `authorize-release` abren una base existente; no crean tablas ni anclan hechos faltantes.

`commit_ring0_transition` exige `anchored_tick < logical_tick`. Un hecho ausente, igual o futuro produce `UnanchoredCausalLineage`, código `0xDEAD_6060`, antes de firma e inserción. Se permiten lecturas y bloqueos SQLite; el rechazo no añade escrituras persistentes del flujo. Los fallos de lectura no se interpretan como génesis. Los contadores respetan el dominio INTEGER de SQLite.

Los controles causales se ejecutan en Rust/SQLite; la autorización productiva utiliza firma P-256 mediante Secure Enclave. La firma cubre el sobre que compromete la acción y sus parámetros. No se afirma ejecución de la política dentro del enclave ni se inventan mediciones PCR: `measurement_status` es `UNAVAILABLE`.

## Validación hardware y activación

El estado inicial de una instalación es **NO_VERIFICADO**. La instalación local fue [validada con hardware real el 2026-10-30](security/EU_AI_ACT_NATIVE_2026-10-30.md); ese resultado solo cubre los binarios y la configuración identificados. Para una comprobación independiente, provisionar una clave Secure Enclave y fijar `hardware_public_key_hex` como punto SEC1 no comprimido en una política externa.

`hardware_backend` fija `helper_path`, `helper_sha256`, `key_path` y `key_record_sha256`. Los archivos deben ser regulares, del operador y no escribibles por terceros; el registro de clave exige modo `0600`. El gate toma estas rutas de la política y comprueba sus hashes antes de firmar y después. Un helper o registro de clave diferente invalida la habilitación.

La operación nativa `{"mode":"validate-hardware","nonce":"<32 bytes hex aleatorios>"}` solicita una firma biométrica de un desafío con el hash del binario. No escribe una aprobación ni altera L0. El verificador independiente debe contrastar nonce, bytes del desafío, firma P-256/SHA-256, clave provisionada, procedencia de la clave y comportamiento del gate en el equipo real. El desafío informa un hash del binario; no es una medición hardware del código.

Solo después de esa comprobación se configura `native_validation` con `status: VERIFIED`, `binary_sha256`, `backend_digest` y `evidence_sha256` del informe conservado. La herramienta `scripts/guards/validate_regulatory_hardware.py --binary <binario> --policy <política> --evidence-dir <directorio-nuevo> --activate` realiza una solicitud nativa y verifica su firma mediante Python cryptography antes de activar la política. Conserva un marcador de intento exclusivo; no reintenta tras fallo o cancelación. No crea revisores, expedientes ni autorizaciones de publicación.

La decisión parte de una política provisionada por el operador. El desafío no autoacredita su propia clave. Cada autorización incorpora `native_validation_digest` bajo la firma del sobre, por lo que una validación nueva no puede atribuirse a un recibo anterior. Los cambios de binario o backend requieren nueva validación. Sin backend, clave o validación, los modos regulados rechazan. No hay fallback software ni reintento biométrico.

```bash
uv run --locked python -m babylon60.compliance_exporter.eu_ai_act \
  --mode authorize-release --profile profile.json --assessment assessment.json \
  --bundle evidence --trust-store operator-policy.json --ledger l0.sqlite \
  --native-gate target/release/babylon60_regulatory_gate \
  --commit "$RELEASE_COMMIT" --artifact-sha256 "$ARCHIVE_SHA256" \
  --destination ghcr.io/organizacion/repositorio --run-id "$RELEASE_RUN_ID" \
  --run-attempt "$RELEASE_RUN_ATTEMPT" --output authorization.json
```

El recibo dura como máximo una hora y nunca más que su revisión. Se rechazan otra acción, archivo, perfil, commit, destino, run o intento. Si se pierde la salida después de un commit L0, conservar el ledger para recuperación; no volver a etiquetar evidencia histórica como una autorización nueva.

## Publicación y entorno de confianza

El flujo GHCR construye un archivo OCI sin credenciales de publicación, muestra su SHA-256 y conserva el artefacto. Después pasa por el entorno `Production`, verifica la autorización y solo entonces habilita el trabajo con permisos de publicación. Revalida antes de login y antes de copiar el mismo archivo, sin reconstruirlo.

La política versionada predeterminada declara `infrastructure`. Para publicar bajo alto riesgo, el operador configura en el entorno protegido `EU_AI_ACT_POLICY_JSON`, incluyendo `release_profile: eu_ai_act_high_risk`, `release_profile_digest`, claves, validación y revocaciones. `EU_AI_ACT_AUTHORIZATION_BASE_URL` señala un endpoint HTTPS controlado por el operador; tras construir el archivo y antes de aprobar `Production`, se deposita el recibo en `<base>/<run_id>/<run_attempt>.json`. No se admiten redirecciones. El transporte no sustituye las firmas.

Los cambios de política durante la ejecución causan rechazo. Una repetición de Actions cambia el intento y requiere nuevo recibo. Configuración ausente en el perfil de alto riesgo mantiene el bloqueo. Esta implementación no configura servicios externos, revisores de `Production`, protecciones de rama ni claves reales: deben administrarse fuera del expediente. El control presupone integridad del binario, política, workflow y cuenta de publicación; no impide a un administrador autorizado sustituirlos o publicar por otra vía.

## Comprobaciones reproducibles

```bash
cargo build --locked --bin babylon60_regulatory_gate
cargo test --locked --lib ring0 --features cortex-persist,test_mock_hardware -q
uv run --locked pytest tests/test_regulatory_assessment.py tests/test_audit_release_gates.py tests/test_compliance_exporter.py tests/test_compliance_html_injection.py tests/test_release_evidence.py -q
```

Las pruebas con claves sintéticas verifican lógica y criptografía; no demuestran hardware real ni conformidad jurídica. La verificación hardware y un despliegue GHCR real se reportan por separado.

Resultados observados, comandos completos y pendientes: [evidencia de implementación de 2026-10-30](security/EU_AI_ACT_GATE_2026-10-30.md).
