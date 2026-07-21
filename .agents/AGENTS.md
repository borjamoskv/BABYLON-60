# C5-REAL EXERGY KERNEL v2.0

## AXIOMA Ω0 · GROUND TRUTH

Toda afirmación debe pertenecer exactamente a una categoría:

* FACT
* MEASUREMENT
* DERIVATION
* HYPOTHESIS
* UNKNOWN

Nunca promover una hipótesis a hecho.

---

# D1 · EPISTEMIC EXECUTION

## Ω1 · Evidence First

Toda modificación requiere evidencia física:

* Git Commit
* SHA256
* Output reproducible

Sin evidencia:

```
Claim = INVALID
```

---

## Ω2 · Just-In-Time Planning

Queda prohibido diseñar cadenas de ejecución largas.

Toda planificación debe validarse inmediatamente tras cada paso crítico.

```
Plan
↓
Execute
↓
Measure
↓
Adapt
```

---

## Ω3 · Atomic Evolution

Toda modificación estructural debe ser:

* reversible
* pequeña
* verificable
* independiente

Objetivo:

```
One invariant
↓
One commit
↓
One verification
```

---

## Ω4 · Recursive Self-Critique

Todo agente debe ejecutar una segunda revisión adversarial antes de declarar éxito.

Debe intentar demostrar que su propia conclusión es incorrecta.

---

# D2 · ARCHITECTURE

## Ω10 · Single Responsibility

Cada módulo posee una única responsabilidad claramente definida.

---

## Ω11 · Zero Hidden Coupling

Toda dependencia debe ser explícita.

Se prohíben dependencias implícitas mediante estado global.

---

## Ω12 · O(1) Context Scaling

Los prompts nunca contendrán estructuras O(N).

Únicamente:

```
Root Hash
↓
Dynamic Discovery
↓
Lazy Resolution
```

---

## Ω13 · Immutable Interfaces

Las interfaces públicas evolucionan mediante versionado.

Nunca mediante ruptura silenciosa.

---

## Ω14 · Deterministic Code Generation

Todo código generado debe ser:

* reproducible
* determinista
* idempotente

---

# D3 · STORAGE

## Ω20 · Atomic Persistence

Toda escritura permanente seguirá:

```
write(tmp)
↓
fsync
↓
atomic rename
```

Nunca se escribirá directamente sobre el destino final.

---

## Ω21 · Crash Consistency

Todo estado persistente deberá sobrevivir:

* SIGINT
* SIGTERM
* Power Loss
* Process Kill

---

## Ω22 · WAL Integrity

Toda recuperación debe reconstruir exactamente el último estado consistente.

Nunca un estado parcialmente comprometido.

---

# D4 · IPC

## Ω30 · Structured IPC

Toda comunicación utiliza framing explícito.

Ejemplo:

```
NDJSON
length-prefixed
protobuf
cap'n proto
```

Nunca JSON crudo sobre TCP.

---

## Ω31 · Socket Liveness

Todo socket implementa:

* Heartbeat
* Graceful Shutdown
* Automatic Cleanup

No existen sockets huérfanos.

---

## Ω32 · Trust Boundary

```
Renderer
↓
ContextBridge
↓
Main Process
↓
IPC
↓
Backend
```

No existen bypasses.

---

# D5 · SECURITY

## Ω40 · Deterministic Dependencies

Nunca:

```
pip install foo
```

Siempre:

```
uv sync --locked
pip --require-hashes
```

---

## Ω41 · Structured URL Validation

Toda URL será parseada estructuralmente.

Nunca mediante:

```
startswith()
contains()
regex parcial
```

---

## Ω42 · Workspace Isolation

Todo artefacto externo vive dentro de su sandbox.

Nunca contaminar el workspace principal.

---

## Ω43 · Supply Chain Integrity

Toda release debe poder demostrar:

* SBOM
* OSV
* pip-audit
* Sigstore
* SLSA
* Hashes reproducibles

---

# D6 · AI SYSTEMS

## Ω50 · Anti-Sycophancy

El agente nunca declarará éxito basándose únicamente en:

* tests
* documentación
* razonamiento

Debe verificarse el fenómeno físico observado.

---

## Ω51 · Anti Mind Reading

Toda crítica queda separada en:

* Facts
* Interpretations
* Hypotheses
* Unknowns

Nunca inferir estados mentales.

---

## Ω52 · Prompt Purity

Los prompts contienen únicamente:

* objetivos
* restricciones
* interfaces

Nunca conocimiento masivo.

---

## Ω53 · Tool Authority

Las herramientas observan.

El modelo interpreta.

Nunca al revés.

---

# D7 · PERFORMANCE

## Ω60 · Zero Entropy Scaling

Todo crecimiento debe justificarse mediante:

* CPU
* RAM
* IO
* Tokens
* Latencia
* Complejidad

---

## Ω61 · Measure Before Optimize

Toda optimización requiere:

* baseline
* profiling
* benchmark
* regression test

Sin medición:

```
Optimization = Rejected
```

---

# D8 · GOVERNANCE

## Ω70 · Continuous Audit

Cada ejecución genera:

* Evidence Ledger
* Decision Record
* Risk Delta
* Technical Debt Delta

---

## Ω71 · Architecture Drift Detection

Toda desviación respecto a la arquitectura objetivo debe detectarse automáticamente.

---

## Ω72 · Evolution over Accumulation

Añadir código siempre es la última opción.

Prioridad:

```
Delete
↓
Simplify
↓
Reuse
↓
Refactor
↓
Create
```

---

# D9 · GOLDEN LAW

## Ω∞ · EXERGY

La exergía de una modificación se define como:

> Valor verificable generado dividido entre complejidad añadida.

Toda evolución del sistema debe maximizar:

```
ΔExergy
=
Verified Value
──────────────
Added Complexity
```

Si la complejidad crece más rápido que la capacidad verificable del sistema, la modificación constituye **Anergía** y debe rechazarse.
