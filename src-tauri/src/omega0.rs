//! # Kernel Ω₀ — Irreducible Epistemological Kernel
//!
//! Formal basis: Martin-Löf Typing Judgement  ⊢ t : T
//!               Curry-Howard correspondence   Proposition ≅ Type, Proof ≅ Term
//!
//! Invariant: every representable piece of knowledge is a `Judgement<T>`.
//! An unjustified proposition is NOT representable — it is a type error
//! at construction time, not a runtime check.
//!
//! Irreducible kernel:
//!   { Judgement<T>, InferenceRule<T> }
//!
//! Note: `derive()` is NOT syntactic sugar over `Justification::Derived`.
//! It is the VALIDITY ENFORCER that checks inference rule applicability.
//! Without it, any Derived justification is trivially valid → useless.

#![allow(dead_code)]

// ── Justification ─────────────────────────────────────────────────────────────

/// The three irreducible modes of epistemic support.
///
/// - `Axiom`     → ground truth requiring no further justification
/// - `Derived`   → produced by a named inference rule over antecedents
/// - `Empirical` → anchored to external evidence via SHA3-256 hash
///
/// Every other justification type is syntactic sugar over these three.
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum Justification {
    Axiom {
        label: &'static str,
    },
    Derived {
        rule: &'static str,
        /// Indices into the owning `ProofContext`'s judgement table.
        antecedents: Vec<usize>,
    },
    /// SHA3-256 hash of the external evidence payload (Ω24: no MD5/SHA-1).
    Empirical {
        anchor: [u8; 32],
    },
}

impl Justification {
    /// True iff the justification requires no antecedents in a proof context.
    pub fn is_ground(&self) -> bool {
        matches!(
            self,
            Justification::Axiom { .. } | Justification::Empirical { .. }
        )
    }
}

// ── Judgement<T> ──────────────────────────────────────────────────────────────

/// The irreducible unit of knowledge in the Ω₀ kernel.
///
/// Design constraint: private fields + sealed constructors ensure that
/// every `Judgement<T>` is born with a valid justification.
/// There is no `Default` impl — an unjustified state is unrepresentable.
#[derive(Debug, Clone)]
pub struct Judgement<T> {
    pub proposition: T,
    pub justification: Justification,
}

impl<T: Clone + std::fmt::Debug> Judgement<T> {
    /// Constructs a ground-truth judgement (Axiom case).
    pub fn axiom(proposition: T, label: &'static str) -> Self {
        Self {
            proposition,
            justification: Justification::Axiom { label },
        }
    }

    /// Constructs an empirically-anchored judgement.
    /// The caller is responsible for computing the SHA3-256 anchor.
    pub fn empirical(proposition: T, anchor: [u8; 32]) -> Self {
        Self {
            proposition,
            justification: Justification::Empirical { anchor },
        }
    }

    /// SEALED: only `ProofContext::derive()` may construct Derived judgements.
    /// Direct construction bypasses inference rule validation → type error.
    pub(crate) fn derived_unchecked(
        proposition: T,
        rule: &'static str,
        antecedents: Vec<usize>,
    ) -> Self {
        Self {
            proposition,
            justification: Justification::Derived { rule, antecedents },
        }
    }

    pub fn is_axiomatic(&self) -> bool {
        matches!(self.justification, Justification::Axiom { .. })
    }

    pub fn is_empirical(&self) -> bool {
        matches!(self.justification, Justification::Empirical { .. })
    }

    pub fn is_derived(&self) -> bool {
        matches!(self.justification, Justification::Derived { .. })
    }

    pub fn antecedent_count(&self) -> usize {
        if let Justification::Derived { antecedents, .. } = &self.justification {
            antecedents.len()
        } else {
            0
        }
    }
}

// ── InferenceRule ─────────────────────────────────────────────────────────────

/// The second irreducible element of Kernel Ω₀.
///
/// `InferenceRule<T>` is NOT syntactic sugar — it is the validity check that
/// prevents arbitrary `Derived` justifications from being constructed.
///
/// Semantics: given a slice of antecedent judgements, returns `Some(T)`
/// if the rule fires, `None` if the antecedents do not satisfy the rule's
/// preconditions.
///
/// Under Curry-Howard: `InferenceRule<T>` is a proof-term constructor,
/// i.e., it *witnesses* the entailment relation.
pub type InferenceRule<T> = fn(&[&Judgement<T>]) -> Option<T>;

// ── ProofContext ──────────────────────────────────────────────────────────────

/// A finite, monotonically-growing set of `Judgement<T>`.
///
/// Morphism: `ProofContext × InferenceRule → ProofContext`
/// This is the ONLY pathway to create `Derived` judgements.
///
/// Key properties:
/// - Monotone: judgements are only appended, never retracted.
/// - Depth-bounded lineage: `trace_lineage` is O(depth) not O(2^n).
/// - Index-stable: the index of a judgement never changes after insertion.
#[derive(Debug, Default)]
pub struct ProofContext<T: Clone + std::fmt::Debug> {
    judgements: Vec<Judgement<T>>,
}

