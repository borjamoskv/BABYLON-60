use epistemic_engine::epistemic;

epistemic! {
    graph pass_fuzz_15 {
        N1 -> N0;
N2 -> N1;
N3 -> N1;
N4 -> N1;
N5 -> N0;
N6 -> N2;
N7 -> N6;
N8 -> N7;
N9 -> N3;
N10 -> N7;
N11 -> N10;
N12 -> N6;
N13 -> N0;
N14 -> N11;
N15 -> N9;
N16 -> N2;
N17 -> N16;
    }
}

fn main() {}
