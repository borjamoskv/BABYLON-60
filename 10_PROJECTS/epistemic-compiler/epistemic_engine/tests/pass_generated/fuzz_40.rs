use epistemic_engine::epistemic;

epistemic! {
    graph pass_fuzz_40 {
        N1 -> N0;
N2 -> N1;
N3 -> N2;
N4 -> N3;
N5 -> N0;
N6 -> N1;
N7 -> N1;
N8 -> N3;
N9 -> N5;
N10 -> N0;
N11 -> N0;
N12 -> N4;
N13 -> N6;
N14 -> N13;
N15 -> N7;
N16 -> N6;
N17 -> N7;
    }
}

fn main() {}
