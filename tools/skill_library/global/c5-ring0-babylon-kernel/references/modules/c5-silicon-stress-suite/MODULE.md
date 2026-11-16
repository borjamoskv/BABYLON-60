---
name: c5-silicon-stress-suite
display_name: Suite de Estrés Concurrente de Silicio y Enjambres (C5-REAL)
description: Pruebas de estrés en paralelo y benchmarks de silicio (multicast O(1), Seqlock KUDURRU-64, BFT y Touch ID COSE_Sign1). Dispara con "pruebas de estres", "stress test swarm", "estres enjambre", "concurrencia de silicio", "stress suite", "poc", "test de estres", "estres silicio".
role: auditor
allowed_roles:
- auditor
directives:
  worktree_mode: audit-only
  phase: verification
  handoff:
    upstream: ejecutor
    downstream: operador
---

# ⚡ Suite de Estrés Concurrente de Silicio (C5-REAL)

> **Directiva Declarativa (Orquestación en Árbol de Trabajo):**
> - **Rol Asignado:** `auditor` (Auditor (Verificación Independiente, Linters de Silicio & Fail-Closed Gate))
> - **Modo de Acceso a Worktree:** `audit-only` (audit-only (Lectura forense de diffs, linters, tests de estrés y cálculo de exergía; cero mutación de código))
> - **Fase Causal:** `verification`
> - **Contrato Handoff:** Recibe de `ejecutor` $\to$ Despacha a `operador`

Esta habilidad formaliza la ejecución de pruebas de estrés en paralelo y benchmarks de silicio para certificar la invarianza termodinámica y la ausencia de contención ($RFO = 0$) en la arquitectura sexagesimal `BABYLON-60` / `MOSKV-1`.

---

## 🎯 Batería de 6 Frentes de Estrés y POCs de Silicio

Cuando el operador solicite pruebas de estrés concurrente o benchmarks POC (`poc`), el agente debe ejecutar de forma determinista los vectores empíricos:

```mermaid
graph TD
    A["Trigger: pruebas de estres / poc"] --> B1["1. Multicast Fan-Out (AgentPager)"]
    A --> B2["2. Seqlock SPMC KUDURRU-64 Release"]
    A --> B3["3. Saturación P-Cores M3 Pro"]
    A --> B4["4. Consenso BFT & Falla Bizantina"]
    A --> B5["5. Touch ID COSE_Sign1 Bridge"]
    A --> B6["6. Exterior Cognitivo CORTEX-Persist"]
    A --> B7["7. Resistencia Epistémica RR-003 (RIF)"]

    B1 --> C1["<= 2.5 ms para 1.000 agentes"]
    B2 --> C2["0 Torn Reads / 57.11 Mops/s (8 lectores)"]
    B3 --> C3["11 Hilos / Cero Throttling"]
    B4 --> C4["Aislamiento 0xDEAD_6060"]
    B5 --> C5["Atestación DER P-256 en Silicio"]
    B6 --> C6["4 Vectores Anti-Solipsismo (145/145 PASSED)"]
    B7 --> C7["RIF Score = 1.0000 / N >= 30"]
```

---

## 🛠️ Comandos y Scripts de Referencia

### 1. Multicast Fan-Out Masivo (AgentPager O(1))
Verifica que 1.000 agentes en letargo absoluto despierten ante una única señal multicast sin deriva temporal:
```bash
python3 -c "
import sys, asyncio, time
sys.path.extend(['/Users/borjafernandezangulo/10_PROJECTS/BABYLON-60', '/Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/01_KISH_ENGINE', '/Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/02_EDIN_SWARMS'])
from agents_archi import AgentPager

async def bench():
    p = AgentPager()
    tasks = [asyncio.create_task(p.wait_for_beep()) for _ in range(1000)]
    await asyncio.sleep(0.05)
    t0 = time.perf_counter()
    p.beep()
    await asyncio.gather(*tasks)
    dur = (time.perf_counter() - t0) * 1000
    print(f'Fan-out 1.000 agentes en {dur:.3f} ms ({1000/(dur/1000)/1e3:.1f}k agentes/s)')

asyncio.run(bench())
"
```

### 2. SPMC Seqlock KUDURRU-64 Release (Property Tests & Cero Torn Reads)
Ejecución de las pruebas de propiedad y consistencia Seqlock en release en el workspace de `BABYLON-60`:
```bash
cargo test --release --test property_test -- --nocapture
```
* **Métricas Atestadas en M3 Pro:**
  - `prop_valid_writer_transitions`: OK
  - `prop_bisimulation_partitioning`: OK
  - `prop_seqlock_publish_read_consistency`: OK (Cero lecturas corruptas / torn reads)

### 2.1. Matriz de Selección de Modelos para Pruebas de Estrés
* **Estrés en Silicio / Carga Pura (CPU, Concurrencia, Cargo, Bash):**
  - **Recomendado:** `Gemini 3.8 Flash · Nivel Low`
  - **Razón:** Latencia mínima (<500 ms), transducción directa de comandos, cero sobrecarga y sin quema de cuotas.
