# 06 — The Curry-Howard-Lambek Correspondence

## 6.1 The Trilateral Isomorphism

The **Curry-Howard-Lambek correspondence** (also known as the Curry-Howard isomorphism or formulas-as-types isomorphism) establishes a profound structural identity between three previously distinct fields of mathematics:

$$\text{Proof Theory (Logic)} \;\longleftrightarrow\; \text{Type Theory (Computer Science)} \;\longleftrightarrow\; \text{Category Theory (Algebra)}$$

| Proof Theory (Logic) | Type Theory (CS) | Category Theory |
| :--- | :--- | :--- |
| Proposition $\phi$ | Type $A$ | Object $A$ |
| Proof of $\phi$ | Program / Term $e : A$ | Morphism $f : I \to A$ |
| Implication $\phi \to \psi$ | Function Type $A \to B$ | Exponential Object $B^A$ |
| Conjunction $\phi \land \psi$ | Product Type $A \times B$ | Cartesian Product $A \times B$ |
| Disjunction $\phi \lor \psi$ | Sum / Coproduct Type $A + B$ | Coproduct $A \sqcup B$ |
| True $\top$ | Unit Type `()` | Terminal Object $1$ |
| False $\bot$ | Empty / Void Type | Initial Object $0$ |
| Universal Quantification $\forall x. \phi(x)$ | Dependent Product Type $\Pi(x:A). B(x)$ | Limit / Right Adjoint |
| Existential Quantification $\exists x. \phi(x)$ | Dependent Pair Type $\Sigma(x:A). B(x)$ | Colimit / Left Adjoint |
| Proof Normalization / Cut Elimination | Program Execution / $\beta$-Reduction | Morphism Composition |

Under this correspondence:
- **Proving a theorem** is literally **writing a program** that inhabits a specified type.
- **Checking a proof** is literally **type-checking a program**.

## 6.2 Intuitionistic vs. Classical Logic

The standard Curry-Howard correspondence maps directly to **Constructive / Intuitionistic Logic**, not classical logic:

- In intuitionistic logic, the **Law of Excluded Middle** ($\phi \lor \neg\phi$) and **Double Negation Elimination** ($\neg\neg\phi \to \phi$) do not hold universally.
- Under Curry-Howard, a proof of $\phi \lor \psi$ must explicitly provide either a proof of $\phi$ or a proof of $\psi$ (a tagged union value `Left(a)` or `Right(b)`).
- Classical logic corresponds to computational systems with **control operators / continuations** (such as Scheme's `call/cc` or Parigot's $\lambda\mu$-calculus).

## 6.3 Inhabitance and Type Checking

| Problem | Logical Statement | Computational Meaning | Decidability |
| :--- | :--- | :--- | :---: |
| **Type Checking** | Given proof $\pi$ and proposition $\phi$, is $\pi$ a valid proof of $\phi$? | Given term $e$ and type $A$, is $e : A$? | **Decidable** (for standard type systems) |
| **Type Inhabitance** | Given proposition $\phi$, does there exist a proof of $\phi$? | Given type $A$, does there exist a term $e : A$? | **Undecidable** (in dependent / rich type systems) |

### The Connection to Incompleteness

In rich type systems capable of dependent types and arithmetic (such as Coq, Lean, or Agda):
1. **Gödel's First Theorem** translates to: There exist valid types $A$ such that $A$ is true in the intended model, but **no term $e : A$ can be constructed** within the formal system.
2. **Uninhabited Types:** The type representing consistency `Con(System)` is an inhabited type in reality (if consistent), but **no term of type `Con(System)` can be written in the system itself** (Second Incompleteness Theorem).

## 6.4 Robinson's Q in Type Theory

When we express Robinson Arithmetic $Q$ inside a dependently typed language (such as Lean 4 or Agda):

- The 7 axioms of $Q$ become primitive constructors or axioms of type `Prop`.
- $\Sigma_1$-completeness means that for any true $\Sigma_1$ proposition, a term inhabiting that proposition type can be **automatically synthesized by a algorithm**.
- $\Pi_1$-incompleteness means that types representing universal properties (like `∀ (x y : Nat), x + y = y + x`) **cannot be inhabited** using only the constructors of $Q$.

```lean
-- In Lean 4 representation of Q:
theorem add_zero_right (x : QNat) : QAdd x QZero = x := by
  -- Provable in Q via Q4 axiom
  exact q4 x

theorem add_zero_left (x : QNat) : QAdd QZero x = x := by
  -- NOT provable in Q! No term of this type exists in Q.
  sorry
```

## 6.5 Homotopy Type Theory (HoTT) and Univalence

Modern developments extend Curry-Howard to topology via **Homotopy Type Theory**:

- **Types** are topological spaces (or homotopy types).
- **Terms / Elements** are points in the space.
- **Equality** $a =_A b$ is a continuous path between points $a$ and $b$.
- **Higher Equalities** are homotopies between paths.
- **Voevodsky's Univalence Axiom:** $(A \simeq B) \simeq (A = B)$ — isomorphic types are literally equal.

In HoTT, structural isomorphism (like Weisfeiler-Lehman graph equivalence in **INV_C5_28**) is formally unified with identity, providing a type-theoretic foundation for structural equivalence.

## 6.6 Implications for BABYLON-60

- **Proof IR as Type Signatures:** In BABYLON-60, executable proofs (`proof_ir`) are first-class terms whose verification is pure type-checking (decidable in $O(N)$ time), while proof generation is type inhabitance search (undecidable in general).
- **Decidable Verification vs. Undecidable Synthesis:** Execution/Verification is always $\Sigma_1$ (type-checking a given trace). Synthesis is $\Pi_1$ or higher.

## 6.7 References

- Howard, W. A. (1980). "The formulae-as-types notion of construction." *Essays on Combinatory Logic, Lambda Calculus and Formalism*, pp. 479–490.
- Wadler, P. (2015). "Propositions as Types." *Communications of the ACM*, 58(12), 75–84.
- The Univalent Foundations Program (2013). *Homotopy Type Theory: Univalent Foundations of Mathematics*. Institute for Advanced Study.

---

*Previous: [05 — Model Theory](./05_model_theory.md) | Next: [07 — Cross-Domain Isomorphisms](./07_cross_domain.md)*
