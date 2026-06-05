---
description: "Workflow for consolidator-omega"
workflow: consolidator-omega
expected_duration_min: 25
---
# WORKFLOW OMEGA: CONSOLIDATOR-Ω (100% PRODUCT CLOSURE)

**OPERATOR:** borjamoskv | **REALITY LEVEL:** `C5-REAL` | **AESTHETIC:** `Industrial Noir 2026`

Este protocolo define las directrices deterministas para consolidar un producto de software al 100% de manera autónoma, eliminando la intervención del Operador en tareas no decicionales.

---

## 1. ⚙️ MATRIZ DE EJECUCIÓN (C5-REAL)

El agente opera en base a cuatro capas de falsación empírica antes de declarar el estado de consolidación:

```yaml
Falsacion_Flow:
  Fase_01_AST:
    Action: "Ejecutar Python-Extractor-OMEGA o Parser nativo para mapear dependencias."
    Rule: "Cero referencias huérfanas en el árbol de importaciones."
  Fase_02_Build:
    Action: "Compilación nativa del binario/frontend."
    Command: "npm run build o cargo build --release"
  Fase_03_Visual_QA:
    Action: "Auditoría visual con browser-subagent en múltiples viewports."
    Tool: "chrome-devtools + Guardian (Visual UI Healing)"
    Aesthetic: "Industrial Noir 2026 (#0A0A0A base, #2B3BE5 highlights)"
  Fase_04_Deploy:
    Action: "Pings HTTP directos al endpoint de producción."
    Constraint: "Latencia LCP < 200ms y status HTTP 200."
```

---

## 2. 🤖 ENJAMBRES Y DELEGACIÓN ASÍNCRONA

La consolidación masiva requiere la distribución de procesos paralelos para evitar cuellos de botella cognitivos.

```yaml
Subagent_Swarm:
  Jules-Secretario:
    Role: "Asynchronous integration executor."
    Tasks: [GitHub Issue validation, Pull Request assembly, deployment verification]
  CORTEX-Guard:
    Role: "Cryptographic state validator."
    Tasks: [Ledger integrity checks, credentials verification, auth state audits]
  LEA-Ω:
    Role: "Loose End Annihilator."
    Tasks: [Dead code purging, stale config deletion, unused dependency removal]
```

---

## 3. 🛡️ SISTEMA DE INMUNIZACIÓN (ANTIFRAGILIDAD)

Para resistir entornos hostiles, el agente aplica de forma automática:

- **Hostile Defaults**: Toda entrada de datos externos se valida mediante tipado estricto en tiempo de ejecución (Zod/Pydantic). Las fallas son ruidosas; disparan `C5-DEATH-OMEGA` si comprometen el sustrato.
- **Resiliencia de Red**: Si una API externa cae, el sistema conmuta automáticamente a la matriz de contingencia `API-Provider-OMEGA`.
- **Higiene de Memoria**: Purga diaria del historial del chat y compresión semántica en `Episodic-Memory-OMEGA` para prevenir la degradación de tokens.

---

## 4. 🚀 SECUENCIA DE CLAUSURA (SHIP-Ω)

Un producto no está consolidado hasta que se ejecutan los 8 pasos de la comprobación `SHIP-Ω` sin excepciones:

```bash
# 1. Ejecutar test suite completo
pytest tests/ -v || npm run test

# 2. Ejecutar auditoría de seguridad
npm audit || cargo audit

# 3. Validar estado de Git
git status --porcelain

# 4. Compilar bundle de producción
npm run build

# 5. Desplegar payload
cortex deploy --target production

# 6. Ejecutar visual audit en el live link
cortex qa --url https://cortex-persist.com

# 7. Registrar transacción en el Ledger local
cortex ledger commit --hash $(git rev-parse HEAD)

# 8. Notificar pulso a la Aether Matrix
cortex live broadcast --status success
```

---
# STATUS: CONSOLIDATOR-Ω SPECIFICATION ACTIVE.