use epistemic_engine::epistemic;

epistemic! {
    graph pass_fuzz_33 {
        N1 -> N0;
N2 -> N0;
N3 -> N0;
N4 -> N0;
N5 -> N3;
N6 -> N5;
N7 -> N0;
N8 -> N7;
N9 -> N7;
N10 -> N8;
    }
}

fn main() {}
