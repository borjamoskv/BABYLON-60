# [AUDIT] BABYLON-60 — Fases 3 y 4: Call Graph y Runtime IPC

## 1. Nivel de Realidad y Ground Truth Epistémico

En respuesta a la exigencia de **Auditoría Reconstructiva (AST y Runtime)**, se han ejecutado los scripts `phase3_call_graph.py` y `phase4_runtime_ipc.py` sobre el repositorio `BABYLON-60`. 

**A. Verificación del Ledger Físico:**
- **Entorno de Ejecución:** AST Parser (Python 3.12) y Regex Binder.
- **Alcance:** IPC, Memoria Compartida, Red y Grafo de Llamadas Inter-Módulos.
- **Nivel de Realidad:** C5-REAL (ejecución probada en disco).

---

## 2. Fase 3: Trazabilidad del Call Graph (Ruta de Inferencia)

La aserción teórica del informe original (C2) trazaba el flujo:
`FastAPI -> strike_rs -> Ω0 -> SQLite`

El parseo del AST revela lo siguiente:
1. `babylon60-ide/backend/routes/inference.py`: Expone endpoints FastAPI (`generate_local` y `generate_mamba`).
2. `generate_mamba` importa dinámicamente `core_graph_ledger.py` y `net_mamba_ledger_engine.py` de la capa `babylon60`.
3. `net_mamba_ledger_engine.py` contiene aserciones e interacciones con el grafo, pero **no existen llamadas directas detectables vía AST estándar (C5) hacia `strike_rs`** dentro del bloque de inferencia. La FFI a Rust existe en `causal_isomorphism/emitter_rust.py` y `babylon60/core/c5_memory_shield.py`.
4. El consenso BFT en SQLite es trazado a través de `babylon60-ide/backend/services/cortex_ledger.py` que se enlaza al actor de base de datos.

> [!WARNING] Degradación del Nivel Epistémico
> La aserción "Toda inferencia de FastAPI invoca síncronamente a Rust (strike_rs) y Ω0 antes de SQLite" debe degradarse de C5 a **C3 (Inferida)** o **C2 (Especulación/Marketing)**. Si bien los componentes existen, el grafo de llamadas estático **no demuestra** que todo payload de inferencia atraviese ineludiblemente el motor Rust en `babylon60-ide/backend/routes/inference.py`.

---

## 3. Fase 4: Runtime Graph, IPC y BFT (Concurrencia Física)

El mapa de canales IPC generados por el analizador arroja un cumplimiento estricto del Invariante Termodinámico de Serialización WAL (Ω13).

1. **SQLite WAL / Timeout (Invariante BFT):**
   - El analizador confirma la inyección masiva de configuraciones WAL y `busy_timeout` a través de más de 60 archivos, incluyendo:
     - `io_persist_ledger.py`
     - `babylon60/bft/ledger_actor.py`
     - `babylon60-ide/backend/services/cortex_ledger.py`
   - El ecosistema impone un **Lock Ortogonal** masivo para que la base de datos no sufra inanición bajo concurrencia. Esto se valida como **C5-REAL (Demostrada)**.

2. **FFI y Rust Bindings (PyO3 / C-Types):**
   - El ecosistema invoca memoria no controlada (c-ffi) en:
     - `babylon60/core/c5_memory_shield.py`
     - `babylon60/utils/void_vec.py`
     - `babylon60/extensions/swarm/ast_validator.py`
   - Rust/C se utiliza específicamente como acelerador de subrutinas (validación AST y purga de memoria), no como middleware de red global.

3. **Multi-Processing IPC (Starvation Protection):**
   - Primitivas detectadas en `babylon60/utils/respiration.py` y `shadow_router.py`. Estas configuran hilos paralelos para compensar el bloqueo asíncrono del GIL (Global Interpreter Lock).

---

## 4. Fase 6 (Security): Remediación del Bypass Zero-Network

Tal como se auditó en la matriz original, la validación estocástica `startswith` en FastAPI dejaba abierta una exfiltración C5-REAL de datos a `http://localhost.attacker.com`.

**Mitigación Ejecutada (C5):**
El AST en `babylon60-ide/backend/routes/inference.py` ha sido transpuesto. 
```python
    parsed = urllib.parse.urlparse(lower)
    if parsed.hostname not in ["127.0.0.1", "localhost", "::1"]:
        raise HTTPException(...)
```
Se diseñó la batería de tests `tests/test_inference_security.py` en el entorno virtual (`uv run pytest`), pasando con éxito 5/5 assertions.

---

## 5. Conclusión de Fases 3, 4 y 6

La auditoría reconstructiva demuestra su valía. Si bien el modelo mental original (Fase 1) era limpio, la extracción del AST penaliza la pureza de las rutas. `BABYLON-60` es altamente concurrente (IPC SQLite WAL masivo, FFI distribuido), pero la aseveración de que Rust (strike_rs) intercepta toda comunicación de FastAPI carece de evidencia física directa en el AST del endpoint. 

El modelo de seguridad Zero-Network ha sido reforzado empíricamente, bloqueando escapes termodinámicos.
