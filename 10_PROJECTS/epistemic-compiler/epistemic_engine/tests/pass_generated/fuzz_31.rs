use epistemic_engine::epistemic;

epistemic! {
    graph pass_fuzz_31 {
        N1 -> N0;
N2 -> N1;
N3 -> N2;
N4 -> N0;
N5 -> N0;
N6 -> N3;
N7 -> N6;
N8 -> N5;
N9 -> N0;
N10 -> N6;
N11 -> N7;
N12 -> N2;
N13 -> N4;
N14 -> N3;
N15 -> N14;
N16 -> N3;
N17 -> N13;
    }
}

fn main() {}
