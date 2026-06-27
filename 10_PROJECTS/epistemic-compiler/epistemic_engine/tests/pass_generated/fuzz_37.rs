use epistemic_engine::epistemic;

epistemic! {
    graph pass_fuzz_37 {
        N1 -> N0;
N2 -> N0;
N3 -> N2;
N4 -> N2;
N5 -> N3;
N6 -> N4;
N7 -> N5;
N8 -> N7;
N9 -> N8;
N10 -> N2;
N11 -> N2;
N12 -> N3;
N13 -> N11;
N14 -> N6;
N15 -> N2;
N16 -> N15;
N17 -> N7;
N18 -> N0;
N19 -> N6;
    }
}

fn main() {}
