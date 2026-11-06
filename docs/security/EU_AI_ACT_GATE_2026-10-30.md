# Evidencia de implementación del control EU AI Act

Fecha: 2026-10-30. Alcance: cambios locales revisables sobre un árbol previamente modificado, sin publicación ni declaración de conformidad. La [guía de operación](../05_compliance_eu_ai_act.md) describe las interfaces y la activación.

Actualización posterior: la [validación nativa local](EU_AI_ACT_NATIVE_2026-10-30.md) cerró el pendiente hardware y confirmó Clippy sin exclusiones. Se conserva aquí el resultado observado antes de esa continuación.

## Resultado observado

Se incorpora un catálogo de 45 requisitos, con 13 requisitos bloqueantes de los artículos 9–14. La versión es `2026-10-30.1`; SHA-256 del archivo: `46d0076102c8bbfe17faf35646089a6d3815e734f049d0ac7bf5c0ba63b15692`. La clasificación y la suficiencia jurídica requieren revisión responsable; las obligaciones fuera de la barrera permanecen visibles.

La evaluación vincula perfil, configuración, versión, todos los metadatos del expediente, archivos de evidencia y catálogo. La revisión Ed25519 utiliza autoridades externas al expediente. La aprobación nativa exige un hecho previamente anclado y una autorización con presencia humana, y verifica la firma P-256 contra la clave provisionada. La publicación vuelve a verificar el recibo y el archivo OCI ya construido antes de usar credenciales y antes de copiarlo al registro.

El estado de Secure Enclave es **NO_VERIFICADO**: no se ejecutó una firma biométrica real ni se generó una aprobación productiva. La operación `validate-hardware` prepara un desafío para la comprobación independiente; su existencia no acredita el hardware. El perfil regulado permanece bloqueado hasta provisionar la política y completar esa comprobación. La política predeterminada identifica infraestructura sin declarar conformidad jurídica.

## Comprobaciones ejecutadas

| Comprobación | Resultado observado |
| --- | --- |
| `cargo build --locked --bin babylon60_regulatory_gate -q` | Correcto |
| Compilación separada con `--features test_mock_hardware` | Correcta; el binario rechaza aprobación y validación productivas |
| `cargo test --locked --lib ring0 --features cortex-persist,test_mock_hardware -q` | 25 pruebas correctas |
| Batería Python dirigida, con ambos binarios compilados | 134 pruebas correctas, sin omisiones |
| Ruff sobre los diez archivos Python modificados o añadidos | Correcto |
| `actionlint` sobre CI y publicación | Correcto |
| Construcción de wheel y comparación de su contenido | Correcta; incluye módulos y catálogo sin alteración |
| Enlaces Markdown locales de los cuatro documentos modificados y este informe | Sin destinos ausentes |
| Control semántico documental, presupuesto y topología del workspace | Correctos; configuración global y telemetría de listeners excluidas |
| `Cargo.toml` y `Cargo.lock` contra la copia anterior a la tarea | Idénticos |
| Clippy estricto del ejecutable | Falla por `clippy::question_mark` en `src/flash_defense.rs:554`, archivo ajeno al cambio |
| Clippy con exclusión temporal de ese único aviso en la orden | Correcto; no se añadió una exclusión al código |

Las pruebas de Ring-0 incluyen hecho ausente, igual o futuro; raíz incorrecta; errores y datos malformados al leer el tip; agotamiento del contador; contención SQLite; fallo de commit y rollback. Las comprobaciones previas comprueban cero llamadas al firmante y cero transiciones. Las pruebas con una base en disco y WAL comparan los archivos tras rechazos previos; esto permite lecturas y bloqueos y no afirma ausencia de acceso al disco.

La batería Python cubre cada requisito nuclear ausente, evidencia alterada, cambios del perfil y expediente, revisión no autorizada o caducada, inaplicabilidad sin justificación, revocación, claves y firmas incorrectas, recibos simulados y vinculados a otra publicación. Incluye los cinco idiomas, el artículo 13, el escape HTML, el anclaje explícito, la migración de hechos preservados y la continuidad de los informes diagnósticos ante un expediente incompleto.

Las firmas sintéticas de prueba ejercitan la verificación criptográfica y no se presentan como evidencia de Secure Enclave. El control causal se ejecuta en Rust/SQLite; la firma hardware autoriza el contenido exacto del sobre. No se atribuye al enclave la ejecución de la política ni se declaran mediciones PCR.

## Reproducción

Desde la raíz del repositorio, sin modificar dependencias ni lockfiles:

```bash
cargo build --locked --bin babylon60_regulatory_gate --features test_mock_hardware -q
cp target/debug/babylon60_regulatory_gate /tmp/babylon60-regulatory-gate-mock-euai
cargo build --locked --bin babylon60_regulatory_gate -q
cargo test --locked --lib ring0 --features cortex-persist,test_mock_hardware -q
BABYLON60_TEST_MOCK_GATE_BINARY=/tmp/babylon60-regulatory-gate-mock-euai \
  uv run --locked pytest \
  tests/test_regulatory_assessment.py tests/test_audit_release_gates.py \
  tests/test_m0_evidence_pack_acceptance.py tests/test_compliance_exporter.py \
  tests/test_compliance_html_injection.py tests/test_release_evidence.py \
  tests/test_compliance_and_attestation.py -q
uv run --locked ruff check \
  01_KISH_ENGINE/babylon60/compliance_exporter/{regulatory.py,regulatory_gate.py,regulatory_cli.py,eu_ai_act.py,i18n.py,m0_evidence_pack.py} \
  scripts/guards/{prepare_regulated_release.py,verify_regulated_release.py} \
  tests/{test_regulatory_assessment.py,test_audit_release_gates.py}
actionlint .github/workflows/production-deploy.yml .github/workflows/ci.yml
```

Los controles documentales de cierre son:

```bash
python3 scripts/c5_quality_gates/audit_semantic_contracts.py --workspace-only
python3 scripts/c5_quality_gates/audit_token_budget.py --workspace-only --skip-ghost-listeners
python3 scripts/guards/verify_active_topology.py
```

El alcance `--workspace-only` excluye configuración global. Se omite deliberadamente telemetría de listeners. No se ejecuta el control `--staged` porque esta tarea no prepara ni crea un commit.

## Pendiente fuera de la verificación local

- Validación independiente en macOS de la clave, desafío, contenido firmado, autenticación humana y procedencia del backend. Hasta entonces: `NO_VERIFICADO`.
- Configuración protegida de Production, revisores, clave pública, evidencia nativa y endpoint de recibos para una publicación regulada real.
- Ejecución de GitHub Actions y transporte OCI contra GHCR. La sintaxis y las condiciones del workflow están verificadas localmente; no se realizó un despliegue.
- Evaluación jurídica del sistema concreto y del procedimiento de conformidad aplicable. No se emitieron declaración UE, marcado CE ni comunicaciones a autoridades.

La política, el binario, los revisores y el workflow forman parte del entorno de confianza del operador. La implementación no ofrece una garantía jurídica universal del 100 % ni impide que un administrador sustituya esos componentes por otras vías.
