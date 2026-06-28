use epistemic_engine::epistemic;

epistemic! {
    graph pass_fuzz_35 {
        N1 -> N0;
N2 -> N0;
N3 -> N1;
N4 -> N1;
N5 -> N4;
N6 -> N1;
N7 -> N2;
N8 -> N7;
N9 -> N6;
N10 -> N2;
N11 -> N0;
N12 -> N9;
N13 -> N1;
N14 -> N13;
N15 -> N6;
N16 -> N15;
N17 -> N14;
N18 -> N9;
N19 -> N6;
    }
}

fn main() {}
