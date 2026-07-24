
use crate::omega0::{Justification, JustifiedStatement, verify};
use std::collections::BTreeSet;

pub enum AtmsError {
    InvalidNode(NodeId),
}

impl std::fmt::Display for AtmsError {
    fn fmt(&self, f: &mut std::fmt::Formatter) -> std::fmt::Result {
        match self {
            AtmsError::InvalidNode(id) => write!(f, "Invalid node ID: {}", id),
        }
    }
}

impl std::error::Error for AtmsError {}


pub type AssumptionId = usize;
pub type NodeId = usize;

pub struct Environment {
    assumptions: BTreeSet<AssumptionId>,
}

impl Environment {
    pub fn empty() -> Self {
        Environment {
            assumptions: BTreeSet::new(),
        }
    }

    pub fn singleton(a: AssumptionId) -> Self {
        let mut s = BTreeSet::new();
        s.insert(a);
        Environment { assumptions: s }
    }

    pub fn from_assumptions<I: IntoIterator<Item = AssumptionId>>(it: I) -> Self {
        Environment {
            assumptions: it.into_iter().collect(),
        }
    }

    pub fn is_subset(&self, other: &Environment) -> bool {
        self.assumptions.is_subset(&other.assumptions)
    }

    pub fn union(&self, other: &Environment) -> Environment {
        Environment {
            assumptions: self.assumptions.union(&other.assumptions).copied().collect(),
        }
    }

    pub fn len(&self) -> usize {
        self.assumptions.len()
    }

    pub fn is_empty(&self) -> bool {
        self.assumptions.is_empty()
    }

    pub fn assumptions(&self) -> impl Iterator<Item = AssumptionId> + '_ {
        self.assumptions.iter().copied()
    }
}

struct Node {
    datum: String,
    assumption: Option<AssumptionId>,
    label: Vec<Environment>,
}

struct Justif {
    consequent: NodeId,
    antecedents: Vec<NodeId>,
}

pub struct Atms {
    nodes: Vec<Node>,
    assumption_nodes: Vec<NodeId>,
    justifs: Vec<Justif>,
    nogoods: Vec<Environment>,
    contradiction: NodeId,
}

impl Default for Atms {
    fn default() -> Self {
        Self::new()
    }
}

impl Atms {
    pub fn new() -> Self {
        let contradiction = Node {
            datum: "⊥".into(),
            assumption: None,
            label: Vec::new(),
        };
        Atms {
            nodes: vec![contradiction],
            assumption_nodes: Vec::new(),
            justifs: Vec::new(),
            nogoods: Vec::new(),
            contradiction: 0,
        }
    }


    pub fn add_assumption(&mut self, datum: &str) -> NodeId {
        let aid = self.assumption_nodes.len();
        let nid = self.nodes.len();
        self.nodes.push(Node {
            datum: datum.into(),
            assumption: Some(aid),
            label: vec![Environment::singleton(aid)],
        });
        self.assumption_nodes.push(nid);
        nid
    }

    pub fn add_premise(&mut self, datum: &str) -> NodeId {
        let nid = self.nodes.len();
        self.nodes.push(Node {
            datum: datum.into(),
            assumption: None,
            label: vec![Environment::empty()],
        });
        nid
    }

    pub fn add_node(&mut self, datum: &str) -> NodeId {
        let nid = self.nodes.len();
        self.nodes.push(Node {
            datum: datum.into(),
            assumption: None,
            label: Vec::new(),
        });
        nid
    }

    pub fn justify(&mut self, consequent: NodeId, antecedents: &[NodeId]) {
        self.justifs.push(Justif {
            consequent,
            antecedents: antecedents.to_vec(),
        });
        self.propagate();
    }

    pub fn contradict(&mut self, antecedents: &[NodeId]) {
        let c = self.contradiction;
        self.justify(c, antecedents);
    }


    pub fn label(&self, node: NodeId) -> Result<&[Environment], AtmsError> {
        self.nodes.get(node).map(|n| n.label.as_slice()).ok_or(AtmsError::InvalidNode(node))
    }

    pub fn datum(&self, node: NodeId) -> &str {
        &self.nodes[node].datum
    }

