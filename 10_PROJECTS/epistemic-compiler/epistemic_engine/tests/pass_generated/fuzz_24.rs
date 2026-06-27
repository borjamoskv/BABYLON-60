use epistemic_engine::epistemic;

epistemic! {
    graph pass_fuzz_24 {
        N1 -> N0;
N2 -> N1;
N3 -> N2;
N4 -> N1;
    }
}

fn main() {}