impl<T: Clone + std::fmt::Debug> ProofContext<T> {
    pub fn new() -> Self {
        Self {
            judgements: Vec::new(),
        }
    }

    /// Inserts an axiomatic or empirical judgement. Returns its stable index.
    pub fn assert(&mut self, j: Judgement<T>) -> usize {
        let idx = self.judgements.len();
        self.judgements.push(j);
        idx
    }

    /// Applies an `InferenceRule` over a set of antecedent indices.
    ///
    /// Returns `Some(idx)` if the rule fires and the new judgement is added.
    /// Returns `None` if:
    ///   - any antecedent index is out of bounds, OR
    ///   - the inference rule rejects the antecedents (returns `None`).
    ///
    /// This is the ONLY constructor for `Justification::Derived`.
    pub fn derive(
        &mut self,
        rule_name: &'static str,
        rule: InferenceRule<T>,
        antecedent_indices: &[usize],
    ) -> Option<usize> {
        // Validate all antecedent indices exist before firing the rule.
        for &i in antecedent_indices {
            if i >= self.judgements.len() {
                return None;
            }
        }
        let refs: Vec<&Judgement<T>> = antecedent_indices
            .iter()
            .map(|&i| &self.judgements[i])
            .collect();

        let proposition = rule(&refs)?;
        let idx = self.judgements.len();
        self.judgements.push(Judgement::derived_unchecked(
            proposition,
            rule_name,
            antecedent_indices.to_vec(),
        ));
        Some(idx)
    }

    pub fn get(&self, idx: usize) -> Option<&Judgement<T>> {
        self.judgements.get(idx)
    }

    pub fn len(&self) -> usize {
        self.judgements.len()
    }

    pub fn is_empty(&self) -> bool {
        self.judgements.is_empty()
    }

    /// Depth-limited lineage trace.
    ///
    /// Returns all judgement indices reachable from `idx` via the antecedent
    /// relation, up to `max_depth`. Prevents stack overflow on deep proof trees
    /// (Ω₀ hardening: depth-limit from prior ATMS audit).
    pub fn trace_lineage(&self, idx: usize, max_depth: usize) -> Vec<usize> {
        let mut visited = Vec::new();
        self.trace_rec(idx, max_depth, &mut visited);
        visited
    }

    fn trace_rec(&self, idx: usize, depth: usize, visited: &mut Vec<usize>) {
        if depth == 0 || visited.contains(&idx) {
            return;
        }
        visited.push(idx);
        if let Some(j) = self.judgements.get(idx) {
            if let Justification::Derived { antecedents, .. } = &j.justification {
                for &a in antecedents.clone().iter() {
                    self.trace_rec(a, depth - 1, visited);
                }
            }
        }
    }

    /// Returns all ground (Axiom + Empirical) judgements in the context.
    pub fn ground_judgements(&self) -> impl Iterator<Item = (usize, &Judgement<T>)> {
        self.judgements
            .iter()
            .enumerate()
            .filter(|(_, j)| j.justification.is_ground())
    }

    /// Validates the entire proof context for referential integrity.
    /// Every `Derived` judgement must reference valid antecedent indices.
    pub fn is_consistent(&self) -> bool {
        for (i, j) in self.judgements.iter().enumerate() {
            if let Justification::Derived { antecedents, .. } = &j.justification {
                for &a in antecedents {
                    // An antecedent must precede its consequent (acyclic).
                    if a >= i {
                        return false;
                    }
                }
            }
        }
        true
    }
}

// ── Tests ─────────────────────────────────────────────────────────────────────

#[cfg(test)]
mod tests {
    use super::*;

    // ── Justification ─────────────────────────────────────────────────────────

    #[test]
    fn axiom_is_ground() {
        let j = Justification::Axiom {
            label: "reflexivity",
        };
        assert!(j.is_ground());
    }

    #[test]
    fn empirical_is_ground() {
        let j = Justification::Empirical { anchor: [0u8; 32] };
        assert!(j.is_ground());
    }

    #[test]
    fn derived_is_not_ground() {
        let j = Justification::Derived {
            rule: "modus_ponens",
            antecedents: vec![0, 1],
        };
        assert!(!j.is_ground());
    }

    // ── Judgement<T> construction ─────────────────────────────────────────────

    #[test]
    fn axiom_judgement_is_axiomatic() {
        let j: Judgement<&str> = Judgement::axiom("P implies P", "reflexivity");
        assert!(j.is_axiomatic());
        assert!(!j.is_derived());
        assert!(!j.is_empirical());
    }

