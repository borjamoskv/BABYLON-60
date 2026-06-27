use epistemic_engine::epistemic;

epistemic! {
    graph pass_fuzz_49 {
        N1 -> N0;
N2 -> N1;
N3 -> N2;
N4 -> N0;
N5 -> N3;
N6 -> N0;
N7 -> N6;
N8 -> N7;
N9 -> N3;
N10 -> N0;
N11 -> N6;
N12 -> N10;
N13 -> N6;
N14 -> N0;
N15 -> N5;
N16 -> N4;
N17 -> N15;
    }
}

fn main() {}
