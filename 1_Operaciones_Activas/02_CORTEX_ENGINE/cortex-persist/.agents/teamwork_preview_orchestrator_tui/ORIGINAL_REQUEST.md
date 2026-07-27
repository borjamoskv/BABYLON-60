# Original User Request

## Follow-up — 2026-06-30T17:13:24Z

Construir una Interfaz de Usuario de Terminal (TUI) para el modelo MOSKV-1 (LoRA) utilizando el framework `Textual` de Python. La interfaz debe erradicar el DOM, operar exclusivamente en la consola, soportar atajos estilo Vim y garantizar máxima exergía en la interacción con el motor MLX local.

Working directory: ~/teamwork_projects/moskv1_tui
Integrity mode: demo

## Requirements

### R1. Arquitectura de Dos Procesos (FastAPI + Textual)
El sistema debe estar desacoplado. El backend será un servidor FastAPI que carga los adaptadores LoRA de MLX y expone un endpoint de Server-Sent Events (SSE). El frontend será una aplicación `Textual` que consume el stream de SSE para renderizar los tokens en tiempo real sin bloquear el Event Loop de la UI.

### R2. Estética "Industrial Noir" y Navegación Vim
La TUI debe tener un esquema de colores estricto: fondo `#0A0A0A`, acentos primarios `#2B3BE5`, y texto de alto contraste. Debe soportar navegación por teclado básica (ej. `j`/`k` para scroll) y no depender del uso del ratón.

### R3. Persistencia Criptográfica (SQLite WAL)
El backend debe registrar cada interacción (Prompt/Respuesta) en una base de datos SQLite local configurada estrictamente con `PRAGMA journal_mode=WAL;` y `PRAGMA busy_timeout=5000;`. No se usarán ORMs pesados (cero SQLAlchemy), solo `aiosqlite` directo.

## Acceptance Criteria

### Integridad Arquitectónica
- [ ] Se incluye un script automatizado `verify_backend.py` que arranca el servidor, envía un prompt falso y valida que el stream SSE emite múltiples chunks en formato JSON antes de cerrar.
- [ ] La base de datos SQLite pasa una aserción estricta de `PRAGMA journal_mode == 'wal'` validada mediante un test programático en `test_db.py`.

### Estética y TUI
- [ ] El código fuente de Textual (archivo CSS/TCSS) contiene explícitamente los hashes de color `#0A0A0A` y `#2B3BE5`.
