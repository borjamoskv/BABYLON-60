# 03 — Computability and Turing

## 3.1 The Church-Turing Thesis

The question "What is a computable function?" received four independent, convergent answers in the 1930s:

| Formalism | Author | Year | Model |
| :--- | :--- | :---: | :--- |
| **$\lambda$-calculus** | Alonzo Church | 1936 | Functional abstraction |
| **Turing machines** | Alan Turing | 1936 | Automaton with infinite tape |
| **$\mu$-recursive functions** | Stephen Kleene | 1936 | Recursion + minimization |
| **Representability in $Q$** | Raphael Robinson | 1950 | Provable formulas |

All four define exactly the **same class** of functions. The **Church-Turing Thesis** postulates that this class captures the intuitive notion of "effective calculability."

Robinson's contribution was proving that the fourth formalism (representability in a system with only 7 axioms) is equivalent to the other three. This was surprising: no one expected a system so weak could capture all of computability.

## 3.2 The Halting Problem

> **Theorem (Turing, 1936):** There is no algorithm that, given a program $p$ and input $n$, determines whether $p$ halts on $n$.

### Proof

1. Suppose such an algorithm $H(p, n)$ exists, returning 1 if $p$ halts on $n$, 0 otherwise.
2. Construct the program $D$:
   ```
   D(p):
       if H(p, p) == 1:
           loop forever
       else:
           halt
   ```
3. Does $D(D)$ halt?
   - If yes → $H(D, D) = 1$ → $D(D)$ loops. Contradiction.
   - If no → $H(D, D) = 0$ → $D(D)$ halts. Contradiction.
4. Therefore $H$ cannot exist. $\square$

### Connection to Robinson's Arithmetic

The Halting Problem connects directly to $Q$ via $\Sigma_1$-completeness:

1. Given a Turing machine $M$ and input $n$, construct the $\Sigma_1$ sentence $\sigma_{M,n}$: "There exists a finite computation trace where $M$ halts on $n$."
2. By $\Sigma_1$-completeness: $M$ halts on $n$ $\iff$ $Q \vdash \sigma_{M,n}$.
3. If $Q$ were decidable, we could decide the Halting Problem. Contradiction.

## 3.3 Turing Degrees

Undecidability is not a binary phenomenon. There exists an **infinite hierarchy** of degrees of unsolvability, organized by **Turing reducibility** ($\le_T$):

### Definition

$A \le_T B$ ("$A$ is Turing-reducible to $B$") if there exists an algorithm that decides $A$ when given access to an oracle for $B$.

### The Arithmetic Hierarchy of Degrees

