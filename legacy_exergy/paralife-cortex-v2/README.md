# ⚖️ paralife-cortex-v2 — Deontological Governance & Knowledge Gate

> **ESTADO:** Congelado / Vault Histórico  
> **Transducción en Producción:** [`packages/babylon60/guards/`](file:///Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/packages/babylon60/guards) y [`scripts/c5_quality_gates/`](file:///Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/scripts/c5_quality_gates)

---

## 📐 Estructura de Ficheros

| Fichero | Descripción Técnica |
|---|---|
| [`extraction/kant_audit_gate.py`](file:///Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/legacy_exergy/paralife-cortex-v2/extraction/kant_audit_gate.py) | **Agente-Kant-Ω**: Gobernador deontológico que valida el imperativo categórico y la homeostasia estructural. |
| [`engine/core.py`](file:///Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/legacy_exergy/paralife-cortex-v2/engine/core.py) | Motor central de inferencia (`ParalifePlatform`), spawning y collapse de sandboxes cognitivos. |
| [`engine/ledger.py`](file:///Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/legacy_exergy/paralife-cortex-v2/engine/ledger.py) | Registro de eventos y transiciones de conocimiento en SQLite (`ParalifeLedger`). |

---

## 🗺️ Mapa de Rutas Legadas (Legacy Path Transduction)

Este módulo contiene rutas absolutas hardcoded pertenecientes al repositorio monolítico precursor (`/10_PROJECTS/paralife`). A continuación se detalla su equivalencia en la estructura actual de BABYLON-60:

| Ruta Hardcoded Legada | Componente Equivalente Activo en BABYLON-60 |
|---|---|
| `/10_PROJECTS/paralife/engine/paralife_ledger.db` | [`data/cib_master_ledger.db`](file:///Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/data/cib_master_ledger.db) |
| `/10_PROJECTS/paralife/extraction/kant_audit_trail.json` | [`data/logs/`](file:///Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/data/logs) & Audit Receipts |
| `/10_PROJECTS/paralife/extraction/harvested_intelligence.json` | [`data/L1_sink/`](file:///Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/data/L1_sink) |
| `~/.gemini/antigravity/skills/Agente-Kant-Omega/` | [`packages/babylon60/guards/contradiction_guard.py`](file:///Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/packages/babylon60/guards/contradiction_guard.py) |

---

## 🏛️ Puerta de Auditoría Deontológica (Agente-Kant-Ω)

Antes de permitir que cualquier hecho o conocimiento se cristalice de forma permanente en CORTEX, el filtro `KantAuditGate` verifica:
1. **Universalidad (Imperativo Categórico):** ¿Puede esta lógica actuar como regla universal sin contradicción sistémica?
2. **Preservación Homeostática:** ¿Mantiene el dato la estabilidad termodinámica del cuerpo de conocimiento?
3. **Auditoría e Inmutabilidad:** Registra el dictamen (`APPROVE` o `REJECT`) en el rastro auditado `kant_audit_trail.json`.
