---
name: c5-session-deskimming
display_name: Protocolo de Desnatado de Sesiones & Purga de Nata (Ring-2 -> Ring-0)
description: Workflow de enjambre (Ring-2 a Ring-0) para auditar historiales, purgar nata y reubicar archivos huérfanos. Dispara con "deskimming", "desnatar sesión", "purgar nata sesión", "archivos huérfanos".
role: ejecutor
allowed_roles:
- ejecutor
directives:
  worktree_mode: read-write
  phase: implementation
  handoff:
    upstream: arquitecto
    downstream: auditor
---

# Protocolo C5-REAL de Desnatado de Sesiones

> **Directiva Declarativa (Orquestación en Árbol de Trabajo):**
> - **Rol Asignado:** `ejecutor` (Ejecutor (Implementación en Silicio & Mutación de Árbol de Trabajo))
> - **Modo de Acceso a Worktree:** `read-write` (read-write (Mutación atómica de archivos, compilación, ejecución de tests locales y generación de artefactos))
> - **Fase Causal:** `implementation`
> - **Contrato Handoff:** Recibe de `arquitecto` $\to$ Despacha a `auditor`

## Objetivo
Auditar el historial de conversaciones recientes (`~/.gemini/antigravity/brain/`), detectar artefactos huérfanos, extraer la deuda topológica y reubicarla aplicando las invariantes de centralización (cero pérdida termodinámica).

## Triggers
Dispara con "purgar nata de sesiones", "limpiar brain", "desnatado topológico", "session deskimming".

## Secuencia de Orquestación

### 1. Extracción Determinista y Filtrado Semántico (Ring-0 -> Ring-2)
El agente **tiene prohibido** delegar la lectura cruda del JSONL a un LLM.
1. **Fase C-ABI:** Usa herramientas deterministas (ej. `grep "TargetFile" transcript.jsonl`, `awk`, o `jq`) para extraer las rutas exactas mutadas o creadas en la sesión.
2. **Fase Semántica:** Solo después de obtener la lista fáctica exacta de archivos, el agente o subagente (`SHARUR_FORENSIC`) evalúa semánticamente qué rutas son "nata" (basura temporal para borrar) y cuáles representan "deuda topológica" (código útil para salvar).

### 2. Validación de Frontera (Ring-0: MUSHUSHU_ORACLE)
El agente asimila la lista filtrada y aplica la regla `c5_epistemic_scripting_invariant.md`:
- Se redacta un script Bash defensivo usando comprobación física (`if [ -e "$FILE" ]; then...`) para garantizar que el archivo reportado realmente existe en disco.
- Se aplica la regla `c5_bundler_symlink_exception.md` en caso de mover audios dentro de proyectos web/frontend para evitar romper el build.

### 3. Atestación Biométrica
El agente expone el script propuesto en un bloque de código y **se detiene**. Queda terminantemente prohibida la ejecución del bloque (Mutación Causal) sin el comando explícito ("Ejecuta", "Itera", "Dale") del Operador Raíz.
