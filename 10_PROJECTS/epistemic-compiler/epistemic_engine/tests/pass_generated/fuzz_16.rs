use epistemic_engine::epistemic;

epistemic! {
    graph pass_fuzz_16 {
        N1 -> N0;
N2 -> N1;
N3 -> N0;
N4 -> N0;
N5 -> N1;
N6 -> N1;
N7 -> N2;
    }
}

fn main() {}
