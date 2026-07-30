// C5-REAL EXERGY CERTIFIED
//! # Omega 1 — Knowledge Graph Rewriting System
//!
//! Iteration over Kernel Ω₀.
//!
//! Thesis: computation of knowledge = rewriting of graphs under invariant preservation.
//!
//! ```text
//! J ──[TypedRewriteRule]──► J'   iff   ∀ Iₖ : Iₖ(G') = ⊤
//!      ↑ precondition          ↑ rollback if any Iₖ fails
//! ```
//!
//! Kernel Ω₁ = { KnowledgeGraph, TypedRewriteRule, EpistemicInvariant }
//!
//! The three terms are not independent:
//! - `TypedRewriteRule` is `InferenceRule` (Ω₀) lifted to the graph level.
//! - `EpistemicInvariant` is the property the rewrite must preserve.
//! - `KnowledgeGraph` is a set of `Judgement<T>` (Ω₀) + typed edges.
//!
//! Relationship to prior reductions:
//!   Category Theory  →  Objects + Morphisms
//!   Logic            →  Judgement + InferenceRule          [Ω₀]
//!   Graph Theory     →  Nodes + Edges + RewriteRules       [Ω₁]  ← here
//!   Type Theory      →  Types + Functions
//!
//! None of these is the "minimum absolute". Ω₁ is chosen because it
//! preserves epistemic invariants expressible as graph properties,
//! which neither Ω₀ nor the type-theoretic kernel can state directly.

#![allow(dead_code)]

use crate::omega0::Judgement;
use std::collections::{HashSet, VecDeque};
use std::fmt;

// ── EdgeKind ──────────────────────────────────────────────────────────────────

/// Typed edge labels. The TYPE of an edge determines which rewrite rules
/// may operate on it — this is the "typed" in Typed Rewrite Rules.
#[derive(Debug, Clone, PartialEq, Eq, Hash)]
pub enum EdgeKind {
    /// A provides positive support for B.
    Supports,
    /// A and B are in epistemic conflict.
    Contradicts,
    /// A is derived from B (consequence ← antecedent direction).
    DerivesFrom,
    /// A is a specialization of B.
    Specializes,
    /// A refines B with strictly greater precision.
    Refines,
}

// ── KnowledgeEdge ─────────────────────────────────────────────────────────────

#[derive(Debug, Clone)]
pub struct KnowledgeEdge {
    pub source: usize,
    pub target: usize,
    pub kind: EdgeKind,
    pub label: &'static str,
}

// ── KnowledgeGraph<T> ─────────────────────────────────────────────────────────

/// A directed graph where nodes are `Judgement<T>` and edges are typed.
///
/// The ONLY way to mutate this graph inside an invariant-preserving regime
/// is through `rewrite()`. Direct mutations bypass invariants — correct usage
/// restricts mutations to the `transform` field of a `TypedRewriteRule`.
#[derive(Clone)]
pub struct KnowledgeGraph<T: Clone + fmt::Debug> {
    pub nodes: Vec<Judgement<T>>,
    pub edges: Vec<KnowledgeEdge>,
}

impl<T: Clone + fmt::Debug> Default for KnowledgeGraph<T> {
    fn default() -> Self {
        Self::new()
    }
}

impl<T: Clone + fmt::Debug> KnowledgeGraph<T> {
    pub fn new() -> Self {
        Self {
            nodes: Vec::new(),
            edges: Vec::new(),
        }
    }

    /// Appends a `Judgement<T>` as a new node. Returns its stable index.
    pub fn add_node(&mut self, j: Judgement<T>) -> usize {
        let idx = self.nodes.len();
        self.nodes.push(j);
        idx
    }

    /// Adds a typed edge. Returns `false` if either endpoint is out of bounds.
    pub fn add_edge(
        &mut self,
        source: usize,
        target: usize,
        kind: EdgeKind,
        label: &'static str,
    ) -> bool {
        if source >= self.nodes.len() || target >= self.nodes.len() {
            return false;
        }
        self.edges.push(KnowledgeEdge {
            source,
            target,
            kind,
            label,
        });
        true
    }

