# BABYLON-60: Proof IR Specification (v2.0-C5-REAL)

> **Régimen C5-REAL | Invariante Asociado: `INV_C5_15`**
> Representación Intermedia (Proof IR) para la traducción determinista de trazas causales a teoremas formales verificables en Lean 4 / Coq.

---

## 1. Objetivo y Arquitectura de Proof IR

Proof IR (Intermediate Representation) es el estrato de abstracción semántica de BABYLON-60. Aisla el núcleo de ejecución en Rust/Python de los motores sintácticos de asistentes de pruebas externos (Lean 4, Coq), transformando las secuencias de eventos del `graph.canonical` en un árbol de proposiciones lógicas e invariantes temporales.

```
┌─────────────────┐       ┌─────────────────┐       ┌─────────────────┐       ┌─────────────────┐
│ graph.canonical │ ────► │    Proof IR     │ ────► │  32-byte Merkle │ ────► │ Lean 4 Harness  │
│  (Pipe-Delim)   │       │ (S-expressions) │       │   OP_RETURN L1  │       │(BabylonTrace.lean)│
└─────────────────┘       └─────────────────┘       └─────────────────┘       └─────────────────┘
```

---

## 2. Gramática Formal S-Expression

La sintaxis de `proof.ir` se estructura en tres tipos de predicados lógicos representados como S-expressions:

### 2.1 Declaraciones Topológicas (Causalidad Temporal)
- `(Event <ID: String> <Tick: u64>)`: Declara la existencia de un evento discreto en el tiempo Planck.
- `(HappensBefore <ID_A: String> <ID_B: String>)`: Declara una relación de orden parcial estricto $\text{ID}_A \prec \text{ID}_B$.

### 2.2 Aserciones de Mutación de Estado (Álgebra Base-60)
- `(Assign <Reg: String> <Value: F60> <EventID: String>)`: Asignación inmutable de registro.
- `(Add <Reg: String> <Delta: F60> <EventID: String>)`: Adición determinista sexagesimal.
- `(Sub <Reg: String> <Delta: F60> <EventID: String>)`: Sustracción determinista sexagesimal.
- `(Spawn <TaskName: String> <ChildID: String> <ParentID: String>)`: Bifurca corrutina (`FORK`).
- `(Block <SignalName: String> <EventID: String>)`: Bloqueo por dependencia externa (`AWAIT`).
- `(Emit <SignalName: String> <EventID: String>)`: Emisión de señal causante de reactivación.

### 2.3 Teoremas de Invariante Derivados
- `(InvariantHold <InvID: String> <StateHash: Byte32>)`: Confirma que la traza respeta el invariante especificado.

---

## 3. Esquema JSON / Struct Rust de Serialization

```rust
#[derive(Debug, Serialize, Deserialize, PartialEq, Eq)]
pub enum ProofPredicate {
    Event { id: String, tick: u64 },
    HappensBefore { parent: String, child: String },
    Assign { reg: String, val: String, event_id: String },
    Spawn { task: String, child_id: String, parent_id: String },
    InvariantHold { inv_id: String, state_hash: String },
}

#[derive(Debug, Serialize, Deserialize)]
pub struct ProofIRBundle {
    pub version: String,
    pub graph_hash: String,
    pub predicates: Vec<ProofPredicate>,
    pub merkle_root_32b: String,
}
```

---

## 4. Compromiso Criptográfico en Bitcoin L1 Sink (`INV_C5_15`)

El conjunto completo de predicados en `proof.ir` se serializa canónicamente. Sobre este buffer se construye un Árbol de Merkle binario.

### Formulación de la Raíz de Merkle:
$$\text{Leaf}_i = \text{SHA256}\big( \text{Predicate}_i \big)$$

$$\text{Parent}_{j} = \text{SHA256}\big( \text{Leaf}_{2j} \;\parallel\; \text{Leaf}_{2j+1} \big)$$

$$\text{MerkleRoot}_{\text{ProofIR}} = \text{RootNode} \in \{0, 1\}^{256} \cong \mathbf{32 \text{ bytes}}$$

> [!NOTE]
> De acuerdo con **`INV_C5_15`**, esta raíz de 32 bytes exactos es inyectada directamente en el script `OP_RETURN` de la transacción L1 de Bitcoin, anclando de forma inmutable e inalterable la validez de la demostración a la blockchain de Bitcoin.

---

## 5. Mapeo al Isomorfismo Curry-Howard

Bajo la correspondencia de Curry-Howard:

$$\text{Proposiciones} \cong \text{Tipos} \qquad \text{Demostraciones} \cong \text{Programas} \qquad \text{Simplificación} \cong \text{Cómputo}$$

Cada predicado `ProofIR` se traduce en Lean 4 a una premisa o constructor del inductivo `CausalStep`:

```lean
inductive CausalStep : Type where
  | event (id : String) (tick : Nat) : CausalStep
  | happens_before (parent child : String) : CausalStep
  | assign (reg : String) (val : Nat) (id : String) : CausalStep
```
