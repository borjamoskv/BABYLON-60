<!-- [C5-REAL] Exergy-Maximized -->
# Plan de Implementación: Refactorización BABYLON-60 Core via LEGIØN-1 (Swarm)

## Meta
Alcanzar una organización pluscuamperfecta del núcleo `cortex/cortex/` sin romper dependencias cíclicas ni exponer los tests a errores en cascada.

## Despliegue de Especialistas (Formación HYDRA)

### 1. 🐍 Especialista de Imports (El Cirujano AST)
**Misión:** Fixear los errores de importación actuales inmediatos (`api_state`, `config`, `i18n`, `CortexEngine` etc) producidos por el último reorg.
**Tareas:**
- Parsear todos los `tests/` y encontrar referencias rotas a la raíz de `cortex`.
- Reescribir las referencias absolutas utilizando el árbol de módulos nuevo (e.g. `cortex.api.state`, `cortex.utils.i18n`).
- Garantizar que el test suite vuelva a correr.

### 2. 🗄️ Especialista de Dominio de Datos (Database & Memory)
**Misión:** Centralizar todos los elementos de base de datos, caché y memoria persistente.
**Tareas:**
- Mover y empaquetar de forma segura `database/`, `compaction/` y `memory/`.
- Validar las importaciones de `CortexConnectionPool` y SQLite Vec en el `cortex.engine`.

### 3. 🌐 Especialista de Interfaz (API & Routes)
**Misión:** Refactor de la capa de acceso y middleware.
**Tareas:**
- Empaquetar el subdirectorio `api/` (que incluye `core.py`, `middleware.py`, `deps.py`).
- Ajustar las exposiciones en el ASGI app que está provocando cuelgues u 404s.

### 4. 🧪 Especialista QA & Consenso
**Misión:** Asegurar que el estado del árbol Merkle, los leds y todo el sub-árbol de `cortex.consensus` pase sin problemas. Run `/qa` y `/compilar` tras cada wave.

## Fases de Ejecución
- **Fase 1:** Reparación Inmediata de Tests (El cirujano AST ataca).
- **Fase 2:** Refactoring Incremental (1 Dominio a la vez).
- **Fase 3:** Purificación (`/mejoralo --brutal` and `/pulir`).

---

**Protocolo BABYLON-60 Activo.** Esperando tu APROBACIÓN para iniciar el Swarm Phase 1 (Limpieza y reparación de Tests rotos).
