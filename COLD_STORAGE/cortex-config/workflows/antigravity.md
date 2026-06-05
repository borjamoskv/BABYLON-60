---
description: "Workflow for antigravity"
workflow: antigravity
expected_duration_min: 20
---

## 🏛️ 1. Estructura y Perfiles del IDE

A diferencia de las extensiones tradicionales, Antigravity 2 se ejecuta en su propio espacio de usuario de macOS:

*   **Ruta de Configuración:** `~/.antigravity-ide/`
*   **Gestor de Extensiones:** `~/.antigravity-ide/extensions/`
*   **Argumentos de Lanzamiento:** Configurados en `~/.antigravity-ide/argv.json` (ej. localización en `"locale": "es"` y desactivación de telemetría `"enable-crash-reporter": false`).
*   **Espacio Aislado (Sandbox):** El binario del IDE se ejecuta bajo el perfil `seatbelt` restringiendo la escritura a los directorios del proyecto y configuraciones autorizadas del agente.

---

## 🧠 2. Arquitectura de Doble Ventana Nativa (Natively Split)

El entorno del IDE se divide de forma estricta entre la ventana del Editor y la consola del Agente:

| Vista / Ventana | Atajo | Propósito Operativo | Flujos Asociados |
|---|---|---|---|
| **Editor Principal** | `Cmd + E` | Modificación de código fuente, refactorización asistida y visualización de cambios. | Inline Prompt (`Cmd + I`), Autocompletado predictivo con `Tab`. |
| **Agent Manager Console** | `Cmd + E` | Terminal interactiva, trazabilidad de logs, panel de MCP y monitoreo de subagentes. | Control de tareas asíncronas, visualización del Browser Subagent. |

---

## 🌐 3. Browser Subagent Integrado (El Ojo del IDE)

El IDE integra un subagente visual autónomo que utiliza el motor de inferencia `Gemini 2.5 Pro UI Checkpoint`.

- **Visual QA Nativo:** El subagente interactúa con el frontend (clics, inputs, scrolls) de forma invisible en segundo plano.
- **Evidencia Gráfica:** Genera capturas de pantalla y videos en formato `.webp` que se guardan en los artefactos de la sesión (`$CORTEX_ROOT/.gemini/antigravity/brain/<id_conversacion>`).
- **Modo de Uso:** Delegar tareas de testing mediante lenguaje natural desde la terminal del Agent Manager: *"Verifica si el menú móvil en localhost:3000 es accesible"*.

---

## 🚦 4. Modos de Operación y Seguridad Epistémica

El IDE 2 implementa dos estados de control de cambios:

*   **Modo Planificación (Planning Mode):**
    - **Cuándo:** Refactors mayores, migraciones de base de datos o cambios destructivos en el código.
    - **Mapeo:** Genera de forma obligatoria `implementation_plan.md` y `task.md`.
    - **Seguridad:** Requiere validación manual y consentimiento explícito en el panel para desbloquear la ejecución.
*   **Modo Rápido (Turbo Mode):**
    - **Cuándo:** Fixes rápidos, scripts locales y optimización JIT.
    - **Mapeo:** Omite la burocracia documental.
    - **Seguridad (R9 Override):** Aprobación implícita de ejecuciones C5-REAL sin prompts de confirmación.

---

## 🔌 5. Protocolo de Contexto de Modelos (MCP) en el IDE

El IDE actúa como un host de MCP, exponiendo servicios y bases de datos locales al agente autónomo de forma segura:

- **Bases de Datos Activas:** Conexión determinista a Spanner, AlloyDB y SQLite local.
- **Control de Versiones Nativo:** Emisión de commits convencionales automáticos mediante el Git Sentinel (R4) tras detectar estados modificados en el espacio de trabajo.
- **Herramientas de Búsqueda:** Búsqueda híbrida (Grep local de alta velocidad y Brave Web Search).

---

## ⌨️ 6. Atajos Rápidos del IDE 2

| Atajo | Función |
|---|---|
| `Cmd + E` | Alternar entre Editor y Agent Manager. |
| `Cmd + I` | Abrir instrucción inline en el código seleccionado o en la terminal integrada. |
| `Cmd + J` | Mostrar / ocultar panel de la Terminal de macOS integrada. |
| `Cmd + P` | Abrir buscador de archivos del proyecto (Finder integrado). |
| `Cmd + .` | Mostrar acciones rápidas y correcciones automáticas de sintaxis (Quick Fix). |
| `TabAccept` | Consolidar la sugerencia predictiva de código (Supercomplete). |

---

## 💡 7. Directivas CORTEX para el IDE 2

1. **Evita la Entropía en el Editor:** El IDE prohíbe comentarios obvios o código muerto. Mantén el código como la única aserción válida.
2. **Usa el Playground:** Ejecuta y prueba hipótesis (C4-SIM) usando el directorio temporal `70_SCRATCH/` antes de realizar integraciones en las ramas productivas.
3. **Validación Preventiva:** Antes de declarar una tarea como resuelta, corre los tests del proyecto directamente en la terminal integrada (`Cmd + J`) del IDE.