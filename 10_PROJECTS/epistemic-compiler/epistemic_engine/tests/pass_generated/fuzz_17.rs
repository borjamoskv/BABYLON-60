use epistemic_engine::epistemic;

epistemic! {
    graph pass_fuzz_17 {
        N1 -> N0;
N2 -> N0;
N3 -> N0;
N4 -> N0;
N5 -> N3;
    }
}

fn main() {}