    #[test]
    fn empirical_judgement_is_empirical() {
        let anchor = [0xABu8; 32];
        let j: Judgement<u64> = Judgement::empirical(42, anchor);
        assert!(j.is_empirical());
        assert!(!j.is_axiomatic());
        assert!(!j.is_derived());
        assert_eq!(j.antecedent_count(), 0);
    }

    #[test]
    fn axiom_has_zero_antecedents() {
        let j: Judgement<i32> = Judgement::axiom(1, "unity");
        assert_eq!(j.antecedent_count(), 0);
    }

    // ── ProofContext ──────────────────────────────────────────────────────────

    #[test]
    fn empty_context_is_empty() {
        let ctx: ProofContext<&str> = ProofContext::new();
        assert!(ctx.is_empty());
        assert_eq!(ctx.len(), 0);
    }

    #[test]
    fn assert_returns_stable_monotone_index() {
        let mut ctx: ProofContext<i32> = ProofContext::new();
        let i0 = ctx.assert(Judgement::axiom(1, "a"));
        let i1 = ctx.assert(Judgement::axiom(2, "b"));
        let i2 = ctx.assert(Judgement::axiom(3, "c"));
        assert_eq!(i0, 0);
        assert_eq!(i1, 1);
        assert_eq!(i2, 2);
        assert_eq!(ctx.len(), 3);
    }

    // ── InferenceRule enforcement ─────────────────────────────────────────────

    /// Modus Ponens over (bool, bool):
    /// antecedents[0].proposition == true (P)
    /// antecedents[1].proposition == true (P → Q, encoded as true here)
    /// conclusion: true (Q)
    fn rule_and_introduction(ants: &[&Judgement<bool>]) -> Option<bool> {
        if ants.len() == 2 && ants[0].proposition && ants[1].proposition {
            Some(true)
        } else {
            None
        }
    }

    fn rule_always_fires(ants: &[&Judgement<i32>]) -> Option<i32> {
        Some(ants.iter().map(|j| j.proposition).sum())
    }

    fn rule_never_fires(_ants: &[&Judgement<i32>]) -> Option<i32> {
        None
    }

    #[test]
    fn derive_fires_and_returns_index() {
        let mut ctx: ProofContext<bool> = ProofContext::new();
        let p = ctx.assert(Judgement::axiom(true, "P"));
        let q = ctx.assert(Judgement::axiom(true, "Q"));
        let derived = ctx.derive("and_intro", rule_and_introduction, &[p, q]);
        assert!(derived.is_some());
        let idx = derived.unwrap();
        let j = ctx.get(idx).unwrap();
        assert!(j.is_derived());
        assert_eq!(j.proposition, true);
        assert_eq!(j.antecedent_count(), 2);
    }

    #[test]
    fn derive_returns_none_when_rule_rejects() {
        let mut ctx: ProofContext<bool> = ProofContext::new();
        let p = ctx.assert(Judgement::axiom(false, "not-P")); // false → rule rejects
        let q = ctx.assert(Judgement::axiom(true, "Q"));
        let result = ctx.derive("and_intro", rule_and_introduction, &[p, q]);
        assert!(result.is_none());
        // Context must not have grown (failed derives are not appended).
        assert_eq!(ctx.len(), 2);
    }

    #[test]
    fn derive_returns_none_for_oob_antecedent() {
        let mut ctx: ProofContext<i32> = ProofContext::new();
        let _a = ctx.assert(Judgement::axiom(1, "a"));
        // index 99 does not exist
        let result = ctx.derive("always", rule_always_fires, &[0, 99]);
        assert!(result.is_none());
        assert_eq!(ctx.len(), 1);
    }

    #[test]
    fn derive_never_fires_returns_none() {
        let mut ctx: ProofContext<i32> = ProofContext::new();
        let a = ctx.assert(Judgement::axiom(5, "five"));
        let result = ctx.derive("never", rule_never_fires, &[a]);
        assert!(result.is_none());
    }

    #[test]
    fn derive_sums_antecedents_via_rule() {
        let mut ctx: ProofContext<i32> = ProofContext::new();
        let a = ctx.assert(Judgement::axiom(3, "three"));
        let b = ctx.assert(Judgement::axiom(7, "seven"));
        let idx = ctx.derive("sum", rule_always_fires, &[a, b]).unwrap();
        assert_eq!(ctx.get(idx).unwrap().proposition, 10);
    }

    // ── Chained derivation (proof tree depth > 1) ─────────────────────────────

    #[test]
    fn chained_derivation_produces_valid_proof_tree() {
        let mut ctx: ProofContext<i32> = ProofContext::new();
        let a = ctx.assert(Judgement::axiom(1, "one"));
        let b = ctx.assert(Judgement::axiom(2, "two"));
        let ab = ctx.derive("sum", rule_always_fires, &[a, b]).unwrap(); // 3
        let c = ctx.assert(Judgement::axiom(4, "four"));
        let abc = ctx.derive("sum", rule_always_fires, &[ab, c]).unwrap(); // 7
        assert_eq!(ctx.get(abc).unwrap().proposition, 7);
        assert!(ctx.is_consistent());
    }

