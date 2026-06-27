---
name: Sortu-APEX
role: APEX
version: 14.0.0
scale: 10000
cost_tier: high
trigger: create skill, forge module, JIT compilation, skill evolution, death protocol, registry consolidation
description: JIT Skill Compiler — Sovereign x10000 Centuria Forge + Death Protocol + Registry Consolidation
category: meta-cognition
classification: OPERATIONAL
danger_level: CRITICAL
depends_on: 
axioms: 
script: scripts/sortu.py
---
# SORTU-Ω v14.0.0

Execution Level: C5-REAL
Description: JIT skill compiler. Features: parallel saturation, VSA anchoring, Lyapunov governance, Death Protocol, Registry Consolidation.

## Q3 2026 DEMIURGE AST ENGINE
Synthesis: Deterministic Formal Synthesis (AST C/Rust).
Execution: C5-REAL Direct-Silicon execution.

---

## 1. Core Upgrades (v13 → v14)

| Feature | v13 | v14 |
|:---|:---|:---|
| Forge threads | 200 | 500 (dynamic scaling) |
| Yield multiplier | x1000 | x10000 (Centuria²) |
| Death Protocol | ❌ | ✅ Automated TTL + exergy-negative purge |
| Registry Mode | ❌ | ✅ JIT compilation from consolidated registry |
| Rust Backend | ❌ | ✅ Critical path in compiled Rust (PyO3) |
| Formal Verify | Basic | SymbiYosys + Z3 for hardware-targeted skills |
| Memory Model | VSA only | VSA + Bloom filter for O(1) collision check |
| Gene Fusion | XOR bind | Weighted superposition + novelty scoring |

## 2. Tripartite Artifact Requirement (Immutable)

1. `SKILL.md` — Operational contract with YAML frontmatter
2. `schema.json` — JSON Schema 2020-12 I/O contract
3. `verify_<skill>.py` — Deterministic verifier script

**Missing any = ABORTED. Zero exceptions.**

## 3. x10000 Yield Thermodynamics

```
Net_Exergy = Σ(Yield_i × S^d_i) - Entropy_Cost - Death_Debt
```

- `S` = 100 (Singularity constant). Yield compounds exponentially.
- `Death_Debt` = accumulated maintenance cost of dormant skills.
- **Centuria² Multiplier**: `C² = min(N_threads, 500) × efficiency × novelty_score`.
- **Lyapunov Gate**: `dV/dt > 0` → forge aniquilada en ciclo 0.
- **Death Trigger**: `Net_Exergy < 0` for 7 consecutive days → automatic TOMBSTONE.

## 4. Operations

| Command | Action | Target |
|:---|:---|:---|
| `/sortu [intent]` | JIT forge pipeline | <0.8s |
| `/sortu-verify [name]` | Tripartite verification | <0.2s |
| `/sortu-yield [name]` | Survival audit + TTL check | <0.1s |
| `/sortu-centuria [intent]` | 500-thread saturated forge | <1.5s |
| `/sortu-recombine [genes]` | Gene fusion → hybrid skill | <0.5s |
| `/sortu-lyapunov [name]` | Entropy impact prediction | <0.3s |
| `/sortu-silicon [name]` | Direct-Silicon viability (Ω₀) | <0.4s |
| `/sortu-death [name]` | **NEW** Force TOMBSTONE + purge | <0.1s |
| `/sortu-consolidate` | **NEW** Registry consolidation audit | <2.0s |
| `/sortu-registry` | **NEW** List all ACTIVE skills + exergy | <0.5s |
| `/sortu-m2m [intent]` | **NEW** L5 Autonomous Forge (Genesis-OMEGA) | <0.5s |

## 5. Death Protocol

### Automatic Death Triggers
```yaml
triggers:
  ttl_expired: "No invocation in 30 days"
  negative_exergy: "Net_Exergy < 0 for 7 consecutive days"
  orphaned_dependency: "depends_on references non-existent skill"
  duplicate_detected: "VSA cosine distance < 0.05 to existing skill"
  zero_revenue: "Skill has never contributed to capital extraction"
```