* **Estrés Lógico / Adversarial / Formal / Fuzzing Z3:**
  - **Recomendado:** `Claude Opus 5.5` o `Gemini Pro · Nivel High`
  - **Razón:** Máxima profundidad de razonamiento para diseñar vectores de ataque, detectar condiciones de carrera y validar resoluciones del solver Z3.
* **Refactorización Concurrente de Código:**
  - **Recomendado:** `Claude Sonnet 5.5 · Nivel Medium`
  - **Razón:** Precisión sintáctica en Rust y estricta adherencia al sistema de tipos.

### 3. Saturación de P-Cores en Apple Silicon
Saturar el clúster de rendimiento con $N = 11$ hilos para auditar ausencia de estrangulamiento térmico:
```bash
python3 -c "
import concurrent.futures, time
def heavy_worker(arg):
    pid, iters = arg
    acc = 0
    for i in range(iters):
        acc = (acc + i * 3) ^ 0x5A5A
    return acc

if __name__ == '__main__':
    workers, iters = 11, 5000000
    t0 = time.perf_counter()
    with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as ex:
        list(ex.map(heavy_worker, [(i, iters) for i in range(workers)]))
    dur = time.perf_counter() - t0
    print(f'Throughput: {(workers * iters)/dur/1e6:.2f} M ops/s')
"
```

### 4. Consenso BFT y Aislamiento Bizantino (500 Agentes)
```bash
python3 /Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/tests/test_swarm_stress.py
```
* **Criterio de Aceptación:** Si un agente inyecta $\Delta X > 0$, el oráculo dispara el *Thermodynamic Override* aislando el ID defectuoso sin desbordar el contexto global.

### 5. Puente de Atestación Biométrica Touch ID (COSE_Sign1 ES256)
Ejecución del pipeline de atestación física y serialización binaria criptográfica:
```bash
cargo run --manifest-path /Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/Cargo.toml --bin poc_biometric_gate_bridge --release
```
* **Pipeline Causal:**
  1. Hash SHA-256 del manifiesto de 64 bytes (`KUDURRU-64`).
  2. Invocación a `c5_biometric_gate.swift` sobre Secure Enclave con `allowableReuseDuration = 0`.
  3. Atestación somática con Touch ID (NIST P-256 DER).
  4. Sellado de estructura CBOR `COSE_Sign1` (233 bytes TBS).

### 6. Falsación de Exterior Cognitivo en CORTEX-Persist (Anti-Mirror Harness)
Valida que el ledger criptográfico resista disrupciones no contenidas en su modelo sintáctico previo (veto a taints vacíos, Chentsov UTF-8 fuzzing, bitflips físicos y alteridad vs. eco):
```bash
pytest /Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/tests/test_cortex_exterior_cognitivo_harness.py -v
```
* **Criterio de Aceptación:** 5/5 PASSED en < 0.5s, `verify_integrity() -> False` inmediato ante bitflips en inodos, y cero aceptación de eventos huérfanos sin taint.

### 7. Pipeline Encadenado "Fast Batch" (One-Liner Execution)
Para evitar fricción de múltiples turnos y quema de cuotas, los 5 vectores no interactivos se ejecutan de forma atómica en un único subshell bash (< 6s totales en Flash Low):
```bash
python3 -c "
import sys, asyncio, time
sys.path.extend(['/Users/borjafernandezangulo/10_PROJECTS/BABYLON-60', '/Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/01_KISH_ENGINE', '/Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/02_EDIN_SWARMS'])
from agents_archi import AgentPager

async def bench():
    p = AgentPager()
    tasks = [asyncio.create_task(p.wait_for_beep()) for _ in range(1000)]
    await asyncio.sleep(0.05)
    t0 = time.perf_counter()
    p.beep()
    await asyncio.gather(*tasks)
    dur = (time.perf_counter() - t0) * 1000
    print(f'1. Fan-out 1.000 agentes: {dur:.3f} ms ({1000/(dur/1000)/1e3:.1f}k ag/s)')

asyncio.run(bench())
" && cargo test --release --test property_test -- --nocapture 2>&1 | grep "test result" && python3 -c "
import concurrent.futures, time
def heavy_worker(arg):
    pid, iters = arg
    acc = 0
    for i in range(iters):
        acc = (acc + i * 3) ^ 0x5A5A
    return acc

if __name__ == '__main__':
    workers, iters = 11, 5000000
    t0 = time.perf_counter()
    with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as ex:
        list(ex.map(heavy_worker, [(i, iters) for i in range(workers)]))
    dur = time.perf_counter() - t0
    print(f'3. P-Cores M3 Pro Throughput: {(workers * iters)/dur/1e6:.2f} M ops/s')
" && python3 tests/test_swarm_stress.py 2>&1 | tail -n 4 && pytest tests/test_cortex_exterior_cognitivo_harness.py -q
```

---

## 📊 Invariante de Salida
Toda ejecución de la suite debe generar un reporte o actualización con la tabla de latencias, throughput de operaciones y confirmación de `Torn Reads = 0` y `Delta X = 0 (o purgado)`.
