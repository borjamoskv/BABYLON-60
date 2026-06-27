use epistemic_engine::epistemic;

epistemic! {
    graph pass_fuzz_31 {
        N1 -> N0;
N2 -> N0;
N3 -> N2;
N4 -> N1;
N5 -> N1;
N6 -> N2;
N7 -> N1;
N8 -> N6;
N9 -> N2;
N10 -> N7;
N11 -> N2;
N12 -> N9;
N13 -> N7;
N14 -> N10;
N15 -> N9;
N16 -> N15;
    }
}

fn main() {}