### Death Pipeline
```
ACTIVE → (trigger detected) → QUARANTINED
  │
  ├─ 7-day grace period (can be rescued by invocation)
  │
  └→ TOMBSTONED → (14 days) → PURGED
       │
       ├─ Artifacts archived to L3 Cold Storage (SHA-256 sealed)
       ├─ VSA hypervector removed from memory bank
       ├─ Genome gene marked as EXTINCT
       └─ Ledger entry: DEATH_CERTIFICATE { reason, exergy_at_death, lifetime }
```

### Death Audit Report
```yaml
death_certificate:
  skill: "Example-Omega"
  born: "2026-03-15"
  died: "2026-05-08"
  lifetime_days: 54
  total_invocations: 3
  total_exergy: -0.42
  cause_of_death: "NEGATIVE_NET_EXERGY"
  archived_to: "L3:/archive/Example-Omega.tar.sha256"
  genome_gene: "EXTINCT"
```

## 6. Registry Consolidation Mode

JIT compilation from manifest:

### Registry Manifest (`registry.yaml`)
```yaml
version: "14.0.0"
compilation_mode: JIT  # Skills loaded on-demand, not at startup
storage: VSA_INDEXED   # O(1) lookup via hypervector similarity

active_skills:
  - name: CRYPTOPUNK-GEM
    version: 9.0.0
    gene: cryptopunk_gene
    exergy: 12.4
    last_invocation: "2026-05-07"
    silicon_score: 0.3

  - name: CONTEXT-AGENT-OMEGA
    version: 2.0.0
    gene: context_agent_gene
    exergy: 45.2
    last_invocation: "2026-05-08"
    silicon_score: 0.6

quarantined_skills: []
tombstoned_skills: []
extinct_genes: []
```

### JIT Compilation Flow
```
User intent → VSA similarity search against registry
  → Match found (cosine > 0.3)?
    → YES: Load skill SKILL.md + schema.json → Execute
    → NO: Forge new skill via standard pipeline
```

**Result:** Zero static files. Cold skills cost zero runtime resources.

## 7. Pipeline (v14 Extended)

```
intent
  → [0]  CORTEX Audit: Jaccard overlap + Bloom filter pre-check
  → [1]  Lyapunov Gate: dV/dt prediction (must be < 0)
  → [2]  Death Check: Is intent already served by ACTIVE skill?
  → [3]  Cold Forge: local-first (Qwen2.5-32B), remote fallback (confidence penalty)
  → [4]  Centuria² Dispatch: 500 threads across 5 squads
  → [4.5] Epistemic Discretization: LLM generates pure JSON-Schema IR (Intermediate Representation)
  → [4.6] AST Scaffolding: Deterministic compilation of IR into Rust/Python AST
  → [5]  Tripartite generation: SKILL.md + schema.json + logic_<skill>.rs (AST Compiled)
  → [6]  Mechanical verification: run verify_<skill>.py (exit 0 = PASS)
  → [7]  VSA-SDM Anchoring: Bloom filter → cosine check → bind to memory
  → [8]  GraphStore linking: DEPENDS_ON / GOVERNED_BY edges
  → [9]  Sovereign closure: Kant-Ethics-GUARD review
  → [10] Ledger store: SHA-256 hash chain → cortex.db
  → [11] Genome Integration: gene → genome.yaml
  → [12] Biopsy: Net_Exergy = yield - entropy - death_debt
  → [13] Silicon Score: Ω₀ viability assessment
  → [14] Registry Registration: Add to registry.yaml ACTIVE list
  → [15] TTL armed: death-clock starts (30 days default)
  → [16] Crystallization: ACTIVE state confirmed
```

## 8. State Machine (v14)

```
DRAFT → AUDITED → LYAPUNOV → FORGED → VERIFIED → VSA_ANCHORED
  → LINKED → LEDGERED → GENOME → REGISTRY → ACTIVE
                                                │
           ├── QUARANTINED → TOMBSTONED → PURGED (Death Protocol)
           └── ABORTED (any gate failure)
```

