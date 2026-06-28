use epistemic_engine::epistemic;

epistemic! {
    graph pass_fuzz_30 {
        N1 -> N0;
N2 -> N1;
N3 -> N0;
N4 -> N0;
N5 -> N2;
N6 -> N1;
N7 -> N2;
N8 -> N3;
N9 -> N4;
N10 -> N7;
N11 -> N8;
N12 -> N0;
N13 -> N6;
N14 -> N3;
N15 -> N5;
N16 -> N1;
    }
}

fn main() {}