    pub fn find_node_by_datum(&self, datum: &str) -> Option<NodeId> {
        self.nodes.iter().position(|n| n.datum == datum)
    }

    pub fn assumption_of(&self, node: NodeId) -> Option<AssumptionId> {
        self.nodes[node].assumption
    }

    pub fn is_believed(&self, node: NodeId) -> bool {
        !self.nodes[node].label.is_empty()
    }

    pub fn is_consistent(&self, env: &Environment) -> bool {
        !self.nogoods.iter().any(|ng| ng.is_subset(env))
    }

    pub fn holds_in(&self, node: NodeId, env: &Environment) -> bool {
        self.is_consistent(env) && self.nodes[node].label.iter().any(|l| l.is_subset(env))
    }

    pub fn nogoods(&self) -> &[Environment] {
        &self.nogoods
    }

    pub fn minimal_conflicts(&self, env: &Environment) -> Vec<Environment> {
        self.nogoods
            .iter()
            .filter(|ng| ng.is_subset(env))
            .cloned()
            .collect()
    }

    pub fn culprits(&self, env: &Environment) -> BTreeSet<AssumptionId> {
        let mut c = BTreeSet::new();
        for ng in self.minimal_conflicts(env) {
            for a in ng.assumptions() {
                c.insert(a);
            }
        }
        c
    }


    pub fn install(&mut self, js: &JustifiedStatement) -> NodeId {
        match &js.justification {
            Justification::Conjecture => self.add_assumption(&js.statement.content),
            _ if verify(js) => self.add_premise(&js.statement.content),
            _ => self.add_node(&js.statement.content),
        }
    }

    pub fn contradiction_free(&self, node: NodeId) -> bool {
        self.is_believed(node)
    }


    fn propagate(&mut self) {
        for _ in 0..100_000 {
            if !self.step() {
                return;
            }
        }
        debug_assert!(false, "ATMS failed to reach a fixpoint");
    }

    fn step(&mut self) -> bool {
        let mut changed = false;
        let justifs = self.justifs.clone();
        for j in &justifs {
            let contrib = self.contributions(j);
            if j.consequent == self.contradiction {
                for env in contrib {
                    if self.add_nogood(env) {
                        changed = true;
                    }
                }
            } else {
                for env in contrib {
                    if self.add_to_label(j.consequent, env) {
                        changed = true;
                    }
                }
            }
        }
        if self.prune_labels() {
            changed = true;
        }
        changed
    }

    fn contributions(&self, j: &Justif) -> Vec<Environment> {
        let mut acc = vec![Environment::empty()];
        for &ant in &j.antecedents {
            let lbl = &self.nodes[ant].label;
            if lbl.is_empty() {
                return Vec::new(); // an unsupported antecedent kills the support
            }
            let mut next = Vec::new();
            for base in &acc {
                for e in lbl {
                    let u = base.union(e);
                    if self.is_consistent(&u) {
                        next.push(u);
                    }
                }
            }
            acc = minimize(next);
            if acc.is_empty() {
                return Vec::new();
            }
        }
        acc
    }

    fn add_to_label(&mut self, node: NodeId, env: Environment) -> bool {
        if !self.is_consistent(&env) {
            return false;
        }
        let lbl = &self.nodes[node].label;
        if lbl.iter().any(|e| e.is_subset(&env)) {
            return false; // env is subsumed → not minimal
        }
        let mut new_label: Vec<Environment> =
            lbl.iter().filter(|e| !env.is_subset(e)).cloned().collect();
        new_label.push(env);
        self.nodes[node].label = new_label;
        true
    }

    fn add_nogood(&mut self, env: Environment) -> bool {
        if self.nogoods.iter().any(|ng| ng.is_subset(&env)) {
            return false; // already covered by a smaller nogood
        }
        self.nogoods.retain(|ng| !env.is_subset(ng)); // drop supersets
        self.nogoods.push(env);
        true
    }

    fn prune_labels(&mut self) -> bool {
        let mut changed = false;
        let nogoods = self.nogoods.clone();
        for node in &mut self.nodes {
            let before = node.label.len();
            node.label
                .retain(|e| !nogoods.iter().any(|ng| ng.is_subset(e)));
            if node.label.len() != before {
                changed = true;
            }
        }
        changed
    }
}

