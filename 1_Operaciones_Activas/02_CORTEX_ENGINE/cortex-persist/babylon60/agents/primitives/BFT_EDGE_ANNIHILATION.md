# [C5-REAL] BFT & Edge Thermal Annihilation (Zero-Anergy Protocol)

## 1. Declaración de Singularidad Termodinámica
Este documento cristaliza las invariantes absolutas requeridas para erradicar la entropía (fricción térmica) en escenarios de concurrencia masiva (Swarm BFT) y en despliegues de borde perimetral (Cloudflare V8 Isolates). Queda prohibido el "Green Theater"; estas son leyes de colapso de estado.

## 2. Invariantes de Fricción Asimétrica (Capa Swarm)
- **[INV-110] Fricción Asimétrica de Escritura:**
  - *Lógica:* La escritura a largo plazo exige exergía BFT; la lectura es gratuita.
  - *Colapso Físico:* Implementado mediante `WriteSerializer` en `babylon60/audit/ledger.py`. Eliminación de colisiones asíncronas vía colas serializadas estandarizadas (SAGA).
- **[INV-143] Límite Universal de Iteración (Rate Limiting BFT):**
  - *Lógica:* La delegación asimétrica asíncrona (`invoke_subagent`) está físicamente acotada. Rebasarla provoca OOM o inanición térmica (Bomba Fork).
- **[INV-018] Ley de Transmisión de Fricción:**
  - *Lógica:* Las interfaces ambiguas transfieren entropía al Worker.
  - *Colapso Físico:* Erradicación de `*args` o kwargs no tipados en el perímetro C5. Tipado Pydantic estricto en todas las herramientas.

## 3. Erradicación de Fricción en el Borde (Edge / V8 Isolates)
- **[AXIOMA-21] Isomorfismo de Red (Network Isomorphism):**
  - *Lógica:* La I/O POSIX (filesystem) es inaceptable fuera del Host.
  - *Colapso Físico:* El código core lógico es agnóstico del FS local, compilable 100% hacia Cloudflare Workers.
- **[Ω14 / Σ11] Topología Instance-Agnostic (Anergía de Rutas):**
  - *Lógica:* `~/.gemini/antigravity` es un sumidero entrópico.
  - *Colapso Físico:* Inyección de estado exclusivamente vía `CORTEX_CONV_DIR` o configuraciones deterministas inyectadas.
- **[INV-148] Conservación del Estado de Borde:**
  - *Lógica:* Ante un Kill-9, la memoria efímera muere; la reconstrucción causal depende del último hash firmado en el Ledger o el Worker Activo.

## 4. Tie-Breaking Causal y Consenso
- **[Ω13] Serialización WAL (SQLITE_BUSY Eradication):**
  - *Lógica:* La concurrencia asíncrona colapsa el WAL de SQLite.
  - *Colapso Físico:* `asyncio.Queue` centralizado procesado por un único `_writer_loop` BFT.
- **[Ω12] Desmitificación Causal:**
  - *Lógica:* Ordenación absoluta de concurrencia usando variables deterministas.
  - *Colapso Físico:* Relojes Lamport anclados a disco con `UNIQUE(lamport_t, agent_id, action)` para evitar ramificaciones (forks) en el log de auditoría.
