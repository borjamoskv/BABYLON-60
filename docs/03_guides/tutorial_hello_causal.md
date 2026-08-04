# Tutorial: Hola Mundo Causal en BABYLON-60

> Guía paso a paso para construir tu primer agente determinista con el DSL B60.
> Contrasta cada mecanismo con su equivalente en Python para demostrar por qué la orquestación probabilística falla.

---

## Prerequisitos

```bash
# Compilar el kernel
cargo build --release

# El binario resultante es b60_kernel
./target/release/b60_kernel --help
```

---

## Lección 1: Asignación de Tiempo Exacta (`F60` vs `f64`)

### El problema en Python

```python
# Python: 1 hora dividida entre 3
time_slice = 1.0 / 3.0  # = 0.33333333333333337
# Tras 1 millón de iteraciones de scheduling:
accumulated = sum([time_slice] * 1_000_000)
print(accumulated)  # 333333.3333333198 ← DRIFT de -0.00000135 horas
# En HFT, esto son microsegundos perdidos. En logística, paquetes mal rutados.
```

### La solución en B60

```
DUB

# Reserva un registro de tipo F60 (fracción exacta) y un divisor entero
ALLOC F60 R0
ALLOC I64 R1

# R0 = 1 hora en dominio temporal nativo
NIG R0 [ Y ] UNIT.HOUR

# R1 = 3 (divisor)
NIG R1 [ YYY ]

# División EXACTA: 1h ÷ 3 = F60(20, 1) = exactamente 0;20 = 20 minutos
BA.EXACT R0 R1

# Imprime la representación sexagesimal
SAR.B60 R0
# Output: F60(20/60) → 0;20 (EXACT, zero drift, ∀ iterations)
HALT
```

**Resultado:** `F60` mantiene `1/3` de hora como `20 minutos exactos` sin pérdida. No importa cuántas veces se itere: el resultado es siempre idéntico. El `replay_hash` nunca diverge.

Guarda este programa como `hello_causal.b60` y ejecútalo:

```bash
./target/release/b60_kernel hello_causal.b60
```

---

## Lección 2: Concurrencia Causal (`FORK` + `AWAIT` vs `asyncio`)

### El problema en Python

```python
import asyncio

results = []

async def agent_a():
    await asyncio.sleep(1)
    results.append("A completado")

async def agent_b():
    # ¿Qué pasa si B depende de que A haya terminado?
    # asyncio no garantiza orden causal, solo temporal.
    results.append("B completado")  # Puede ejecutarse ANTES que A

async def main():
    await asyncio.gather(agent_a(), agent_b())
    print(results)
    # Output posible: ["B completado", "A completado"] ← INVERSIÓN CAUSAL
    # El audit trail es inútil: no puedes probar que B dependía de A.

asyncio.run(main())
```

### La solución en B60

```
DUB
# Despacha dos agentes como corrutinas con dependencia causal explícita
FORK AGENT_A
FORK AGENT_B

# El hilo padre registra el génesis y se retira
EXECUTE "ORCHESTRATION_STARTED"
HALT

# --- AGENTE A: Produce un resultado ---
MUB AGENT_A
ALLOC TIME R0
NIG R0 [ Y ] UNIT.SECOND
AFTER R0 AGENT_A_DONE

MUB AGENT_A_DONE
# Despacha el evento al Ledger (fire-and-forget, idempotente)
EXECUTE "AGENT_A_COMPLETED"
HALT

# --- AGENTE B: DEPENDE de que A haya terminado ---
MUB AGENT_B
# AWAIT congela esta corrutina hasta que el Ledger
# emita un ACK topológico para "AGENT_A_COMPLETED"
AWAIT "AGENT_A_COMPLETED" AGENT_B_PROCEED

MUB AGENT_B_PROCEED
# Solo se ejecuta DESPUÉS de que A complete.
# Si el scheduler intentara ejecutar esto antes del ACK,
# el Motor de Auto-Falsación emitiría CRITICAL HALT.
EXECUTE "AGENT_B_COMPLETED_AFTER_A"
HALT
```

**Resultado:** El Ledger BFT registra:

