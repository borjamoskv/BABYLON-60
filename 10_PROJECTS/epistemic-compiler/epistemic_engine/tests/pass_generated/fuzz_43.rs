use epistemic_engine::epistemic;

epistemic! {
    graph pass_fuzz_43 {
        N1 -> N0;
N2 -> N0;
N3 -> N1;
N4 -> N3;
N5 -> N1;
N6 -> N3;
N7 -> N2;
N8 -> N7;
N9 -> N8;
N10 -> N0;
N11 -> N5;
N12 -> N7;
N13 -> N7;
N14 -> N13;
N15 -> N11;
N16 -> N1;
N17 -> N3;
N18 -> N8;
N19 -> N5;
    }
}

fn main() {}