| Degree | Name | Example | Description |
| :---: | :--- | :--- | :--- |
| $\mathbf{0}$ | Computable | "Is $2+3=5$?" | Algorithmically decidable |
| $\mathbf{0'}$ | Turing jump | "Does $M$ halt on $n$?" | $\Sigma_1$-complete (Halting Problem) |
| $\mathbf{0''}$ | Double jump | "Is $\phi$ independent of $Q$?" | $\Sigma_2$-complete |
| $\mathbf{0'''}$ | Triple jump | "Is $T$ essentially undecidable?" | $\Sigma_3$-complete |
| $\mathbf{0^{(n)}}$ | $n$-th jump | $\Sigma_n$-complete problems | Each strictly harder than the previous |

### The Jump Operator

The **Turing jump** of a set $A$ is:
$$A' = \{e : \phi_e^A(e) \downarrow\}$$
(the halting problem relativized to $A$).

Key properties:
- $A <_T A'$ — the jump is strictly harder.
- $\mathbf{0'} = $ the Halting Problem.
- $\mathbf{0^{(n)}}$ captures exactly the $\Sigma_n$-complete sets.

### Beyond the Finite Hierarchy

At limit ordinals, the hierarchy continues:
$$\mathbf{0} < \mathbf{0'} < \mathbf{0''} < \dots < \mathbf{0^{(\omega)}} < \dots < \mathbf{0^{(\omega^2)}} < \dots < \mathbf{0^{(\omega_1^{CK})}}$$

$\omega_1^{CK}$ (the Church-Kleene ordinal) is the first non-computable ordinal. Beyond it, the very notion of "algorithm" breaks down.

## 3.4 The Arithmetic Hierarchy

The arithmetic hierarchy classifies formulas by quantifier alternation:

| Level | Form | Characteristic |
| :---: | :--- | :--- |
| $\Delta_0$ | No unbounded quantifiers | Decidable (bounded search) |
| $\Sigma_1$ | $\exists x_1 \dots \exists x_n \; \phi_{\Delta_0}$ | Semi-decidable (r.e.) |
| $\Pi_1$ | $\forall x_1 \dots \forall x_n \; \phi_{\Delta_0}$ | Co-semi-decidable (co-r.e.) |
| $\Sigma_n$ | $\exists \forall \exists \dots$ ($n$ alternations, starting with $\exists$) | $\Sigma_n$-complete |
| $\Pi_n$ | $\forall \exists \forall \dots$ ($n$ alternations, starting with $\forall$) | $\Pi_n$-complete |

### Robinson's Asymmetry

$Q$ exhibits a fundamental epistemic asymmetry with respect to this hierarchy:

| Level | $Q$'s capability |
| :--- | :--- |
| $\Sigma_1$ | **Complete** — every true $\Sigma_1$ sentence is provable |
| $\Pi_1$ | **Incomplete** — cannot prove $\forall x \; (0 + x = x)$ |
| $\Sigma_n$ ($n \ge 2$) | Increasingly incomplete |

> $Q$ can **verify** any concrete computation ($\Sigma_1$) but cannot **generalize** over all numbers ($\Pi_1$).

## 3.5 Rice's Theorem

> **Theorem (Rice, 1953):** Every non-trivial property of the behavior of programs is undecidable.

A property $P$ of computable functions is **non-trivial** if some computable functions have it and some don't. Rice's Theorem says no algorithm can determine whether a given program computes a function with property $P$.

### Proof Sketch

By reduction to the Halting Problem:
1. Let $P$ be a non-trivial property. WLOG, $P(\bot) = 0$ (the empty function lacks $P$).
2. Let $f_0$ be a function with $P(f_0) = 1$.
3. Given $(M, n)$, construct $M'$:
   ```
   M'(x):
       Run M on n
       If M halts: return f_0(x)
   ```
4. If $M$ halts on $n$: $M'$ computes $f_0$, so $P(M') = 1$.
5. If $M$ doesn't halt: $M'$ computes $\bot$, so $P(M') = 0$.
6. Deciding $P$ decides the Halting Problem. $\square$

### Consequence for BABYLON-60

Rice's Theorem implies that **no automatic verifier can determine whether an arbitrary smart contract satisfies a non-trivial behavioral specification**. All verification systems must operate on restricted subclasses or use heuristics.

## 3.6 The Ackermann Function: At the Exact Boundary

The **Ackermann function** $A(m, n)$ is the canonical example of a function that is **computable but not primitive recursive**:

$$A(0, n) = n + 1$$
$$A(m+1, 0) = A(m, 1)$$
$$A(m+1, n+1) = A(m, A(m+1, n))$$

| $m \backslash n$ | 0 | 1 | 2 | 3 | 4 |
| :---: | :---: | :---: | :---: | :---: | :---: |
| 0 | 1 | 2 | 3 | 4 | 5 |
| 1 | 2 | 3 | 4 | 5 | 6 |
| 2 | 3 | 5 | 7 | 9 | 11 |
| 3 | 5 | 13 | 29 | 61 | 125 |
| 4 | 13 | 65533 | $2^{65536}-3$ | ⫶ | ⫶ |

The Ackermann function is **representable in $Q$** (because it is computable) but **not expressible via primitive recursion schemes** — it requires the $\mu$-operator (unbounded search).

## 3.7 The Function Hierarchy

```
┌───────────────────────────────────────────────────────┐
│ ALL FUNCTIONS f: ℕ → ℕ                               │
│ Cardinality: 2^ℵ₀ (uncountable)                      │
│                                                       │
│  ┌─────────────────────────────────────────────────┐  │
│  │ ARITHMETIC FUNCTIONS (definable in ℕ)           │  │
│  │ Cardinality: ℵ₀ (countable)                    │  │
│  │                                                 │  │
│  │  ┌───────────────────────────────────────────┐  │  │
│  │  │ COMPUTABLE = Representable in Q           │  │  │
│  │  │ Cardinality: ℵ₀                           │  │  │
│  │  │                                           │  │  │
│  │  │  ┌─────────────────────────────────────┐  │  │  │
│  │  │  │ PRIMITIVE RECURSIVE                 │  │  │  │
│  │  │  │ (without μ-operator)                │  │  │  │
│  │  │  │  ┌───────────────────────────────┐  │  │  │  │
│  │  │  │  │ ELEMENTARY (Kalmár)           │  │  │  │  │
│  │  │  │  │  ┌─────────────────────────┐  │  │  │  │  │
│  │  │  │  │  │ POLYNOMIAL (P)          │  │  │  │  │  │
│  │  │  │  │  └─────────────────────────┘  │  │  │  │  │
│  │  │  │  └───────────────────────────────┘  │  │  │  │
│  │  │  └─────────────────────────────────────┘  │  │  │
│  │  └───────────────────────────────────────────┘  │  │
│  └─────────────────────────────────────────────────┘  │
└───────────────────────────────────────────────────────┘
```

Each level is strictly contained in the next. The Ackermann function witnesses the strict separation between primitive recursive and computable.

## 3.8 References

- Turing, A. M. (1936). "On Computable Numbers, with an Application to the Entscheidungsproblem." *Proceedings of the London Mathematical Society*, s2-42(1), 230–265.
- Church, A. (1936). "An Unsolvable Problem of Elementary Number Theory." *American Journal of Mathematics*, 58(2), 345–363.
- Rice, H. G. (1953). "Classes of Recursively Enumerable Sets and Their Decision Problems." *Transactions of the AMS*, 74, 358–366.
- Rogers, H. (1967). *Theory of Recursive Functions and Effective Computability*. MIT Press.

---

*Previous: [02 — Gödel's Incompleteness](./02_goedel_incompleteness.md) | Next: [04 — Chaitin & Kolmogorov](./04_chaitin_kolmogorov.md)*
