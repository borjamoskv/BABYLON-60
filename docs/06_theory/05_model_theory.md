# 05 — Model Theory

## 5.1 Structures and Models

A **structure** (or model) $\mathfrak{A}$ for a first-order language $\mathcal{L}$ consists of:
- A non-empty **domain** (universe) $|\mathfrak{A}|$
- An interpretation for each symbol in $\mathcal{L}$: constants → elements, function symbols → functions, relation symbols → relations

A structure $\mathfrak{A}$ is a **model** of a theory $T$ (written $\mathfrak{A} \models T$) if every axiom of $T$ is true in $\mathfrak{A}$.

The **standard model** of Robinson Arithmetic $Q$ is $\mathbb{N} = (\mathbb{N}, 0, S, +, \cdot)$ with their usual interpretations. But $Q$ admits many **non-standard models**.

## 5.2 The Compactness Theorem

> **Theorem:** A set of sentences $\Gamma$ has a model if and only if every **finite** subset of $\Gamma$ has a model.

### Proof (Two Routes)

**Via Gödel's Completeness Theorem (1930):**
1. Completeness: $\Gamma \models \phi \iff \Gamma \vdash \phi$.
2. Every proof is finite → uses finitely many axioms.
3. If $\Gamma$ has no model, then $\Gamma \models \bot$, so $\Gamma \vdash \bot$ using finitely many axioms $\Gamma_0$. Hence $\Gamma_0$ has no model. $\square$

