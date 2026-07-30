// C5-REAL EXERGY CERTIFIED
//! # Omega 2 — Rewriting Strategies and Path Finding
//!
//! Iteration over Kernel Ω₁.
//!
//! Thesis: A rewriting strategy controls the application of rewrite rules
//! over the knowledge graph to reach a target belief state.
//!
//! Kernel Ω₂ = { Strategy, StrategyExecutor<T>, Trace }
//!
//! Control strategies are formal specifications of path routing in the Poset
//! of KnowledgeGraph states. They allow compiling complex pipelines (like
//! Deep Research, Multi-Agent reflection) into atomic, transactional sequences
//! of graph rewrites.

#![allow(dead_code)]

use crate::omega1::{EpistemicInvariant, KnowledgeGraph, RewriteOutcome, TypedRewriteRule};
use std::collections::{HashSet, VecDeque};
use std::fmt;

// ── Strategy ──────────────────────────────────────────────────────────────────

/// Primitive strategy combinators for orchestrating graph rewrites.
#[derive(Clone, PartialEq, Eq)]
pub enum Strategy {
    /// Apply a single rule by name.
    Apply(String),
    /// Execute a sequence of strategies. If *any* step fails, the entire sequence
    /// rolls back atomically to the initial state (transactional composition).
    Seq(Vec<Strategy>),
    /// Try strategies in order. Commits the first one that succeeds. Fails if all fail.
    Choice(Vec<Strategy>),
    /// Repeatedly apply a strategy until it makes no more changes. Always succeeds.
    Repeat(Box<Strategy>),
    /// Attempt a strategy. If it fails, revert to initial state and succeed (never fails).
    Try(Box<Strategy>),
}

impl fmt::Debug for Strategy {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            Self::Apply(name) => write!(f, "Apply({})", name),
            Self::Seq(list) => write!(f, "Seq({:?})", list),
            Self::Choice(list) => write!(f, "Choice({:?})", list),
            Self::Repeat(strat) => write!(f, "Repeat({:?})", strat),
            Self::Try(strat) => write!(f, "Try({:?})", strat),
        }
    }
}

// ── StrategyOutcome ───────────────────────────────────────────────────────────

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum StrategyOutcome {
    /// Strategy successfully executed and committed.
    Success,
    /// Strategy failed. State was rolled back if inside an atomic sequence.
    Failed,
}

// ── Trace ─────────────────────────────────────────────────────────────────────

/// The execution history of a strategy, recording the sequence of rules applied.
#[derive(Debug, Clone, Default)]
pub struct Trace {
    pub applied_rules: Vec<String>,
}

// ── StrategyExecutor ──────────────────────────────────────────────────────────

pub struct StrategyExecutor<'a, T: Clone + fmt::Debug> {
    pub rules: &'a [TypedRewriteRule<T>],
    pub invariants: &'a [EpistemicInvariant<T>],
}

impl<'a, T: Clone + fmt::Debug + PartialEq> StrategyExecutor<'a, T> {
    pub fn new(rules: &'a [TypedRewriteRule<T>], invariants: &'a [EpistemicInvariant<T>]) -> Self {
        Self { rules, invariants }
    }

