use epistemic_engine::epistemic;

epistemic! {
    graph pass_fuzz_43 {
        N1 -> N0;
N2 -> N1;
N3 -> N1;
N4 -> N2;
N5 -> N3;
N6 -> N1;
N7 -> N6;
N8 -> N7;
N9 -> N5;
N10 -> N8;
N11 -> N7;
N12 -> N7;
N13 -> N10;
N14 -> N8;
N15 -> N1;
N16 -> N15;
N17 -> N2;
N18 -> N14;
N19 -> N14;
    }
}

fn main() {}
