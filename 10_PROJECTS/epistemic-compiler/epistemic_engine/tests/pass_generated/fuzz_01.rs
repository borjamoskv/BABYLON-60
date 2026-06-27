use epistemic_engine::epistemic;

epistemic! {
    graph pass_fuzz_1 {
        N1 -> N0;
N2 -> N1;
N3 -> N2;
N4 -> N3;
    }
}

fn main() {}