    /// **The core Ω₁ operation.** `J → J'`
    ///
    /// Protocol:
    /// 1. Evaluate `rule.precondition(graph)`. If false → `PreconditionFailed`.
    /// 2. Snapshot the current state.
    /// 3. Apply `rule.transform(graph)`.
    /// 4. Evaluate ALL `invariants` on the post-transform state.
    ///    - All pass → `Committed`.
    ///    - Any fails → atomic rollback → `InvariantViolated`.
    ///
    /// Atomicity: rollback restores nodes AND edges to the pre-transform state.
    pub fn rewrite(
        &mut self,
        rule: &TypedRewriteRule<T>,
        invariants: &[EpistemicInvariant<T>],
    ) -> RewriteOutcome {
        if !(rule.precondition)(self) {
            return RewriteOutcome::PreconditionFailed;
        }

        // Snapshot for atomic rollback.
        let snap_nodes = self.nodes.clone();
        let snap_edges = self.edges.clone();

        (rule.transform)(self);

        for inv in invariants {
            if !inv(self) {
                self.nodes = snap_nodes;
                self.edges = snap_edges;
                return RewriteOutcome::InvariantViolated;
            }
        }

        RewriteOutcome::Committed
    }

    // ── Graph predicates ──────────────────────────────────────────────────────

    /// Detects a directed cycle via iterative DFS.
    /// A cycle in a `DerivesFrom` subgraph violates the acyclicity invariant.
    pub fn has_cycle(&self) -> bool {
        let n = self.nodes.len();
        if n == 0 {
            return false;
        }
        // 0 = unvisited, 1 = in-stack (gray), 2 = done (black)
        let mut state = vec![0u8; n];

        fn dfs(node: usize, edges: &[KnowledgeEdge], state: &mut Vec<u8>) -> bool {
            match state[node] {
                1 => return true,  // back-edge → cycle
                2 => return false, // already fully explored
                _ => {}
            }
            state[node] = 1;
            for e in edges {
                if e.source == node
                    && e.kind == EdgeKind::DerivesFrom
                    && e.target < state.len()
                    && dfs(e.target, edges, state)
                {
                    return true;
                }
            }
            state[node] = 2;
            false
        }

        for i in 0..n {
            if state[i] == 0 && dfs(i, &self.edges, &mut state) {
                return true;
            }
        }
        false
    }

    /// BFS reachability from `start` over all edge kinds.
    pub fn reachable_from(&self, start: usize) -> HashSet<usize> {
        let mut visited = HashSet::new();
        if start >= self.nodes.len() {
            return visited;
        }
        let mut queue = VecDeque::new();
        queue.push_back(start);
        while let Some(cur) = queue.pop_front() {
            if visited.insert(cur) {
                for e in &self.edges {
                    if e.source == cur && !visited.contains(&e.target) {
                        queue.push_back(e.target);
                    }
                }
            }
        }
        visited
    }

    /// Iterates over edges of a specific kind.
    pub fn edges_of_kind<'a>(
        &'a self,
        kind: &'a EdgeKind,
    ) -> impl Iterator<Item = &'a KnowledgeEdge> + 'a {
        self.edges.iter().filter(move |e| &e.kind == kind)
    }

    /// Iterates over all ground (Axiom + Empirical) nodes with their indices.
    pub fn ground_nodes(&self) -> impl Iterator<Item = (usize, &Judgement<T>)> {
        self.nodes
            .iter()
            .enumerate()
            .filter(|(_, j)| j.justification.is_ground())
    }

    pub fn node_count(&self) -> usize {
        self.nodes.len()
    }

    pub fn edge_count(&self) -> usize {
        self.edges.len()
    }

    pub fn is_empty(&self) -> bool {
        self.nodes.is_empty()
    }
}

// ── TypedRewriteRule ──────────────────────────────────────────────────────────

/// A named transformation over `KnowledgeGraph<T>` with a precondition.
///
/// Both `precondition` and `transform` are `fn` pointers (not closures):
/// this enforces that rules are stateless — their behaviour depends only
/// on the graph, not on captured environment. Stateless rules are
/// compositional and independently testable.
pub struct TypedRewriteRule<T: Clone + fmt::Debug> {
    pub name: &'static str,
    pub precondition: fn(&KnowledgeGraph<T>) -> bool,
    pub transform: fn(&mut KnowledgeGraph<T>),
}

// ── EpistemicInvariant ────────────────────────────────────────────────────────

/// A graph property that must hold before AND after every `rewrite()` call.
/// Violation triggers atomic rollback.
pub type EpistemicInvariant<T> = fn(&KnowledgeGraph<T>) -> bool;