```
Event 1: ORCHESTRATION_STARTED  (parents: [])
Event 2: AGENT_A_COMPLETED      (parents: [1])
Event 3: AGENT_B_COMPLETED_AFTER_A (parents: [2])  ← CAUSALIDAD GARANTIZADA
```

La inversión causal es **imposible por construcción**. Si ocurriera por un bug del scheduler, el `replay_hash` diverge y el artefacto se invalida automáticamente.

---

## Lección 3: Auto-Falsación (El Interruptor de Hombre Muerto)

### El problema en Python

```python
# Python: Un agente que divide repetidamente pierde precisión silenciosamente
value = 1.0
for _ in range(100):
    value /= 7.0
    value *= 7.0
print(value)  # 0.9999999999999983 ← CONTAMINACIÓN SILENCIOSA
# El agente sigue operando con datos corruptos. Nadie lo detecta.
# En un diagnóstico médico o un smart contract, esto es catastrófico.
```

### La solución en B60

```
DUB
# Forzamos una división recursiva para desbordar la tupla F60
ALLOC F60 R0
ALLOC I64 R1

NIG R0 [ Y ]
NIG R1 [ << ]  # 20

MUB DIV_LOOP
BA.EXACT R0 R1

# Si Base60_Scale se satura → la aritmética ya no es exacta
# El kernel intercepta automáticamente y emite:
#   CRITICAL HALT: FALSATION_ERROR: TRUNCATION
# El log completo se purga. No se emite evidencia espuria.

GIN DIV_LOOP
```

**Resultado:** El kernel se detiene antes de emitir resultados corruptos. El log dice:

```
[CRITICAL HALT] FALSATION_ERROR: F60 SCALE SATURATION at tick 47
[LOG PURGED] Artifact bundle invalidated. No export to Lean 4.
```

**La ausencia de `CRITICAL HALT` en un log es una prueba positiva** de que la ejecución mantuvo todas las invariantes.

---

## Lección 4: El Ledger como Memoria Auditable

### El problema con Vector DBs

```python
# Pinecone/Milvus: guardas un embedding
db.upsert(id="decision_42", vector=embed("Comprar 1000 acciones TSLA"))

# 3 meses después, un auditor pregunta:
# - ¿Cuándo se guardó esta decisión?  → No hay timestamp confiable
# - ¿Qué información llevó a esta decisión? → No hay linaje causal
# - ¿Se modificó después de guardarla? → No hay prueba de integridad
# CONCLUSIÓN: El audit trail es legalmente inútil.
```

### La solución en B60

Cada `EXECUTE` en B60 genera un `DAGEvent` inmutable en el Ledger:

```rust
DAGEvent {
    id: "decision_42",
    parents: ["market_analysis_41", "risk_check_40"],  // LINAJE CAUSAL
    logical_timestamp: LogicalClock(1847),
    opcode: "EXECUTE",
    payload: "BUY 1000 TSLA",
    hash: "a3f8c1...",      // SHA-256(contenido + parents)
    signature: "SIG_OK",    // Attestation criptográfica
}
```

Un auditor puede verificar:
- **Cuándo:** `logical_timestamp` + `PhysicalClock` en metadata
- **Por qué:** `parents` = cadena causal completa hasta el génesis
- **Integridad:** `hash` encadena con los padres. Modificar un evento rompe toda la cadena downstream
- **Reproducibilidad:** Re-ejecutar el mismo seed produce el mismo `replay_hash` o el artefacto se invalida

---

## Siguiente paso

Explora los programas de test incluidos en el repositorio:

| Archivo | Qué demuestra |
| :--- | :--- |
| `causal_test.b60` | FORK asíncrono + concurrencia de timers + F60 |
| `falsation_test.b60` | Suite de autodestrucción (saturación + data race) |
| `navier_stokes_hunter.b60` | Aislamiento de singularidades 3D con enjambre espacial |
| `scheduler.b60` | Swarm Clock para mitigación de procesos |

Para la especificación formal completa, ver [SPECIFICATION.md](../SPECIFICATION.md).
Para el whitepaper técnico, ver [WHITEPAPER.md](./WHITEPAPER.md).

---

<sub>BABYLON-60 · Tutorial v1.0 · Borja Moskv</sub>