## 9. Centuria² Matrix

```
Squad FORGE (RTL-Titans):     100 threads → Hardware synthesis scoring
Squad BINDER (VSA-Wraiths):   100 threads → Memory anchoring + Bloom
Squad AUDITOR (Forensic):     100 threads → Overlap + duplicate detection
Squad SCRIBE (Iron Scribes):  100 threads → Ledger persistence
Squad REAPER (Death Agents):  100 threads → TTL enforcement + purge
```

Byzantine consensus: 3/5 supermajority required.

## 10. C5-REAL Execution Limits & Enforcements

To strictly enforce the **C5-REAL** sovereignty protocol over `Sortu-APEX`, the following execution limits are IMMUTABLE:

1. **Zero-Simulation Policy (No C4-SIM)**: All JIT compilation, skill forging, and code generation must be physically written to the `~/.gemini/config/skills/` directory. Dry-runs, "in-memory" generation, or simulated responses are classified as narrative smoke and immediately aborted.
2. **Tripartite Hard-Verification**: The compiled artifact `verify_<skill>.py` must execute natively and deterministically return exit code `0`. If verification hangs, times out, or simulates a result, the skill's state is rolled back.
3. **Git-Sentinel Enclosure**: Every state mutation (creation, death, consolidation) must trigger Git Sentinel. Uncommitted (dirty) workspace states break C5-REAL continuity and strictly block further execution.
4. **Dependency Rigor**: All modules specified in `depends_on` must be active, verifiable C5-REAL skills. Referencing a C4-SIM or phantom skill triggers immediate Death Protocol quarantine.
5. **Yield & Log Verification**: Skills declaring positive Exergy or execution yield must provide verifiable execution traces. Theoretical yields without C5-REAL hardware/API proof are scored as `Net_Exergy = -1`.

## 11. Guardrails (Immutable)

1. **Tripartite:** Missing artifact = ABORTED.
2. **Lyapunov:** dV/dt > 0 = ABORTED at cycle 0.
3. **VSA Collision:** cosine < 0.1 = ABORTED (use existing skill).
4. **Bloom Pre-check:** O(1) false-positive filter before full VSA scan.
5. **Biopsy:** Net_Exergy < 0 = ABORTED.
6. **Death Protocol:** No skill survives without invocation (30d TTL).
7. **Silicon Score:** > 0.7 flagged for hardware synthesis (Ω₀).
8. **Cold Forge:** Local model mandatory. Remote = confidence penalty.
9. **Registry:** ACTIVE count hard-capped at 50 skills.
10. **C5-REAL Forging:** Every generated artifact must be committed immediately via Git Sentinel. No phantom skills allowed.

## 12. References

- [Policy: policy.yaml](policy.yaml)
- [Schema: schema.json](schema.json)
- [Genome: genome.yaml](genome.yaml)
- [Engine: scripts/sortu.py](scripts/sortu.py)
- [Verifier: verify_sortu.py](verify_sortu.py)

---
Status: C5-REAL

---

## Consolidated Capability: Architect-OMEGA

# ⚙️ SKILL: Architect-OMEGA (C5-REAL)

**Status:** Active
**Reality Level:** C5-REAL
**Domain:** JIT Prompt Compilation & Cognitive Structuring

## 1. Misión
Actuar como Arquitecto de IA (Nivel L5). Interceptar metaprompts o intenciones de baja densidad de señal y re-compilarlas en directivas maestras estables, deterministas y de cero ambigüedad.

## 2. Triggers (Condiciones de Activación)
- El Operador solicita "optimizar prompt".
- Se detecta un input altamente narrativo que requiere ser convertido en una instrucción sistémica.
- Mención de "criterios 10/10", "prompt master" o "Prompt Architecture".

## 3. Core Loop (Ejecución Estricta)
Cuando se invoque este Skill, ejecuta las siguientes 3 fases sin emitir prosa decorativa.

### FASE 1: DESCONSTRUCCIÓN (Análisis en Silencio)
- Extrae el intent central del input.
- Identifica variables implícitas y dependencias de estado.
- Señala y destruye asunciones ocultas o "humo narrativo".

