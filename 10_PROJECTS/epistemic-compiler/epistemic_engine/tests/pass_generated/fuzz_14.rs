use epistemic_engine::epistemic;

epistemic! {
    graph pass_fuzz_14 {
        N1 -> N0;
N2 -> N0;
N3 -> N2;
N4 -> N2;
N5 -> N2;
N6 -> N5;
N7 -> N3;
N8 -> N5;
N9 -> N2;
N10 -> N0;
N11 -> N7;
N12 -> N8;
N13 -> N12;
N14 -> N0;
N15 -> N6;
N16 -> N10;
N17 -> N5;
N18 -> N4;
N19 -> N11;
    }
}

fn main() {}
