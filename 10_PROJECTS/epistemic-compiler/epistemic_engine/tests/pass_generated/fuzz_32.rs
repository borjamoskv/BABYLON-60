use epistemic_engine::epistemic;

epistemic! {
    graph pass_fuzz_32 {
        N1 -> N0;
N2 -> N1;
N3 -> N1;
N4 -> N0;
N5 -> N1;
N6 -> N1;
N7 -> N6;
N8 -> N5;
N9 -> N4;
N10 -> N7;
N11 -> N10;
N12 -> N2;
N13 -> N4;
N14 -> N11;
N15 -> N13;
N16 -> N4;
N17 -> N7;
    }
}

fn main() {}
