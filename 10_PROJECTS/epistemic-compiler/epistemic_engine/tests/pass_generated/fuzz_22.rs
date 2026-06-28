use epistemic_engine::epistemic;

epistemic! {
    graph pass_fuzz_22 {
        N1 -> N0;
N2 -> N0;
N3 -> N2;
N4 -> N2;
N5 -> N3;
N6 -> N3;
N7 -> N1;
N8 -> N0;
    }
}

fn main() {}