**Via Ultraproducts (Łoś, 1955):**
1. If every finite subset has a model, form the family $\{\mathfrak{A}_i\}$.
2. Extend the Fréchet filter to an ultrafilter $\mathcal{U}$ (Zorn's Lemma).
3. The ultraproduct $\prod_i \mathfrak{A}_i / \mathcal{U}$ satisfies $\Gamma$ by Łoś's Theorem. $\square$

### Consequences

#### Non-Standard Models of $Q$

Let $\Gamma = \text{Axioms of } Q \cup \{c \neq \bar{0}, c \neq \bar{1}, c \neq \bar{2}, \dots\}$ with a new constant $c$.

Every finite subset has a model (interpret $c$ as a sufficiently large number). By compactness, $\Gamma$ has a model $\mathcal{M}$ where $c^{\mathcal{M}}$ differs from every standard numeral — a **non-standard element**.

#### Finiteness is Inexpressible

No first-order sentence (or set of sentences) is true exactly in finite structures. If you try to axiomatize "finite," compactness forces an infinite model.

#### First-Order Cannot Fix Cardinality

If a theory has an infinite model, it has models of every infinite cardinality (combining compactness with Löwenheim-Skolem).

### The Topological Connection

The name "compactness" comes from topology. For each sentence $\phi$, define $[\phi] = \{\text{models of } \phi\}$. These form a base for the **Stone space** of the theory. Logical compactness **is** topological compactness of this Stone space.

## 5.3 The Löwenheim-Skolem Theorem

### Downward (Löwenheim 1915, Skolem 1920)

> If a theory $T$ in a countable language has an infinite model, it has a **countable** model.

**Proof (Skolem hull construction):**
1. For each formula $\exists y \; \phi(x, y)$ true in model $\mathfrak{A}$, choose a Skolem witness function $f_\phi$.
2. Starting from a countable subset $A_0$, close under all Skolem functions: $A_{n+1} = A_n \cup \{f_\phi(a) : a \in A_n\}$.
3. $\mathcal{M} = \bigcup_n A_n$ is an **elementary substructure** of $\mathfrak{A}$ with $|\mathcal{M}| = \aleph_0$. $\square$

### Upward (Tarski, via Compactness)

> If a theory has an infinite model, it has models of **arbitrarily large cardinality**.

**Proof:**
1. Add $\kappa$ new constants $\{c_\alpha : \alpha < \kappa\}$ and axioms $\{c_\alpha \neq c_\beta : \alpha \neq \beta\}$.
2. Every finite subset is satisfiable (the original infinite model provides enough distinct elements).
3. By compactness, the extended theory has a model with at least $\kappa$ elements. $\square$

### Combined Statement

> If a first-order theory has an infinite model, it has models of **every infinite cardinality**.

### Skolem's Paradox

ZFC proves that uncountable sets exist ($\mathbb{R}$, $\mathcal{P}(\mathbb{N})$). Yet by Löwenheim-Skolem, ZFC has a **countable model** $\mathcal{M}$.

**Resolution:** "Uncountable" means "no bijection with $\mathbb{N}$ **exists within the model**." The countable model $\mathcal{M}$ is "blind" to the external bijection — it doesn't belong to $\mathcal{M}$.

| Perspective | Is $\mathbb{R}^{\mathcal{M}}$ uncountable? |
| :--- | :--- |
| **Internal** (within $\mathcal{M}$) | **Yes** — no bijection $\mathbb{N}^{\mathcal{M}} \to \mathbb{R}^{\mathcal{M}}$ in $\mathcal{M}$ |
| **External** (from outside) | **No** — $\mathcal{M}$ is countable, so everything in it is |

## 5.4 Lindström's Theorem (1969)

> **Theorem (Lindström):** First-order logic is the **most expressive logic** satisfying both:
> (a) The Compactness Theorem, and
> (b) The Downward Löwenheim-Skolem Theorem.

Any logic strictly more expressive than first-order (second-order, infinitary, etc.) **loses at least one**.

### What is an "Abstract Logic"?

Lindström defined a logic $\mathcal{L}$ as a pair $(\text{Sent}_\mathcal{L}, \models_\mathcal{L})$ satisfying:
1. **Isomorphism invariance**
2. **Renaming invariance**
3. **Boolean closure**
4. **Existential quantification**

### The Landscape

| Logic | Extends FO? | Compactness | Löwenheim-Skolem |
| :--- | :---: | :---: | :---: |
| **First-order (FO)** | — | ✅ | ✅ |
| **Second-order (SO)** | ✅ | ❌ | ❌ |
| $L_{\omega_1, \omega}$ (countable conjunctions) | ✅ | ❌ | ✅ |
| FO + "there exist infinitely many" | ✅ | ❌ | ✅ |
| FO + cardinality quantifier | ✅ | ❌ | ❌ |

### The Fundamental Trade-Off

First-order logic is a **fixed point** in the space of all possible logics:

```
            Expressiveness →
 ┌────────────────────────────────────────┐
 │  FO           SO           L∞,ω       │
 │  ●────────────●────────────●           │
 │  Compact      No compact   No compact  │
 │  + L-S        No L-S       Partial L-S │
 │  + Complete   No Complete               │
 ← Metamathematical Properties            │
 └────────────────────────────────────────┘
```

## 5.5 Tennenbaum's Theorem (1959)

> **Theorem (Tennenbaum):** There is no **computable non-standard model** of Peano Arithmetic ($PA$). If $\mathcal{M} \models PA$ and $\mathcal{M} \not\cong \mathbb{N}$, then $+^{\mathcal{M}}$ and $\cdot^{\mathcal{M}}$ are not computable.

### Contrast with $Q$

| | Computable non-standard models? |
| :--- | :---: |
| **$Q$ (Robinson)** | **Yes** — exist and can be constructed |
| **$PA$ (Peano)** | **No** — Tennenbaum forbids it |

The induction schema (the only ingredient separating $PA$ from $Q$) imposes a **computational barrier** on non-standard models. In $PA$, pathological models exist mathematically but are **computationally unreachable** — Platonic objects without algorithmic realization.

### Philosophical Implication

$\mathbb{N}$ is, in a sense, the **only computationally accessible model** of $PA$. Non-standard models are phantoms — they satisfy the axioms but cannot be built by any algorithm.

For $Q$, non-standard models are **algorithmically real** — you can program one.

## 5.6 Categoricity and Its Impossibility

A theory is **categorical** if it has exactly one model (up to isomorphism). Löwenheim-Skolem implies:

> **No first-order theory with infinite models can be categorical.**

$Q$ cannot "fix" its intended model as $\mathbb{N}$. Neither can $PA$. To achieve categoricity, you need **second-order logic** (where the full induction axiom categorizes $\mathbb{N}$), but then you lose compactness and the mechanizability of proofs (Lindström).

This is the **irreducible dilemma** at the heart of mathematical foundations.

## 5.7 References

- Lindström, P. (1969). "On extensions of elementary logic." *Theoria*, 35(1), 1–11.
- Tennenbaum, S. (1959). "Non-Archimedean models for arithmetic." *Notices of the AMS*, 6, 270.
- Chang, C. C. & Keisler, H. J. (1990). *Model Theory*. North-Holland (3rd edition).
- Hodges, W. (1993). *Model Theory*. Cambridge University Press.

---

*Previous: [04 — Chaitin & Kolmogorov](./04_chaitin_kolmogorov.md) | Next: [06 — Curry-Howard Correspondence](./06_curry_howard.md)*