// ── RewriteOutcome ────────────────────────────────────────────────────────────

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum RewriteOutcome {
    /// Rewrite applied; all invariants passed.
    Committed,
    /// Precondition false; graph unchanged.
    PreconditionFailed,
    /// Invariant violated; graph rolled back atomically.
    InvariantViolated,
}

// ── Built-in EpistemicInvariants ──────────────────────────────────────────────

/// The graph contains no directed cycle.
/// Required for derivation DAGs to be well-founded.
pub fn invariant_acyclic<T: Clone + fmt::Debug>(g: &KnowledgeGraph<T>) -> bool {
    !g.has_cycle()
}

/// The graph has at least one node.
pub fn invariant_nonempty<T: Clone + fmt::Debug>(g: &KnowledgeGraph<T>) -> bool {
    !g.is_empty()
}

/// No (source, target) pair has BOTH a `Supports` and a `Contradicts` edge.
/// A single node simultaneously supporting and contradicting another is a
/// logical contradiction at the graph level.
pub fn invariant_no_direct_contradiction<T: Clone + fmt::Debug>(g: &KnowledgeGraph<T>) -> bool {
    let supports: HashSet<(usize, usize)> = g
        .edges_of_kind(&EdgeKind::Supports)
        .map(|e| (e.source, e.target))
        .collect();
    let contradicts: HashSet<(usize, usize)> = g
        .edges_of_kind(&EdgeKind::Contradicts)
        .map(|e| (e.source, e.target))
        .collect();
    supports.is_disjoint(&contradicts)
}

// ── Tests ─────────────────────────────────────────────────────────────────────

#[cfg(test)]
mod tests {
    use super::*;
    use crate::omega0::Judgement;

    // ── Helpers ───────────────────────────────────────────────────────────────

    fn graph_i32() -> KnowledgeGraph<i32> {
        KnowledgeGraph::new()
    }

    fn axiom(v: i32, l: &'static str) -> Judgement<i32> {
        Judgement::axiom(v, l)
    }

    // ── Rewrite rule fn pointers ──────────────────────────────────────────────

    fn pre_always(_g: &KnowledgeGraph<i32>) -> bool {
        true
    }
    fn pre_never(_g: &KnowledgeGraph<i32>) -> bool {
        false
    }
    fn pre_has_nodes(g: &KnowledgeGraph<i32>) -> bool {
        g.node_count() >= 2
    }
    fn pre_has_edge(g: &KnowledgeGraph<i32>) -> bool {
        g.edge_count() > 0
    }

    fn tx_noop(_g: &mut KnowledgeGraph<i32>) {}

    fn tx_add_node(g: &mut KnowledgeGraph<i32>) {
        g.add_node(axiom(999, "added_by_rule"));
    }

    fn tx_add_back_edge(g: &mut KnowledgeGraph<i32>) {
        // Adds a DerivesFrom edge from last node back to first → cycle.
        if g.node_count() >= 2 {
            let last = g.node_count() - 1;
            g.add_edge(last, 0, EdgeKind::DerivesFrom, "back_edge");
        }
    }

    fn tx_add_contradiction(g: &mut KnowledgeGraph<i32>) {
        // Adds a Contradicts edge for the first Supports edge found.
        let pair = g
            .edges_of_kind(&EdgeKind::Supports)
            .map(|e| (e.source, e.target))
            .next();
        if let Some((s, t)) = pair {
            g.add_edge(s, t, EdgeKind::Contradicts, "injected_contradiction");
        }
    }

    // ── KnowledgeGraph basic operations ───────────────────────────────────────

    #[test]
    fn new_graph_is_empty() {
        let g = graph_i32();
        assert!(g.is_empty());
        assert_eq!(g.node_count(), 0);
        assert_eq!(g.edge_count(), 0);
    }

    #[test]
    fn add_node_returns_stable_monotone_index() {
        let mut g = graph_i32();
        let a = g.add_node(axiom(1, "a"));
        let b = g.add_node(axiom(2, "b"));
        let c = g.add_node(axiom(3, "c"));
        assert_eq!((a, b, c), (0, 1, 2));
        assert_eq!(g.node_count(), 3);
    }

    #[test]
    fn add_edge_valid_endpoints_succeeds() {
        let mut g = graph_i32();
        let a = g.add_node(axiom(1, "a"));
        let b = g.add_node(axiom(2, "b"));
        assert!(g.add_edge(a, b, EdgeKind::Supports, "a_supports_b"));
        assert_eq!(g.edge_count(), 1);
    }

