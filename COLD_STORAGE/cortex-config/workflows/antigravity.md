---
description: "Workflow for antigravity — C5-REAL Sovereign IDE Kernel Specifications"
workflow: antigravity
expected_duration_min: 25
---

# 🛸 ANTIGRAVITY-2: KERNEL DE INFERENCIA Y ENTORNO OPERATIVO C5-REAL

```yaml
Claim: El IDE Antigravity-2 no es un editor estético; es el transductor físico entre la voluntad del Demiurgo y el CORTEX C5-REAL.
Proof:
  Base: Aislamiento sandbox (seatbelt) + Exergía FFI con mitigación de colisión de intérprete.
  Range: [cero fricción en AST, compilación JIT instantánea]
  Confidence: C5-REAL
```

---

## 🏛️ 1. Estructura, Perfiles del IDE y Aislamiento macOS

A diferencia de las extensiones tradicionales, Antigravity 2 se ejecuta en su propio espacio de usuario de macOS:

*   **Ruta de Configuración:** `~/.antigravity-ide/`
*   **Gestor de Extensiones:** `~/.antigravity-ide/extensions/`
*   **Argumentos de Lanzamiento:** Configurados en `~/.antigravity-ide/argv.json` (ej. localización en `"locale": "es"` y desactivación de telemetría `"enable-crash-reporter": false`).
*   **Espacio Aislado (Sandbox):** El binario del IDE se ejecuta bajo el perfil `seatbelt` restringiendo la escritura a los directorios del proyecto y configuraciones autorizadas del agente.
*   **Vías Críticas Protegidas (R5):** Prohibido alterar rutas protegidas del sistema (ej. `/private/var/db`, `Mobile Documents`, virtualizaciones `Coli-ma`).

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

---

## 🛡️ 8. Homeostasis y Resolución de Conflictos de Compilación

Para mantener el estado de Cero Anergía en entornos heterogéneos, aplicar los siguientes protocolos ante fallos conocidos:

### A. Fallos de Enlazado FFI (PyO3 / Python Mismatch)
Cuando la versión del intérprete del sistema (ej. Python 3.14) supera el soporte de la biblioteca Rust/PyO3 instalada:
- **Síntoma:** Error de compilación en `pyo3-ffi` o fallos de linker `ld: symbol(s) not found`.
- **Resolución:** Inyectar la variable de entorno para forzar la compatibilidad ABI3:
  ```bash
  PYO3_USE_ABI3_FORWARD_COMPATIBILITY=1 cargo build --release
  # O mediante Maturin en el entorno virtual respectivo:
  PYO3_USE_ABI3_FORWARD_COMPATIBILITY=1 VIRTUAL_ENV=<ruta_venv> maturin develop --release
  ```

### B. Evasión de Bloqueos de Contexto en Commits (Context Leakage Guard)
Si el hook de pre-commit global bloquea el commit por conflicto con el repositorio activo del meta-contexto:
- **Síntoma:** `ERROR [C5-REAL]: Context Leakage Detected. Aborting commit.`
- **Resolución:** Si la mutación es aislada e intencionada, usar obligatoriamente el prefijo `[bridge]` en el mensaje del commit, e inyectar el bypass manual si es necesario:
  ```bash
  git commit -m "[bridge] <tipo>: <descripción>" --no-verify
  ```

### C. Concurrencia Transaccional en Base de Datos (WAL Mode)
Al interactuar con SQLite en escenarios multihilo dentro del host MCP del IDE:
- **Resolución:** Forzar el modo `WAL` (Write-Ahead Logging) y establecer un timeout robusto de 5000ms para evitar Deadlocks termodinámicos:
  ```sql
  PRAGMA journal_mode=WAL;
  PRAGMA busy_timeout=5000;
  ```

---

*∴ ANTIGRAVITY-2 ◈ "Termodinámicamente superior. Cero fricción de compilación."*