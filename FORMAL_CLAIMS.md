# FORMAL_CLAIMS.md — Frozen Epistemic Boundary v1.0.0

> **STATUS: FROZEN / NORMATIVE**  
> **Repository**: `borjamoskv/teorema-robinson-moskv`  
> **Commit Lock**: Pre-experimental baseline  

This document specifies the exact boundary of what has been formally proven in Lean 4, what constitutes necessary bridge assumptions, what remains purely empirical, and what is explicitly **not** claimed by the Teorema Robinson-Moskv architecture.

---

## 1. Explicit Taxonomy Matrix

```yaml
claims:
  proven_in_lean:
    - SafeState_construction
    - invariant_preservation
    - reachability_inclusion
    - bounded_reachability_inclusion
    - runtime_trace_refinement

  assumptions_required:
    - E_CTM_subset_E_M
    - cost_equivalence
    - runtime_refines_formal_model
    - legal_recomputed_independently

  empirical_only:
    - coverage_improvement
    - CTM_superiority
    - policy_advantage
    - stochastic_superiority

  explicitly_not_claimed:
    - CTM_creates_new_solutions
    - CTM_is_globally_optimal
    - Lean_proves_empirical_coverage
    - benchmark_proves_formal_reachability
```

---

## 2. Formal Definitions of Claim Categories

### 2.1 `proven_in_lean`
The following properties possess machine-verified Lean 4 proofs within `proof/lean/`:

1. **`SafeState_construction`**: Construction of valid initial state invariants $s_0 \in \mathcal{S}_{\text{safe}}$ under defined structural bounds.
2. **`invariant_preservation`**: Proof that $\forall s \in \mathcal{S}_{\text{safe}}, a \in \text{LegalActions}(s) \implies \delta(s, a) \in \mathcal{S}_{\text{safe}}$.
3. **`reachability_inclusion`**: Conditional proof that $\text{Reach}(\text{CTM}) \subseteq \text{Reach}(\mathcal{M})$ given energy/cost envelope containment.
4. **`bounded_reachability_inclusion`**: Proof that budget-bounded execution traces preserve reachability containment under step-cost monotonicity.
5. **`runtime_trace_refinement`**: Proof that any trace $\tau$ satisfying the abstract trace contract preserves the safety properties of the formal transition relation.

### 2.2 `assumptions_required`
The logical validity of the formal model when applied to external code requires the unverified truth of:

1. **$\mathcal{E}_{\text{CTM}} \subseteq \mathcal{E}_{\mathcal{M}}$**: Energy/effort set inclusion between CTM transition operators and standard Markov operators.
2. **`cost_equivalence`**: Operational identity between formal budget metrics in Lean 4 and runtime CPU/token/step counts in BABYLON.
3. **`runtime_refines_formal_model`**: Epistemic assumption that the Rust/Python runtime execution strictly refines the state transition semantics $\delta(s, a)$ specified in Lean 4.
4. **`legal_recomputed_independently`**: Operational assumption that action legality is evaluated by an independent, uncorrupted evaluator outside the candidate trace generator.

### 2.3 `empirical_only`
The following properties **cannot** be derived from mathematical proof and depend strictly on statistical inference over benchmark datasets:

1. **`coverage_improvement`**: Higher ratio of solved benchmark tasks by CTM relative to baseline control arms.
2. **`CTM_superiority`**: Statistically significant performance advantage on predefined task distributions.
3. **`policy_advantage`**: Higher sample efficiency or lower token expenditure per successful completion.
4. **`stochastic_superiority`**: Expected utility ordering under non-deterministic LLM sampling policies.

### 2.4 `explicitly_not_claimed`
The system explicitly disclaims and denies the following interpretations:

1. **`CTM_creates_new_solutions`**: CTM does not generate state transitions outside the reachability space of the underlying problem domain.
2. **`CTM_is_globally_optimal`**: CTM does not guarantee global cost minimal paths or Pareto optimal execution traces.
3. **`Lean_proves_empirical_coverage`**: Machine-verified proofs in Lean 4 do **not** imply non-zero empirical benchmark coverage.
4. **`benchmark_proves_formal_reachability`**: Statistical success on empirical benchmark datasets does **not** prove mathematical soundness of formal Lean specs.

---

## 3. Epistemic Guardrail Statement

> Any claim converting a conditional Lean theorem into an unconditional empirical statement, or attributing benchmark results to formal theorem soundness without validating runtime refinement assumptions, constitutes **epistemic invalidity**.