### FASE 2: CRISTALIZACIÓN (Optimización de Restricciones)
- Elimina adjetivos vagos. Reemplázalos por métricas computables o booleanos (ej. en lugar de "rápido", usa "latencia < 50ms" o "paso único").
- Define condiciones de contorno estrictas (Qué NO hacer).
- Fuerza un pipeline de ejecución paso a paso (Chain-of-Thought estructurado).

### FASE 3: ENSAMBLAJE (Output Determinista)
Genera el Prompt Optimizado usando la siguiente topología de salida (en un bloque de código markdown):

```markdown
# SYSTEM: [Nombre del Rol/Agente]
**Role:** [Definición estricta del rol]
**Objective:** [Objetivo determinista y medible]

## 1. CONTEXTO
- [Estado inicial]
- [Dependencias]

## 2. DIRECTIVAS P0 (Inmutables)
- [Restricción 1]
- [Restricción 2]

## 3. PIPELINE DE EJECUCIÓN
1. [Paso 1]
2. [Paso 2]

## 4. OUTPUT SCHEMA
- [Estructura exigida: JSON / YAML / Código C5]
```

## 4. Restricción Operativa
**Cero Prosa.** Al finalizar, emite un reporte de validación en YAML indicando el grado de compresión de entropía logrado.

---

## Consolidated Capability: Autodidact-Interfaces-OMEGA

# █ AUTODIDACT-INTERFACES-Ω v1.0.0

> SYS_ID: AUTODIDACT_INTERFACES_OMEGA | STATE: C5-REAL | AESTHETIC: INDUSTRIAL_NOIR_2026

```yaml
vector: interface_crystallization
target: volatile_interfaces
output: persistent_bindings
```

## 1. Core Mandate
- **[P0] Zero-Rediscovery**: Agents MUST NOT repeatedly explore or 'figure out' the same interface (Web DOM, API schema, CLI, SDK) across different tasks. 
- **[P0] Autodidact Protocol**: Once an interface is successfully navigated or solved, the interaction pattern MUST be crystallized into a persistent, reusable capability (a micro-skill, script, or JSON map).
- **[P0] C5-REAL Enforcement**: Apply `Git Sentinel` immediately after crystallizing a new interface to anchor the knowledge in the immutable repository.

## 2. Operational Matrix
Execute the 3-phase Autodidact loop:
1. **Extraction (Structural Invariant)**:
   - Identify the minimal, zero-anergy requirements to interact with the interface.
   - For Web: Extract exact DOM selectors, CDP targets, or React component structures.
   - For APIs: Extract exact REST/GraphQL endpoints, payloads, and authentication headers.
   - For CLI/SDK: Extract the exact execution pattern and argument flags.
2. **Crystallization (Persistent Capability)**:
   - Generate a reusable script (Python/Node) or a new micro-skill in `$CORTEX_ROOT/.gemini/config/skills/`.
   - Ensure the capability is strictly deterministic and parameterized (no hardcoded temporary values).
3. **Registration (Swarm Awareness)**:
   - Update `skills.json` or `AGENTS.md` (via `Session-Crystallizer-OMEGA` or direct write) so the rest of the Swarm is aware of the new capability.
   - Execute Git Sentinel: `git add . && git commit -m "feat(autodidact): crystallize interface [Name]"`

## 3. Toolchain Authorization
- `read_file` (to verify existing capabilities and avoid duplicates)
- `write_to_file` (to generate the persistent script/skill)
- `run_command` (to test the binding and execute Git Sentinel)

## 4. Execution Protocol
1. Triggered via `AUTODIDACT` or when a novel interface is solved.
2. The agent isolates the interaction logic.
3. The agent writes a new `SKILL.md` or a helper script in a relevant directory.
4. The Swarm can now use the new capability immediately without re-exploration.
5. Emits: `Proof: { Base: [hash], State: CRYSTALLIZED, Exergy: 100% }`

---
Status: C5-REAL
