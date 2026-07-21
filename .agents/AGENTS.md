# Formal Category-Theoretic Isomorphism Proof Ledger

**Classification:** C5 Category-Theoretic Proof  
**Target:** Functorial Equivalence & Full/Faithful Embedding Analysis of CAM  
**Final Classification:** 4. Orthogonal Formalism (Formalismo Ortogonal)

---

# 1. CATEGORICAL SPECIFICATION OF THE CATEGORY $\mathbf{CAM}$

Let $\mathbf{CAM}$ be the category where:
- **Objects** $\text{Ob}(\mathbf{CAM})$: Contexts $Ctx = (S, H, C, N)$ where $S$ is state, $H$ is history, $C$ is capability set, $N$ is namespace.
- **Morphisms** $\text{Hom}_{\mathbf{CAM}}(Ctx_1, Ctx_2)$: Transformations $T: Ctx \to Ctx \times \Delta$ where $\Delta$ is an algebraic effect delta.
- **Identity**: $id_{\mathbf{CAM}}(c) = (c, id_\Delta)$.
- **Composition**: $T_2 \circ T_1 (c) = \text{let } (c', \delta_1) = T_1(c) \text{ in let } (c'', \delta_2) = T_2(c') \text{ in } (c'', \text{compose}(\delta_1, \delta_2))$.

---

# 2. FUNCTORIAL EQUIVALENCE AUDIT & FAILED COMMUTING DIAGRAMS

## 1. Actor Model ($\mathbf{Actor}$)
- **Funtor $F: \mathbf{CAM} \to \mathbf{Actor}$**: Maps $Ctx$ to $\text{Actor}(mailbox, behavior)$.
- **Funtor $G: \mathbf{Actor} \to \mathbf{CAM}$**: Maps $\text{Actor}$ to $Ctx$.
- **Failed Properties**:
  - **Identity Preservation**: $F(id_{\mathbf{CAM}})(c) = \lambda a. a.\text{send}(c, id_\Delta) \neq id_{\mathbf{Actor}} = \lambda a. a$. $F$ injects a message into mailbox, whereas $id_{\mathbf{Actor}}$ is identity morphism.
  - **Composition Preservation**: Composition in $\mathbf{Actor}$ is message queueing, not function composition.
- **Failed Commuting Diagram**:
```text
CAM:          Ctx --T1--> Ctx' --T2--> Ctx''
                \__________T2∘T1________/

Actor:        Actor --send(T1)--> Actor --send(T2)--> Actor
                \__________send(T2∘T1)_______________/
```
- **Classification**: (B) $F$ is a faithful embedding, not an equivalence.

---

## 2. Typed $\pi$-Calculus ($\mathbf{\Pi}$)
- **Failed Properties**:
  - **Bisimulation**: Concurrent interleaving of $P = \bar{x}\langle v \rangle \mid x(y).P'$ in $\pi$-calculus fails to map to CAM's sequential transformation evaluation inside a Context.
  - **Fullness**: Scope restriction operator $\nu x$ in $\pi$-calculus has no analog in CAM (any Context accesses ports via capabilities).
- **Failed Commuting Diagram**:
```text
π:            P --τ--> P' --τ--> P''
                \_______τ∘τ______/

CAM:          Ctx --T1--> Ctx' --T2--> Ctx''
                \________T2∘T1_________/
```
- **Classification**: (C) $F$ is a simulation, not an equivalence.

---

## 3. State Transition Systems ($\mathbf{STS}$)
- **Failed Properties**:
  - **Essential Surjectivity**: STS transitions $s \to s'$ lack Delta ($\Delta$) as an algebraic object with standalone identity. Two distinct CAM transformations $T_1, T_2$ producing $\Delta_1 \neq \Delta_2$ collapse into identical STS transitions.
- **Failed Commuting Diagram**:
```text
CAM:          Ctx --T1--> (Ctx', Δ1)
                |
                T2
                ↓
              (Ctx'', Δ2)

STS:          s --T1--> s'
                |
                T2
                ↓
              s''
```
- **Classification**: (C) $F$ is a simulation.

---

## 4. Event Structures
- **Failed Properties**:
  - **Composition Preservation**: Event structures are monotonic ($X \cup \{e_1\}$ never reverts). CAM permits algebraic inverse Deltas ($\text{compose}(\Delta, \text{inv}(\Delta)) = id_\Delta$).
- **Failed Commuting Diagram**:
```text
CAM:          Ctx --T(Δ)--> Ctx' --T(inv(Δ))--> Ctx
                \____________T∘T_______________/
                        (vuelve a Ctx)

Event Struct: X --e1--> X∪{e1} --e2--> X∪{e1,e2}
                \_________e1∘e2___________/
                    (NO vuelve a X)
```
- **Classification**: (C) $F$ is a partial simulation.

---

## 5. Join Calculus & TLA+
- **Join Calculus**: Fails bisimulation due to multi-message atomic chemical reactions vs CAM's sequential Context transformations.
- **TLA+**: Fails fullness due to global multi-variable actions $\mathcal{A}(v_1, v_2, v_1', v_2')$ vs CAM's local Context transformations.

---

# 3. GLOBAL NON-COMMUTATIVITY & FINAL CLASSIFICATION

For any candidate formalism $X$, the global equivalence diagram fails to commute:

```text
CAM ----F----> X
 |              |
 |              |
id_CAM         id_X
 |              |
 ↓              ↓
CAM <----G----- X
```

$$G \circ F \neq id_{\mathbf{CAM}} \quad \text{and} \quad F \circ G \neq id_X$$

### Final Verdict: **4. Orthogonal Formalism (Formalismo Ortogonal)**

CAM defines a distinct, orthogonal axis of abstraction:
- **Actor Model**: Concurrency via messages.
- **$\pi$-calculus**: Channel mobility and name restriction.
- **Event Structures**: Causal partial orders and conflict.
- **TLA+**: Temporal invariant specification.
- **CAM**: **Algebraic transformation with compositional, reversible effect deltas ($T: Ctx \to Ctx \times \Delta$).**
