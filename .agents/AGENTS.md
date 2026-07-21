# CAM 1.0 (C5 Abstract Machine Specification)
## Normative & Informative Specification for Cognitive Runtimes

**Classification:** C5 Formal Specification  
**Status:** Living Abstract Machine Specification  
**Conformance Target:** CAM Standard / CAM Verified

---

```text
┌─────────────────────────────────────────────────────┐
│                   CAM Specification                 │
├─────────────────────────────────────────────────────┤
│  Core          Syntax · Type System · Interfaces    │  NORMATIVE
│  Semantics     Operational · Effects · Purezza      │  NORMATIVE
│  Machine       State · Transitions · Scheduler      │  NORMATIVE
│  Models        Exergy · Entropy · Cost Vectors      │  INFORMATIVE
│  Conformance   Minimal · Standard · Verified        │  NORMATIVE
└─────────────────────────────────────────────────────┘
```

---

# 1. EPISTEMIC LAYERS & TRUST INVARIANT (NORMATIVE)

The epistemic pipeline is unidirectional:

$$\text{World} \longrightarrow \text{Observation} \longrightarrow \text{Evidence} \longrightarrow \text{Inference} \longrightarrow \text{Confidence} \longrightarrow \text{Policy} \longrightarrow \text{Trust}$$

## Trust Inequality Invariant
For any agent $a$ and target assertion $x$:

$$\text{Trust}(a, x) \le \text{Policy}(a, \text{Confidence}(x))$$

A runtime MUST reject any transition where an agent attempts to grant $\text{Trust} > \text{Policy}(\text{Confidence}(x))$.

---

# 2. EPISTEMIC STATES (10-STATE SPECTRUM) (NORMATIVE)

Every node in the Knowledge Graph MUST occupy exactly one of the following 10 states:

| State | Semantic Definition |
|---|---|
| `Undefined` | Unspecified or uninitialized (Accessing produces Undefined Behaviour) |
| `Unknown` | Unexplored domain node |
| `KnownUnknown` | Identified boundary, unmeasured |
| `Measured` | Observed value with empirical variance |
| `Estimated` | Inferred value with confidence interval $[0, 1] \in \mathbb{R}$ |
| `Verified` | Independently reproduced via empirical evidence |
| `Refuted` | Falsified by contradictory evidence |
| `Superseded` | Replaced by subsequent verified version |
| `ImplDefined` | Delegated to backend implementation |
| `Impossible` | Proven logically or physically contradictory |

---

# 3. KNOWLEDGE GRAPH AS A TYPED DAG (NORMATIVE)

The Knowledge Graph $\mathcal{KG} = (\mathcal{V}, \mathcal{E})$ is a Directed Acyclic Graph:

## Node Types ($\mathcal{V}$)
`Observation`, `Evidence`, `Claim`, `Inference`, `Decision`, `Artifact`, `Incident`, `Policy`.

## Edge Types ($\mathcal{E}$)
`supports` ($E \to C$), `refutes` ($E \to C$), `derives_from` ($I \to E$), `supersedes` ($A \to A$), `depends_on` ($C \to C$), `invalidates` ($Inc \to A$), `implements` ($A \to Dec$).

## Invariants
1. $\mathcal{KG}$ MUST remain strictly acyclic. Cycle detection failure is **Undefined Behaviour**.
2. Lamport timestamps MUST strictly increase along directed edges.

---

# 4. EFFECTS ALGEBRA (NORMATIVE)

Every transition MUST declare its exact effect footprint:

```yaml
effects:
  pure:       bool                       # true if zero side effects
  knowledge:  [read, write]              # Graph mutations
  ledger:     [append]                   # Append-only ledger updates
  filesystem: [read, write, delete]
  network:    [send, recv]
  memory:     [alloc, free]
  external:   [call_api, emit_event]
```

## Undefined Behaviour Rule
Executing any effect not contained within the declared effect set $\text{Effects}_{\text{actual}} \not\subseteq \text{Effects}_{\text{declared}}$ constitutes **Undefined Behaviour (UB)** and causes immediate process termination (`SIGKILL`).

---

# 5. TRAITS & INTERFACES (NORMATIVE)

## Primitive Traits
- `Traceable`: `{ lamport_t: Int, created_at: Timestamp, created_by: AgentId }`
- `Versioned`: `{ version: SemVer, supersedes: NodeId? }`
- `Verifiable`: `{ verify() -> bool }`
- `Identifiable`: `{ id: UUIDv5 }`
- `Signed`: `{ signature: Bytes, public_key: Bytes }`
- `HashLinked`: `{ prev_hash: Hash256, entry_hash: Hash256 }`

## Standard Interfaces
- `KnowledgeStore`: Methods `get_node`, `add_node`, `add_edge`, `check_acyclic`.
- `Scheduler`: Methods `enqueue`, `next`, `can_parallel`.
- `Reasoner`: Methods `infer`, `detect_contradictions`.

---

# 6. CAPABILITY ALGEBRA (NORMATIVE)

Capabilities are compositional sets:

$$\text{CapabilitySet} = \text{Set}[\text{Capability}]$$
$$\text{Auditor} = \text{Read} \cup \text{Verify}$$
$$\text{Collector} = \text{Observe} \cup \text{Write}$$
$$\text{Analyst} = \text{Collect} \cup \text{Infer}$$

Privilege checking requires set containment:
$$\text{TransitionAllowed} \iff \text{RequiredCaps} \subseteq \text{AgentCaps}$$

---

# 7. UNDEFINED BEHAVIOUR VS IMPLEMENTATION DEFINED (NORMATIVE)

## Undefined Behaviour (UB)
- Deleting a KnowledgeNode without migration.
- Appending to Ledger with broken `prev_hash` chain.
- $\text{Trust} > \text{Policy}_{\max}(\text{Confidence})$.
- Introducing a cyclic edge into $\mathcal{KG}$.
- Executing undeclared side-effects.

## Implementation Defined (ImplDefined)
- Scheduler algorithm (FIFO, Priority Queue, Min-Latency).
- Storage engine (SQLite WAL, Postgres, S3, Memory).
- Hash primitive (Default: SHA3-256 / BLAKE3).
- Concurrency backend (Asyncio, Threads, Actors).

---

# 8. CONFORMANCE PROFILES (NORMATIVE)

- **CAM Minimal**: Core Syntax + Epistemic States + KnowledgeStore Interface.
- **CAM Standard**: Minimal + Effects Algebra + Purity Scheduler.
- **CAM Enterprise**: Standard + Cryptographic Signatures + Ledger Audit.
- **CAM Verified**: Enterprise + Formal Proofs (Lean4 / Coq).

---

# 9. ABSTRACT MACHINE STATE (NORMATIVE)

$$\text{CAM\_State} = \langle \mathcal{KG}, \text{Ledger}, \text{Queue}, \text{Caps}, \text{Clock}, \text{EffectsLog}, \text{ConformanceProfile} \rangle$$

Atomic Transition Step:
$$\text{step}: \text{CAM\_State} \times \text{Transition} \longrightarrow \text{CAM\_State}' \times \text{Effects}$$
