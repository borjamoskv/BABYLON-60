---
name: anergy-purge-protocol
display_name: Motor de Purga de Anergía, Código Muerto y Entropía APFS
description: Purga de código muerto, artefactos efímeros, ghost listeners, saturación APFS y prompt bloat. Dispara con "purga de anergía", "purga de entropía", "dead code", "scandisk", "disco lleno", "limpiar conversaciones", "ghost listeners", "prompt bloat".
role: auditor
allowed_roles:
- auditor
directives:
  worktree_mode: audit-only
  phase: verification
  handoff:
    upstream: ejecutor
    downstream: operador
---

# Skill: Code & Artifact Redundancy Purge Protocol

> **Directiva Declarativa (Orquestación en Árbol de Trabajo):**
> - **Rol Asignado:** `auditor` (Auditor (Verificación Independiente, Linters de Silicio & Fail-Closed Gate))
> - **Modo de Acceso a Worktree:** `audit-only` (audit-only (Lectura forense de diffs, linters, tests de estrés y cálculo de exergía; cero mutación de código))
> - **Fase Causal:** `verification`
> - **Contrato Handoff:** Recibe de `ejecutor` $\to$ Despacha a `operador`

## Protocolo de Purga Acotada (Fail-Closed)
Este módulo opera en modo `audit-only`: inventaría y prepara una propuesta. No ejecuta borrados, cambios de estado de conversaciones, limpiezas de paquetes ni mutaciones remotas.

### Inventario previo obligatorio
1. Fijar el workspace y las rutas autorizadas para inspección. No ampliar el alcance a todos los proyectos o al directorio personal por defecto.
2. Generar un inventario de solo lectura con ruta exacta, tipo, bytes, dispositivo/inodo, estado Git (incluidos ignorados), referencias y procesos que lo usan. No interpretar `.gitignore`, una extensión o un tamaño como evidencia de que un archivo es prescindible.
3. Clasificar candidatos: cachés reconstruibles; binarios de PoC; temporales; recibos sujetos a retención; logs y bases; recursos audiovisuales; referencias documentales. Distinguir originales, copias verificadas y artefactos cuya procedencia falta.
4. Informar candidatos, exclusiones, incertidumbres y evidencia de reconstrucción o recuperación. La similitud Jaccard solo propone revisión; no demuestra duplicidad semántica ni permite eliminación.

### Bloqueos, SQLite y procesos vivos
- Antes de proponer retirar un archivo de bloqueo, consultar descriptores con `lsof` y comprobar el PID identificado mediante `kill -0`, cuando esas herramientas estén disponibles. Un error de permisos o ausencia de datos deja el estado NO_VERIFICADO; no prueba que el proceso esté muerto.
- Si existe un proceso vivo, detener la propuesta para esa ruta y reportar el PID. Un bloqueo no habilita borrado forzoso.
- No proponer borrar archivos WAL/SHM de SQLite de forma aislada por su nombre. Verificar propietarios, conexiones, recuperación y checkpoint mediante el procedimiento de la base afectada antes de cualquier intervención.
- Las bases de conversaciones y sus estados no se reescriben para aparentar inactividad.

### Autorización de una intervención
Presentar el inventario concreto y esperar autorización explícita para las rutas y operaciones indicadas. Si ya existe autorización humana vigente que cubre exactamente el inventario y la operación, documentarla sin pedirla de nuevo. Cambios de alcance requieren nueva autorización.

La ejecución autorizada corresponde a un procedimiento de implementación separado, con revalidación de identidad y uso de las rutas antes de actuar, respaldo o cuarentena recuperable cuando proceda y las compuertas de atestación aplicables. No trasladar globs globales del diagnóstico a un borrado. Abortarla ante cambios concurrentes, identidad incierta o procesos activos.

### Exclusiones y activación
- Ningún umbral de tamaño, archivo no rastreado, ejecución de PoC o coincidencia de trigger inicia una purga automática.
- Preservar trabajo ajeno, fuentes, activos privados, stems y masters. `~/Music/` y especialmente `~/Music/LIBRARY` quedan excluidos de cualquier purga.
- No eliminar lockfiles de dependencias ni modificar dependencias sobre un árbol sucio.
- No desactivar plugins, borrar ramas o despliegues, purgar CDN ni modificar credenciales como efecto lateral de una limpieza local.

### Salida
Entregar inventario, bytes observados, exclusiones y siguiente acción propuesta. Declarar NO_VERIFICADO lo no inspeccionado. Solo informar espacio recuperado o estado posterior con medición de una intervención autorizada; los bytes no son una medida de exergía física.
