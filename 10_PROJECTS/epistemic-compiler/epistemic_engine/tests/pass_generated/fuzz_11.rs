use epistemic_engine::epistemic;

epistemic! {
    graph pass_fuzz_11 {
        N1 -> N0;
N2 -> N0;
N3 -> N0;
N4 -> N3;
N5 -> N2;
N6 -> N4;
N7 -> N4;
N8 -> N7;
N9 -> N2;
N10 -> N1;
    }
}

fn main() {}