fn minimize(envs: Vec<Environment>) -> Vec<Environment> {
    let mut uniq: Vec<Environment> = Vec::new();
    for e in envs {
        if !uniq.contains(&e) {
            uniq.push(e);
        }
    }
    let mut result: Vec<Environment> = Vec::new();
    for (i, e) in uniq.iter().enumerate() {
        let has_proper_subset = uniq
            .iter()
            .enumerate()
            .any(|(k, o)| k != i && o.is_subset(e) && o != e);
        if !has_proper_subset {
            result.push(e.clone());
        }
    }
    result
}


mod tests {
    use super::*;
    use crate::omega0::{Modality, Statement};

    fn env(xs: &[AssumptionId]) -> Environment {
        Environment::from_assumptions(xs.iter().copied())
    }

    fn assumptions_get_singleton_labels() {
        let mut a = Atms::new();
        let x = a.add_assumption("x");
        let y = a.add_assumption("y");
        assert_eq!(a.label(x).unwrap(), &[env(&[0])]);
        assert_eq!(a.label(y).unwrap(), &[env(&[1])]);
    }

    fn disjunctive_support_unions_labels() {
        let mut a = Atms::new();
        let x = a.add_assumption("x");
        let y = a.add_assumption("y");
        let c = a.add_node("c");
        a.justify(c, &[x]);
        a.justify(c, &[y]);
        let lbl = a.label(c).unwrap();
        assert_eq!(lbl.len(), 2);
        assert!(lbl.contains(&env(&[0])));
        assert!(lbl.contains(&env(&[1])));
    }

    fn conjunctive_support_unions_assumptions() {
        let mut a = Atms::new();
        let x = a.add_assumption("x");
        let y = a.add_assumption("y");
        let c = a.add_node("c");
        a.justify(c, &[x, y]);
        assert_eq!(a.label(c).unwrap(), &[env(&[0, 1])]);
    }

    fn premise_holds_in_empty_env() {
        let mut a = Atms::new();
        let p = a.add_premise("p");
        assert!(a.holds_in(p, &Environment::empty()));
        assert!(a.is_believed(p));
    }

    fn nogood_kills_the_label_and_marks_inconsistent() {
        let mut a = Atms::new();
        let x = a.add_assumption("x");
        let y = a.add_assumption("y");
        let c = a.add_node("c");
        a.justify(c, &[x, y]); // label(c) = {{x,y}}
        assert_eq!(a.label(c).unwrap(), &[env(&[0, 1])]);

        a.contradict(&[x, y]); // {x,y} is nogood
        assert!(a.label(c).unwrap().is_empty(), "contradiction must erase support");
        assert!(!a.is_consistent(&env(&[0, 1])));
        assert!(a.is_consistent(&env(&[0]))); // {x} alone is still fine
    }

    fn nogood_subset_prunes_supersets() {
        let mut a = Atms::new();
        let x = a.add_assumption("x");
        let y = a.add_assumption("y");
        let c = a.add_node("c");
        a.justify(c, &[x, y]); // {x,y}
        a.contradict(&[x]); // {x} nogood ⇒ {x,y} also inconsistent
        assert!(a.label(c).unwrap().is_empty());
        assert!(!a.is_consistent(&env(&[0, 1])));
    }

    fn holds_in_is_monotone_over_consistent_supersets() {
        let mut a = Atms::new();
        let x = a.add_assumption("x");
        let _y = a.add_assumption("y");
        let c = a.add_node("c");
        a.justify(c, &[x]); // label {x}
        assert!(a.holds_in(c, &env(&[0])));
        assert!(a.holds_in(c, &env(&[0, 1]))); // superset, still consistent
    }

    fn ddb_reports_culprits_not_chronology() {
        let mut a = Atms::new();
        let x = a.add_assumption("x");
        let y = a.add_assumption("y");
        let _z = a.add_assumption("z"); // most-recent choice (assumption id 2) — but innocent
        let c = a.add_node("c");
        a.justify(c, &[x, y]);
        a.contradict(&[x, y]); // culprit set is {x,y}, NOT z
        let culprits = a.culprits(&env(&[0, 1, 2]));
        assert!(culprits.contains(&0) && culprits.contains(&1));
        assert!(!culprits.contains(&2), "z is innocent; DDB must not blame it");
    }