    #[test]
    fn add_edge_oob_source_returns_false() {
        let mut g = graph_i32();
        let b = g.add_node(axiom(2, "b"));
        assert!(!g.add_edge(99, b, EdgeKind::Supports, "bad"));
    }

    #[test]
    fn add_edge_oob_target_returns_false() {
        let mut g = graph_i32();
        let a = g.add_node(axiom(1, "a"));
        assert!(!g.add_edge(a, 99, EdgeKind::Supports, "bad"));
    }

    // ── has_cycle ─────────────────────────────────────────────────────────────

    #[test]
    fn acyclic_chain_has_no_cycle() {
        let mut g = graph_i32();
        let a = g.add_node(axiom(1, "a"));
        let b = g.add_node(axiom(2, "b"));
        let c = g.add_node(axiom(3, "c"));
        g.add_edge(a, b, EdgeKind::DerivesFrom, "ab");
        g.add_edge(b, c, EdgeKind::DerivesFrom, "bc");
        assert!(!g.has_cycle());
    }

    #[test]
    fn back_edge_creates_cycle() {
        let mut g = graph_i32();
        let a = g.add_node(axiom(1, "a"));
        let b = g.add_node(axiom(2, "b"));
        let c = g.add_node(axiom(3, "c"));
        g.add_edge(a, b, EdgeKind::DerivesFrom, "ab");
        g.add_edge(b, c, EdgeKind::DerivesFrom, "bc");
        g.add_edge(c, a, EdgeKind::DerivesFrom, "back"); // cycle!
        assert!(g.has_cycle());
    }

    #[test]
    fn self_loop_is_a_cycle() {
        let mut g = graph_i32();
        let a = g.add_node(axiom(1, "a"));
        g.add_edge(a, a, EdgeKind::DerivesFrom, "self");
        assert!(g.has_cycle());
    }

    #[test]
    fn empty_graph_has_no_cycle() {
        let g = graph_i32();
        assert!(!g.has_cycle());
    }

    // ── reachable_from ────────────────────────────────────────────────────────

    #[test]
    fn reachable_from_isolated_node_returns_self() {
        let mut g = graph_i32();
        let a = g.add_node(axiom(1, "a"));
        let reach = g.reachable_from(a);
        assert_eq!(reach, HashSet::from([a]));
    }

    #[test]
    fn reachable_from_traverses_all_edges() {
        let mut g = graph_i32();
        let a = g.add_node(axiom(1, "a"));
        let b = g.add_node(axiom(2, "b"));
        let c = g.add_node(axiom(3, "c"));
        g.add_edge(a, b, EdgeKind::Supports, "ab");
        g.add_edge(b, c, EdgeKind::Supports, "bc");
        let reach = g.reachable_from(a);
        assert_eq!(reach, HashSet::from([a, b, c]));
    }

    #[test]
    fn reachable_from_oob_returns_empty() {
        let g = graph_i32();
        assert!(g.reachable_from(99).is_empty());
    }

    // ── rewrite: PreconditionFailed ───────────────────────────────────────────

    #[test]
    fn rewrite_precondition_false_returns_precondition_failed() {
        let mut g = graph_i32();
        g.add_node(axiom(1, "a"));
        let rule = TypedRewriteRule {
            name: "never",
            precondition: pre_never,
            transform: tx_noop,
        };
        let outcome = g.rewrite(&rule, &[]);
        assert_eq!(outcome, RewriteOutcome::PreconditionFailed);
        assert_eq!(g.node_count(), 1); // unchanged
    }

    // ── rewrite: Committed ────────────────────────────────────────────────────

    #[test]
    fn rewrite_committed_applies_transform() {
        let mut g = graph_i32();
        g.add_node(axiom(1, "a"));
        let rule = TypedRewriteRule {
            name: "add",
            precondition: pre_always,
            transform: tx_add_node,
        };
        let outcome = g.rewrite(&rule, &[]);
        assert_eq!(outcome, RewriteOutcome::Committed);
        assert_eq!(g.node_count(), 2);
    }

