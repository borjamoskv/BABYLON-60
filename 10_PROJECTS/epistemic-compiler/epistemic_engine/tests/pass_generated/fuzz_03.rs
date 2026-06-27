use epistemic_engine::epistemic;

epistemic! {
    graph pass_fuzz_3 {
        N1 -> N0;
N2 -> N1;
N3 -> N0;
N4 -> N2;
N5 -> N1;
N6 -> N1;
N7 -> N0;
N8 -> N6;
N9 -> N7;
N10 -> N5;
N11 -> N10;
N12 -> N3;
N13 -> N11;
N14 -> N0;
N15 -> N5;
N16 -> N10;
N17 -> N16;
N18 -> N9;
N19 -> N10;
    }
}

fn main() {}
