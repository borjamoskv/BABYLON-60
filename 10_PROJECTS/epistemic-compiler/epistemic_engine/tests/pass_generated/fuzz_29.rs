use epistemic_engine::epistemic;

epistemic! {
    graph pass_fuzz_29 {
        N1 -> N0;
N2 -> N1;
N3 -> N0;
N4 -> N0;
N5 -> N2;
N6 -> N2;
N7 -> N4;
N8 -> N3;
N9 -> N5;
N10 -> N1;
N11 -> N7;
    }
}

fn main() {}
