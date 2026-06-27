use epistemic_engine::epistemic;

epistemic! {
    graph pass_fuzz_4 {
        N1 -> N0;
N2 -> N1;
N3 -> N2;
N4 -> N0;
N5 -> N0;
N6 -> N2;
N7 -> N2;
N8 -> N2;
N9 -> N7;
N10 -> N1;
N11 -> N8;
N12 -> N3;
N13 -> N2;
N14 -> N12;
N15 -> N13;
N16 -> N15;
N17 -> N16;
    }
}

fn main() {}