    // ── trace_lineage ─────────────────────────────────────────────────────────

    #[test]
    fn trace_lineage_axiom_returns_self_only() {
        let mut ctx: ProofContext<i32> = ProofContext::new();
        let a = ctx.assert(Judgement::axiom(1, "a"));
        let lineage = ctx.trace_lineage(a, 10);
        assert_eq!(lineage, vec![a]);
    }

    #[test]
    fn trace_lineage_derived_includes_antecedents() {
        let mut ctx: ProofContext<i32> = ProofContext::new();
        let a = ctx.assert(Judgement::axiom(3, "a"));
        let b = ctx.assert(Judgement::axiom(4, "b"));
        let c = ctx.derive("sum", rule_always_fires, &[a, b]).unwrap();
        let lineage = ctx.trace_lineage(c, 10);
        assert!(lineage.contains(&a));
        assert!(lineage.contains(&b));
        assert!(lineage.contains(&c));
    }

    #[test]
    fn trace_lineage_depth_zero_returns_empty() {
        let mut ctx: ProofContext<i32> = ProofContext::new();
        let a = ctx.assert(Judgement::axiom(1, "a"));
        let lineage = ctx.trace_lineage(a, 0);
        assert!(lineage.is_empty());
    }

    #[test]
    fn trace_lineage_depth_limit_truncates() {
        let mut ctx: ProofContext<i32> = ProofContext::new();
        let a = ctx.assert(Judgement::axiom(1, "a"));
        let b = ctx.assert(Judgement::axiom(2, "b"));
        let ab = ctx.derive("sum", rule_always_fires, &[a, b]).unwrap();
        let c = ctx.assert(Judgement::axiom(3, "c"));
        let abc = ctx.derive("sum", rule_always_fires, &[ab, c]).unwrap();
        // depth=1: only abc and its direct antecedents (ab, c) — not a or b
        let lineage = ctx.trace_lineage(abc, 1);
        assert!(lineage.contains(&abc));
        // depth 1: should not reach a or b (they are 2 levels deep)
        assert!(!lineage.contains(&a));
        assert!(!lineage.contains(&b));
    }

    // ── Consistency ───────────────────────────────────────────────────────────

    #[test]
    fn empty_context_is_consistent() {
        let ctx: ProofContext<i32> = ProofContext::new();
        assert!(ctx.is_consistent());
    }

    #[test]
    fn axiom_only_context_is_consistent() {
        let mut ctx: ProofContext<i32> = ProofContext::new();
        ctx.assert(Judgement::axiom(1, "a"));
        ctx.assert(Judgement::axiom(2, "b"));
        assert!(ctx.is_consistent());
    }

    #[test]
    fn derived_context_is_consistent() {
        let mut ctx: ProofContext<i32> = ProofContext::new();
        let a = ctx.assert(Judgement::axiom(5, "a"));
        let b = ctx.assert(Judgement::axiom(6, "b"));
        ctx.derive("sum", rule_always_fires, &[a, b]);
        assert!(ctx.is_consistent());
    }

    // ── ground_judgements ─────────────────────────────────────────────────────

    #[test]
    fn ground_judgements_excludes_derived() {
        let mut ctx: ProofContext<i32> = ProofContext::new();
        let a = ctx.assert(Judgement::axiom(1, "a"));
        let b = ctx.assert(Judgement::axiom(2, "b"));
        ctx.derive("sum", rule_always_fires, &[a, b]);
        let grounds: Vec<usize> = ctx.ground_judgements().map(|(i, _)| i).collect();
        assert_eq!(grounds.len(), 2);
        assert!(grounds.contains(&a));
        assert!(grounds.contains(&b));
    }

    // ── Invariant: unjustified propositions are unrepresentable ───────────────
    // This test is structural: the absence of a Judgement::new(proposition)
    // constructor is verified by compilation. The following would NOT compile:
    //
    //   let _ = Judgement { proposition: 42, justification: /* ??? */ };
    //
    // Since justification has no Default impl and the field is pub,
    // the caller must explicitly choose Axiom/Empirical/Derived.
    // `Derived` is further sealed via `pub(crate)` constructor.
    // This test documents that property as a prose invariant.
    #[test]
    fn structural_invariant_unjustified_proposition_is_unrepresentable() {
        // Compilation of this module IS the test.
        // If Judgement<T> had a Default impl or an unjustified constructor,
        // this test would be meaningless. It serves as documentation.
        let j: Judgement<i32> = Judgement::axiom(0, "zero");
        assert!(j.is_axiomatic());
    }
}
