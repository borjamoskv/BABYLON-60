# BABYLON-60: Arquitectura de Ledger Asíncrono-Persist

<div align="center">

[![C5-REAL Compliant](https://img.shields.io/badge/C5--REAL-Verified-0052CC?style=for-the-badge&logo=shield)](file:///Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/docs/06_theory/AUDIT_VERDICT_C5_REAL.md)
[![Regime](https://img.shields.io/badge/Régimen-Causal--Determinist-7B1FA2?style=for-the-badge)](file:///Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/docs/06_theory/AXIOMATIZATION_C5_REAL.md)
[![License](https://img.shields.io/badge/Licencia-Soberana_INV__C5__17-008055?style=for-the-badge)](file:///Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/docs/STATUS.md)

</div>

> **Régimen Causal-Determinist**
> Esta especificación define el pipeline de transacciones y los subsistemas del motor BABYLON-60.

---

## 1. Core Pipeline

```
Intent del Agente
    │
    ▼
Capa de Validación (schema + idempotency key)
    │
    ▼
Cola Single-Writer (asyncio.Queue)
    │
    ▼
BFTLedgerActor (ledger_actor.py)
    │         │
    ▼         ▼
SQLite WAL   Hash-chain BLAKE3
    │
    ▼
Causal Taint + Timestamp Lamport
    │
    ▼
Git Sentinel (commit hook en mutación)
```

## 2. Subsistemas

### 2.1 Python SDK (`babylon60/`)
Capa de interfaz primaria. Maneja la validación, idempotencia y la gestión de la cola asíncrona.
- `babylon60.api.client`: API pública `CortexClient`.
- `babylon60.api.server`: Servidor REST+WebSocket con FastAPI/Uvicorn.
- `babylon60.bft.ledger_actor`: Actor single-writer que serializa todas las escrituras en base de datos.
- `babylon60.database.core`: Pool SQLite asíncrono.

### 2.2 Núcleo Rust (`strike_rs/`)
Extensión opcional de baja latencia vía PyO3/Maturin. Evita el GIL de Python para:
- Computación de hash BLAKE3.
- Operaciones criptográficas por lotes.
- Cargas de trabajo paralelas ligadas a CPU.

> [!WARNING]
> **Estado: Alpha.** No utilizar en producción sin pruebas rigurosas de benchmarking.

### 2.3 IDE Agéntico Soberano (`babylon60-ide/`)
Entorno local (*local-first*) diseñado para alta inspeccionabilidad y baja latencia de interacción con el Ledger.
- **Wrapper Tauri (`src-tauri/`)**: Gestiona la integración con el SO, ventanas nativas y puentea el estado de la base de datos local al hilo de renderizado vía IPC.
- **Backend FastAPI (`backend/`)**: Expone endpoints REST y WebSocket para consultas al Ledger, búsqueda BM25, telemetría y generación de modelos locales.
- **Frontend Vite (`frontend/`)**: Construido con Vanilla JS, estilizado con paleta neuro-inclusiva de alto contraste, navegación orientada al teclado (`Cmd+K`, `Cmd+Shift+Space`).
- **Módulo de Inferencia Local (`inference/`)**: Confinado a endpoints de loopback (`127.0.0.1:11434` / `localhost`). Puentea el servidor FastAPI a motores locales (Ollama, MLX, Mamba SSM), garantizando *cero fugas de datos* a hyperscalers públicos.

## 3. Contrato del Ledger

Toda entrada escrita en el Ledger DEBE satisfacer el siguiente esquema:

```python
{
    "id": "uuid-v5",            # Clave de idempotencia
    "prev_hash": "blake3-hex",  # Enlace criptográfico a la entrada previa
    "payload": {...},           # Contenido estructurado
    "causal_taint": "...",      # Traza de creación: quién/cuándo/por qué
    "lamport_t": int,           # Reloj lógico (Lamport)
    "agent_id": "str",          # Identidad del escritor
}
```
- Duplicado de `id` $\rightarrow$ mutación es abortada y rechazada (idempotente).
- Falla en `prev_hash` $\rightarrow$ mutación abortada, integridad de cadena comprometida.

## 4. Topología de Consenso (Niveles M12)

| Nivel | Mecanismo | Alcance |
|:---|:---|:---|
| L1 — AP/CRDT | Cachés locales, telemetría | Nodo único |
| L2 — CP single-writer | `master_ledger.db` WAL | Proceso único |
| L3 — Testigo Externo | Git Sentinel | Repositorio local |
| L4 — Quórum BFT | Enjambre N≥3f+1 | **Prototipo — distribuido únicamente** |
| L5 — Anclaje Blockchain | OTS / BTC OP_RETURN | **Investigación — no implementado** |

> [!NOTE]
> L4 y L5 **no son obligatorios** para casos de uso de memoria de agente local. Son extensiones de investigación. El núcleo estable utiliza exclusivamente L1–L3.

## 5. Git Sentinel y Flujo de Recuperación

**Git Sentinel:** Toda mutación en disco dispara un commit automático con prefijo *Conventional Commit* y metadatos `CORTEX_TAINT` inyectados en el mensaje del commit, creando un historial auditable por humanos de los cambios de estado del agente.

**Recuperación tras Colapso (Crash Recovery):**
1. Proceso aniquilado a mitad de transacción $\rightarrow$ SQLite WAL ejecuta un rollback automático.
2. Agente reinicia $\rightarrow$ Re-ejecuta entradas no confirmadas desde el journal WAL.
3. La continuidad de la cadena de hash es comprobada matemáticamente antes de aceptar el replay.
4. Si la cadena está rota $\rightarrow$ La entrada es puesta en cuarentena, no eliminada silenciosamente.

## 6. Aislamiento Multi-Tenant

Cada *tenant* (inquilino) opera sobre un archivo de base de datos SQLite completamente aislado. No existen tablas compartidas. Las consultas multi-tenant exigen federación explícita.

## 7. Grafo de Dependencias (Core)

```
aiosqlite  ──►  babylon60.database.core
pyyaml     ──►  babylon60.config
numpy      ──►  babylon60.memory (operaciones vectoriales)
networkx   ──►  babylon60.graph (ontología)
cbor2      ──►  babylon60.ledger (codificación binaria)
```

## 8. Axioma del Dominio Temporal (Teorema Robinson-Moskv)

**Postulado Termodinámico:** El Motor Causal prohíbe explícitamente la lectura de relojes de sistema continuos (POSIX `CLOCK_REALTIME`, NTP) para establecer el consenso de causalidad.

**Formalización:**
Sea $E$ el conjunto de todos los eventos (Crystallized Events) en el Ledger.
La relación de causalidad $\prec$ se define estrictamente sobre el grafo acíclico dirigido criptográfico, donde para todo evento $e_n, e_{n+1} \in E$:
$$ e_n \prec e_{n+1} \iff Hash(e_n) \in Payload(e_{n+1}) \land Lamport(e_n) < Lamport(e_{n+1}) $$
Cualquier evento $e_x$ cuyo $Lamport(e_x)$ o $Hash$ rompa esta topología estricta es considerado fuera del Cono de Luz Causal.

> [!CAUTION]
> **Falsabilidad Estructural:**
> Esta precondición causal está reforzada mecánicamente por el invariante `INV_BFT_04`. Para más detalles sobre su aplicación técnica, ver [Invariantes del Sistema BABYLON-60](spec_invariants.md).