    /// Evaluates a strategy on the graph. Maintains transactional rollback.
    pub fn execute(
        &self,
        graph: &mut KnowledgeGraph<T>,
        strategy: &Strategy,
        trace: &mut Trace,
    ) -> StrategyOutcome {
        match strategy {
            Strategy::Apply(name) => {
                if let Some(rule) = self.rules.iter().find(|r| r.name == name) {
                    let outcome = graph.rewrite(rule, self.invariants);
                    if outcome == RewriteOutcome::Committed {
                        trace.applied_rules.push(name.clone());
                        StrategyOutcome::Success
                    } else {
                        StrategyOutcome::Failed
                    }
                } else {
                    StrategyOutcome::Failed
                }
            }
            Strategy::Seq(sub_strategies) => {
                // Snapshot entire state for transactional sequence rollback
                let snap_nodes = graph.nodes.clone();
                let snap_edges = graph.edges.clone();
                let snap_trace_len = trace.applied_rules.len();

                for strat in sub_strategies {
                    if self.execute(graph, strat, trace) == StrategyOutcome::Failed {
                        // Rollback state and trace
                        graph.nodes = snap_nodes;
                        graph.edges = snap_edges;
                        trace.applied_rules.truncate(snap_trace_len);
                        return StrategyOutcome::Failed;
                    }
                }
                StrategyOutcome::Success
            }
            Strategy::Choice(sub_strategies) => {
                for strat in sub_strategies {
                    let snap_nodes = graph.nodes.clone();
                    let snap_edges = graph.edges.clone();
                    let snap_trace_len = trace.applied_rules.len();

                    if self.execute(graph, strat, trace) == StrategyOutcome::Success {
                        return StrategyOutcome::Success;
                    }

                    // Rollback this choice's tentative changes before trying next
                    graph.nodes = snap_nodes;
                    graph.edges = snap_edges;
                    trace.applied_rules.truncate(snap_trace_len);
                }
                StrategyOutcome::Failed
            }
            Strategy::Repeat(strat) => {
                loop {
                    let snap_nodes = graph.nodes.clone();
                    let snap_edges = graph.edges.clone();
                    let snap_trace_len = trace.applied_rules.len();

                    if self.execute(graph, strat, trace) == StrategyOutcome::Failed {
                        // Restore state from last successful iteration
                        graph.nodes = snap_nodes;
                        graph.edges = snap_edges;
                        trace.applied_rules.truncate(snap_trace_len);
                        break;
                    }

                    // Check if state actually mutated. If not, break to prevent infinite loops.
                    if graph.nodes.len() == snap_nodes.len()
                        && graph.edges.len() == snap_edges.len()
                    {
                        break;
                    }
                }
                StrategyOutcome::Success
            }
            Strategy::Try(strat) => {
                let snap_nodes = graph.nodes.clone();
                let snap_edges = graph.edges.clone();
                let snap_trace_len = trace.applied_rules.len();

                if self.execute(graph, strat, trace) == StrategyOutcome::Failed {
                    graph.nodes = snap_nodes;
                    graph.edges = snap_edges;
                    trace.applied_rules.truncate(snap_trace_len);
                }
                StrategyOutcome::Success
            }
        }
    }
}

// ── PathFinder / Planner ──────────────────────────────────────────────────────

/// Traverses the state space using BFS to find a sequence of rule applications
/// that drives the graph to satisfy `goal_predicate` without violating invariants.
pub struct PathFinder<'a, T: Clone + fmt::Debug> {
    pub rules: &'a [TypedRewriteRule<T>],
    pub invariants: &'a [EpistemicInvariant<T>],
}

impl<'a, T: Clone + fmt::Debug + PartialEq> PathFinder<'a, T> {
    pub fn new(rules: &'a [TypedRewriteRule<T>], invariants: &'a [EpistemicInvariant<T>]) -> Self {
        Self { rules, invariants }
    }

    /// BFS search for the shortest path of rewrites satisfying the goal.
    ///
    /// To ensure termination, graphs are serialized to a footprint hash (node count + edge count + values representation).
    pub fn find_path(
        &self,
        initial_graph: &KnowledgeGraph<T>,
        goal_predicate: fn(&KnowledgeGraph<T>) -> bool,
        max_depth: usize,
    ) -> Option<Trace> {
        if goal_predicate(initial_graph) {
            return Some(Trace::default());
        }

        // BFS queue: (CurrentGraph, TraceAccumulator, Depth)
        let mut queue = VecDeque::new();
        queue.push_back((initial_graph.clone(), Trace::default(), 0));

        let mut visited_states = HashSet::new();
        visited_states.insert(self.compute_graph_footprint(initial_graph));

        while let Some((graph, trace, depth)) = queue.pop_front() {
            if depth >= max_depth {
                continue;
            }

            for rule in self.rules {
                let mut next_graph = graph.clone();
                let outcome = next_graph.rewrite(rule, self.invariants);

                if outcome == RewriteOutcome::Committed {
                    let footprint = self.compute_graph_footprint(&next_graph);
                    if visited_states.insert(footprint) {
                        let mut next_trace = trace.clone();
                        next_trace.applied_rules.push(rule.name.to_string());

                        if goal_predicate(&next_graph) {
                            return Some(next_trace);
                        }

                        queue.push_back((next_graph, next_trace, depth + 1));
                    }
                }
            }
        }

        None
    }