    #[test]
    fn rewrite_committed_with_passing_invariants() {
        let mut g = graph_i32();
        let a = g.add_node(axiom(1, "a"));
        let b = g.add_node(axiom(2, "b"));
        // Rule: add a Supports edge between nodes 0 and 1
        fn tx_add_support(g: &mut KnowledgeGraph<i32>) {
            g.add_edge(0, 1, EdgeKind::Supports, "s");
        }
        let rule = TypedRewriteRule {
            name: "add_support",
            precondition: pre_has_nodes,
            transform: tx_add_support,
        };
        let outcome = g.rewrite(&rule, &[invariant_acyclic, invariant_nonempty]);
        assert_eq!(outcome, RewriteOutcome::Committed);
        assert_eq!(g.edge_count(), 1);
        let _ = (a, b); // used in setup
    }

    // ── rewrite: InvariantViolated + Rollback ─────────────────────────────────

    #[test]
    fn rewrite_cycle_violation_triggers_rollback() {
        let mut g = graph_i32();
        let a = g.add_node(axiom(1, "a"));
        let b = g.add_node(axiom(2, "b"));
        g.add_edge(a, b, EdgeKind::DerivesFrom, "forward");

        let initial_edge_count = g.edge_count();
        let rule = TypedRewriteRule {
            name: "create_cycle",
            precondition: pre_always,
            transform: tx_add_back_edge,
        };
        let outcome = g.rewrite(&rule, &[invariant_acyclic]);
        assert_eq!(outcome, RewriteOutcome::InvariantViolated);
        // Rollback: edge count must be restored
        assert_eq!(g.edge_count(), initial_edge_count);
        assert!(!g.has_cycle());
    }

    #[test]
    fn rewrite_contradiction_violation_triggers_rollback() {
        let mut g = graph_i32();
        let a = g.add_node(axiom(1, "a"));
        let b = g.add_node(axiom(2, "b"));
        g.add_edge(a, b, EdgeKind::Supports, "support");

        let rule = TypedRewriteRule {
            name: "inject_contradiction",
            precondition: pre_has_edge,
            transform: tx_add_contradiction,
        };
        let outcome = g.rewrite(&rule, &[invariant_no_direct_contradiction]);
        assert_eq!(outcome, RewriteOutcome::InvariantViolated);
        // Rollback: only the original Supports edge remains
        assert_eq!(g.edge_count(), 1);
        assert!(g.edges_of_kind(&EdgeKind::Contradicts).next().is_none());
        let _ = (a, b);
    }

    #[test]
    fn rollback_preserves_exact_node_count() {
        let mut g = graph_i32();
        let a = g.add_node(axiom(10, "a"));
        let b = g.add_node(axiom(20, "b"));
        // Setup: a(0) →[ab]→ b(1)  (valid DAG)
        g.add_edge(a, b, EdgeKind::DerivesFrom, "ab");

        // Transform: adds c(2), then b→c and c→a, closing the loop a→b→c→a.
        fn tx_three_node_cycle(g: &mut KnowledgeGraph<i32>) {
            let c = g.add_node(Judgement::axiom(30, "c")); // idx = 2
            g.add_edge(1, c, EdgeKind::DerivesFrom, "bc");
            g.add_edge(c, 0, EdgeKind::DerivesFrom, "ca"); // closes cycle
        }
        let rule = TypedRewriteRule {
            name: "three_node_cycle",
            precondition: pre_always,
            transform: tx_three_node_cycle,
        };
        let pre_count = g.node_count();
        let outcome = g.rewrite(&rule, &[invariant_acyclic]);
        // The cycle must be detected → rollback must trigger
        assert_eq!(outcome, RewriteOutcome::InvariantViolated);
        // Both node AND edge additions must be rolled back atomically
        assert_eq!(g.node_count(), pre_count); // 2 nodes restored
        assert_eq!(g.edge_count(), 1); // only original "ab" edge
    }

    // ── Built-in invariants ───────────────────────────────────────────────────

    #[test]
    fn invariant_acyclic_passes_on_dag() {
        let mut g = graph_i32();
        let a = g.add_node(axiom(1, "a"));
        let b = g.add_node(axiom(2, "b"));
        g.add_edge(a, b, EdgeKind::DerivesFrom, "ab");
        assert!(invariant_acyclic(&g));
    }

    #[test]
    fn invariant_acyclic_fails_on_cycle() {
        let mut g = graph_i32();
        let a = g.add_node(axiom(1, "a"));
        let b = g.add_node(axiom(2, "b"));
        g.add_edge(a, b, EdgeKind::DerivesFrom, "ab");
        g.add_edge(b, a, EdgeKind::DerivesFrom, "ba");
        assert!(!invariant_acyclic(&g));
    }

