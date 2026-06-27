use epistemic_engine::epistemic;

epistemic! {
    graph pass_fuzz_28 {
        N1 -> N0;
N2 -> N0;
N3 -> N1;
N4 -> N2;
N5 -> N4;
N6 -> N2;
N7 -> N3;
N8 -> N3;
N9 -> N4;
N10 -> N3;
N11 -> N8;
N12 -> N4;
N13 -> N7;
N14 -> N2;
N15 -> N11;
N16 -> N1;
N17 -> N10;
    }
}

fn main() {}
