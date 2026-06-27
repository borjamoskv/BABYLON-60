use epistemic_engine::epistemic;

epistemic! {
    graph pass_fuzz_21 {
        N1 -> N0;
N2 -> N1;
N3 -> N0;
N4 -> N0;
    }
}

fn main() {}
