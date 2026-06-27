use epistemic_engine::epistemic;

epistemic! {
    graph bad_syntax {
        A -> B // FALTA PUNTO Y COMA
    }
}

fn main() {}
