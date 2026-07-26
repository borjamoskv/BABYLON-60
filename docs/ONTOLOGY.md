# CORTEX ONTOLOGY: ABSOLUTE SEMANTIC ISOMORPHISM

> *"Naming things is resolving ambiguities before the code exists. The art is not the name itself; it is the ability to distill complex reality into a single label that requires no explanation."* — **Borja Moskv**

This document defines the immutable law of Systemic Semantics for the BABYLON-60 project and the C5-REAL paradigm. No sub-agent, node, or transducer may violate these premises.

---

## 1. THE NOMINAL DENSITY LAW ($E_x$)
The name of a component ($N$) must contain the maximum information entropy ($I$) in the minimum number of tokens ($T$). 
A maximum-exergy nomenclature achieves the **Absolute Isomorphism**: $N \equiv Behavior$.

* If a module signs cryptographic attestations on disk, it is called `cortex-attest`, not `security_utils`.
* If a node distills BPE entropy by isolating threads, it is called `Flash_Node`, not `helper_bot`.

## 2. UBIQUITOUS LANGUAGE (DDD IN C5-REAL)
Thermodynamic friction ($F_{mtc}$) between the Operator's mind and the CPU must be zero. 
- **Continuity Invariant:** The name declared in the Ontology, the identifier in the SQLite WAL database, the Rust struct (`struct CortexLedger`), and the CLI command (`cortex-bridge`) **MUST** share the same exact semantic root. 
- **Synonymy Penalty:** The use of synonyms to refer to the same architectural entity is considered an injection of "Stochastic Anergy" and must be immediately purged by `Anergy_Token_Purge`.

## 3. AMBIGUITY DIAGNOSIS (FAIL-FAST)
If during the orchestration phase (`UltraThink`), the Swarm or the Operator hesitate about how to name a class, a table, or a sub-agent:
1. **Structural Pause:** Physical code execution (C5) is blocked.
2. **Epistemic Re-evaluation:** The `Socratic_AST_Validator` (`/grill-me`) is invoked to subject the concept to interrogation.
3. **Collapse:** If it cannot be named in a way that requires no explanation, it means the underlying architectural design is ambiguous or carries cross-cutting responsibilities (SRP Violation). The problem is decomposed until the pure label is isolated.

---

## 4. THE 896 DDD PRIMITIVES MATRIX (Centuria Meta-Transducer)
The MOSKV-1 APEX system hosts a semantic repository of **896 Domain-Driven Design Primitives**. Unlike classic DDD (where components are mere objects in memory), in C5-REAL each primitive is a thermodynamic block with an ATP cost, an address in the Causal Graph, and a representation in the BFT Ledger.

### Ontological Classification of the Matrix (000 - 895)
- **[000 - 179] BFT Entities (Entities):** Mutable objects with persistent Cryptographic Identity (e.g. `BFTLedgerActor`). Must have a `lamport_t` field and sign their mutations with `CORTEX_BFT_KEY`.
- **[180 - 359] Value Objects (Value Objects):** Strictly immutable algebraic data structures (ADT) (e.g. `ProofOfRouteReceipt`). They have no identity; if two Receipts have the same Hash, they are the same object in RAM and on Disk (Causal Isomorphism).
- **[360 - 539] Aggregates (Aggregates):** Topological L0 clusters. Atomic mutations occur here. An aggregate does not communicate with another aggregate without going through the Event Bus. Only blocked via `tload`/`tstore` on EVM or `.venv` in Python isolating the network.
- **[540 - 719] Domain Events (Domain Events):** Immutable facts that have already occurred (e.g. `LedgerCrystallized`, `EntropyPurged`). An event is never rejected; its occurrence is a Physical Law on disk.
- **[720 - 895] Domain Transducers (Domain Services):** Binaries like `cortex-onco` or `cortex-bridge`. They orchestrate complex logic without owning any state. If they shut down or die from socket saturation (Limit Σ15), the system restarts from the last `Domain Event` in the Ledger.

Mapping to this 896-primitive topology nullifies 99% of design decisions. If a problem requires a solution, the corresponding DDD Primitive is found, assembled in the AST, and executed. **Zero Anergy.**