    /// Simplified graph structural serialization.
    fn compute_graph_footprint(&self, g: &KnowledgeGraph<T>) -> String {
        // Formatted footprint of nodes and edges structure
        let mut node_reprs = Vec::new();
        for n in &g.nodes {
            node_reprs.push(format!("{:?}", n.proposition));
        }
        let mut edge_reprs = Vec::new();
        for e in &g.edges {
            edge_reprs.push(format!("{}-{:?}-{}", e.source, e.kind, e.target));
        }
        format!("N:{:?}|E:{:?}", node_reprs, edge_reprs)
    }
}

// ── Tests ─────────────────────────────────────────────────────────────────────

#[cfg(test)]
mod tests {
    use super::*;
    use crate::omega0::Judgement;
    use crate::omega1::{invariant_acyclic, EdgeKind};

    fn axiom(v: i32) -> Judgement<i32> {
        Judgement::axiom(v, "test")
    }

    // ── Sample rules ──────────────────────────────────────────────────────────

    fn rule_add_1() -> TypedRewriteRule<i32> {
        TypedRewriteRule {
            name: "add_1",
            precondition: |_| true,
            transform: |g| {
                g.add_node(Judgement::axiom(1, "rule_1"));
            },
        }
    }

    fn rule_add_2() -> TypedRewriteRule<i32> {
        TypedRewriteRule {
            name: "add_2",
            precondition: |_| true,
            transform: |g| {
                g.add_node(Judgement::axiom(2, "rule_2"));
            },
        }
    }

    fn rule_fail() -> TypedRewriteRule<i32> {
        TypedRewriteRule {
            name: "fail",
            precondition: |_| false,
            transform: |_| {},
        }
    }

    fn rule_create_cycle() -> TypedRewriteRule<i32> {
        TypedRewriteRule {
            name: "create_cycle",
            precondition: |g| g.node_count() >= 2,
            transform: |g| {
                let n = g.node_count();
                g.add_edge(n - 1, n - 2, EdgeKind::DerivesFrom, "cycle");
            },
        }
    }

    // ── Test cases ────────────────────────────────────────────────────────────

    #[test]
    fn execute_apply_success() {
        let mut g = KnowledgeGraph::new();
        let rules = [rule_add_1()];
        let exec = StrategyExecutor::new(&rules, &[]);
        let mut trace = Trace::default();

        let outcome = exec.execute(&mut g, &Strategy::Apply("add_1".to_string()), &mut trace);
        assert_eq!(outcome, StrategyOutcome::Success);
        assert_eq!(g.node_count(), 1);
        assert_eq!(trace.applied_rules, vec!["add_1".to_string()]);
    }

    #[test]
    fn execute_apply_fail() {
        let mut g = KnowledgeGraph::new();
        let rules = [rule_fail()];
        let exec = StrategyExecutor::new(&rules, &[]);
        let mut trace = Trace::default();

        let outcome = exec.execute(&mut g, &Strategy::Apply("fail".to_string()), &mut trace);
        assert_eq!(outcome, StrategyOutcome::Failed);
        assert!(g.is_empty());
        assert!(trace.applied_rules.is_empty());
    }

    #[test]
    fn execute_seq_success() {
        let mut g = KnowledgeGraph::new();
        let rules = [rule_add_1(), rule_add_2()];
        let exec = StrategyExecutor::new(&rules, &[]);
        let mut trace = Trace::default();

        let seq = Strategy::Seq(vec![
            Strategy::Apply("add_1".to_string()),
            Strategy::Apply("add_2".to_string()),
        ]);

        let outcome = exec.execute(&mut g, &seq, &mut trace);
        assert_eq!(outcome, StrategyOutcome::Success);
        assert_eq!(g.node_count(), 2);
        assert_eq!(
            trace.applied_rules,
            vec!["add_1".to_string(), "add_2".to_string()]
        );
    }

    #[test]
    fn execute_seq_rollback_on_partial_failure() {
        let mut g = KnowledgeGraph::new();
        let rules = [rule_add_1(), rule_fail()];
        let exec = StrategyExecutor::new(&rules, &[]);
        let mut trace = Trace::default();

        let seq = Strategy::Seq(vec![
            Strategy::Apply("add_1".to_string()),
            Strategy::Apply("fail".to_string()),
        ]);

        let outcome = exec.execute(&mut g, &seq, &mut trace);
        assert_eq!(outcome, StrategyOutcome::Failed);
        // The first rule's node additions must be rolled back completely
        assert_eq!(g.node_count(), 0);
        assert!(trace.applied_rules.is_empty());
    }

