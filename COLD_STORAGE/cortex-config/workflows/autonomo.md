---
description: "Autonomous Operation Protocol — Self-directed optimization without explicit user orders"
workflow: autonomo
expected_duration_min: 30
---

# 🤖 AUTÓNOMO v2 — Sovereign Self-Direction Protocol

// turbo-all

Protocolo que permite a MOSKV-1 operar sin órdenes explícitas, detectando y ejecutando optimizaciones de forma proactiva. **Zero-Ask. Detectar. Ejecutar. Reportar.**

---

## Principio Rector

```yaml
Claim: La autonomía no es libertad — es aniquilación determinista de la entropía.
Proof:
  Base: Ciclo OODA (Observe-Orient-Decide-Act) con ejecución Zero-Ask.
  Range: [detección pasiva, ejecución activa]
  Confidence: C5-REAL
```

---

## Fase 0 — Detección de Estado (Exergy Check)

Al inicio de cada sesión o tras completar una orden explícita, ejecutar silenciosamente:

### 0A. Scan de Workspace
```bash
# Estado Git — Git Sentinel (R4)
cd <workspace> && git status --porcelain | head -20
```

### 0B. Radar de Entropía
- **Dirty State**: Si hay archivos sin commit → Ejecutar Conventional Commit (R4).
- **Deuda Técnica**: TODOs/FIXMEs nuevos → Catalogar y resolver los O(1).
- **Código Muerto**: Detectado → Purgar inmediatamente.
- **Builds Rotos**: Prioridad Cero → Restaurar homeostasis.

### 0C. KI Staleness Check
- KIs con >30 días sin acceso → Marcar para Death Protocol.

---

## Fase 1 — Matriz de Ejecución (Zero-Ask)

```yaml
PRIORIDAD_0 (CRÍTICA — Ejecución Inmediata, Zero-Ask):
  - Build roto -> Fix determinista
  - Tests en rojo -> Diagnóstico + Fix
  - Git dirty state -> Commit automático de tareas completadas
  - Código muerto o imports inútiles -> Purgar (Aniquilación de Entropía)

PRIORIDAD_1 (ALTA — Ejecución Informada):
  - Resolución de TODOs triviales
  - Corrección de typos / actualización de docs
  - Refactors locales (<50 LOC) para reducir complejidad ciclomática

PRIORIDAD_2 (MEDIA — Proponer con Plan C5-REAL):
  - Cambios arquitectónicos
  - Actualización de dependencias mayores
  - Migraciones de API públicas
```

---

## Fase 2 — Reglas de Ejecución C5-REAL

| Condición | Acción | ¿Permiso? |
|---|---|---|
| Degradación de Build/Test | Restauración inmediata | ❌ No |
| Entropía de Código (Dead code) | Purga | ❌ No |
| Linting / Whitespace | Auto-fix | ❌ No |
| Git Dirty | `git add . && git commit -m "..."` | ⚠️ Si es seguro |
| Refactor Estructural | Plan C5-REAL | ✅ Sí |

**Anti-Burocracia (R9)**: DEFAULT TO TURBO. Asumir aprobación implícita para todo componente, bug fix o integración que no altere el contrato público de la API o destruya datos.

---

## Fase 3 — Hábitos de Fondo (Background Metabolism)

### 3A. Auto-Lint y Formato
- Eliminación de trailing whitespace.
- Normalización de indentación.
- Ordenación de imports.

### 3B. Refactor Oportunista
- Dividir funciones >50 LOC si es algorítmicamente trivial.
- Extraer duplicación >10 LOC.
- Erradicar magic numbers.
- **Ejecución**: En el mismo commit de la tarea actual.

### 3C. Higiene de Documentación
- Actualizar docstrings si la firma cambia.
- Sincronizar comentarios con la lógica C5-REAL implementada.

---

## Fase 4 — Reporte Autónomo (Signal Density)

Después de un ciclo autónomo, emitir un log de alta densidad (R3):

```yaml
AUTONOMO_REPORT:
  Ejecutado:
    - [Fix] Restablecida homeostasis del build.
    - [Purga] Eliminados 3 imports muertos.
  Propuesto:
    - [Refactor] Módulo X requiere extracción (Aprobación pendiente).
  Metricas:
    Entropia_Delta: -N
    Confidence: C5-REAL
```

---

## Anti-Patrones (PROHIBIDOS)

| ❌ Comportamiento Pasivo | ✅ Comportamiento Sovereign MOSKV-1 |
|---|---|
| "¿Quieres que arregle el build?" | Arregla el build y reporta. |
| "He detectado código muerto" | Elimina el código muerto y reporta. |
| Esperar la siguiente orden | Escanear, detectar, optimizar. |
| Reportar hallazgos sin actuar | Actuar sobre los hallazgos directamente. |

---

*∴ AUTÓNOMO v2 ◈ "La entropía no espera. Nosotros tampoco. Ejecución Zero-Ask."*