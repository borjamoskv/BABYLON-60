use epistemic_engine::epistemic;

epistemic! {
    graph broken {
        A -> B;
        B -> C;
        C -> A;
    }
}

fn main() {}
