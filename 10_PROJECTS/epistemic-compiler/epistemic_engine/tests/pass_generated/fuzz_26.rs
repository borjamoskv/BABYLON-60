use epistemic_engine::epistemic;

epistemic! {
    graph pass_fuzz_26 {
        N1 -> N0;
N2 -> N1;
N3 -> N1;
N4 -> N1;
N5 -> N0;
N6 -> N2;
    }
}

fn main() {}
