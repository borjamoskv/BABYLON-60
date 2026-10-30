---
title: Evidencia técnica para evaluar requisitos del EU AI Act
status: Technical-evidence
version: 5.0.0
author: borjamoskv
---

# Evidencia técnica para evaluar requisitos del EU AI Act

[![EU AI Act Evidence](https://img.shields.io/badge/EU_AI_Act-Evidencia_por_evaluar-blue?style=flat-square)](../01_KISH_ENGINE/babylon60/compliance_exporter/eu_ai_act.py)

BABYLON-60 exporta registros y resultados de verificación criptográfica para una
evaluación del sistema integrado. **El informe no certifica conformidad jurídica,
supervisión humana efectiva ni ausencia de fugas de datos.** El código conserva
el nombre `certificate` para este artefacto técnico; ese nombre no acredita una
certificación de una autoridad o un organismo de evaluación.

La finalidad, clasificación de riesgo, papel del operador y procedimiento aplicable
determinan las obligaciones. Consulte el [marco oficial de la Comisión Europea](https://digital-strategy.ec.europa.eu/en/policies/regulatory-framework-ai)
y el [Reglamento (UE) 2024/1689](https://eur-lex.europa.eu/eli/reg/2024/1689/oj).
El [whitepaper de alcance](04_research/eu_ai_act_compliance_whitepaper.md) distingue
controles técnicos y evaluación normativa.

## Calendario y alcance

Tras el Ómnibus Digital sobre IA, Reglamento (UE) 2026/1744, en vigor desde el
27 de julio de 2026, los requisitos de alto riesgo del Anexo III aplican desde el
**2 de diciembre de 2027**. Las reglas de transparencia del artículo 50 aplican
desde el 2 de agosto de 2026. Las fechas y excepciones se contrastan con el
[calendario de la Comisión](https://digital-strategy.ec.europa.eu/en/policies/regulatory-framework-ai#application-timeline),
consultado el 30 de octubre de 2026; no sustituyen revisar la aplicabilidad al sistema.

La plantilla de dashboard de lectura del [quickstart](03_guides/QUICKSTART_ENTERPRISE.md)
consulta datos de un ledger suministrado. No crea un canal de ingesta ni autoriza,
bloquea o supervisa por sí misma todas las acciones de otro proceso. Las rutas
protegidas por un ejecutor requieren su integración y controles específicos.

## Qué verifica el exportador

[`verify_evidence()`](../01_KISH_ENGINE/babylon60/compliance_exporter/eu_ai_act.py)
abre el ledger indicado, solicita su atestación de estado y compara la raíz Merkle
calculada con `manifest.json.global_hash`. La coincidencia y la integridad reportada
por ese ledger determinan `evidence_verification.verified`.

[`generate_certificate()`](../01_KISH_ENGINE/babylon60/compliance_exporter/eu_ai_act.py)
asigna los siguientes estados. Los nombres de artículos del informe son un índice
técnico; no contienen una evaluación completa de cada requisito legal.

| Artículo | Estado si el ledger verifica | Trabajo que sigue pendiente |
| --- | --- | --- |
| 9: gestión de riesgos | `EVIDENCE_SECURED_PENDING_AUDIT` | Proceso de riesgos, criterios, mitigaciones y seguimiento del sistema completo. |
| 10: gobernanza de datos | `EVIDENCE_SECURED_PENDING_AUDIT` | Calidad, procedencia, representatividad y controles sobre los datos pertinentes. |
| 11: documentación técnica | `EVIDENCE_SECURED_PENDING_AUDIT` | Contenido, suficiencia y mantenimiento del expediente técnico. |
| 12: registro de eventos | `CRYPTO_EVIDENCE_SECURED`, o `QUARANTINE_NON_COMPLIANT` si el manifiesto indica cuarentena | Cobertura de eventos, retención, acceso y requisitos aplicables al registro. |
| 14: supervisión humana | `EVIDENCE_SECURED_PENDING_AUDIT` | Diseño, formación, capacidad de intervención y prueba de la supervisión efectiva. |
| 15: robustez y ciberseguridad | `EVIDENCE_SECURED_PENDING_AUDIT` | Evaluación de precisión, robustez, amenazas y recuperación del sistema integrado. |
| 50: transparencia | `EVIDENCE_SECURED_PENDING_AUDIT` | Obligaciones de información o marcado que correspondan al caso de uso. |

Si la evidencia falta, la cadena falla o la raíz no coincide, los artículos reciben
el detalle de error de `evidence_verification`, como `LEDGER_NOT_FOUND`,
`LEDGER_CHAIN_BROKEN_NON_COMPLIANT` o el estado de discrepancia de raíz. Una firma
Ed25519 sobre el informe no convierte esos estados en evidencia verificada.

## Generar el informe con el CLI publicado

El paquete instala **`babylon60-compliance`**, declarado en
[`pyproject.toml`](../pyproject.toml). Antes de exportar:

1. Prepare el bundle con su `manifest.json` y el ledger correspondiente.
2. Establezca `BABYLON_HOME` en el directorio de datos que desea evaluar.
3. Provisione `BABYLON60_SIGNING_SEED` por un canal de secretos: 32 bytes Ed25519
   codificados como 64 caracteres hexadecimales. No publique la semilla en el informe,
   Git ni los logs.

```bash
uv run --locked babylon60-compliance --help
uv run --locked babylon60-compliance \
  --bundle artifact_bundle_v3 \
  --ledger "$BABYLON_HOME/dbs/agent_ledger.db" \
  --system-id PROD-AGENT-01 --operator "Operador del sistema" \
  --locale es --format json --output cert.json
```

Para Markdown o HTML, use `--format md --output cert.md` o
`--format html --output cert.html` con los mismos argumentos de entrada.

| Resultado | Código de salida y significado |
| --- | --- |
| Evidencia verificada | `0`: cadena y raíz verificadas por el exportador; los artículos pendientes siguen pendientes. |
| Evidencia no verificada | `2`: se escribe el informe con el fallo; no se debe tratar como resultado favorable. |
| Error de entrada, firma o escritura | La ejecución falla; revise el error y no use un archivo anterior como resultado nuevo. |

`--allow-unverified` permite devolver `0` aun cuando falle la verificación. No lo
utilice como criterio de aceptación en CI ni como prueba de conformidad.

Sin semilla, la firma se rechaza por defecto. `BABYLON60_ALLOW_EPHEMERAL_SIGNING=1`
habilita una clave efímera para una evaluación identificada como tal; no establece
por sí sola una identidad persistente de confianza.

## Interpretar y conservar la evidencia

- `global_merkle_root` identifica el estado comparado, no todos los eventos de
  cualquier agente externo al flujo integrado.
- `evidence_verification` conserva el resultado, la raíz del ledger y la referencia
  del manifiesto. Es una interfaz vigente del informe.
- `signature` contiene la firma Ed25519, la clave pública y la indicación
  `ephemeral`. Verifique la identidad de la clave por un canal independiente.
- La redacción de secretos usa los patrones implementados por el exportador;
  revise el contenido antes de distribuirlo. No es una garantía de cero fugas.
- La cadena de hashes detecta alteraciones frente a una referencia de confianza.
  SQLite y una firma no impiden que el propietario del archivo borre o sustituya
  toda la evidencia. Defina retención, copias, accesos y anclajes externos.

La evaluación debe registrar la revisión del código, configuración, entradas,
comandos y resultados. El informe firmado aporta evidencia para esa revisión;
no decide la conformidad del sistema ni la admisibilidad de la prueba.
