use epistemic_engine::epistemic;

epistemic! {
    graph self_referential {
        NodeA -> NodeB;
        NodeB -> NodeB; // Ciclo directo!
    }
}

fn main() {}
