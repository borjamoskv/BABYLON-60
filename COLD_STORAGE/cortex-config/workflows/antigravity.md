---
description: Guía maestra de superpoderes y referencia rápida de Google Antigravity
---


// turbo-all
# 🌌 Google Antigravity — Manual de Campo

## 🧠 Arquitectura del Agente

Antigravity no es un chat, es un sistema de **doble ventana** con **agentes autónomos**.

| Ventana | Atajo | Propósito |
|---|---|---|
| **Editor** | `Cmd+E` | Código, `Cmd+I` (instrucciones inline), Panel Lateral |
| **Agent Manager** | `Cmd+E` | Orquestación, Terminal, Archivos, Paneles, Bandeja de entrada |

---


// turbo-all
## 🌐 Browser Subagent (El Ojo que Todo lo Ve)

Un modelo especializado (`Gemini 2.5 Pro UI Checkpoint`) que navega por ti.

### Capacidades
- **Navegación Real:** Clics, scroll, input en formularios complejos.
- **Evidencia Visual:** Genera capturas de pantalla y grabaciones de vídeo (`.webp`).
- **Aislamiento:** Usa un perfil de Chrome independiente (limpio, sin cookies personales).
- **Multitarea:** Funciona en background sin robar el foco de tu editor.

### Cómo invocarlo
Simplemente pide tareas que requieran ver una web:
- *"Ve a localhost:3000 y comprueba si el botón de login funciona"*
- *"Busca en la documentación de Stripe cómo hacer un refund"*
- *"Haz scroll en la home y dime si hay errores de layout"*

### Seguridad
- **Allowlist/Denylist:** Controla a qué dominios puede acceder.
- **Modo Estricto:** Bloquea URLs no permitidas por defecto.

---


// turbo-all
## 🚦 Modos de Agente

| Modo | Cuándo usarlo | Comportamiento |
|---|---|---|
| **Planificación** | Tareas complejas, refactors grandes | Desglosa en **Grupos de Tareas**, crea **Planes de Implementación**. Piensa antes de actuar. |
| **Rápido** | Fixes rápidos, scripts sencillos | Ejecución directa. "Dispara y pregunta después". |

---


// turbo-all
## 📦 Artefactos (Tu evidencia)

El agente se comunica con algo más que texto:

1.  **Lista de Tareas:** Dashboard en tiempo real del progreso.
2.  **Plan de Implementación:** Propuesta técnica detallada. **Léelo** antes de aprobar.
3.  **Tutorial (Walkthrough):** Resumen post-misión con lo que cambió.
4.  **Conocimiento:** Memoria persistente que el agente extrae y guarda automáticamente.
5.  **Grabaciones:** Vídeo de lo que hizo el Browser Subagent.

---


// turbo-all
## 🛡️ Seguridad y Entorno

- **Modo Estricto:**
    - Fuerza revisión manual de comandos de terminal y JS.
    - Respeta `.gitignore` (no ve archivos ignorados).
    - Bloquea acceso a URLs no confiables.
- **Sandbox (Zona Protegida):**
    - Aislamiento a nivel de kernel (`seatbelt` en macOS).
    - El agente solo puede escribir en el proyecto, no en tu sistema.

---


// turbo-all
## 🔌 MCP (Model Context Protocol)

Antigravity es extensible. Conecta herramientas externas:
- **Bases de Datos:** Lee esquemas de PostgreSQL/Supabase.
- **Servicios:** Crea tickets en Linear, busca en Notion.
- **Local:** Ejecuta scripts locales de forma segura.

---


// turbo-all
## ⌨️ Atajos Imprescindibles

| Atajo | Acción |
|---|---|
| `Cmd + E` | Alternar Editor <-> Agent Manager |
| `Cmd + I` | Instrucción Inline (Editor y Terminal) |
| `Cmd + J` | Abrir Terminal Integrada |
| `Cmd + P` | Abrir Panel (Archivos, Artefactos) |
| `Cmd + .` | Acciones rápidas (Quick Fix) |

---


// turbo-all
## 💡 Pro Tips

1.  **Playground:** Usa el botón "Use Playground" para probar ideas sin ensuciar tu workspace.
2.  **Comentarios en Archivos:** Abre un archivo en el panel del Manager y deja comentarios. El agente los lee como instrucciones ultra-precisas.
3.  **Supercomplete:** `Tab` no solo completa la línea, puede refactorizar el archivo entero si es necesario.
4.  **Terminal Inline:** Usa `Cmd+I` en la terminal para pedir comandos complejos ("Mata el proceso en el puerto 3000") en lugar de escribirlos.