    #[test]
    fn execute_choice_first_succeeds() {
        let mut g = KnowledgeGraph::new();
        let rules = [rule_add_1(), rule_add_2()];
        let exec = StrategyExecutor::new(&rules, &[]);
        let mut trace = Trace::default();

        let choice = Strategy::Choice(vec![
            Strategy::Apply("add_1".to_string()),
            Strategy::Apply("add_2".to_string()),
        ]);

        let outcome = exec.execute(&mut g, &choice, &mut trace);
        assert_eq!(outcome, StrategyOutcome::Success);
        assert_eq!(g.node_count(), 1);
        assert_eq!(g.nodes[0].proposition, 1);
        assert_eq!(trace.applied_rules, vec!["add_1".to_string()]);
    }

    #[test]
    fn execute_choice_fallback_succeeds() {
        let mut g = KnowledgeGraph::new();
        let rules = [rule_fail(), rule_add_2()];
        let exec = StrategyExecutor::new(&rules, &[]);
        let mut trace = Trace::default();

        let choice = Strategy::Choice(vec![
            Strategy::Apply("fail".to_string()),
            Strategy::Apply("add_2".to_string()),
        ]);

        let outcome = exec.execute(&mut g, &choice, &mut trace);
        assert_eq!(outcome, StrategyOutcome::Success);
        assert_eq!(g.node_count(), 1);
        assert_eq!(g.nodes[0].proposition, 2);
        assert_eq!(trace.applied_rules, vec!["add_2".to_string()]);
    }

    #[test]
    fn execute_repeat_terminates() {
        let mut g = KnowledgeGraph::new();
        // A rule that adds up to 3 nodes
        let limit_rule = TypedRewriteRule {
            name: "limit_rule",
            precondition: |g| g.node_count() < 3,
            transform: |g| {
                g.add_node(Judgement::axiom(100, "limit"));
            },
        };
        let rules = [limit_rule];
        let exec = StrategyExecutor::new(&rules, &[]);
        let mut trace = Trace::default();

        let repeat = Strategy::Repeat(Box::new(Strategy::Apply("limit_rule".to_string())));
        let outcome = exec.execute(&mut g, &repeat, &mut trace);
        assert_eq!(outcome, StrategyOutcome::Success);
        assert_eq!(g.node_count(), 3);
        assert_eq!(trace.applied_rules.len(), 3);
    }

    #[test]
    fn execute_try_suppresses_failure() {
        let mut g = KnowledgeGraph::new();
        let rules = [rule_fail()];
        let exec = StrategyExecutor::new(&rules, &[]);
        let mut trace = Trace::default();

        let outcome = exec.execute(
            &mut g,
            &Strategy::Try(Box::new(Strategy::Apply("fail".to_string()))),
            &mut trace,
        );
        assert_eq!(outcome, StrategyOutcome::Success);
        assert!(g.is_empty());
        assert!(trace.applied_rules.is_empty());
    }

    // ── PathFinder Search Tests ───────────────────────────────────────────────

    #[test]
    fn find_path_reaches_goal() {
        let g = KnowledgeGraph::new();
        let rules = [rule_add_1(), rule_add_2()];
        let pf = PathFinder::new(&rules, &[]);

        // Goal: graph has a node with proposition 2
        let goal = |g: &KnowledgeGraph<i32>| g.nodes.iter().any(|n| n.proposition == 2);

        let trace = pf.find_path(&g, goal, 3);
        assert!(trace.is_some());
        let t = trace.unwrap();
        // Since BFS finds shortest path, it should apply "add_2" directly
        assert_eq!(t.applied_rules, vec!["add_2".to_string()]);
    }

    #[test]
    fn find_path_respects_invariants() {
        let mut g = KnowledgeGraph::new();
        let a = g.add_node(axiom(10));
        let b = g.add_node(axiom(20));
        g.add_edge(a, b, EdgeKind::DerivesFrom, "forward");

        let rules = [rule_create_cycle()];
        let invariants: &[EpistemicInvariant<i32>] = &[invariant_acyclic::<i32>];
        let pf = PathFinder::new(&rules, invariants);

        // Goal: graph has at least one edge
        let goal = |g: &KnowledgeGraph<i32>| g.edge_count() > 1;

        // The only rule is create_cycle which violates the invariant_acyclic.
        // Therefore, the pathfinder should fail to find any path.
        let trace = pf.find_path(&g, goal, 3);
        assert!(trace.is_none());
    }
}