    #[test]
    fn invariant_nonempty_passes_with_nodes() {
        let mut g = graph_i32();
        g.add_node(axiom(1, "a"));
        assert!(invariant_nonempty(&g));
    }

    #[test]
    fn invariant_nonempty_fails_on_empty_graph() {
        let g = graph_i32();
        assert!(!invariant_nonempty(&g));
    }

    #[test]
    fn invariant_no_direct_contradiction_passes_clean_graph() {
        let mut g = graph_i32();
        let a = g.add_node(axiom(1, "a"));
        let b = g.add_node(axiom(2, "b"));
        g.add_edge(a, b, EdgeKind::Supports, "support");
        assert!(invariant_no_direct_contradiction(&g));
    }

    #[test]
    fn invariant_no_direct_contradiction_fails_on_contradicting_pair() {
        let mut g = graph_i32();
        let a = g.add_node(axiom(1, "a"));
        let b = g.add_node(axiom(2, "b"));
        g.add_edge(a, b, EdgeKind::Supports, "s");
        g.add_edge(a, b, EdgeKind::Contradicts, "c"); // same (a,b) pair → violation
        assert!(!invariant_no_direct_contradiction(&g));
    }

    // ── edges_of_kind ─────────────────────────────────────────────────────────

    #[test]
    fn edges_of_kind_filters_correctly() {
        let mut g = graph_i32();
        let a = g.add_node(axiom(1, "a"));
        let b = g.add_node(axiom(2, "b"));
        let c = g.add_node(axiom(3, "c"));
        g.add_edge(a, b, EdgeKind::Supports, "s1");
        g.add_edge(b, c, EdgeKind::DerivesFrom, "d1");
        g.add_edge(a, c, EdgeKind::Supports, "s2");

        let supports: Vec<_> = g.edges_of_kind(&EdgeKind::Supports).collect();
        assert_eq!(supports.len(), 2);
        let derives: Vec<_> = g.edges_of_kind(&EdgeKind::DerivesFrom).collect();
        assert_eq!(derives.len(), 1);
        let contradicts: Vec<_> = g.edges_of_kind(&EdgeKind::Contradicts).collect();
        assert_eq!(contradicts.len(), 0);
    }

    // ── ground_nodes ──────────────────────────────────────────────────────────

    #[test]
    fn ground_nodes_excludes_derived_judgements() {
        use crate::omega0::ProofContext;
        let mut ctx: ProofContext<i32> = ProofContext::new();
        fn rule_sum(ants: &[&crate::omega0::Judgement<i32>]) -> Option<i32> {
            Some(ants.iter().map(|j| j.proposition).sum())
        }
        let a = ctx.assert(Judgement::axiom(1, "a"));
        let b = ctx.assert(Judgement::axiom(2, "b"));
        let derived_idx = ctx.derive("sum", rule_sum, &[a, b]).unwrap();

        let mut g: KnowledgeGraph<i32> = KnowledgeGraph::new();
        g.add_node(ctx.get(a).unwrap().clone());
        g.add_node(ctx.get(b).unwrap().clone());
        g.add_node(ctx.get(derived_idx).unwrap().clone());

        let grounds: Vec<usize> = g.ground_nodes().map(|(i, _)| i).collect();
        assert_eq!(grounds.len(), 2);
        assert!(grounds.contains(&0));
        assert!(grounds.contains(&1));
        assert!(!grounds.contains(&2));
    }

    // ── Chained rewrites maintain consistency ─────────────────────────────────

    #[test]
    fn chained_rewrites_accumulate_state_correctly() {
        let mut g = graph_i32();
        g.add_node(axiom(1, "seed"));

        let rule = TypedRewriteRule {
            name: "grow",
            precondition: pre_always,
            transform: tx_add_node,
        };

        for _ in 0..5 {
            let outcome = g.rewrite(&rule, &[invariant_acyclic, invariant_nonempty]);
            assert_eq!(outcome, RewriteOutcome::Committed);
        }

        // 1 seed + 5 applied = 6 nodes
        assert_eq!(g.node_count(), 6);
        assert!(invariant_acyclic(&g));
        assert!(invariant_nonempty(&g));
    }
}
