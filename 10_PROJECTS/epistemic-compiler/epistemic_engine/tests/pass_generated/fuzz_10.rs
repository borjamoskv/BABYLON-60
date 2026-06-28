use epistemic_engine::epistemic;

epistemic! {
    graph pass_fuzz_10 {
        N1 -> N0;
N2 -> N0;
N3 -> N1;
N4 -> N3;
N5 -> N1;
    }
}

fn main() {}
