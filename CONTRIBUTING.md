<!-- C5-REAL EXERGY CERTIFIED -->

# Guía de Contribución y Gobernanza Agentica (CONTRIBUTING.md)

## 1. Arquitectura de Gobernanza (Single-Human / Multi-Agent)

- **Única Autoridad Humana y Arquitecto Líder:** Borja Fernández Angulo ([@borjamoskv](https://github.com/borjamoskv)) es el único desarrollador y decisor humano del proyecto.
- **Jerarquía Agentica:** Todos los agentes sintéticos, subagentes autónomos y modelos de lenguaje operan bajo delegación determinista de @borjamoskv y deben cumplir estrictamente las invariantes C5-REAL.
- **Protocolo HITL (Human-In-The-Loop):**
  - **Auto-ejecución autorizada para agentes:** Modificaciones locales en el *Working Tree*, compilación (`cargo check`, `py_compile`), ejecución de tests unitarios y formateo.
  - **HITL Obligatorio de @borjamoskv:** Operaciones mutacionales externas, des-archivado de remotos, rotación de credenciales, `git push --force` o reescritura del historial Git.

---

## 2. Invariantes de Compilación y Calidad Pre-Atestación

- **Validación Estricta de Sintaxis Antes de Commits:** Ningún archivo de script o módulo (Python, Rust, TypeScript) debe ser enviado a `git commit` ni atestado sin haber superado una prueba empírica silenciosa:
  - Python: `python3 -m py_compile <archivo>`
  - Rust: `cargo check --workspace`
  - TypeScript/Web: `tsc --noEmit`
- **Prohibición de Bypass Ciego:** Queda estrictamente prohibido el uso de `--no-verify` en comandos `git commit` o scripts de automatización.
- **Sin Parches Superficiales:** Prohibido silenciar errores con `try/except` vacíos, fallbacks dummy, comentar aserciones o eliminar tests que fallan.

---

## 3. Protocolo Git & Autenticación SSH

- **Esquema Remoto:** Utilizar SIEMPRE el esquema SSH (`git@github.com:borjamoskv/Teorema-Robinson-Moskv.git`).
- **Estructura de Ramas:**
  - `main`: Producción y estado canónico (push directo bloqueado).
  - `develop`: Rama de integración de subsistemas.
  - `feature/*`: Desarrollo de nuevas capacidades.
  - `fix/*`: Corrección de errores y remediación.
  - `refactor/*`: Optimización de exergía sin cambio funcional.
  - `docs/*`: Actualizaciones ontológicas y de documentación.

---

## 4. Convenciones de Commits y Atestación SCITT

- **Formato Estándar:** Usar *Conventional Commits*:
  - `feat(...)`: Nueva funcionalidad.
  - `fix(...)`: Corrección de fallos.
  - `docs(...)`: Cambios en documentación u ontología.
  - `perf(...)`: Optimización de latencia o memoria (`T_eff < 5 ms`).
  - `chore(...)`: Tareas de mantenimiento e infraestructura.
- **Atestación Criptográfica:** Toda transición relevante se firma mediante Merkle Tree SHA3-256 en el Kernel Ring-0 y emite recibo SCITT en la compuerta de commit.

---

## 5. Higiene de Repositorio (Nivel 0 / Zero-Residual)

- **Cero Entropía Transitoria en Raíz:** NUNCA dejar volcados de datos, logs, transcripciones ni scripts de un solo uso en la raíz del repositorio.
- **Zona de Cuarentena:** Todo material efímero o transitorio debe guardarse en `scratch/` (ej. `scratch/c5_real_poc.py`).
- **Verificación Final:** Antes de dar por concluida cualquier tarea, el agente debe verificar visual o programáticamente que el árbol de código está inmaculado.

---

## 6. Flujo de Trabajo Agentico

Issue → Rama (feature/fix) → Preflight Local → Pull Request → Revisión HITL (@borjamoskv) → Merge SCITT

---

## 7. Suite de Verificación Preflight y Auditoría de Código

Antes de solicitar una revisión o atestación SCITT, el entorno o agente DEBE ejecutar la suite de verificación local:

- **Preflight Unificado:** `./scripts/preflight.sh` (si está presente) o ejecución manual de:
  - Validaciones Python: `python3 -m py_compile` sobre módulos modificados y `pytest` sobre la suite relevante.
  - Validaciones Rust: `cargo check --workspace --all-targets`
- **Auditoría de Inexistencia (Existence Gap Audit):** Garantizar que ningún `import` ni referencia apunte a módulos, símbolos o rutas locales fantasma que no existan en el árbol de código.
- **Formateo e Higiene Visual:** Eliminación de espacios al final de línea y adición de nueva línea al final del archivo (`files.trimTrailingWhitespace`, `files.insertFinalNewline`).

---

## 8. Invariantes de Memoria FFI y Kernel IPC (Rust / Python)

Para cualquier contribución que toque el Kernel de Ring-0 (`src/cortex_kernel`) o los conectores FFI en Python:

- **Alineación de Caché L1:** Las estructuras de memoria compartida (`SharedManifest`) deben mantener alineación `#[repr(C, align(128))]` en Apple Silicon (macOS M1/M2/M3) o `align(64)` en x86_64/ARM64 Linux para prevenir *False Sharing*.
- **Cero Liberación de Basura Externa (Bare-Metal Atomics):** Prohibido el uso de recolectores de basura o crates pesados de EBR. Se exige la gestión mediante primitivas atómicas puras (`AtomicPtr`, `AtomicUsize`).
- **Concurrencia Débil y Semántica Acquire/Release:** Las transiciones de estado de slots deben sincronizarse mediante semántica `Acquire/Release` con barreras de silicio (`dmb ish`).

---

## 9. Trazabilidad de Issues y Transparencia Epistémica

- **Vinculación Obligatoria:** Todo commit debe citar el issue correspondiente (`Fixes #X` o `Refs #X`).
- **Explicación Racional No Trivia:** Las descripciones de Pull Requests y commits no deben restarse a repetir el código, sino justificar la causalidad, el análisis de compensación (*trade-offs*) y las alternativas descartadas.

