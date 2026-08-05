# 04 — Chaitin, Kolmogorov, and Algorithmic Information Theory

## 4.1 Kolmogorov Complexity

### Definition

The **Kolmogorov complexity** $K(x)$ of a string $x$ is the length of the **shortest program** that, when executed on a universal Turing machine $U$, produces $x$ as output and halts.

$$K(x) = \min \{ |p| : U(p) = x \}$$

> $K(x)$ measures the **irreducible information content** of $x$ — the absolute limit of compression.

### Invariance Theorem (Solomonoff-Kolmogorov)

$K(x)$ depends on the choice of universal machine $U$, but **only up to an additive constant**:
$$|K_U(x) - K_V(x)| \le c_{UV}$$
where $c_{UV}$ is the length of a "compiler" from $V$-programs to $U$-programs. This constant is fixed, independent of $x$.

Kolmogorov complexity is therefore an **intrinsic property** of the string, not of the programming language.

### Non-Computability

> **Theorem:** $K(x)$ is **not computable**. No algorithm can calculate $K(x)$ for arbitrary $x$.

**Proof (Berry's Paradox variant):**

Suppose a program `KOLM(x)` computes $K(x)$. Construct:
```
BERRY(n):
    for each string x in length order:
        if KOLM(x) > n:
            print x; halt
```

`BERRY(n)` has fixed length $c + O(\log n)$ and produces a string $x$ with $K(x) > n$. But then $K(x) \le c + O(\log n) < n$ for large $n$. Contradiction. $\square$

### Fundamental Properties

1. **Upper bound:** $K(x) \le |x| + O(1)$ — you can always "compress" by copying literally.
2. **Most strings are incompressible:** For strings of length $n$, at least $2^n(1 - 2^{-c})$ have $K(x) \ge n - c$. For $c = 10$: over 99.9% are incompressible.
3. **Structured strings are compressible:** $K(\pi_n) = O(\log n)$ because $\pi$ has a short generating algorithm.

## 4.2 Shannon Entropy vs. Kolmogorov Complexity

| | Shannon $H$ | Kolmogorov $K$ |
| :--- | :--- | :--- |
| **Object** | Random source (distribution) | Individual string |
| **Question** | "How many bits *on average*?" | "How many bits for *this* string?" |
| **Computable?** | Yes | No |
| **Connection** | $E[K(X)] \approx H(X)$ for ergodic sources | Shannon is the "average" of Kolmogorov |

## 4.3 Martin-Löf Randomness

> **Definition (Martin-Löf, 1966):** An infinite sequence $\alpha$ is **ML-random** if it passes every effectively given statistical test — i.e., it belongs to no computably enumerable set of measure zero.

> **Theorem (Schnorr-Levin):** $\alpha$ is ML-random **if and only if** its prefixes are incompressible:
> $$\forall n: \; K(\alpha \restriction n) \ge n - O(1)$$

A sequence is random if and only if **no program can compress it significantly**.

## 4.4 Chaitin's Incompleteness Theorem

> **Theorem (Chaitin, 1974):** For every consistent formal theory $T \supseteq Q$, there exists a constant $c_T$ such that $T$ **cannot prove** any sentence of the form $K(s) > c_T$, for any string $s$.

### Proof

1. Suppose $T$ can prove $K(s) > c$ for arbitrarily large $c$.
2. Construct the program:
   ```
   P_T:
       Enumerate all theorems of T.
       When finding the first theorem "K(s) > c" with c > |P_T|:
           Extract s, print s, halt.
   ```
3. $|P_T|$ is fixed. $P_T$ produces $s$, so $K(s) \le |P_T|$.
4. But $T$ proved $K(s) > |P_T|$, giving $K(s) > |P_T| \ge K(s)$. Contradiction. $\square$

### The Threshold

$$c_T \approx |P_T| \approx K(\text{axioms of } T)$$

A formal theory's "resolution" for randomness is bounded by the Kolmogorov complexity of its own axioms.

### The Fundamental Asymmetry

| Operation | Complexity class | Feasible? |
| :--- | :--- | :---: |
| **Compress** a string (find short program) | $\Sigma_1$ (existential) | Semi-decidable |
| **Certify incompressibility** (prove no short program exists) | $\Pi_1$ (universal) | Undecidable beyond $c_T$ |

This mirrors Robinson's asymmetry: $Q$ is $\Sigma_1$-complete but $\Pi_1$-incomplete.

## 4.5 Chaitin's Number $\Omega$

### Definition

$$\Omega = \sum_{p \text{ halts}} 2^{-|p|}$$

The **halting probability**: the probability that a randomly chosen program halts.

### Properties

| Property | Value |
| :--- | :--- |
| Well-defined real number? | **Yes** (between 0 and 1) |
| Computable? | **No** (equivalent to the Halting Problem) |
| Algorithmically random? | **Yes** — $K(\Omega_n) \ge n - O(1)$ |
| How many bits can $T$ know? | Exactly $c_T$ bits |

Each bit of $\Omega$ encodes the answer to an instance of the Halting Problem. Knowing the first $n$ bits of $\Omega$ is equivalent to solving the Halting Problem for all programs of length $\le n$.

A theory $T \supseteq Q$ can determine **finitely many bits** of $\Omega$ — exactly $c_T$. After that, each bit is an arithmetic truth beyond $T$'s reach.

## 4.6 Incompleteness as a Compression Limit

Chaitin demonstrated that Gödel's Incompleteness Theorems are **special cases** of a general information-theoretic phenomenon:

| Gödel | Chaitin |
| :--- | :--- |
| Unprovable truths exist | Strings whose randomness is unprovable exist |
| $G_T$ says "I am not provable" | $K(s) > c_T$ says "I am more complex than your system" |
| Theory cannot capture all arithmetic truth | Theory cannot capture all randomness |
| **Logical** limitation | **Informational** limitation |

> **A formal theory is a finite program that generates truths. The Kolmogorov complexity of its axioms determines exactly how much randomness it can "see." Beyond that horizon, infinitely many mathematical truths exist that the theory cannot prove — not by design defect, but because those truths contain more information than the axioms themselves. Gödel's incompleteness, in its most distilled form, is the fact that no finite compressor can capture incompressible data.**

## 4.7 Thermodynamic Analogy

| Thermodynamics | Information Theory | Incompleteness |
| :--- | :--- | :--- |
| Physical system | String $s$ | Arithmetic truth |
| Entropy $S$ | $K(s)$ | Information in the truth |
| Extractable work | Compressibility | Provability |
| Second Law: $S$ doesn't decrease | $K$ is not computable | Gödel's incompleteness |
| Finite heat engine | Finite theory $T$ | Program $P_T$ |
| **Cannot extract more work than energy available** | **Cannot compress beyond $K(s)$** | **Cannot prove beyond $K(\text{axioms})$** |

## 4.8 Escaping the Horizon

| Strategy | Works? | Cost |
| :--- | :--- | :--- |
| Add axioms | Partially — raises $c_T$ | Each axiom is an unverifiable bet |
| Oracles (Turing jump) | Yes, but creates new horizon | Infinite regress: $0' < 0'' < \dots$ |
| Self-modification | No — Löb forbids self-verification | Cannot prove improved version is consistent |
| Randomness as axiom ($\Omega$ bits) | Yes, but bits are "brute truths" | Abandonment of rational explanation |

## 4.9 The Three Independent Discoverers

| Author | Year | Motivation |
| :--- | :---: | :--- |
| **Ray Solomonoff** | 1960 | Universal inductive inference |
| **Andrei Kolmogorov** | 1965 | Foundations of probability |
| **Gregory Chaitin** | 1966 | Gödel's Incompleteness |

Three completely different motivations → the same mathematical concept. This suggests $K(x)$ is a **natural concept**, not an artifact of any particular perspective.

## 4.10 References

- Kolmogorov, A. N. (1965). "Three approaches to the quantitative definition of information." *Problems of Information Transmission*, 1(1), 1–7.
- Chaitin, G. J. (1974). "Information-Theoretic Limitations of Formal Systems." *Journal of the ACM*, 21(3), 403–424.
- Li, M. & Vitányi, P. (2008). *An Introduction to Kolmogorov Complexity and Its Applications*. Springer (3rd edition).
- Calude, C. S. (2002). *Information and Randomness: An Algorithmic Perspective*. Springer (2nd edition).

---

*Previous: [03 — Computability & Turing](./03_computability_turing.md) | Next: [05 — Model Theory](./05_model_theory.md)*
