# CAM-3.0 (C5 Abstract Effect Machine - AEM Core Specification)
## Minimalist Normative Specification for Abstract Effect Machines

**Classification:** C5 Formal Core Specification  
**Status:** Living Minimalist Abstract Machine  
**Paradigm:** Abstract Effect Machine (AEM) · Algebraic Effects · Micro-ISA · Opaque Handles

---

```text
┌─────────────────────────────────────────────────────────────────────────┐
│                        CAM-3.0 AEM ARCHITECTURE                         │
├─────────────────────────────────────────────────────────────────────────┤
│  Execution Model   Instruction ➔ Algebraic Effects ➔ State Transition   │
│  Object Space      Allocate · Lookup · Bind · Release (Opaque Handles) │
│  Micro-ISA         ALLOC · LOAD · STORE · LINK · UNLINK · CALL · ASSERT │
│  Effects Algebra   Read(Store) + Write(Store) + Append(Ledger) + Call() │
│  Capabilities      Capabilities defined directly over Algebraic Effects  │
└─────────────────────────────────────────────────────────────────────────┘
```

---

# 1. ABSTRACT MODEL SEPARATION (NORMATIVE)

The Abstract Machine separates static state from dynamic execution:

```text
Persistent Model (Object Space)          Execution Model (AEM Runtime)
┌──────────────────────────────┐         ┌──────────────────────────────┐
│  Opaque Handle               │         │  Instruction                 │
│  Object Payload              │         │  ExecutionContext            │
│  Link / Reference            │         │  Algebraic Effect            │
└──────────────────────────────┘         │  Event Log                   │
                                         └──────────────────────────────┘
```

The Core ISA operates over an abstract **Object Space**, independent of underlying storage implementations (SQL, Graph, HashMap, RDF).

---

# 2. OPAQUE HANDLES & OBJECT SPACE (NORMATIVE)

All references inside the machine are opaque `Handle` identifiers:

$$\text{Handle} \in \mathcal{H}_{\text{opaque}}$$

The Object Space supports exactly four primitive operations:

1. `Allocate(payload) -> Handle`
2. `Lookup(handle) -> Payload`
3. `Bind(handle_a, handle_b, relation_tag) -> Status`
4. `Release(handle) -> Status`

---

# 3. MINIMAL MICRO-ISA (INSTRUCTION SET ARCHITECTURE) (NORMATIVE)

The machine executes micro-instructions. Domain concepts (`Claim`, `Knowledge`, `Evidence`) are high-level libraries compiled into these micro-instructions:

| Instruction | Operational Semantics | Declared Effects |
|---|---|---|
| `ALLOC` | Allocates new payload in Object Space, returns `Handle` | `Write(Store)` |
| `LOAD` | Reads payload referenced by `Handle` | `Read(Store)` |
| `STORE` | Mutates payload referenced by `Handle` | `Write(Store)` |
| `LINK` | Binds two handles with a typed relation tag | `Write(Store)` |
| `UNLINK` | Removes typed relation tag between handles | `Write(Store)` |
| `CALL` | Invokes external module or driver procedure | `Call(External)` |
| `ASSERT` | Evaluates predicate; triggers `IntegrityError` if false | `None` (Pure) |
| `COMMIT` | Flushes transaction to hash-chained ledger event log | `Append(Ledger)` |
| `ABORT` | Reverts uncommitted Object Space mutations | `None` |

---

# 4. ALGEBRAIC EFFECT SYSTEM (NORMATIVE)

Effects are algebraic compositions of primitive operations:

$$\text{Effect} = \text{Read}(\text{Resource}) + \text{Write}(\text{Resource}) + \text{Append}(\text{Ledger}) + \text{Call}(\text{External})$$

$$\text{Effects}_{\text{actual}} \subseteq \text{Effects}_{\text{declared}}$$

Executing an undeclared effect triggers `CapabilityError` or `ExecutionError`.

---

# 5. EFFECT-BASED CAPABILITY ALGEBRA (NORMATIVE)

Capabilities grant permission over specific algebraic effects, not high-level commands:

```text
CapabilitySet = Set[Effect]

AgentPermissions:
  Grant Read(Store)
  Grant Write(Store)
  Grant Append(Ledger)
```

Privilege Check:
$$\text{InstructionAllowed} \iff \text{RequiredEffect}(\text{Inst}) \in \text{AgentPermissions}$$

---

# 6. UNIFIED ERROR MODEL (NORMATIVE)

The AEM classifies failures into exactly four structural errors:

1. `ExecutionError`: Invalid instruction, stack underflow, or divide-by-zero.
2. `CapabilityError`: Agent attempted an instruction requiring an unauthorized Effect.
3. `IntegrityError`: `ASSERT` predicate evaluation failed or hash chain broke.
4. `ImplementationError`: Backend storage engine or driver internal failure.

---

# 7. EXTENSIBLE CONFORMANCE MATRIX (NORMATIVE)

- **CAM-3.0 Core**: Micro-ISA + Object Space + Opaque Handles + Error Model.
- **Core + Effects**: Core + Algebraic Effect Composition.
- **Core + Capabilities**: Core + Effects + Effect-Based Permission Enforcer.
- **Core + Persistence**: Core + Capabilities + Hash-Chained Ledger Commit.

---

# 8. THE ABSTRACT EFFECT MACHINE SEMANTICS (NORMATIVE)

```text
Instruction  ──►  Effect Verification  ──►  State Transition & Event Emission
```

High-level domain models exist purely as user-space libraries. The AEM microkernel is strictly an **Abstract Effect Engine**.
