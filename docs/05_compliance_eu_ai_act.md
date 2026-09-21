---
title: Guía de Cumplimiento Normativo EU AI Act (Artículos 9, 10, 11, 12, 14)
status: Causal-Determinist
version: 4.0.0
author: borjamoskv
---

# ⚖️ Guía de Cumplimiento Normativo: EU AI Act en BABYLON-60

<div align="center">

[![EU AI Act Compliant](https://img.shields.io/badge/EU_AI_Act-Art._9--14_Verified-00F0FF?style=for-the-badge&logo=shield)](../01_KISH_ENGINE/babylon60/compliance_exporter/eu_ai_act.py)
[![Autoridad](https://img.shields.io/badge/Supervisión-AESIA_/_BSI_/_NIST-7B1FA2?style=for-the-badge)](./04_research/eu_ai_act_compliance_whitepaper.md)

</div>

## 📌 Resumen Ejecutivo

El **Reglamento Europeo de Inteligencia Artificial (EU AI Act - Reglamento UE 2024/1689)** impone requisitos legales estrictos para los sistemas de IA de alto riesgo. BABYLON-60 v4.0 proporciona una capa de infraestructura local (*Local-First*) y determinista que transforma automáticamente las trazas de ejecución de los agentes agénticos en **certificados de auditoría criptográfica** legalmente defendibles ante la Agencia Española de Supervisión de Inteligencia Artificial (AESIA), la BSI alemana y estándares NIST AI RMF.

> [!IMPORTANT]
> **Calendario actualizado (2026-09-10):** tras el **Ómnibus Digital sobre IA (Reglamento (UE)
> 2026/1744, en vigor desde el 27 de julio de 2026)**, las obligaciones para sistemas de alto
> riesgo del Anexo III (Arts. 9–15, incluido el Art. 12 de conservación de registros) aplican
> desde el **2 de diciembre de 2027** (antes: 2 de agosto de 2026). Las obligaciones de
> transparencia del Art. 50 ya aplican desde el 2 de agosto de 2026. Planifique la
> certificación de evidencia en consecuencia.

> [!NOTE]
> **Verificación de evidencia (2026-09-10):** el exportador ya no emite estados CONFORME sobre
> evidencia no verificada. Con `--ledger <ruta>`, re-ejecuta `verify_integrity()` y la
> comparación de la raíz Merkle contra el `global_hash` del manifiesto; ante cualquier fallo,
> los artículos se degradan a `UNVERIFIED_*` / `*_NON_COMPLIANT` y el CLI retorna código 2.
> Cada certificado se firma con Ed25519 (variable `BABYLON60_SIGNING_SEED`).

---

## 🏛️ Matriz de Mapeo Regulatorio (Artículos 9 - 14)

| Requisito Legal (EU AI Act) | Artículo | Mecanismo Técnico BABYLON-60 v4.0 | Garantía Matemática |
| :--- | :--- | :--- | :--- |
| **Sistema de Gestión de Riesgos** | **Artículo 9** | Transductor Oncogénico y Filtro Popperiano. Cuarentena WORM automática ante colapso entrópico o anomalías en el DAG de razonamiento. | Falsabilidad popperiana estricta ($\Omega22$) y aislamiento preventivo en $O(1)$. |
| **Gobernanza de Datos** | **Artículo 10** | Sanitización y redacción criptográfica no reversible en el transductor de entrada (`EUAIActComplianceExporter.redact_sensitive_data`). Cero-fugas de PII o API Keys. | Privacidad por diseño y redacción no reversible de credenciales. |
| **Documentación Técnica** | **Artículo 11** | Registro automático de esquemas algebraicos, AST auditados y manifiesto canónico `manifest.json` firmado. | Inmutabilidad de la especificación técnica mediante raíces de Merkle. |
| **Registro de Eventos (Logging & Record-Keeping)** | **Artículo 12** | Base de datos SQLite WAL append-only con encadenamiento de hashes SHA-3 y sincronización síncrona `synchronous=FULL`. | Hash-chain no repudiable donde cualquier alteración rompe la cadena. |
| **Supervisión Humana (Human Oversight)** | **Artículo 14** | Contratos Saga de validación explícita. El operador humano ejerce como nodo validador BFT sobre el transductor. | Invariante $V_A$: No hay ejecución autónoma sin atestación/firma del nodo validador. |

---

## 🛠️ Generación de Certificados de Auditoría (CLI)

Cualquier operador corporativo o auditor externo puede generar el certificado de cumplimiento normativo utilizando la herramienta CLI `cortex-compliance`:

### 1. Exportación en formato JSON (para integración en CI/CD y trazabilidad M2M)
```bash
cortex-compliance --bundle artifact_bundle_v3 --ledger "$BABYLON_HOME/dbs/agent_ledger.db" --system-id PROD-AGENT-01 --operator "Banco Corporativo" --format json --output cert.json
```

### 2. Exportación en formato Markdown (para informes internos y documentación)
```bash
cortex-compliance --bundle artifact_bundle_v3 --ledger "$BABYLON_HOME/dbs/agent_ledger.db" --system-id PROD-AGENT-01 --operator "Banco Corporativo" --format md --output cert.md
```

### 3. Exportación en formato HTML (con diseño Brutalist UI / Glassmorphism listo para auditoría presencial y PDF)
```bash
cortex-compliance --bundle artifact_bundle_v3 --ledger "$BABYLON_HOME/dbs/agent_ledger.db" --system-id PROD-AGENT-01 --operator "Banco Corporativo" --format html --output cert.html
```

---

## 🔒 Inviolabilidad Criptográfica de la Evidencia

Cada certificado emitido incluye:
- **Global Merkle Root:** La raíz del Árbol de Merkle que sella en una única impronta de 32 bytes la totalidad de los eventos ejecutados por los agentes.
- **Bloque `evidence_verification`:** transcripción de la re-verificación fail-closed del ledger (cadena íntegra, Merkle recomputado, coincidencia con el manifiesto, veredicto).
- **Firma Ed25519:** firma del payload canónico del certificado (clave estable vía `BABYLON60_SIGNING_SEED`; clave efímera marcada explícitamente en caso contrario).
- **Fingerprint Digital (Cert SHA-256):** Un hash combinatorio del ID del sistema, el nombre del operador, la raíz global de evidencia y la marca temporal ISO 8601 UTC.
- **Redacción Preventiva de Secretos:** Eliminación automática de claves privadas, JWTs, AWS credentials y contraseñas previo al estampado del certificado.
