use epistemic_engine::epistemic;

epistemic! {
    graph pass_fuzz_29 {
        N1 -> N0;
N2 -> N1;
N3 -> N1;
N4 -> N2;
N5 -> N3;
N6 -> N1;
N7 -> N6;
N8 -> N4;
N9 -> N8;
N10 -> N9;
N11 -> N1;
N12 -> N5;
N13 -> N8;
N14 -> N1;
N15 -> N10;
N16 -> N3;
N17 -> N12;
N18 -> N2;
N19 -> N9;
    }
}

fn main() {}
