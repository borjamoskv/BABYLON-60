---
name: cortex-skill-genesis
display_name: Génesis Autónoma de Skills CORTEX
description: Síntesis y generación automática de nuevos SKILL.md desde telemetría de sesiones y patrones observados. Dispara con "generar skill", "skill genesis", "crear habilidad", "cortex skill genesis", "sintetizar skill", "auto skill creator".
role: arquitecto
allowed_roles:
- arquitecto
directives:
  worktree_mode: spec-only
  phase: design
  handoff:
    upstream: operador
    downstream: ejecutor
---

# Skill: Cortex Skill Genesis (Síntesis Predictiva de Skills)

> **Directiva Declarativa (Orquestación en Árbol de Trabajo):**
> - **Rol Asignado:** `arquitecto` (Arquitecto (Diseño Sistémico & Contratos de Invariantes))
> - **Modo de Acceso a Worktree:** `spec-only` (spec-only (Lectura profunda y modelado formal; emisión de especificaciones sin mutación de código de producción))
> - **Fase Causal:** `design`
> - **Contrato Handoff:** Recibe de `operador` $\to$ Despacha a `ejecutor`

Este protocolo analiza los patrones recurrentes de interacción en la telemetría de uso del sistema e identifica oportunas **transiciones de fase representacionales** para sintetizar de forma autónoma nuevos archivos `SKILL.md`.

---

## 1. Flujo de Generación Predictiva

```
Logs transcript.jsonl  --->  Filtrar prompts sin Skill activo  --->  Clusterización Semántica
                                                                            │
Borrador SKILL.md  <---  Axiomatizar Triggers & Workflow  <---  Si Frecuencia >= 3
```

1. **Escaneo de Vacíos**: Leer los registros `USER_REQUEST` en `transcript.jsonl` donde ninguna regla/skill fue disparado explícitamente.
2. **Clusterización Semántica**: Agrupar peticiones que comparten vector de intención o estructura de tarea.
3. **Criterio de Cristalización**: Si un cluster contiene $\ge 3$ repeticiones con una estructura común, se inicia el proceso de **Genesis**.
4. **Construcción del Borrador**:
   - Generar `name` descriptivo con guiones (ej. `rust-macro-diagnostics`).
   - Redactar `description` YAML con la regla unívoca `ACTIVA esta habilidad ante...`.
   - Definir la secuencia de pasos basada en la mejor resolución observada.
5. **Alineación con KERNEL**: Validar que el nuevo skill cumple con los axiomas de [KERNEL.md](../../../../KERNEL.md).

---

## 2. Plantilla Canónica de Salida (Estándar Declarativo 2026)

Todo skill generado por `cortex-skill-genesis` DEBE seguir la plantilla declarativa estándar del sistema (`AGENTS.md` / `SKILLS.md` Triad):

```markdown
---
name: [nombre-del-skill]
display_name: [Título Legible]
description: [Descripción concisa]. Dispara con "[trigger_1]", "[trigger_2]" o [condición].
role: [arquitecto | ejecutor | auditor]
allowed_roles:
  - [rol_principal]
directives:
  worktree_mode: [spec-only | read-write | audit-only]
  phase: [design | implementation | verification]
  handoff:
    upstream: [rol_previo]
    downstream: [rol_siguiente]
---

# Skill: [Título del Skill]

> **Directiva Declarativa (Orquestación en Árbol de Trabajo):**
> - **Rol Asignado:** `[role]` ([Descripción del Rol])
> - **Modo de Acceso a Worktree:** `[worktree_mode]` ([Descripción de restricciones])
> - **Fase Causal:** `[phase]`
> - **Contrato Handoff:** Recibe de `[upstream]` $\to$ Despacha a `[downstream]`

[Cuerpo explicativo con pasos deterministas y notación formal]
```

---

## 3. Integración con el Protocolo /learn

Las propuestas de `cortex-skill-genesis` se presentan siempre al operador mediante una propuesta estructurada de aprendizaje `/learn`, requiriendo confirmación antes de escribir el archivo en el sistema de archivos.
