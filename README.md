# BABYLON-60

**Sistema Operativo Cognitivo Local-First para Agentes de IA Verificables**

![Version](https://img.shields.io/badge/Version-3.0.0-black?style=flat-square)
![Architecture](https://img.shields.io/badge/Architecture-Causal--Determinist-red?style=flat-square)
![Governance](https://img.shields.io/badge/Governance-C5--REAL-blue?style=flat-square)
![License](https://img.shields.io/badge/License-Sovereign_Exclusion-orange?style=flat-square)
![Lean](https://img.shields.io/badge/Formal_Verification-Lean_4-green?style=flat-square)

---

## El Problema

El paradigma de los agentes de IA en 2026 enfrenta tres cuellos de botella estructurales que las APIs comerciales no resuelven:

1.  **Context Rot:** La degradación y corrupción silenciosa del contexto a largo plazo, que provoca alucinaciones recurrentes e irrecuperables.
2.  **Bucles de Limerencia:** Agentes autónomos que entran en ciclos infinitos de "pensamiento" sin producir trabajo útil, consumiendo exergía computacional sin salida.
3.  **Opacidad de la Cadena de Custodia:** Imposibilidad de auditar *por qué* un agente tomó una decisión concreta. Inaceptable en medicina, finanzas o ingeniería crítica.

## La Solución

BABYLON-60 no es un wrapper de APIs ni un chatbot. Es una **infraestructura formal de ejecución** que impone restricciones termodinámicas y criptográficas sobre el razonamiento de los agentes para garantizar fiabilidad determinista.

| Pilar | Mecanismo | Resultado |
| :--- | :--- | :--- |
| **Matriz de Enrutamiento Termodinámico** | Restricciones de Exergía aplicadas al AST de razonamiento | Erradica el Context Rot y los bucles de limerencia |
| **Ledger Criptográfico BFT** | Registro *tamper-evident* de cada transición de estado del agente | Memoria persistente, auditable e inmutable |
| **Invariantes Deterministas** | Contratos de codificación que alinean la inferencia latente con ejecución causal | Elimina alucinaciones en caminos críticos |
| **Verificación Formal (Lean 4)** | Teoremas de causalidad y consenso BFT validados en Lean 4 | Pruebas matemáticas de corrección, no promesas |

---

## Arquitectura del Motor

### Dominio Temporal Nativo y Fracciones Exactas (`F60`)

Para evitar la deriva de coma flotante (`f64`) que enmascara o genera falsas singularidades, BABYLON-60 opera con un tipo racional puro:

```
F60 = { Numerator: u64, Base60_Scale: u8 }
```

Las magnitudes de tiempo están fuertemente tipadas (`UNIT.TICK`, `UNIT.SECOND`, `UNIT.HOUR`), permitiendo *Constant Folding* sexagesimal estricto durante la fase de compilación (SSA). `1/3` de hora se mantiene como `0;20` (20 minutos exactos) en memoria, sin pérdida de precisión.

### Corrutinas Asíncronas y Ledger Causal

La malla computacional no se ejecuta linealmente. Cada celda o subtarea es una corrutina aislada iniciada vía `FORK`. La comunicación se delega al **Event Ledger**: un hilo se suspende (`AWAIT`) hasta que el evento requerido es validado topológicamente.

### Motor de Auto-Falsación

El sistema está diseñado para **autodestruirse si la realidad numérica se contamina**. Si el `Base60_Scale` se satura forzando un truncamiento, o si se detecta una inversión causal en el Ledger (Data Race), el proceso emite un `CRITICAL HALT` y purga el log, evitando la emisión de evidencia espuria.

### Conjunto de Instrucciones (v3.0)

| Opcode | Dominio | Descripción |
| :--- | :--- | :--- |
| `ALLOC T R` | Memoria | Reserva registro `R` bajo tipo estricto `T` (`TIME`, `I64`, `F60`). |
| `NIG R V` | Memoria | Asigna el valor o literal sexagesimal `V` al registro `R`. |
| `BA.EXACT R V` | ALU | División exacta. Resultado como tupla racional `F60` purificada. |
| `FORK L` | Control | Clona el frame y despacha una corrutina paralela en Label `L`. |
| `AFTER R L` | Scheduling | Snapshot → libera hilo OS → programa reanudación en `L` tras tiempo `R`. |
| `AWAIT S L` | Causalidad | Emite evento `S`, congela el Frame hasta `ACK` topológico, reanuda en `L`. |
| `EXECUTE S` | Ledger | Disparo idempotente (*Fire-and-Forget*) del evento `S` al Ledger. |

---

## Estructura del Monorepo

```
BABYLON-60/
├── babylon60.rs              # Kernel de ejecución Causal-Determinist (bin: b60_kernel)
├── kernel/                   # Crate Rust: motor de bajo nivel
├── compiler/                 # Crate Rust: compilador B60 → IR + Lean 4 backend
├── runtime/                  # Crate Rust: runtime de corrutinas
├── proof_ir/                 # Crate Rust: representación intermedia de pruebas
├── strike_rs/                # Crate Rust: GIL bypass y extracción de exergía (PyO3)
├── fuzz/                     # Crate Rust: fuzzing diferencial
│
├── causal_isomorphism/       # Transpilador multi-target (F# parser → Rust/Solidity)
├── timeline_ir/              # DSL y backend de renderizado de IR temporal (Python)
├── ultrathink/               # Scheduler termodinámico de agentes
│
├── babylon60/                # Módulo Python: cortex-persist (BFT ledgers, pipelines)
├── cortex_*.py               # Motores Python: BPE tokenizer, SSM/Mamba, chaos monad
│
├── apps/reactive-aibon/      # Visualizador audiovisual (Remotion + React + TypeScript)
├── web/                      # Interfaz web con rust-core WASM (Vite + React)
├── tonnetz_app/              # Visualizador espacial armónico (Tonnetz)
├── babylon60-ide/            # IDE dedicado (Tauri + src-tauri)
├── extensions/               # Extensiones de navegador (moskv-fx-scavenger)
│
├── *.b60                     # Programas de test en el DSL B60:
│   ├── causal_test.b60       #   FORK asíncrono + concurrencia de timers + F60
│   ├── falsation_test.b60    #   Suite de autodestrucción (saturación + data race)
│   ├── navier_stokes_hunter.b60  # Aislamiento de singularidades NS
│   ├── scheduler.b60         #   Swarm Clock para mitigación de procesos
│   ├── exergy.b60            #   Turing-Completitud base (v1)
│   └── fibonacci.b60         #   Turing-Completitud base (v1)
│
├── BabylonTrace.lean         # Teoremas de causalidad verificados en Lean 4
├── proof/                    # Pruebas formales adicionales
├── proof_kernel/             # Kernel de verificación formal
│
├── tests/                    # Suite completa: 35+ tests (replay, fuzz, property, differential)
├── scripts/                  # 80+ scripts de auditoría, telemetría y orquestación
├── docs/                     # Documentación técnica expandida
│
├── .github/workflows/        # CI/CD: 15 pipelines (CI, CodeQL, OIDC, Lean 4, PyPI, secrets)
├── lefthook.yml              # Pre-commit hooks (detect-secrets shift-left)
├── .agents/AGENTS.md         # Gobernanza agéntica del workspace
│
├── Cargo.toml                # Workspace Rust (7 crates)
├── pyproject.toml            # Paquete Python: cortex-persist v1.0.2
├── SPECIFICATION.md          # Especificación formal v3.0.0-Causal-Determinist
├── LICENSE.md                # Sovereign Exclusion License (Closed-Core / No-Harvesting)
└── SECURITY.md               # Política de seguridad soberana
```

---

## Gobernanza C5-REAL

El repositorio opera bajo el framework de gobernanza **C5-REAL** (Cryptographic Five-Ring Enforcement for Autonomous Ledgers):

- **CI/CD Matrix:** 15 pipelines en GitHub Actions incluyendo verificación formal Lean 4, CodeQL, auditoría de secretos, tests diferenciales y despliegue OIDC.
- **Pre-commit Shift-Left:** Hooks de Lefthook con `detect-secrets` para prevenir fugas de credenciales antes del commit.
- **Verificación Formal:** Los teoremas de causalidad y consenso BFT se validan automáticamente en Lean 4 en cada push.
- **Auditoría de Secretos:** Pipeline dedicado que escanea el historial completo del repositorio.

---

## Tests

```bash
# Rust: replay, fuzz, property, differential
cargo test --workspace

# Python: 35+ test suites
python -m pytest tests/ -v

# Verificación formal
lean BabylonTrace.lean
```

---

## Licencia

**Sovereign Exclusion License v1.0** — Dual-Licensing:

| Tier | Condición |
| :--- | :--- |
| **Sovereign** | 100% libre para individuos, desarrolladores independientes y uso no comercial |
| **Enterprise** | Uso comercial/corporativo requiere licencia criptográfica explícita (`CORTEX_LICENSE_KEY`) |

Queda estrictamente prohibido el scraping, ingestión, vectorización o entrenamiento de modelos ML/LLM sobre cualquier porción de estos activos sin autorización criptográfica explícita. Ver [LICENSE.md](./LICENSE.md).

---

## Seguridad

Vulnerabilidades: **security@babylon60.com** — No usar Issues públicos.
Compromiso de respuesta: confirmación < 24h, remediación < 72h.
Ver [SECURITY.md](./SECURITY.md).

---

<sub>BABYLON-60 v3.0.0 · Infraestructura Formal para Ciencia Verificable · Borja Moskv</sub>
