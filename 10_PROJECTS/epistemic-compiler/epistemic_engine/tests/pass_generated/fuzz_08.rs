use epistemic_engine::epistemic;

epistemic! {
    graph pass_fuzz_8 {
        N1 -> N0;
N2 -> N0;
N3 -> N2;
N4 -> N1;
N5 -> N0;
N6 -> N4;
N7 -> N1;
N8 -> N2;
N9 -> N2;
N10 -> N5;
N11 -> N10;
N12 -> N3;
N13 -> N8;
N14 -> N2;
N15 -> N2;
N16 -> N4;
    }
}

fn main() {}
