use epistemic_engine::epistemic;

epistemic! {
    graph pass_fuzz_21 {
        N1 -> N0;
N2 -> N0;
N3 -> N2;
N4 -> N1;
N5 -> N4;
N6 -> N3;
N7 -> N0;
N8 -> N5;
N9 -> N7;
N10 -> N3;
N11 -> N3;
    }
}

fn main() {}
