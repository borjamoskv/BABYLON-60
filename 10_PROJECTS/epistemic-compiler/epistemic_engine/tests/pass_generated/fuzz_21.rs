use epistemic_engine::epistemic;

epistemic! {
    graph pass_fuzz_21 {
        N1 -> N0;
N2 -> N1;
N3 -> N1;
N4 -> N3;
N5 -> N2;
N6 -> N2;
N7 -> N1;
N8 -> N2;
N9 -> N8;
N10 -> N3;
N11 -> N3;
N12 -> N10;
N13 -> N10;
N14 -> N4;
N15 -> N6;
N16 -> N9;
    }
}

fn main() {}
