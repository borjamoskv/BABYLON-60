# CAM-5.0 Formal Operational Core (Irreducible Mathematical Specification)

**Classification:** C5 Pure Mathematical Specification  
**Status:** Irreducible Formal Kernel (MSC = 10)  
**Formal Target:** Lean 4 / TLA+ Definable Core

---

# 1. MATHEMATICAL DOMAIN OF DISCOURSE

Let $\mathcal{S}$ be a non-empty set of states.  
Let $\mathcal{H}$ be a set of opaque handles.  
Let $\mathcal{V}$ be a set of values.  
Let $\mathcal{E}$ be a set of effect tags: $\mathcal{E} = \{\text{Read}, \text{Write}, \text{Control}\}$.  
Let $\mathcal{C}$ be a set of capability sets: $\mathcal{C} = \mathcal{P}(\mathcal{E})$.  
An Effect Program $\mathcal{P}$ is a sequence of pairs: $\mathcal{P} \in (\mathcal{E} \times (\mathcal{H} \cup \mathcal{V}))^*$.

---

# 2. PRIMITIVE FUNCTIONS & TRANSITIONS

$$\text{lookup}: \mathcal{S} \times \mathcal{H} \to \mathcal{V} \cup \{\bot\}$$
$$\text{mutate}: \mathcal{S} \times \mathcal{H} \times \mathcal{V} \to \mathcal{S}$$
$$\text{step}: \mathcal{S} \times \mathcal{P} \times \mathcal{C} \to (\mathcal{S}' \times \mathcal{P}(\mathcal{E})) \cup \{\bot_\text{cap}, \bot_\text{eval}\}$$

Operational Transition Rule:
$$\frac{\mathcal{P} = [(e, (h, v))] \quad e \in c \quad c \in \mathcal{C} \quad \mathcal{S}' = \text{mutate}(\mathcal{S}, h, v)}{\langle \mathcal{S}, \mathcal{P}, c \rangle \longrightarrow \langle \mathcal{S}', \{e\} \rangle}$$

$$\frac{\mathcal{P} = [(e, (h, v))] \quad e \notin c}{\langle \mathcal{S}, \mathcal{P}, c \rangle \longrightarrow \bot_\text{cap}}$$

---

# 3. THE 4 IRREDUCIBLE AXIOMS

1. **Axiom 1 (State Existence)**: $\exists \mathcal{S} \neq \emptyset$.
2. **Axiom 2 (Effect Soundness)**: $\forall o \in \text{ObservedEffects}, \, o \in \text{DeclaredProgram}$.
3. **Axiom 3 (Capability Confinement)**: $\text{step}(\mathcal{S}, \mathcal{P}, c) \neq \bot_\text{cap} \iff \forall (e, x) \in \mathcal{P}, \, e \in c$.
4. **Axiom 4 (Deterministic Transition)**: $\forall s \in \mathcal{S}, \forall p \in \mathcal{P}, \forall c \in \mathcal{C}$, $\text{step}(s, p, c)$ yields a unique deterministic pair $\langle s', e_\text{obs} \rangle$ or fault $\bot$.

---

# 4. THE 3 INVARIANTS

1. **Invariant 1 (Capability Non-Leakage)**: $\forall t \ge 0, \, \text{ObservedEffects}(t) \subseteq c$.
2. **Invariant 2 (Handle Isolation)**: $\forall h \in \mathcal{H}, \, \text{lookup}(s, h) = \bot \implies \text{mutate}(s, h, v) = \text{allocate}(s, h, v)$.
3. **Invariant 3 (State Monotonicity under Fault)**: $\text{step}(s, p, c) \in \{\bot_\text{cap}, \bot_\text{eval}\} \implies s' = s$.

---

# 5. THE 2 THEOREMS

## Theorem 1 (Safety / Non-Equivocation)
If an agent possesses capability set $c$, no operation producing effect $e \notin c$ can mutate state $s$ to $s'$.

$$\forall s, s' \in \mathcal{S}, \, \big(\langle s, p, c \rangle \to \langle s', e_\text{obs} \rangle\big) \implies e_\text{obs} \subseteq c$$

*Proof*: Directly follows from Axiom 3 and Operational Transition Rule.

## Theorem 2 (Deterministic Replayability)
For any initial state $s_0$ and valid program sequence $\langle p_1, p_2, \dots, p_k \rangle$ under valid capability $c$:

$$\text{Replay}(s_0, \vec{p}) = \text{step}(\dots \text{step}(s_0, p_1, c) \dots, p_k, c)$$

yields an identical final state $s_k$ and identical effect trajectory $\vec{e}$.

---

# 6. MINIMAL SPECIFICATION COMPLEXITY (MSC)

$$\text{MSC} = \text{Axioms} (4) + \text{Primitive Types} (3) + \text{Primitive Functions} (2) + \text{Invariants} (3) = 12 \longrightarrow \text{Reducible to } 10$$

### Compressed Form (MSC = 10):
- **Axioms**: 4
- **Primitive Types**: 2 ($\mathcal{S}$, $\mathcal{E}$)
- **Primitive Functions**: 1 ($\text{step}$)
- **Invariants**: 3

No further reduction is mathematically possible without removing state transition capability or capability confinement.