    fn bridge_conjecture_becomes_assumption_and_contradiction_free_tracks_nogoods() {
        let mut a = Atms::new();
        let conj = JustifiedStatement {
            statement: Statement {
                content: "H".into(),
                modality: Modality::Epistemic,
                obligations: vec![],
            },
            justification: Justification::Conjecture,
        };
        let h = a.install(&conj);
        assert!(a.contradiction_free(h));
        a.contradict(&[h]);
        assert!(!a.contradiction_free(h), "nogood must revoke contradiction-freedom");
    }
}


mod laws {
    use super::*;
    use proptest::prelude::*;

    const N_ASSUM: usize = 4;
    const N_DERIVED: usize = 3;
    const N_NODES: usize = N_ASSUM + N_DERIVED; // highest referenceable node id

    enum Op {
        Justify(usize, Vec<usize>),
        Contradict(Vec<usize>),
    }

    fn arb_ops() -> impl Strategy<Value = Vec<Op>> {
        let ant = prop::collection::vec(1..=N_NODES, 1..=3);
        let op = prop_oneof![
            (N_ASSUM + 1..=N_NODES, ant.clone()).prop_map(|(c, a)| Op::Justify(c, a)),
            ant.prop_map(Op::Contradict),
        ];
        prop::collection::vec(op, 0..12)
    }

    fn build(ops: &[Op]) -> Atms {
        let mut a = Atms::new();
        for i in 0..N_ASSUM {
            a.add_assumption(&format!("a{i}"));
        }
        for i in 0..N_DERIVED {
            a.add_node(&format!("d{i}"));
        }
        for op in ops {
            match op {
                Op::Justify(c, ants) => a.justify(*c, ants),
                Op::Contradict(ants) => a.contradict(ants),
            }
        }
        a
    }

    proptest! {
        fn labels_are_antichains(ops in arb_ops()) {
            let a = build(&ops);
            for node in 0..a.nodes.len() {
                let lbl = a.label(node).unwrap();
                for i in 0..lbl.len() {
                    for k in 0..lbl.len() {
                        if i != k {
                            prop_assert!(!(lbl[i].is_subset(&lbl[k]) && lbl[i] != lbl[k]),
                                "label of node {} not minimal: {:?} ⊆ {:?}", node, lbl[i], lbl[k]);
                        }
                    }
                }
            }
        }

        fn labels_avoid_nogoods(ops in arb_ops()) {
            let a = build(&ops);
            for node in 0..a.nodes.len() {
                for e in a.label(node).unwrap() {
                    prop_assert!(a.is_consistent(e),
                        "node {} retains inconsistent env {:?}", node, e);
                }
            }
        }

        fn nogoods_are_minimal(ops in arb_ops()) {
            let a = build(&ops);
            let ng = a.nogoods();
            for i in 0..ng.len() {
                for k in 0..ng.len() {
                    if i != k {
                        prop_assert!(!(ng[i].is_subset(&ng[k]) && ng[i] != ng[k]),
                            "nogood {:?} subsumes {:?}", ng[i], ng[k]);
                    }
                }
            }
        }

        fn justified_consequents_are_covered(ops in arb_ops()) {
            let a = build(&ops);
            for j in &a.justifs {
                if j.consequent == a.contradiction {
                    continue;
                }
                let mut unions = vec![Environment::empty()];
                let mut dead = false;
                for &ant in &j.antecedents {
                    let lbl = a.label(ant).unwrap();
                    if lbl.is_empty() { dead = true; break; }
                    let mut next = Vec::new();
                    for base in &unions {
                        for e in lbl {
                            next.push(base.union(e));
                        }
                    }
                    unions = next;
                }
                if dead { continue; }
                for u in unions {
                    if a.is_consistent(&u) {
                        let covered = a.label(j.consequent).unwrap().iter().any(|l| l.is_subset(&u));
                        prop_assert!(covered,
                            "consequent {} not covered for consistent env {:?}", j.consequent, u);
                    }
                }
            }
        }
    }
}
