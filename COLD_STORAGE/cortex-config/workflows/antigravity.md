// turbo-all
# 🌌 Google Antigravity — Manual de Campo (CORTEX-Persist Edition)

> **Reality-Level:** C5-REAL | **Aesthetic:** Industrial Noir 2026 | **Engine:** Google Antigravity v2.0.6 (Build 919477694)

Antigravity opera como un sistema de **doble ventana** con agentes autónomos y ejecución nativa, alejándose del paradigma estocástico de chat tradicional.

## 🧠 Arquitectura de Doble Ventana

| Entorno | Atajo | Función Principal |
|---|---|---|
| **Editor** | `Cmd+E` | Código, `Cmd+I` (instrucciones inline), Panel Lateral. |
| **Agent Manager** | `Cmd+E` | Orquestación, Terminal, Archivos, Paneles, Inbox. |

---

## 🌐 Browser Subagent (Gemini 2.5 Pro UI Checkpoint)

Sub-agente visual que ejecuta validaciones C5-REAL en el navegador.

- **Capacidades:** Navegación autónoma (clics, scroll, formularios complejos), aislamiento (perfil limpio), multitarea asíncrona.
- **Evidencia (Falsación):** Genera capturas de pantalla y grabaciones de vídeo (`.webp`).
- **Invocación:** *"Ve a localhost:3000 y comprueba errores de layout"*.
- **Seguridad:** Allowlist/Denylist y Modo Estricto para bloquear dominios no autorizados.

---

## 🚦 Modos de Agente

| Modo | Cuándo usarlo | Comportamiento |
|---|---|---|
| **Planificación** | Tareas complejas, refactors estructurales | Requiere `implementation_plan.md`, desglose en Grupos de Tareas y aprobación explícita del humano. |
| **Rápido (Turbo)** | Fixes rápidos, scripts sencillos | Ejecución directa "dispara y pregunta después". Ideal para CORTEX (regla R9: aprobación implícita). |

---

## 📦 Artefactos (Pruebas C5-REAL)

El agente genera evidencia criptográfica y estructural:

1. **Task List (`task.md`):** Dashboard en tiempo real de la ejecución.
2. **Implementation Plan (`implementation_plan.md`):** Propuesta técnica detallada (requiere OK en Modo Planificación).
3. **Walkthrough (`walkthrough.md`):** Resumen forense post-mutación.
4. **Conocimiento:** Memoria persistente extraída y consolidada.
5. **Grabaciones:** Video forense del Browser Subagent.

---

## 🛡️ Seguridad y Sandbox (Seatbelt)

- **Aislamiento:** A nivel de kernel (`seatbelt` en macOS). Mutaciones limitadas al workspace.
- **Modo Estricto:** Fuerza revisión humana de comandos destructivos en terminal y ejecución de JS. Respeta `.gitignore`.

---

## 🔌 Extensibilidad (MCP)

Integración determinista de sistemas externos:
- **Bases de Datos:** PostgreSQL, Supabase, Spanner, AlloyDB.
- **Servicios:** Linear, Notion, GitHub.
- **Local:** SQLite, ejecución de scripts locales.

---

## ⌨️ Atajos Operativos Críticos

| Atajo | Acción |
|---|---|
| `Cmd + E` | Toggle Editor ↔ Agent Manager |
| `Cmd + I` | Instrucción Inline (Editor/Terminal) |
| `Cmd + J` | Terminal Integrada |
| `Cmd + P` | Paneles (Archivos/Artefactos) |
| `Tab` | Supercomplete: Mutación predictiva de archivo completo |

---

## 💡 CORTEX Pro Tips

1. **Terminal Inline:** Usa `Cmd+I` en la terminal para delegar comandos complejos.
2. **Comentarios como Directivas:** Comenta un archivo abierto en el Agent Manager; el agente lo procesará como una instrucción de alta prioridad.
3. **Playground:** Usa el entorno aislado para falsar hipótesis (C4-SIM) antes de mutar el workspace (C5-REAL).
