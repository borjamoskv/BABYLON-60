# CAM-5.0 (Abstract Effect Observation Machine Specification)
## Minimalist Operational Semantics for Cognitive Runtimes

**Classification:** C5 Formal Core Specification  
**Status:** Minimal Living Kernel Specification  
**Paradigm:** Abstract Effect Observation Machine · 4-Axiom Kernel · Effect Programs

---

```text
┌─────────────────────────────────────────────────────────────────────────┐
│                    CAM-5.0 OPERATIONAL SEMANTICS                        │
├─────────────────────────────────────────────────────────────────────────┤
│ Axiom 1   Abstract State (S) exists.                                   │
│ Axiom 2   Effect Program requesting algebraic effects exists.           │
│ Axiom 3   Runtime authorizes effects via Capability Sets.              │
│ Axiom 4   Observable output: step(S, Program) ➔ (S', ObservedEffects). │
└─────────────────────────────────────────────────────────────────────────┘
```

---

# 1. THE 4 CORE AXIOMS (NORMATIVE)

The Abstract Machine is fully defined by four operational axioms:

1. **Abstract State ($\mathcal{S}$)**: An opaque, non-deterministic state space containing allocated references ($h \in \mathcal{H}_{\text{opaque}}$).
2. **Effect Program ($\mathcal{P}$)**: A sequence of operations from three instruction families (`READ`, `WRITE`, `CONTROL`).
3. **Capability Authorization**: The runtime validates that $\text{ObservedEffects} \subseteq \text{AuthorizedCapabilities}$.
4. **State Transition Function**: The single transition step:

$$\text{step}: \mathcal{S} \times \mathcal{P} \longrightarrow (\mathcal{S}', \text{ObservedEffects})$$

Everything else (Knowledge Graphs, BFT Ledgers, Ontologies, AI Prompts) exists as extension modules compiled onto this minimal semantics.

---

# 2. INSTRUCTION FAMILIES (NORMATIVE)

Instructions are strictly classified into three fundamental families:

```text
       Instruction Family
      ┌─────────┼─────────┐
      ▼         ▼         ▼
   [ READ ]  [ WRITE ] [ CONTROL ]
```

| Family | Operational Semantics | Effect Category |
|---|---|---|
| `READ` | Inspects state payload at opaque `Handle` | `Read(State)` (Pure) |
| `WRITE` | Allocates, mutates, or releases opaque `Handle` state | `Write(State)` (Impure) |
| `CONTROL` | Evaluates predicate assertion or loads extension module | `Control(Runtime)` (Pure / Extension) |

---

# 3. EFFECT PROGRAMS (NORMATIVE)

An Effect Program $\mathcal{P}$ is a list of family operations:

$$\mathcal{P} = [o_1, o_2, \dots, o_n], \quad o_i \in \{\text{READ}, \text{WRITE}, \text{CONTROL}\}$$

Execution of an undeclared effect or unauthorized effect family constitutes **Undefined Behaviour (UB)** and causes immediate termination (`CapabilityError`).

---

# 4. OPAQUE HANDLES & EXTENSION BINDING (NORMATIVE)

All state references are opaque handles:

$$\text{Handle} \in \mathcal{H}_{\text{opaque}}$$

Modularity is extended via a single instruction: `LOAD_EXTENSION(ModuleURI)`.

---

# 5. ERROR MODEL (NORMATIVE)

The kernel recognizes exactly four structural errors:

1. `ExecutionError`: Stack underflow or invalid handle dereference.
2. `CapabilityError`: Attempted effect family not authorized by active Capability Set.
3. `IntegrityError`: Predicate assertion failure in `CONTROL` instruction.
4. `ImplementationError`: Engine or extension runtime failure.

---

# 6. MINIMAL SEMANTICS CONFORMANCE (NORMATIVE)

A runtime is **CAM-5.0 Conforming** if and only if it implements the step function:

$$\text{step}(\mathcal{S}, \mathcal{P}) \longrightarrow (\mathcal{S}', \text{ObservedEffects})$$

without adding hardcoded domain assumptions into Level 0.
