---
title: Evidencia técnica para evaluar requisitos del EU AI Act — BABYLON-60
status: Technical-Evidence
version: 5.0.0
author: Borja Moskv
jurisdiction: UE (Reglamento UE 2024/1689)
---

# Evidencia técnica para evaluar requisitos del EU AI Act

BABYLON-60 registra y exporta evidencia sobre los flujos integrados en el sistema.
Una firma, una raíz Merkle o una prueba Lean acredita una propiedad concreta bajo
sus hipótesis; ninguna de ellas establece por sí sola conformidad jurídica.
La clasificación del sistema, los papeles de proveedor y desplegador, la finalidad
y el procedimiento aplicable requieren una evaluación del expediente completo.

Este documento describe el comportamiento del
[exportador público](../../01_KISH_ENGINE/babylon60/compliance_exporter/eu_ai_act.py)
revisado el 30 de octubre de 2026. La revisión de fuentes no constituye una prueba
de despliegue, aislamiento, biometría ni ejecución del runtime.

## 1. Marco y calendario de referencia

El [Reglamento (UE) 2024/1689](https://eur-lex.europa.eu/eli/reg/2024/1689/oj)
establece obligaciones según el sistema y su uso. Tras la modificación del
calendario por el Ómnibus de IA, las obligaciones de alto riesgo del Anexo III
aplican desde el **2 de diciembre de 2027**; las de sistemas integrados en productos
del Anexo I, desde el **2 de agosto de 2028**. Las reglas de transparencia del
artículo 50 tienen su propio calendario. Véase la
[explicación y calendario de la Comisión Europea](https://digital-strategy.ec.europa.eu/en/policies/regulatory-framework-ai),
consultada el 30 de octubre de 2026.

Una comparación de arquitecturas o lenguajes de programación no determina la
admisibilidad legal de un sistema. Un componente de registro tampoco reemplaza
las obligaciones de gestión de riesgos, gobernanza de datos o supervisión humana.

## 2. Estados que emite el exportador

`verify_evidence()` comprueba la integridad del ledger y compara su raíz Merkle con
el `global_hash` del manifiesto. `generate_certificate()` usa ese resultado para
componer el informe. Los estados describen la evidencia disponible, no una
declaración de conformidad emitida por una autoridad supervisora.

| Artículo | Estado con evidencia verificada | Evaluación pendiente |
| --- | --- | --- |
| 9 — Gestión de riesgos | `EVIDENCE_SECURED_PENDING_AUDIT` | Riesgos identificados, medidas, responsables y seguimiento. |
| 10 — Gobernanza de datos | `EVIDENCE_SECURED_PENDING_AUDIT` | Procedencia, calidad, representatividad y controles del conjunto de datos. |
| 11 — Documentación técnica | `EVIDENCE_SECURED_PENDING_AUDIT` | Expediente técnico completo, actualizado y ligado a la versión del sistema. |
| 12 — Registro de eventos | `CRYPTO_EVIDENCE_SECURED`, salvo cuarentena | Cobertura del registro, contenido pertinente, retención y acceso. |
| 13 — Información al desplegador | Sin estado específico en el exportador | Instrucciones, capacidades, límites e información exigible al desplegador. |
| 14 — Supervisión humana | `EVIDENCE_SECURED_PENDING_AUDIT` | Competencias, interfaz, intervención, interrupción y uso efectivo por personas. |
| 15 — Robustez y ciberseguridad | `EVIDENCE_SECURED_PENDING_AUDIT` | Pruebas y controles correspondientes al sistema y a sus amenazas. |
| 50 — Transparencia | `EVIDENCE_SECURED_PENDING_AUDIT` | Información y marcado exigibles al caso de uso. |

En cuarentena, el artículo 12 recibe `QUARANTINE_NON_COMPLIANT`. Si la integridad o
la comparación fallan, los artículos reciben el detalle de no verificación. El
CLI devuelve código 2 cuando la evidencia no se verifica; `--allow-unverified`
permite exportar sin ese bloqueo de salida y no mejora el estado de la evidencia.

## 3. Registro, autorización y supervisión son controles distintos

La plantilla de dashboard del
[quickstart](../03_guides/QUICKSTART_ENTERPRISE.md) consulta datos de un ledger
suministrado. No establece ingesta de eventos ni una barrera frente a rutas
alternativas del agente. El nombre histórico `READ_ONLY_SHADOW_TAP` tampoco
implementa esas propiedades por aparecer en un manifiesto.
La mediación preventiva requiere integrar los efectos con el ejecutor autorizado
y comprobar el confinamiento del proceso en el dominio de recursos protegido.

Las compuertas de autorización o interrupción aportan controles técnicos en las
rutas donde se aplican. La evaluación de supervisión humana también exige revisar
qué ve el operador, qué decide, cuándo interviene y cómo se verifica el resultado.
Los modelos oncológicos y los visualizadores musicales son referencias de diseño;
sus analogías no constituyen evidencia de gestión de riesgos ni supervisión legal.

## 4. Alcance criptográfico y formal

Una cadena de hashes facilita detectar alteraciones al compararla con una
referencia confiable. Un administrador con control del archivo conserva la
capacidad de borrarlo o sustituirlo; SQLite WAL no acredita almacenamiento WORM.
La retención y la referencia externa requieren controles independientes.

El informe incluye `evidence_verification` y firma Ed25519. La variable vigente
`BABYLON60_SIGNING_SEED` configura la clave de firma; la verificación de firma,
identidad, custodia y confianza en la clave se evalúan por separado. Un campo de
anclaje hardware en un informe no sustituye comprobar su origen y su firma.

Cada prueba Lean se interpreta conforme al modelo y sus hipótesis. Compilar un
teorema no demuestra la correspondencia universal de todo el compilador, la
ausencia de rutas alternativas del agente ni el cumplimiento de un artículo.
Los niveles y límites de evidencia se consultan en [CLAIMS.toml](../../CLAIMS.toml)
y en la [auditoría de seguridad](../security/kernel-audit-2026-10-15.md).

## 5. Preparación de un expediente

1. Identificar sistema, versión, finalidad, clasificación y responsables efectivos.
2. Definir los efectos protegidos y comprobar las rutas de autorización y rechazo.
3. Obtener el ledger y el manifiesto correspondientes a la misma ejecución.
4. Exportar con el [CLI documentado](../05_compliance_eu_ai_act.md), conservar el
   resultado de verificación y revisar la firma contra una clave confiable.
5. Adjuntar las evaluaciones externas al registro: riesgos, datos, documentación,
   supervisión, robustez e información al desplegador según corresponda.
6. Registrar controles fallidos y pendientes antes de decidir sobre el expediente.

La revisión establece alcance, entradas y plazos propios. Este documento no fija
un plazo garantizado de respuesta o exportación, ni cuantifica multas evitadas o
ahorro de auditoría por instalar BABYLON-60. Las condiciones de licencia se
consultan en [COMMERCIAL_LICENSE.md](../COMMERCIAL_LICENSE.md).
